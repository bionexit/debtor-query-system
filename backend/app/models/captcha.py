"""Captcha models - re-exported from app.models.models to avoid table redefinition conflicts."""
from app.models.models import Captcha as CaptchaModel
Captcha = CaptchaModel
__all__ = ["Captcha", "CaptchaModel"]
