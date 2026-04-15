from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.partner import (
    PartnerCreate, PartnerUpdate, PartnerResponse, PartnerQueryRequest, PartnerQueryResponse, PartnerStatsResponse
)
from app.services.partner_service import PartnerService
from app.models.partner import Partner

router = APIRouter(prefix="/partner", tags=["Partner API"])

X_API_KEY_HEADER = "X-API-Key"


def get_partner_from_header(
    x_api_key: str = Header(None, alias=X_API_KEY_HEADER),
    db: Session = Depends(get_db)
) -> Partner:
    """Get and verify partner from X-API-Key header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )
    
    partner_service = PartnerService(db)
    partner, error = partner_service.verify_api_key(x_api_key)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    return partner


@router.get("/query", response_model=PartnerQueryResponse)
def partner_query(
    request: Request,
    debtor_number: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    id_card: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    partner: Partner = Depends(get_partner_from_header),
    db: Session = Depends(get_db)
):
    """
    Query debtor data via Partner API.
    Requires X-API-Key authentication.
    """
    client_ip = request.client.host if request.client else None
    
    partner_service = PartnerService(db)
    result, error = partner_service.query_debtor(
        partner=partner,
        debtor_number=debtor_number,
        name=name,
        id_card=id_card,
        phone=phone,
        query_ip=client_ip
    )
    
    if error and not result.get('success'):
        return PartnerQueryResponse(
            success=False,
            error_code=result.get('error_code', 'ERROR'),
            error_message=error
        )
    
    return PartnerQueryResponse(
        success=True,
        data=result.get('data')
    )


@router.get("/stats", response_model=PartnerStatsResponse)
def partner_get_stats(
    partner: Partner = Depends(get_partner_from_header),
    db: Session = Depends(get_db)
):
    """Get partner query statistics."""
    partner_service = PartnerService(db)
    stats = partner_service.get_stats(partner)
    return PartnerStatsResponse(**stats)


@router.get("/query-logs")
def partner_get_query_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    partner: Partner = Depends(get_partner_from_header),
    db: Session = Depends(get_db)
):
    """Get partner query logs."""
    partner_service = PartnerService(db)
    logs = partner_service.get_query_logs(partner.id, skip=skip, limit=limit)
    
    return [
        {
            "id": log.id,
            "debtor_id": log.debtor_id,
            "query_data": log.query_data,
            "response_data": log.response_data,
            "query_ip": log.query_ip,
            "status_code": log.status_code,
            "error_message": log.error_message,
            "created_at": log.created_at
        }
        for log in logs
    ]
