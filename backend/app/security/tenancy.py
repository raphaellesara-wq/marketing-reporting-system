"""
Reusable FastAPI dependencies that enforce strict tenant isolation.

Every route that touches a Client, Integration, or Report must use these
dependencies — they guarantee the resource belongs to the authenticated user
before any business logic runs.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Client, Integration, Report, User
from app.routes.auth import get_current_user


def get_owned_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Client:
    """Return the client only if it belongs to the current user."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.owner_id == current_user.id,
        Client.is_active == True,
    ).first()
    if not client:
        # Return 404 instead of 403 to avoid leaking resource existence
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def get_owned_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Integration:
    """Return the integration only if its parent client belongs to the current user."""
    integration = (
        db.query(Integration)
        .join(Client, Integration.client_id == Client.id)
        .filter(
            Integration.id == integration_id,
            Client.owner_id == current_user.id,
        )
        .first()
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


def get_owned_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Report:
    """Return the report only if its parent client belongs to the current user."""
    report = (
        db.query(Report)
        .join(Client, Report.client_id == Client.id)
        .filter(
            Report.id == report_id,
            Client.owner_id == current_user.id,
        )
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
