from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum
from datetime import datetime
import enum
from app.core.database import Base


class SMSStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SMSType(str, enum.Enum):
    VERIFICATION = "verification"
    NOTIFICATION = "notification"
    ALERT = "alert"


class SMSLog(Base):
    __tablename__ = "sms_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    phone = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    
    sms_type = Column(SQLEnum(SMSType), nullable=False)
    status = Column(SQLEnum(SMSStatus), default=SMSStatus.PENDING, nullable=False)
    
    provider = Column(String(50), nullable=True)
    provider_message_id = Column(String(100), nullable=True)
    
    error_code = Column(String(20), nullable=True)
    error_message = Column(String(255), nullable=True)
    
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SMSLog {self.id} - {self.phone} - {self.status}>"
