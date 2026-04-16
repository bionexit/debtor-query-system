from pydantic import BaseModel
from datetime import datetime


class CaptchaResponse(BaseModel):
    captcha_key: str
    image: str
    captcha_value: str = None  # For testing purposes


class CaptchaVerifyRequest(BaseModel):
    captcha_key: str
    captcha_value: str
