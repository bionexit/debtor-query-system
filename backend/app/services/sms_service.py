from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.sms import SMSLog, SMSStatus, SMSType
from app.plugins.sms.manager import sms_manager


class SMSService:
    """
    Service for SMS operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, sms_id: int) -> Optional[SMSLog]:
        """Get SMS log by ID."""
        return self.db.query(SMSLog).filter(SMSLog.id == sms_id).first()
    
    def get_by_provider_message_id(self, provider_message_id: str) -> Optional[SMSLog]:
        """Get SMS log by provider message ID."""
        return self.db.query(SMSLog).filter(
            SMSLog.provider_message_id == provider_message_id
        ).first()
    
    def get_by_phone(self, phone: str, skip: int = 0, limit: int = 100) -> List[SMSLog]:
        """Get SMS logs by phone number."""
        return self.db.query(SMSLog).filter(
            SMSLog.phone == phone
        ).order_by(SMSLog.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_recent_by_phone(self, phone: str, minutes: int = 10) -> Optional[SMSLog]:
        """Get recent SMS log by phone within specified minutes."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return self.db.query(SMSLog).filter(
            SMSLog.phone == phone,
            SMSLog.created_at >= cutoff
        ).order_by(SMSLog.created_at.desc()).first()
    
    def send(self, phone: str, message: str, sms_type: SMSType = SMSType.NOTIFICATION,
             provider: Optional[str] = None) -> tuple[Optional[SMSLog], Dict[str, Any]]:
        """
        Send an SMS message.
        
        Returns:
            Tuple of (SMSLog or None, send_result)
        """
        sms_log = SMSLog(
            phone=phone,
            message=message,
            sms_type=sms_type,
            status=SMSStatus.PENDING,
            provider=provider or sms_manager.get_default_provider_name(),
        )
        
        self.db.add(sms_log)
        self.db.commit()
        self.db.refresh(sms_log)
        
        result = sms_manager.send(phone, message, provider_name=provider)
        
        if result.get('success'):
            sms_log.status = SMSStatus.SENT
            sms_log.provider_message_id = result.get('message_id')
            sms_log.sent_at = datetime.utcnow()
        else:
            sms_log.status = SMSStatus.FAILED
            sms_log.error_code = result.get('error_code')
            sms_log.error_message = result.get('error_message')
        
        self.db.commit()
        self.db.refresh(sms_log)
        
        return sms_log, result
    
    def send_verification_code(self, phone: str, code: str) -> tuple[Optional[SMSLog], Dict[str, Any]]:
        """Send a verification code SMS."""
        message = f"Your verification code is: {code}"
        return self.send(phone, message, SMSType.VERIFICATION)
    
    def handle_callback(self, message_id: str, status: str,
                        delivered_at: Optional[datetime] = None,
                        error_code: Optional[str] = None,
                        error_message: Optional[str] = None) -> Optional[SMSLog]:
        """Handle SMS status callback from provider."""
        sms_log = self.get_by_provider_message_id(message_id)
        
        if not sms_log:
            return None
        
        status_mapping = {
            'DELIVERED': SMSStatus.DELIVERED,
            'SENT': SMSStatus.SENT,
            'FAILED': SMSStatus.FAILED,
            'UNKNOWN': SMSStatus.UNKNOWN,
        }
        
        sms_log.status = status_mapping.get(status.upper(), SMSStatus.UNKNOWN)
        
        if delivered_at:
            sms_log.delivered_at = delivered_at
        elif status.upper() == 'DELIVERED':
            sms_log.delivered_at = datetime.utcnow()
        
        if error_code:
            sms_log.error_code = error_code
        if error_message:
            sms_log.error_message = error_message
        
        sms_log.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(sms_log)
        
        return sms_log
    
    def query_status(self, message_id: str) -> Dict[str, Any]:
        """Query SMS status from provider."""
        sms_log = self.get_by_provider_message_id(message_id)
        
        if not sms_log:
            return {
                'found': False,
                'error': 'Message not found'
            }
        
        provider = sms_log.provider or sms_manager.get_default_provider_name()
        result = sms_manager.query_status(message_id, provider_name=provider)
        
        if result.get('status'):
            status_mapping = {
                'DELIVERED': SMSStatus.DELIVERED,
                'SENT': SMSStatus.SENT,
                'FAILED': SMSStatus.FAILED,
                'PENDING': SMSStatus.PENDING,
            }
            sms_log.status = status_mapping.get(result['status'].upper(), SMSStatus.UNKNOWN)
            
            if result.get('delivered_at'):
                sms_log.delivered_at = result['delivered_at']
            
            if result.get('error_code'):
                sms_log.error_code = result['error_code']
            if result.get('error_message'):
                sms_log.error_message = result['error_message']
            
            self.db.commit()
        
        return {
            'found': True,
            'id': sms_log.id,
            'phone': sms_log.phone,
            'status': sms_log.status.value,
            'sent_at': sms_log.sent_at,
            'delivered_at': sms_log.delivered_at,
            'error_code': sms_log.error_code,
            'error_message': sms_log.error_message,
        }
    
    def update_status(self, sms_id: int, status: SMSStatus,
                      delivered_at: Optional[datetime] = None,
                      error_code: Optional[str] = None,
                      error_message: Optional[str] = None) -> Optional[SMSLog]:
        """Manually update SMS status."""
        sms_log = self.get_by_id(sms_id)
        
        if not sms_log:
            return None
        
        sms_log.status = status
        
        if delivered_at:
            sms_log.delivered_at = delivered_at
        
        if error_code:
            sms_log.error_code = error_code
        
        if error_message:
            sms_log.error_message = error_message
        
        sms_log.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(sms_log)
        
        return sms_log
    
    def delete(self, sms_id: int) -> bool:
        """Delete an SMS log."""
        sms_log = self.get_by_id(sms_id)
        
        if not sms_log:
            return False
        
        self.db.delete(sms_log)
        self.db.commit()
        return True
    
    def get_logs(self, skip: int = 0, limit: int = 100,
                 status: Optional[SMSStatus] = None,
                 sms_type: Optional[SMSType] = None) -> List[SMSLog]:
        """Get SMS logs with filters."""
        query = self.db.query(SMSLog)
        
        if status:
            query = query.filter(SMSLog.status == status)
        if sms_type:
            query = query.filter(SMSLog.sms_type == sms_type)
        
        return query.order_by(SMSLog.created_at.desc()).offset(skip).limit(limit).all()


    def get_templates(self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List["SmsTemplate"]:
        """Get SMS templates with optional active filter."""
        from app.models.sms import SmsTemplate
        query = self.db.query(SmsTemplate)
        if is_active is not None:
            query = query.filter(SmsTemplate.status == ("active" if is_active else "inactive"))
        return query.order_by(SmsTemplate.created_at.desc()).offset(skip).limit(limit).all()

    def get_template_by_id(self, template_id: int) -> Optional["SmsTemplate"]:
        """Get SMS template by ID."""
        from app.models.sms import SmsTemplate
        return self.db.query(SmsTemplate).filter(SmsTemplate.id == template_id).first()

    def create_template(self, name: str, content: str, variables: Optional[str] = None, created_by: Optional[int] = None) -> tuple[Optional["SmsTemplate"], Optional[str]]:
        """Create a new SMS template."""
        from app.models.sms import SmsTemplate
        import uuid
        try:
            template = SmsTemplate(
                template_id=str(uuid.uuid4())[:8],
                template_name=name,
                template_content=content,
                variables=variables.split(",") if variables else [],
                status="active"
            )
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            return template, None
        except Exception as e:
            self.db.rollback()
            return None, str(e)

    def update_template(self, template_id: int, **kwargs) -> tuple[Optional["SmsTemplate"], Optional[str]]:
        """Update an SMS template."""
        from app.models.sms import SmsTemplate
        template = self.get_template_by_id(template_id)
        if not template:
            return None, "Template not found"
        try:
            if "name" in kwargs:
                template.template_name = kwargs["name"]
            if "content" in kwargs:
                template.template_content = kwargs["content"]
            if "variables" in kwargs:
                variables = kwargs["variables"]
                template.variables = variables.split(",") if isinstance(variables, str) else variables
            if "is_active" in kwargs:
                template.status = "active" if kwargs["is_active"] else "inactive"
            self.db.commit()
            self.db.refresh(template)
            return template, None
        except Exception as e:
            self.db.rollback()
            return None, str(e)

    def delete_template(self, template_id: int) -> tuple[bool, Optional[str]]:
        """Delete an SMS template."""
        from app.models.sms import SmsTemplate
        template = self.get_template_by_id(template_id)
        if not template:
            return False, "Template not found"
        try:
            self.db.delete(template)
            self.db.commit()
            return True, None
        except Exception as e:
            self.db.rollback()
            return False, str(e)
