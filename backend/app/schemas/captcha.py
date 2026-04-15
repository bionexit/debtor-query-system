from pydantic import BaseModel
from datetime import datetime


class CaptchaResponse(BaseModel):
    captcha_key: str
    image: str


class CaptchaVerifyRequest(BaseModel):
    captcha_key: str
    captcha_value: str
