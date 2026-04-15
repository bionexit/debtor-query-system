from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary
from datetime import datetime
from app.core.database import Base


class Captcha(Base):
    __tablename__ = "captchas"

    id = Column(Integer, primary_key=True, index=True)
    captcha_key = Column(String(50), unique=True, index=True, nullable=False)
    captcha_value = Column(String(10), nullable=False)
    image_data = Column(LargeBinary, nullable=False)
    
    is_used = Column(Boolean, default=False)
    expire_at = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Captcha {self.captcha_key}>"
