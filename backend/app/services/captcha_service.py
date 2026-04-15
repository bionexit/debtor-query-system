import base64
import random
import string
import io
from datetime import datetime, timedelta
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session
from app.models.captcha import Captcha
from app.core.config import settings


class CaptchaService:
    """
    Service for captcha generation and verification.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_code(self, length: int = 4) -> str:
        """Generate random alphanumeric code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def _generate_image(self, code: str) -> bytes:
        """Generate captcha image."""
        width, height = 120, 40
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Core/Helvetica.ttc", 24)
            except:
                font = ImageFont.load_default()
        
        text_width = draw.textlength(code, font=font)
        position = ((width - text_width) // 2, (height - 24) // 2)
        
        draw.text(position, code, fill=(0, 0, 0), font=font)
        
        for _ in range(3):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 200), width=1)
        
        for _ in range(30):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def generate(self) -> Tuple[str, str]:
        """
        Generate a new captcha.
        
        Returns:
            Tuple of (captcha_key, captcha_image_base64)
        """
        captcha_key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        captcha_value = self._generate_code(4)
        image_data = self._generate_image(captcha_value)
        
        expire_at = datetime.utcnow() + timedelta(seconds=settings.CAPTCHA_EXPIRE_SECONDS)
        
        captcha = Captcha(
            captcha_key=captcha_key,
            captcha_value=captcha_value,
            image_data=image_data,
            expire_at=expire_at,
        )
        
        self.db.add(captcha)
        self.db.commit()
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        return captcha_key, f"data:image/png;base64,{image_base64}"
    
    def verify(self, captcha_key: str, captcha_value: str) -> Tuple[bool, str]:
        """
        Verify a captcha.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        captcha = self.db.query(Captcha).filter(
            Captcha.captcha_key == captcha_key
        ).first()
        
        if not captcha:
            return False, "Captcha not found"
        
        if captcha.is_used:
            return False, "Captcha already used"
        
        if datetime.utcnow() > captcha.expire_at:
            return False, "Captcha expired"
        
        if captcha.captcha_value.upper() != captcha_value.upper():
            return False, "Invalid captcha"
        
        captcha.is_used = True
        captcha.used_at = datetime.utcnow()
        self.db.commit()
        
        return True, ""
    
    def get_captcha(self, captcha_key: str) -> Optional[Captcha]:
        """Get captcha by key."""
        return self.db.query(Captcha).filter(
            Captcha.captcha_key == captcha_key
        ).first()
    
    def delete_expired(self) -> int:
        """Delete expired captchas."""
        result = self.db.query(Captcha).filter(
            Captcha.expire_at < datetime.utcnow()
        ).delete()
        self.db.commit()
        return result
    
    def delete_used(self, older_than_hours: int = 1) -> int:
        """Delete used captchas older than specified hours."""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        result = self.db.query(Captcha).filter(
            Captcha.is_used == True,
            Captcha.used_at < cutoff
        ).delete()
        self.db.commit()
        return result
