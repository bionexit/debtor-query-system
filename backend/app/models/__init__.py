"""All SQLAlchemy models."""
# Import Base from main models file
from app.models.models import Base

# Import enums
from app.models.models import (
    UserRole, DebtorStatus, BatchStatus, VoucherStatus,
    SMSTaskStatus, SmsTemplateStatus, ChannelStatus,
    AttemptType, AIStatus, ImportTaskStatus,
)

# Import all models from the central models.py
from app.models.models import (
    Partner, Admin, AdminSession, CaseBatch,
    PaymentAccount, AccessToken, SessionToken, FailedAttempt,
    PaymentVoucher, SmsTemplate, SmsTask, SmsSendLog,
    SmsChannel, SystemConfig, ConfigChangeLog,
    ImportTask, ApiAccessLog, Captcha,
)

# Import models from sub-modules
from app.models.user import User
from app.models.debtor import Debtor, QueryLog, ImportBatch
from app.models.captcha import Captcha as CaptchaFromCaptchaPy  # captcha.py has its own Captcha
from app.models.sms import SmsTemplate, SmsTask, SmsSendLog, SmsChannel

# Aliases for backward compatibility
Batch = CaseBatch
Voucher = PaymentVoucher

__all__ = [
    "Base",
    "UserRole", "DebtorStatus", "BatchStatus", "VoucherStatus",
    "SMSTaskStatus", "SmsTemplateStatus", "ChannelStatus",
    "AttemptType", "AIStatus", "ImportTaskStatus",
    "Partner", "Admin", "AdminSession", "CaseBatch", "Debtor",
    "PaymentAccount", "AccessToken", "SessionToken", "FailedAttempt",
    "PaymentVoucher", "SmsTemplate", "SmsTask", "SmsSendLog",
    "SmsChannel", "SystemConfig", "ConfigChangeLog",
    "ImportTask", "ApiAccessLog", "Captcha",
    "User", "QueryLog", "ImportBatch",
    "SmsTemplate", "SmsTask", "SmsSendLog", "SmsChannel",
    "CaptchaFromCaptchaPy",
    "Batch", "Voucher",
]
