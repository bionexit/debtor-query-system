from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db
from app.models.models import H5User
from app.schemas.schemas import (
    H5CaptchaRequest, H5CaptchaResponse, H5VerifyRequest, H5TokenResponse,
    H5DebtInfoRequest, DebtInfoResponse, PaymentAccountResponse
)
from app.services.h5_service import H5AuthService, H5DebtInfoService
from app.core.security import verify_token
from app.api.deps import get_db as deps_get_db

router = APIRouter(prefix="/api/h5", tags=["h5"])


def get_h5_user_from_token(authorization: str = None, db: Session = Depends(get_db)) -> H5User:
    """Get H5 user from authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    if payload.get("type") != "h5":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    user = H5AuthService.get_user_by_id(db, int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.is_locked and user.locked_until and user.locked_until.replace(tzinfo=None) > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked"
        )
    
    return user


from datetime import datetime

# ============ H5 Auth ============
@router.post("/captcha", response_model=H5CaptchaResponse)
def request_captcha(
    request: H5CaptchaRequest,
    db: Session = Depends(get_db)
):
    """Request a captcha for phone verification"""
    try:
        captcha, expires_in = H5AuthService.request_captcha(db, request.phone)
        # In production, send captcha via SMS here
        return H5CaptchaResponse(captcha_id=captcha, expires_in=expires_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )


@router.post("/verify", response_model=H5TokenResponse)
def verify_captcha(
    request: H5VerifyRequest,
    db: Session = Depends(get_db)
):
    """Verify captcha and get access token"""
    success, result = H5AuthService.verify_captcha(db, request.phone, request.captcha)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    return H5TokenResponse(access_token=result, expires_in=604800)  # 7 days


# ============ H5 Debt Info ============
@router.post("/debt-info", response_model=DebtInfoResponse)
def query_debt_info(
    request: H5DebtInfoRequest,
    current_user: H5User = Depends(get_h5_user_from_token),
    db: Session = Depends(get_db)
):
    """Query debt information"""
    result, error = H5DebtInfoService.query_debt_info(db, current_user.id, request.debtor_id_card)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.get("/payment-accounts", response_model=List[PaymentAccountResponse])
def get_payment_accounts(
    current_user: H5User = Depends(get_h5_user_from_token),
    db: Session = Depends(get_db)
):
    """Get payment accounts"""
    accounts = H5DebtInfoService.get_payment_accounts(db)
    return accounts


@router.get("/query-limit")
def get_query_limit(
    current_user: H5User = Depends(get_h5_user_from_token),
    db: Session = Depends(get_db)
):
    """Get remaining query limit"""
    from app.core.config import settings
    
    today = datetime.utcnow().date()
    if current_user.query_date and current_user.query_date.date() < today:
        remaining = settings.H5_DAILY_QUERY_LIMIT
    else:
        remaining = max(0, settings.H5_DAILY_QUERY_LIMIT - current_user.daily_query_count)
    
    return {
        "remaining": remaining,
        "limit": settings.H5_DAILY_QUERY_LIMIT,
        "reset_at": f"{today} 23:59:59"
    }
