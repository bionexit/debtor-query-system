from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class PartnerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    partner_code = Column(String(50), unique=True, index=True, nullable=False)
    partner_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    api_key = Column(String(100), unique=True, index=True, nullable=False)
    api_secret = Column(String(255), nullable=True)
    
    status = Column(SQLEnum(PartnerStatus), default=PartnerStatus.ACTIVE, nullable=False)
    
    daily_query_limit = Column(Integer, default=1000)
    monthly_query_limit = Column(Integer, default=30000)
    
    allowed_ips = Column(Text, nullable=True)
    
    today_query_count = Column(Integer, default=0)
    this_month_query_count = Column(Integer, default=0)
    last_query_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<Partner {self.partner_code} - {self.partner_name}>"


class PartnerQueryLog(Base):
    __tablename__ = "partner_query_logs"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    partner = relationship("Partner")
    
    debtor_id = Column(Integer, ForeignKey("debtors.id"), nullable=True)
    
    query_data = Column(Text, nullable=True)
    response_data = Column(Text, nullable=True)
    
    query_ip = Column(String(50), nullable=True)
    
    status_code = Column(Integer, nullable=True)
    error_message = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PartnerQueryLog {self.id} - Partner {self.partner_id}>"
