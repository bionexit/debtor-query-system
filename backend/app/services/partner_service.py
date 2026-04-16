from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import time
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.partner import Partner, PartnerStatus, PartnerQueryLog
from app.models.debtor import Debtor, QueryLog
from app.core.security import create_api_key
from app.utils.encryption import phone_encryption


class PartnerService:
    """
    Service for partner management operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, partner_id: int) -> Optional[Partner]:
        """Get partner by ID."""
        return self.db.query(Partner).filter(Partner.id == partner_id).first()
    
    def get_by_code(self, partner_code: str) -> Optional[Partner]:
        """Get partner by partner code."""
        return self.db.query(Partner).filter(Partner.partner_code == partner_code).first()
    
    def get_by_api_key(self, api_key: str) -> Optional[Partner]:
        """Get partner by API key."""
        return self.db.query(Partner).filter(Partner.api_key == api_key).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, status: Optional[PartnerStatus] = None) -> List[Partner]:
        """Get all partners with pagination."""
        query = self.db.query(Partner)
        if status:
            query = query.filter(Partner.status == status)
        return query.offset(skip).limit(limit).all()
    
    def create(self, partner_code: str, partner_name: str, description: Optional[str] = None,
               daily_query_limit: int = 1000, monthly_query_limit: int = 30000,
               allowed_ips: Optional[str] = None, created_by_id: Optional[int] = None) -> Tuple[Optional[Partner], str]:
        """Create a new partner."""
        existing = self.get_by_code(partner_code)
        if existing:
            return None, f"Partner with code {partner_code} already exists"
        
        api_key = create_api_key()
        
        partner = Partner(
            partner_code=partner_code,
            partner_name=partner_name,
            description=description,
            api_key=api_key,
            status=PartnerStatus.ACTIVE,
            daily_query_limit=daily_query_limit,
            monthly_query_limit=monthly_query_limit,
            allowed_ips=allowed_ips,
            created_by_id=created_by_id,
        )
        
        self.db.add(partner)
        self.db.commit()
        self.db.refresh(partner)
        
        return partner, ""
    
    def update(self, partner_id: int, **kwargs) -> Tuple[Optional[Partner], str]:
        """Update partner fields."""
        partner = self.get_by_id(partner_id)
        if not partner:
            return None, "Partner not found"
        
        for key, value in kwargs.items():
            if hasattr(partner, key) and value is not None:
                setattr(partner, key, value)
        
        partner.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(partner)
        
        return partner, ""
    
    def regenerate_api_key(self, partner_id: int) -> Tuple[Optional[str], str]:
        """
        Regenerate API key for a partner.
        
        Returns:
            Tuple of (new_api_key or None, error_message)
        """
        partner = self.get_by_id(partner_id)
        if not partner:
            return None, "Partner not found"
        
        new_api_key = create_api_key()
        partner.api_key = new_api_key
        partner.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return new_api_key, ""
    
    def delete(self, partner_id: int) -> bool:
        """Soft delete a partner (set status to inactive)."""
        partner = self.get_by_id(partner_id)
        if not partner:
            return False
        
        partner.status = PartnerStatus.INACTIVE
        partner.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    @staticmethod
    def create_partner(db: Session, name: str, rate_limit: int = 100, daily_limit: int = 10000) -> Tuple[Optional["Partner"], Optional[str]]:
        """Create a new partner account (simplified static method for API compatibility)."""
        import uuid
        partner_id = f"PTNR{uuid.uuid4().hex[:8].upper()}"
        partner_code = f"CODE{uuid.uuid4().hex[:8].upper()}"
        api_key = create_api_key()
        secret_key = create_api_key()
        
        partner = Partner(
            partner_id=partner_id,
            partner_code=partner_code,
            partner_name=name,
            api_key=api_key,
            secret_key=secret_key,
            status=PartnerStatus.ACTIVE,
            daily_query_limit=daily_limit,
            monthly_query_limit=daily_limit * 30,
            rate_limit_per_minute=rate_limit,
            rate_limit_per_day=daily_limit,
            is_api_enabled=True,
            is_revoked=False,
        )
        
        db.add(partner)
        db.commit()
        db.refresh(partner)
        
        return partner, None

    @staticmethod
    def revoke_partner(db: Session, partner_id: int) -> Tuple[bool, str]:
        """Revoke a partner account."""
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            return False, "Partner not found"
        
        partner.is_revoked = True
        partner.updated_at = datetime.utcnow()
        db.commit()
        return True, "Partner revoked successfully"

    @staticmethod
    def regenerate_keys(db: Session, partner_id: int) -> Tuple[Optional["Partner"], Optional[str]]:
        """Regenerate API keys for a partner."""
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            return None, "Partner not found"
        
        partner.api_key = create_api_key()
        partner.secret_key = create_api_key()
        partner.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(partner)
        
        return partner, None

    @staticmethod
    def get_partner_by_api_key(db: Session, api_key: str) -> Optional["Partner"]:
        """Get partner by API key (static method for API compatibility)."""
        return db.query(Partner).filter(Partner.api_key == api_key).first()

    @staticmethod
    def check_rate_limit(db: Session, partner_id: int) -> Tuple[bool, Optional[str]]:
        """Check if partner has exceeded rate limits (static method for API compatibility)."""
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            return False, "Partner not found"
        
        if partner.today_query_count >= partner.daily_query_limit:
            return False, f"Daily query limit exceeded ({partner.daily_query_limit})"
        
        return True, None

    @staticmethod
    def check_daily_limit(db: Session, partner_id: int) -> Tuple[bool, Optional[str]]:
        """Check if partner has exceeded daily limits (static method for API compatibility)."""
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            return False, "Partner not found"
        
        if partner.today_query_count >= partner.daily_query_limit:
            return False, f"Daily limit exceeded ({partner.today_query_count}/{partner.daily_query_limit})"
        
        return True, None

    @staticmethod
    def increment_usage(db: Session, partner_id: int):
        """Increment partner's usage counters (static method for API compatibility)."""
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if partner:
            partner.today_query_count += 1
            partner.last_query_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def verify_signature(api_key: str, signature: str, timestamp: int, secret_key: str) -> Tuple[bool, Optional[str]]:
        """Verify HMAC-SHA256 signature for Partner API auth."""
        import hmac
        import hashlib
        
        # Check timestamp is within 5 minutes
        current_time = int(time.time())
        if abs(current_time - timestamp) > 300:
            return False, "Timestamp expired"
        
        # Compute expected signature
        message = f"{api_key}{timestamp}"
        expected_signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return False, "Invalid signature"
        
        return True, None
    
    def verify_api_key(self, api_key: str) -> Tuple[Optional[Partner], str]:
        """
        Verify API key and check partner status.
        
        Returns:
            Tuple of (Partner or None, error_message)
        """
        partner = self.get_by_api_key(api_key)
        
        if not partner:
            return None, "Invalid API key"
        
        if partner.status == PartnerStatus.INACTIVE:
            return None, "Partner account is inactive"
        
        if partner.status == PartnerStatus.SUSPENDED:
            return None, "Partner account is suspended"
        
        return partner, ""
    
    def check_ip_whitelist(self, partner: Partner, ip: str) -> bool:
        """
        Check if IP is in partner's allowed IPs list.
        
        Returns True if allowed or no whitelist configured.
        """
        if not partner.allowed_ips:
            return True
        
        allowed_list = [ip.strip() for ip in partner.allowed_ips.split(',')]
        return ip in allowed_list

    def increment_query_count(self, partner_id: int):
        """Increment partner's query counters."""
        partner = self.get_by_id(partner_id)
        if partner:
            partner.today_query_count += 1
            partner.this_month_query_count += 1
            partner.last_query_at = datetime.utcnow()
            self.db.commit()
    
    def reset_daily_counters(self):
        """Reset daily query counters for all partners."""
        partners = self.db.query(Partner).all()
        for partner in partners:
            partner.today_query_count = 0
        self.db.commit()
    
    def reset_monthly_counters(self):
        """Reset monthly query counters for all partners."""
        partners = self.db.query(Partner).all()
        for partner in partners:
            partner.this_month_query_count = 0
            partner.today_query_count = 0
        self.db.commit()
    
    def query_debtor(self, partner: Partner, debtor_number: Optional[str] = None,
                     name: Optional[str] = None, id_card: Optional[str] = None,
                     phone: Optional[str] = None, query_ip: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
        """
        Query debtor data for a partner.
        
        Returns:
            Tuple of (result_dict, error_message)
        """
        is_allowed, error = PartnerService.check_rate_limit(self.db, partner.id)
        if not is_allowed:
            return {'success': False, 'error_code': 'RATE_LIMIT', 'error_message': error}, error
        
        if query_ip and not self.check_ip_whitelist(partner, query_ip):
            return {'success': False, 'error_code': 'IP_NOT_ALLOWED', 'error_message': 'IP not allowed'}, "IP not allowed"
        
        debtor_query = self.db.query(Debtor).filter(Debtor.is_deleted == False)
        
        if debtor_number:
            debtor_query = debtor_query.filter(Debtor.debtor_number == debtor_number)
        if name:
            debtor_query = debtor_query.filter(Debtor.name.contains(name))
        if id_card:
            debtor_query = debtor_query.filter(Debtor.id_card.contains(id_card))
        
        debtor = debtor_query.first()
        
        self.increment_query_count(partner.id)
        
        if not debtor:
            return {'success': False, 'error_code': 'NOT_FOUND', 'error_message': 'Debtor not found'}, "Debtor not found"
        
        query_log = QueryLog(
            debtor_id=debtor.id,
            query_type='partner_api',
            query_channel='partner',
            partner_id=partner.id,
            query_ip=query_ip,
            success=True,
        )
        self.db.add(query_log)
        
        debtor.last_query_at = datetime.utcnow()
        debtor.query_count += 1
        
        self.db.commit()
        
        phone_decrypted = None
        if debtor.encrypted_phone and debtor.phone_nonce and debtor.phone_tag:
            try:
                phone_decrypted = phone_encryption.decrypt_from_storage(
                    debtor.encrypted_phone,
                    debtor.phone_nonce,
                    debtor.phone_tag
                )
            except:
                phone_decrypted = None
        
        result = {
            'success': True,
            'data': {
                'debtor_number': debtor.debtor_number,
                'name': debtor.name,
                'id_card': debtor.id_card,
                'phone': phone_decrypted,
                'email': debtor.email,
                'bank_name': debtor.bank_name,
                'bank_account': debtor.bank_account,
                'bank_account_name': debtor.bank_account_name,
                'address': debtor.address,
                'status': debtor.status.value,
                'overdue_amount': debtor.overdue_amount,
                'overdue_days': debtor.overdue_days,
            }
        }
        
        partner_query_log = PartnerQueryLog(
            partner_id=partner.id,
            debtor_id=debtor.id,
            query_data=f"number:{debtor_number},name:{name},id_card:{id_card}",
            response_data=str(result),
            query_ip=query_ip,
            status_code=200,
        )
        self.db.add(partner_query_log)
        self.db.commit()
        
        return result, ""
    
    def log_query_error(self, partner: Partner, query_data: str, error_message: str,
                        status_code: int, query_ip: Optional[str] = None):
        """Log a partner query error."""
        log = PartnerQueryLog(
            partner_id=partner.id,
            query_data=query_data,
            status_code=status_code,
            error_message=error_message,
            query_ip=query_ip,
        )
        self.db.add(log)
        self.db.commit()
    
    def get_query_logs(self, partner_id: int, skip: int = 0, limit: int = 100) -> List[PartnerQueryLog]:
        """Get query logs for a partner."""
        return self.db.query(PartnerQueryLog).filter(
            PartnerQueryLog.partner_id == partner_id
        ).order_by(PartnerQueryLog.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_stats(self, partner: Partner) -> Dict[str, Any]:
        """Get partner statistics."""
        return {
            'partner_code': partner.partner_code,
            'partner_name': partner.partner_name,
            'today_query_count': partner.today_query_count,
            'this_month_query_count': partner.this_month_query_count,
            'daily_limit': partner.daily_query_limit,
            'monthly_limit': partner.monthly_query_limit,
            'remaining_today': partner.daily_query_limit - partner.today_query_count,
            'remaining_this_month': partner.monthly_query_limit - partner.this_month_query_count,
        }
