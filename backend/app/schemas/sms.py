from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class SMSStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SMSType(str, Enum):
    VERIFICATION = "verification"
    NOTIFICATION = "notification"
    ALERT = "alert"


class SMSBase(BaseModel):
    phone: str
    message: str
    sms_type: SMSType


class SMSRequest(SMSBase):
    pass


class SMSResponse(BaseModel):
    id: int
    phone: str
    sms_type: SMSType
    status: SMSStatus
    provider: Optional[str]
    provider_message_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SMSCallbackRequest(BaseModel):
    message_id: str
    status: str
    delivered_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
