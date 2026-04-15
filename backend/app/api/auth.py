from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_token
from app.schemas.user import UserLogin, TokenResponse, UserResponse, H5TokenRequest, H5TokenResponse, PasswordResetRequest
from app.services.user_service import UserService
from app.services.captcha_service import CaptchaService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user_service = UserService(db)
    user = user_service.get_by_id(int(user_id))
    
    if user is None:
        raise credentials_exception
    
    return user


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    """Require superadmin role."""
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required"
        )
    return current_user


@router.post("/login", response_model=TokenResponse)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    User login with username and password.
    Optionally includes captcha verification.
    """
    captcha_service = CaptchaService(db)
    if user_login.captcha_key and user_login.captcha_value:
        is_valid, error = captcha_service.verify(user_login.captcha_key, user_login.captcha_value)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Captcha verification failed: {error}"
            )
    
    user_service = UserService(db)
    user, error = user_service.authenticate(user_login.username, user_login.password)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    access_token = user_service.create_access_token(user)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/h5/token", response_model=H5TokenResponse)
def get_h5_token(request: H5TokenRequest, db: Session = Depends(get_db)):
    """
    Get H5 access token via SMS verification.
    """
    user_service = UserService(db)
    token, error = user_service.create_h5_token_for_user(request.phone, request.sms_code)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return H5TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.H5_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        expires_days=settings.H5_TOKEN_EXPIRE_DAYS
    )


@router.post("/password/reset")
def password_reset_request(phone: str, db: Session = Depends(get_db)):
    """
    Request password reset SMS code.
    """
    user_service = UserService(db)
    success, message = user_service.send_password_reset_sms(phone)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}


@router.post("/password/reset/confirm")
def password_reset_confirm(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Confirm password reset with SMS code.
    """
    user_service = UserService(db)
    success, message = user_service.reset_password_with_sms(
        request.phone, request.sms_code, request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout current user (client should discard token)."""
    return {"message": "Successfully logged out"}
