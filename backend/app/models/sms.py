"""SMS models - re-exported from app.models.models to avoid table redefinition conflicts."""
from app.models.models import SmsTemplate, SmsTask, SmsSendLog, SmsChannel
from app.models.models import SMSStatus, SMSType
SMSLog = SmsSendLog  # Alias for backward compatibility
__all__ = ["SmsTemplate", "SmsTask", "SmsSendLog", "SmsChannel", "SMSLog", "SMSStatus", "SMSType"]
