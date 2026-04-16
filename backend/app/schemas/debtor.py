from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DebtorStatus(str, Enum):
    ACTIVE = "active"
    OVERDUE = "overdue"
    CLEARED = "cleared"
    LEGAL = "legal"
    BLACKLISTED = "blacklisted"


class DebtorBase(BaseModel):
    debtor_number: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    id_card: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account: Optional[str] = Field(None, max_length=50)
    bank_account_name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    remark: Optional[str] = None
    status: DebtorStatus = DebtorStatus.ACTIVE
    overdue_amount: Optional[int] = 0
    overdue_days: Optional[int] = 0


class DebtorCreate(DebtorBase):
    pass


class DebtorUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    id_card: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account: Optional[str] = Field(None, max_length=50)
    bank_account_name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[DebtorStatus] = None
    overdue_amount: Optional[int] = None
    overdue_days: Optional[int] = None


class DebtorResponse(DebtorBase):
    id: int
    query_count: int
    last_query_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int]
    updated_by_id: Optional[int]

    class Config:
        from_attributes = True


class DebtorQueryRequest(BaseModel):
    debtor_number: Optional[str] = None
    name: Optional[str] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None


class DebtorQueryResponse(BaseModel):
    debtor_number: str
    name: str
    id_card: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_account_name: Optional[str] = None
    address: Optional[str] = None
    status: DebtorStatus
    overdue_amount: int
    overdue_days: int


class DebtorImportResult(BaseModel):
    total: int
    success: int
    failed: int
    errors: List[str]


class QueryLogResponse(BaseModel):
    id: int
    debtor_id: int
    query_type: str
    query_channel: str
    query_ip: Optional[str]
    success: bool
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ImportBatchResponse(BaseModel):
    id: int
    filename: str
    total_count: int
    success_count: int
    fail_count: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
