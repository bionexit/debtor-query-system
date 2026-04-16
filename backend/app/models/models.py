"""
All SQLAlchemy models for the Debtor Payment Account Query System.
Based on PRD Section 5 data models.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON, BigInteger
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

# Create the declarative base - this provides the .metadata attribute needed by SQLAlchemy
Base = declarative_base()


# ============= Enums =============
class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class DebtorStatus(str, enum.Enum):
    ACTIVE = "active"
    BLACKLISTED = "blacklisted"
    CLEARED = "cleared"
    OVERDUE = "overdue"
    LEGAL = "legal"


class VoucherStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SMSTaskStatus(str, enum.Enum):
    PENDING = "pending"
    SENDING = "sending"
    SUCCESS = "success"
    FAILED = "failed"


class SmsTemplateStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


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


class ChannelStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    SCANNED = "scanned"


class AttemptType(str, enum.Enum):
    IDENTITY = "identity"
    CAPTCHA = "captcha"
    LOGIN = "login"


class AIStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    MANUAL = "manual"


class ImportTaskStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PartnerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


# ============= Partner (合作方) =============
class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(32), unique=True, nullable=False, index=True)
    partner_name = Column(String(100), nullable=False)
    partner_code = Column(String(50), unique=True, nullable=False)
    contact_person = Column(String(50))
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    status = Column(String(20), default="active")
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    secret_key = Column(String(64), unique=True, nullable=False, index=True)
    api_key_expires_at = Column(DateTime, nullable=True)
    is_api_enabled = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(255), nullable=True)
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_day = Column(Integer, default=10000)
    daily_query_limit = Column(Integer, default=1000)
    monthly_query_limit = Column(Integer, default=30000)
    today_query_count = Column(Integer, default=0)
    last_query_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= Admin (管理员) =============
class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String(32), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")
    real_name = Column(String(50))
    email = Column(String(100))
    phone = Column(String(20))
    status = Column(String(20), default="active")
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= AdminSession (管理员会话) =============
class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    admin_id = Column(String(32), ForeignKey("admins.admin_id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= BatchStatus (for Batch model) =============
class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============= CaseBatch (委案批次) =============
class CaseBatch(Base):
    __tablename__ = "case_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_no = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    partner_id = Column(String(32), ForeignKey("partners.partner_id"), nullable=False)
    status = Column(SQLEnum(BatchStatus), default=BatchStatus.PENDING, nullable=False)
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    debtors = relationship("Debtor", back_populates="batch")


# ============= PaymentAccount (还款账户) =============
class PaymentAccount(Base):
    __tablename__ = "payment_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(32), unique=True, nullable=False, index=True)
    partner_id = Column(String(32), ForeignKey("partners.partner_id"), nullable=False)
    bank_name = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=False)
    account_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= AccessToken (访问令牌) =============
class AccessToken(Base):
    __tablename__ = "access_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(32), unique=True, nullable=False, index=True)  # 5-char short token
    user_id = Column(String(32), nullable=False)
    expires_at = Column(DateTime, nullable=True)  # NULL = permanent
    max_visits = Column(Integer, default=3)  # 0 = unlimited
    visit_count = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= SessionToken (会话令牌) =============
class SessionToken(Base):
    __tablename__ = "session_tokens"

    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(32), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= FailedAttempt (身份验证失败记录) =============
class FailedAttempt(Base):
    __tablename__ = "failed_attempts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(32), nullable=False, index=True)
    attempt_type = Column(String(20), nullable=False)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= PaymentVoucher (还款凭证) =============
class PaymentVoucher(Base):
    __tablename__ = "payment_vouchers"

    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(String(32), unique=True, nullable=False, index=True)
    # File upload fields
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    error_details = Column(Text, nullable=True)
    # Status and review
    status = Column(String(20), default="pending")
    uploaded_by = Column(Integer, nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)
    # Legacy AI fields (for backward compatibility)
    user_id = Column(String(32), nullable=True)
    batch_id = Column(String(32), nullable=True)
    amount = Column(Float, nullable=True)
    voucher_image_urls = Column(JSON)  # ["url1", "url2"]
    payment_date = Column(DateTime)
    remark = Column(Text)
    # AI识别字段
    ai_amount = Column(Float)
    ai_transaction_no = Column(String(64))
    ai_bank_name = Column(String(100))
    ai_transaction_time = Column(DateTime)
    ai_recipient_account = Column(String(64))
    ai_confidence = Column(Float)
    ai_status = Column(String(20), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= SmsTemplate (短信模板) =============
class SmsTemplate(Base):
    __tablename__ = "sms_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(32), unique=True, nullable=False, index=True)
    template_name = Column(String(100), nullable=False)
    template_content = Column(Text, nullable=False)
    variables = Column(JSON)
    status = Column(String(20), default="active")
    channel_id = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= SmsTask (短信发送任务) =============
class SmsTask(Base):
    __tablename__ = "sms_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(32), unique=True, nullable=False, index=True)
    template_id = Column(String(32), nullable=False)
    user_ids = Column(JSON)  # ["USER_001", "USER_002"]
    phone_numbers = Column(JSON)
    variables_data = Column(JSON)
    status = Column(String(20), default="pending")
    gateway_response = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# ============= SmsSendLog (短信发送日志) =============
class SmsSendLog(Base):
    __tablename__ = "sms_send_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    log_id = Column(BigInteger, index=True)
    task_id = Column(String(32), nullable=False, index=True)
    user_id = Column(String(32), nullable=False)
    phone_number = Column(String(20), nullable=False)
    template_id = Column(String(32), nullable=False)
    gateway_type = Column(String(50))
    status = Column(String(20), default="success")
    error_code = Column(String(50))
    error_message = Column(String(255))
    send_time = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Integer)


# ============= SmsChannel (短信渠道) =============
class SmsChannel(Base):
    __tablename__ = "sms_channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String(32), unique=True, nullable=False, index=True)
    channel_name = Column(String(100), nullable=False)
    channel_code = Column(String(50), unique=True, nullable=False)
    class_name = Column(String(100))
    file_path = Column(String(255))
    config_data = Column(JSON)
    is_default = Column(Boolean, default=False)
    status = Column(String(20), default="active")
    priority = Column(Integer, default=1)
    last_scan_at = Column(DateTime, nullable=True)
    remark = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields expected by service/tests
    name = Column(String(100))  # Alias for channel_name
    provider = Column(String(100))
    endpoint = Column(String(255))
    api_key = Column(String(255))
    success_rate = Column(Float, default=0.0)
    avg_response_time = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)


# ============= SystemConfig (系统配置) =============
class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(String(32), unique=True, nullable=False, index=True)
    config_key = Column(String(50), unique=True, nullable=False)
    config_value = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=False)
    description = Column(Text)
    changed_by = Column(String(32))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============= ConfigChangeLog (配置变更记录) =============
class ConfigChangeLog(Base):
    __tablename__ = "config_change_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(Integer, index=True)
    config_id = Column(Integer, index=True)  # Foreign key to SystemConfig.id
    config_name = Column(String(50), nullable=False)
    config_key = Column(String(100), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    change_reason = Column(Text)
    changed_by = Column(String(32))
    changed_at = Column(DateTime, default=datetime.utcnow)


# ============= ImportTask (导入任务记录) =============
class ImportTask(Base):
    __tablename__ = "import_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(32), unique=True, nullable=False, index=True)
    file_name = Column(String(100), nullable=False)
    total_rows = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    status = Column(String(20), default="processing")
    error_report_url = Column(String(500))
    created_by = Column(String(32))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer)


# ============= ApiAccessLog (API访问日志) =============
class ApiAccessLog(Base):
    __tablename__ = "api_access_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    log_id = Column(BigInteger, index=True)
    partner_id = Column(String(32), nullable=False, index=True)
    api_key = Column(String(64))
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    request_ip = Column(String(45))
    request_body = Column(Text)
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    rate_limit_remaining = Column(Integer)
    rate_limit_reset_at = Column(DateTime)
    error_code = Column(String(50))
    error_message = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= Captcha (图形验证码) =============
class Captcha(Base):
    __tablename__ = "captchas"

    id = Column(Integer, primary_key=True, index=True)
    captcha_key = Column(String(64), unique=True, nullable=False, index=True)
    captcha_code = Column(String(10), nullable=False)
    image_data = Column(Text, nullable=False)  # Base64 encoded image
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= Backward Compatibility Aliases =============
Batch = CaseBatch
Voucher = PaymentVoucher


# ============= Re-export from sub-modules (must be at end to avoid circular imports) =============
# These models are defined in sub-modules but many files import them from here
from app.models.user import User, UserRole, UserStatus
from app.models.debtor import Debtor, QueryLog, ImportBatch

# Re-export schema classes that some files incorrectly import from models
# (These are Pydantic schemas, not SQLAlchemy models - import from schemas instead)
# H5User, DebtInfo, Config - these don't exist as SQLAlchemy models

# Alias for backward compatibility
Config = SystemConfig
SMSChannel = SmsChannel  # Some files use SMSChannel
SMSTemplate = SmsTemplate  # Some files use SMSTemplate
SMSTask = SmsTask  # Some files use SMSTask
SMSTaskStatus = SMSTaskStatus  # Some files expect this name
ChannelStatus = ChannelStatus  # Already correct, just for completeness

# ============= H5User - H5 authentication user =============
class H5User(Base):
    __tablename__ = "h5_users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    id_card_hash = Column(String(64), nullable=True)
    is_locked = Column(Boolean, default=False)
    locked_until = Column(DateTime, nullable=True)
    captcha = Column(String(10), nullable=True)
    captcha_expire_at = Column(DateTime, nullable=True)
    verification_attempts = Column(Integer, default=0)
    daily_query_count = Column(Integer, default=0)
    query_date = Column(DateTime, nullable=True)
    last_query_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============= PartnerQueryLog (合作方查询日志) =============
class PartnerQueryLog(Base):
    __tablename__ = "partner_query_logs"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    debtor_id = Column(Integer, ForeignKey("debtors.id"), nullable=True)
    query_data = Column(Text, nullable=True)
    response_data = Column(Text, nullable=True)
    query_ip = Column(String(50), nullable=True)
    status_code = Column(Integer, nullable=True)
    error_message = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
