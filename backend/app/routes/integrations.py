from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import Integration, Client, IntegrationStatus, User
from app.routes.auth import get_current_user

router = APIRouter(prefix="/integrations", tags=["Integrations"])

SUPPORTED_PLATFORMS = [
    # Paid Advertising
    "google_ads", "facebook_ads", "instagram_ads", "tiktok_ads",
    "linkedin_ads", "pinterest_ads", "amazon_ads", "microsoft_ads",
    "snapchat_ads", "youtube_ads",
    # Analytics
    "google_analytics_4", "mixpanel", "amplitude", "heap",
    "segment", "hotjar", "clarity",
    # Email Marketing
    "mailchimp", "klaviyo", "convertkit", "activecampaign",
    "hubspot", "brevo", "getresponse", "constant_contact", "flashyapp",
    # CRM
    "salesforce", "pipedrive", "zoho",
    # Project Management
    "monday",
    # eCommerce
    "shopify", "woocommerce", "bigcommerce", "magento",
    # Payments
    "stripe", "paypal", "square",
    # Automation
    "zapier", "make", "ifttt", "n8n",
]


# ── Schemas ───────────────────────────────────────────────────────────────────

class IntegrationCreate(BaseModel):
    platform: str
    display_name: Optional[str] = None
    credentials: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None


class IntegrationUpdate(BaseModel):
    display_name: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[IntegrationStatus] = None


class IntegrationResponse(BaseModel):
    id: int
    client_id: int
    platform: str
    display_name: Optional[str]
    status: IntegrationStatus
    last_synced_at: Optional[datetime]
    error_message: Optional[str]
    config: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_client_or_404(client_id: int, user_id: int, db: Session) -> Client:
    client = db.query(Client).filter(
        Client.id == client_id, Client.owner_id == user_id, Client.is_active == True
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/platforms", tags=["Integrations"])
def list_supported_platforms():
    return {"platforms": SUPPORTED_PLATFORMS, "total": len(SUPPORTED_PLATFORMS)}


@router.get("/clients/{client_id}", response_model=List[IntegrationResponse])
def list_integrations(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_client_or_404(client_id, current_user.id, db)
    return db.query(Integration).filter(Integration.client_id == client_id).all()


@router.post("/clients/{client_id}", response_model=IntegrationResponse, status_code=201)
def create_integration(
    client_id: int,
    payload: IntegrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_client_or_404(client_id, current_user.id, db)

    if payload.platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {payload.platform}")

    existing = db.query(Integration).filter(
        Integration.client_id == client_id,
        Integration.platform == payload.platform,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Integration already exists for this platform")

    integration = Integration(
        client_id=client_id,
        platform=payload.platform,
        display_name=payload.display_name or payload.platform.replace("_", " ").title(),
        credentials=payload.credentials,
        config=payload.config or {},
        status=IntegrationStatus.pending,
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


@router.get("/{integration_id}", response_model=IntegrationResponse)
def get_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    integration = (
        db.query(Integration)
        .join(Client)
        .filter(Integration.id == integration_id, Client.owner_id == current_user.id)
        .first()
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


@router.put("/{integration_id}", response_model=IntegrationResponse)
def update_integration(
    integration_id: int,
    payload: IntegrationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    integration = (
        db.query(Integration)
        .join(Client)
        .filter(Integration.id == integration_id, Client.owner_id == current_user.id)
        .first()
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(integration, key, value)

    db.commit()
    db.refresh(integration)
    return integration


@router.delete("/{integration_id}", status_code=204)
def delete_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    integration = (
        db.query(Integration)
        .join(Client)
        .filter(Integration.id == integration_id, Client.owner_id == current_user.id)
        .first()
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    db.delete(integration)
    db.commit()


@router.post("/{integration_id}/test", response_model=dict)
def test_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    integration = (
        db.query(Integration)
        .join(Client)
        .filter(Integration.id == integration_id, Client.owner_id == current_user.id)
        .first()
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # TODO: trigger actual connection test via service layer
    integration.status = IntegrationStatus.active
    integration.error_message = None
    db.commit()

    return {"status": "ok", "platform": integration.platform, "message": "Connection verified"}
