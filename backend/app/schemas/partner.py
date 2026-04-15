from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PartnerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class PartnerBase(BaseModel):
    partner_code: str = Field(..., max_length=50)
    partner_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    daily_query_limit: int = 1000
    monthly_query_limit: int = 30000
    allowed_ips: Optional[str] = None


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(BaseModel):
    partner_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    status: Optional[PartnerStatus] = None
    daily_query_limit: Optional[int] = None
    monthly_query_limit: Optional[int] = None
    allowed_ips: Optional[str] = None


class PartnerResponse(PartnerBase):
    id: int
    api_key: str
    status: PartnerStatus
    today_query_count: int
    this_month_query_count: int
    last_query_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int]

    class Config:
        from_attributes = True


class PartnerQueryRequest(BaseModel):
    debtor_number: Optional[str] = None
    name: Optional[str] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None


class PartnerQueryResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class PartnerStatsResponse(BaseModel):
    partner_code: str
    partner_name: str
    today_query_count: int
    this_month_query_count: int
    daily_limit: int
    monthly_limit: int
