from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user
from app.schemas.sms import SMSRequest, SMSResponse, SMSCallbackRequest
from app.services.sms_service import SMSService
from app.models.sms import SMSStatus, SMSType
from app.models.user import User, UserRole

router = APIRouter(prefix="/sms", tags=["SMS"])


@router.post("/send", response_model=SMSResponse)
def send_sms(
    request: SMSRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send an SMS message.
    Requires authentication.
    """
    sms_service = SMSService(db)
    sms_log, result = sms_service.send(
        phone=request.phone,
        message=request.message,
        sms_type=request.sms_type
    )
    
    if not result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error_message', 'Failed to send SMS')
        )
    
    return SMSResponse.model_validate(sms_log)


@router.get("/{sms_id}", response_model=SMSResponse)
def get_sms(
    sms_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SMS log by ID."""
    sms_service = SMSService(db)
    sms_log = sms_service.get_by_id(sms_id)
    
    if not sms_log:
        raise HTTPException(status_code=404, detail="SMS not found")
    
    return SMSResponse.model_validate(sms_log)


@router.get("/{sms_id}/status")
def query_sms_status(
    sms_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Query SMS delivery status."""
    sms_service = SMSService(db)
    sms_log = sms_service.get_by_id(sms_id)
    
    if not sms_log:
        raise HTTPException(status_code=404, detail="SMS not found")
    
    status_result = sms_service.query_status(sms_log.provider_message_id)
    
    return status_result


@router.post("/callback")
def sms_callback(
    request: SMSCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Handle SMS provider callback.
    This endpoint is typically called by the SMS provider to update delivery status.
    """
    sms_service = SMSService(db)
    sms_log = sms_service.handle_callback(
        message_id=request.message_id,
        status=request.status,
        delivered_at=request.delivered_at,
        error_code=request.error_code,
        error_message=request.error_message
    )
    
    if not sms_log:
        return {"received": True, "found": False}
    
    return {"received": True, "found": True, "status": sms_log.status.value}


@router.get("/", response_model=List[SMSResponse])
def list_sms_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[SMSStatus] = None,
    sms_type: Optional[SMSType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List SMS logs with filters."""
    if not current_user.is_superadmin and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    sms_service = SMSService(db)
    logs = sms_service.get_logs(skip=skip, limit=limit, status=status, sms_type=sms_type)
    
    return [SMSResponse.model_validate(log) for log in logs]
