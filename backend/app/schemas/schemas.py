from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class DebtorStatus(str, Enum):
    ACTIVE = "active"
    BLACKLISTED = "blacklisted"
    CLEARED = "cleared"


class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VoucherStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SMSTaskStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class ChannelStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"


# ============ Auth Schemas ============
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ============ User Schemas ============
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.OPERATOR


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_locked: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Debtor Schemas ============
class DebtorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    id_card: str = Field(..., min_length=15, max_length=18)
    phone: str = Field(..., min_length=11, max_length=20)
    address: Optional[str] = None
    debt_amount: Optional[float] = 0.0
    remark: Optional[str] = None


class DebtorCreate(DebtorBase):
    batch_id: Optional[int] = None


class DebtorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    debt_amount: Optional[float] = None
    status: Optional[DebtorStatus] = None
    remark: Optional[str] = None


class DebtorResponse(DebtorBase):
    id: int
    status: DebtorStatus
    batch_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Batch Schemas ============
class BatchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class BatchCreate(BatchBase):
    pass


class BatchUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BatchStatus] = None


class BatchResponse(BatchBase):
    id: int
    batch_no: str
    status: BatchStatus
    total_count: int
    success_count: int
    fail_count: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Voucher Schemas ============
class VoucherBase(BaseModel):
    file_name: str
    file_path: str


class VoucherUploadResponse(BaseModel):
    id: int
    file_name: str
    total_count: int
    status: VoucherStatus
    message: str


class VoucherReviewRequest(BaseModel):
    comment: Optional[str] = None


class VoucherResponse(VoucherBase):
    id: int
    file_size: Optional[int]
    status: VoucherStatus
    total_count: int
    success_count: int
    fail_count: int
    uploaded_by: Optional[int]
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    review_comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ SMS Schemas ============
class SMSTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    variables: Optional[str] = None


class SMSTemplateCreate(SMSTemplateBase):
    pass


class SMSTemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[str] = None
    is_active: Optional[bool] = None


class SMSTemplateResponse(SMSTemplateBase):
    id: int
    is_active: bool
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class SMSTaskBase(BaseModel):
    template_id: int
    channel_id: int
    recipient_count: int
    scheduled_at: Optional[datetime] = None


class SMSTaskCreate(SMSTaskBase):
    phones: List[str]


class SMSTaskResponse(SMSTaskBase):
    id: int
    task_no: str
    status: SMSTaskStatus
    success_count: int
    fail_count: int
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ H5 Schemas ============
class H5CaptchaRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)


class H5CaptchaResponse(BaseModel):
    captcha_id: str
    expires_in: int


class H5VerifyRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)
    captcha: str = Field(..., min_length=4, max_length=10)


class H5TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class H5DebtInfoRequest(BaseModel):
    debtor_id_card: str = Field(..., min_length=15, max_length=18)


class DebtInfoResponse(BaseModel):
    debtor_id: int
    name: str
    id_card: str
    phone: str
    debt_amount: float
    status: str
    query_time: datetime


class PaymentAccountResponse(BaseModel):
    bank_name: str
    account_no: str
    account_name: str
    bank_code: Optional[str]


# ============ Partner API Schemas ============
class PartnerAuthRequest(BaseModel):
    api_key: str
    signature: str
    timestamp: int


class PartnerQueryRequest(BaseModel):
    id_card: str = Field(..., min_length=15, max_length=18)
    name: str


class PartnerResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None


# ============ Config Schemas ============
class ConfigBase(BaseModel):
    config_key: str = Field(..., min_length=1, max_length=100)
    config_value: str
    description: Optional[str] = None


class ConfigCreate(ConfigBase):
    pass


class ConfigUpdate(BaseModel):
    config_value: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ConfigChangeLogResponse(BaseModel):
    id: int
    config_id: int
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: Optional[int]
    change_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ConfigResponse(ConfigBase):
    id: int
    is_active: bool
    changed_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Channel Schemas ============
class ChannelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: str
    endpoint: Optional[str] = None
    api_key: Optional[str] = None


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    status: Optional[ChannelStatus] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class ChannelTestRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)


class ChannelResponse(ChannelBase):
    id: int
    status: ChannelStatus
    priority: int
    success_rate: float
    avg_response_time: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Import Schemas ============
class ImportRequest(BaseModel):
    batch_id: int
    file_path: str


class ImportResponse(BaseModel):
    batch_id: int
    total_count: int
    success_count: int
    fail_count: int
    errors: List[str] = []
