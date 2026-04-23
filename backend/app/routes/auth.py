from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
import redis as redis_lib

from app.database import get_db
from app.models import User, UserRole, AuditLog
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Redis client — used for refresh token storage and access token blacklist
_redis = redis_lib.from_url(settings.redis_url, decode_responses=True)

# Redis key prefixes
_REFRESH_PREFIX = "refresh:"   # refresh:{uuid} → user_id  (TTL = 30 days)
_BLACKLIST_PREFIX = "bl:"      # bl:{jti}       → "1"       (TTL = remaining access token life)


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Token helpers ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> tuple[str, str]:
    """Return (encoded_jwt, jti). JTI is stored for blacklisting on logout."""
    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "jti": jti, "exp": expire, "type": "access"}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def create_refresh_token(user_id: int) -> str:
    """Store a random UUID in Redis → user_id with TTL and return it."""
    token = str(uuid.uuid4())
    ttl = int(timedelta(days=settings.refresh_token_expire_days).total_seconds())
    _redis.setex(f"{_REFRESH_PREFIX}{token}", ttl, str(user_id))
    return token


def blacklist_access_token(jti: str, exp: datetime) -> None:
    """Add the JTI to the Redis blacklist until the token naturally expires."""
    remaining = int((exp - datetime.utcnow()).total_seconds())
    if remaining > 0:
        _redis.setex(f"{_BLACKLIST_PREFIX}{jti}", remaining, "1")


def is_blacklisted(jti: str) -> bool:
    return _redis.exists(f"{_BLACKLIST_PREFIX}{jti}") == 1


# ── Auth dependency ───────────────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type")

        if not user_id or not jti or token_type != "access":
            raise credentials_exception

        if is_blacklisted(jti):
            raise credentials_exception

        exp = datetime.utcfromtimestamp(payload["exp"])

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if user is None:
        raise credentials_exception

    # Attach exp + jti to user object for use in /logout without re-decoding
    user._token_jti = jti
    user._token_exp = exp
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.manager,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(AuditLog(user_id=user.id, action="signup", resource_type="user", resource_id=user.id))
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username, User.is_active == True).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token, _ = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    db.add(AuditLog(user_id=user.id, action="login", resource_type="user", resource_id=user.id))
    db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Issue a new access token (and rotate the refresh token) if the refresh token is valid."""
    key = f"{_REFRESH_PREFIX}{payload.refresh_token}"
    user_id_str = _redis.get(key)

    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == int(user_id_str), User.is_active == True).first()
    if not user:
        _redis.delete(key)
        raise HTTPException(status_code=401, detail="User not found")

    # Rotate: delete old refresh token, issue new pair
    _redis.delete(key)
    access_token, _ = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=200)
def logout(
    payload: RefreshRequest,
    current_user: User = Depends(get_current_user),
):
    """Invalidate both the current access token (via blacklist) and the refresh token."""
    # Blacklist access token until it naturally expires
    blacklist_access_token(current_user._token_jti, current_user._token_exp)

    # Delete refresh token from Redis
    _redis.delete(f"{_REFRESH_PREFIX}{payload.refresh_token}")

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = {"full_name"}
    for key, value in payload.items():
        if key in allowed:
            setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user
