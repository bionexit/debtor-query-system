from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user, require_superadmin
from app.schemas.partner import PartnerCreate, PartnerUpdate, PartnerResponse
from app.services.partner_service import PartnerService
from app.models.user import User, UserRole

router = APIRouter(prefix="/partners", tags=["Partners Management"])


@router.get("/", response_model=List[PartnerResponse])
def list_partners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all partners (admin only)."""
    if not current_user.is_superadmin and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    partner_service = PartnerService(db)
    
    from app.models.partner import PartnerStatus
    status_enum = PartnerStatus(status) if status else None
    
    partners = partner_service.get_all(skip=skip, limit=limit, status=status_enum)
    return [PartnerResponse.model_validate(p) for p in partners]


@router.get("/{partner_id}", response_model=PartnerResponse)
def get_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get partner by ID (admin only)."""
    if not current_user.is_superadmin and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    partner_service = PartnerService(db)
    partner = partner_service.get_by_id(partner_id)
    
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    return PartnerResponse.model_validate(partner)


@router.post("/", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
def create_partner(
    partner_data: PartnerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Create a new partner (superadmin only)."""
    partner_service = PartnerService(db)
    partner, error = partner_service.create(
        partner_code=partner_data.partner_code,
        partner_name=partner_data.partner_name,
        description=partner_data.description,
        daily_query_limit=partner_data.daily_query_limit,
        monthly_query_limit=partner_data.monthly_query_limit,
        allowed_ips=partner_data.allowed_ips,
        created_by_id=current_user.id
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return PartnerResponse.model_validate(partner)


@router.put("/{partner_id}", response_model=PartnerResponse)
def update_partner(
    partner_id: int,
    partner_data: PartnerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Update partner (superadmin only)."""
    partner_service = PartnerService(db)
    
    update_data = partner_data.model_dump(exclude_unset=True)
    
    partner, error = partner_service.update(partner_id, **update_data)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return PartnerResponse.model_validate(partner)


@router.post("/{partner_id}/regenerate-key")
def regenerate_partner_api_key(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Regenerate partner API key (superadmin only)."""
    partner_service = PartnerService(db)
    new_key, error = partner_service.regenerate_api_key(partner_id)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {"api_key": new_key, "message": "API key regenerated successfully"}


@router.delete("/{partner_id}")
def delete_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Delete a partner (superadmin only)."""
    partner_service = PartnerService(db)
    success = partner_service.delete(partner_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    return {"message": "Partner deleted successfully"}
