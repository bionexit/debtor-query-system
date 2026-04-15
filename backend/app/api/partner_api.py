from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.models.database import get_db
from app.models.models import Partner, Debtor
from app.schemas.schemas import PartnerQueryRequest, PartnerResponse
from app.services.partner_service import PartnerService
from datetime import datetime
import hmac
import hashlib
import time

router = APIRouter(prefix="/partner", tags=["partner"])


def verify_partner_auth(
    authorization: str = None,
    db: Session = Depends(get_db)
) -> Partner:
    """Verify partner API authentication"""
    if not authorization or not authorization.startswith("Partner "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    # Parse: Partner <api_key>:<signature>:<timestamp>
    try:
        auth_parts = authorization.replace("Partner ", "").split(":")
        if len(auth_parts) != 3:
            raise ValueError("Invalid authorization format")
        
        api_key, signature, timestamp = auth_parts
        timestamp = int(timestamp)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )
    
    # Get partner
    partner = PartnerService.get_partner_by_api_key(db, api_key)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Verify signature
    is_valid, error = PartnerService.verify_signature(api_key, signature, timestamp, partner.secret_key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    # Check rate limit
    is_allowed, error = PartnerService.check_rate_limit(db, partner.id)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error
        )
    
    # Check daily limit
    is_allowed, error = PartnerService.check_daily_limit(db, partner.id)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error
        )
    
    return partner


@router.get("/health")
def health_check():
    """Partner API health check"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.post("/query", response_model=PartnerResponse)
def query_debtor(
    request: PartnerQueryRequest,
    current_partner: Partner = Depends(verify_partner_auth),
    db: Session = Depends(get_db)
):
    """Query debtor information"""
    # Increment usage
    PartnerService.increment_usage(db, current_partner.id)
    
    # Find debtor
    debtor = db.query(Debtor).filter(Debtor.id_card == request.id_card).first()
    
    if not debtor:
        return PartnerResponse(
            code=404,
            message="No debtor found",
            data=None
        )
    
    # Check name matches (case insensitive)
    if debtor.name.lower() != request.name.lower():
        return PartnerResponse(
            code=403,
            message="Name does not match",
            data=None
        )
    
    return PartnerResponse(
        code=200,
        message="Success",
        data={
            "debtor_id": debtor.id,
            "name": debtor.name,
            "id_card": debtor.id_card,
            "phone": debtor.phone,
            "debt_amount": debtor.debt_amount,
            "status": debtor.status.value
        }
    )


@router.get("/partners")
def list_partners(
    current_partner: Partner = Depends(verify_partner_auth),
    db: Session = Depends(get_db)
):
    """List partner accounts (admin only - simplified for demo)"""
    partners = db.query(Partner).all()
    return {
        "partners": [
            {
                "id": p.id,
                "name": p.name,
                "is_active": p.is_active,
                "rate_limit": p.rate_limit,
                "daily_limit": p.daily_limit,
                "today_usage": p.today_usage
            }
            for p in partners
        ]
    }


@router.post("/partners")
def create_partner(
    name: str,
    rate_limit: int = 100,
    daily_limit: int = 10000,
    db: Session = Depends(get_db)
):
    """Create a new partner account (simplified - no auth for demo)"""
    partner, error = PartnerService.create_partner(db, name, rate_limit, daily_limit)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "id": partner.id,
        "name": partner.name,
        "api_key": partner.api_key,
        "secret_key": partner.secret_key,
        "message": "Partner created successfully"
    }


@router.post("/partners/{partner_id}/revoke")
def revoke_partner(
    partner_id: int,
    current_partner: Partner = Depends(verify_partner_auth),
    db: Session = Depends(get_db)
):
    """Revoke a partner account"""
    success, message = PartnerService.revoke_partner(db, partner_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}


@router.post("/partners/{partner_id}/regenerate-keys")
def regenerate_partner_keys(
    partner_id: int,
    current_partner: Partner = Depends(verify_partner_auth),
    db: Session = Depends(get_db)
):
    """Regenerate API keys for a partner"""
    partner, error = PartnerService.regenerate_keys(db, partner_id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "api_key": partner.api_key,
        "secret_key": partner.secret_key,
        "message": "Keys regenerated successfully"
    }
