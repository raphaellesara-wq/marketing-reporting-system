from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import Client, User
from app.routes.auth import get_current_user
from app.security.tenancy import get_owned_client

router = APIRouter(prefix="/clients", tags=["Clients"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    brand_color_primary: Optional[str] = "#3B82F6"
    brand_color_secondary: Optional[str] = "#1E40AF"


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    brand_color_primary: Optional[str] = None
    brand_color_secondary: Optional[str] = None
    is_active: Optional[bool] = None


class ClientResponse(BaseModel):
    id: int
    name: str
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    logo_url: Optional[str]
    brand_color_primary: str
    brand_color_secondary: str
    is_active: bool
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ClientResponse])
def list_clients(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Client)
        .filter(Client.owner_id == current_user.id, Client.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(
    payload: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = Client(**payload.model_dump(), owner_id=current_user.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client: Client = Depends(get_owned_client)):
    return client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    payload: ClientUpdate,
    client: Client = Depends(get_owned_client),
    db: Session = Depends(get_db),
):
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client: Client = Depends(get_owned_client),
    db: Session = Depends(get_db),
):
    client.is_active = False
    db.commit()
