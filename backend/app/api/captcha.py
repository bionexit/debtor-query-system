from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.captcha import CaptchaResponse, CaptchaVerifyRequest
from app.services.captcha_service import CaptchaService

router = APIRouter(prefix="/captcha", tags=["Captcha"])


@router.get("/generate", response_model=CaptchaResponse)
def generate_captcha(db: Session = Depends(get_db)):
    """
    Generate a new captcha image.
    Returns captcha_key and base64-encoded image.
    """
    captcha_service = CaptchaService(db)
    captcha_key, image = captcha_service.generate()
    
    return CaptchaResponse(
        captcha_key=captcha_key,
        image=image
    )


@router.post("/verify")
def verify_captcha(
    request: CaptchaVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a captcha code.
    """
    captcha_service = CaptchaService(db)
    is_valid, error = captcha_service.verify(request.captcha_key, request.captcha_value)
    
    if not is_valid:
        return {
            "success": False,
            "message": error
        }
    
    return {
        "success": True,
        "message": "Captcha verified successfully"
    }
