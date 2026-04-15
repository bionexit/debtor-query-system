from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class DebtorStatus(str, enum.Enum):
    ACTIVE = "active"
    OVERDUE = "overdue"
    CLEARED = "cleared"
    LEGAL = "legal"


class PhoneEncryptData(Base):
    __tablename__ = "phone_encrypt_data"

    id = Column(Integer, primary_key=True, index=True)
    debtor_id = Column(Integer, ForeignKey("debtors.id"), unique=True, nullable=False)
    encrypted_phone = Column(LargeBinary, nullable=False)
    nonce = Column(LargeBinary, nullable=False)
    tag = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Debtor(Base):
    __tablename__ = "debtors"

    id = Column(Integer, primary_key=True, index=True)
    debtor_number = Column(String(50), unique=True, index=True, nullable=False)
    
    name = Column(String(100), nullable=False)
    id_card = Column(String(20), index=True, nullable=True)
    
    encrypted_phone = Column(String(255), nullable=True)
    phone_nonce = Column(String(50), nullable=True)
    phone_tag = Column(String(50), nullable=True)
    
    email = Column(String(100), nullable=True)
    
    bank_name = Column(String(100), nullable=True)
    bank_account = Column(String(50), nullable=True)
    bank_account_name = Column(String(100), nullable=True)
    
    address = Column(Text, nullable=True)
    remark = Column(Text, nullable=True)
    
    status = Column(SQLEnum(DebtorStatus), default=DebtorStatus.ACTIVE, nullable=False)
    
    overdue_amount = Column(Integer, default=0)
    overdue_days = Column(Integer, default=0)
    
    last_query_at = Column(DateTime, nullable=True)
    query_count = Column(Integer, default=0)
    
    is_deleted = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])

    def __repr__(self):
        return f"<Debtor {self.debtor_number} - {self.name}>"


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    debtor_id = Column(Integer, ForeignKey("debtors.id"), nullable=False)
    debtor = relationship("Debtor")
    
    query_type = Column(String(20), nullable=False)
    query_channel = Column(String(20), nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    
    query_ip = Column(String(50), nullable=True)
    query_phone = Column(String(20), nullable=True)
    
    success = Column(Boolean, default=True)
    error_message = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    
    status = Column(String(20), default="pending")
    error_log = Column(Text, nullable=True)
    
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
