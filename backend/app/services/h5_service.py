from sqlalchemy.orm import Session
from typing import Optional, Tuple, List
from datetime import datetime, timedelta
import random
import hashlib
from app.models.models import H5User, Debtor, PaymentAccount
from app.core.security import create_h5_token
from app.core.config import settings


class H5AuthService:
    """H5 (mobile) authentication service"""
    
    @staticmethod
    def generate_captcha() -> str:
        """Generate a 6-digit captcha"""
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def request_captcha(db: Session, phone: str) -> Tuple[str, int]:
        """
        Request a captcha for phone verification.
        Returns (captcha_id, expires_in_seconds)
        """
        # Check if user is locked
        user = db.query(H5User).filter(H5User.phone == phone).first()
        if user and user.is_locked and user.locked_until and user.locked_until > datetime.utcnow():
            remaining = (user.locked_until - datetime.utcnow()).seconds
            raise ValueError(f"Account locked. Try again in {remaining // 60} minutes")
        
        captcha = H5AuthService.generate_captcha()
        expires_at = datetime.utcnow() + timedelta(seconds=settings.CAPTCHA_EXPIRE_SECONDS)
        
        if user:
            user.captcha = captcha
            user.captcha_expire_at = expires_at
        else:
            user = H5User(
                phone=phone,
                captcha=captcha,
                captcha_expire_at=expires_at
            )
            db.add(user)
        
        db.commit()
        return captcha, settings.CAPTCHA_EXPIRE_SECONDS
    
    @staticmethod
    def verify_captcha(db: Session, phone: str, captcha: str) -> Tuple[bool, str]:
        """
        Verify captcha and return access token.
        Returns (success, message_or_token)
        """
        user = db.query(H5User).filter(H5User.phone == phone).first()
        if not user:
            return False, "Phone not registered"
        
        # Check if user is locked
        if user.is_locked and user.locked_until and user.locked_until > datetime.utcnow():
            return False, "Account is locked"
        
        # Verify captcha
        if not user.captcha or user.captcha != captcha:
            user.verification_attempts += 1
            
            if user.verification_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.is_locked = True
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
                db.commit()
                return False, f"Too many failed attempts. Account locked for {settings.LOCKOUT_DURATION_MINUTES} minutes"
            
            db.commit()
            remaining = settings.MAX_LOGIN_ATTEMPTS - user.verification_attempts
            return False, f"Invalid captcha. {remaining} attempts remaining"
        
        # Check captcha expiry
        if not user.captcha_expire_at or user.captcha_expire_at < datetime.utcnow():
            return False, "Captcha expired"
        
        # Clear captcha and reset attempts on success
        user.captcha = None
        user.captcha_expire_at = None
        user.verification_attempts = 0
        user.is_locked = False
        user.locked_until = None
        db.commit()
        
        # Generate access token
        token = create_h5_token(data={"phone": phone, "sub": str(user.id)})
        return True, token
    
    @staticmethod
    def get_user_by_phone(db: Session, phone: str) -> Optional[H5User]:
        """Get H5 user by phone"""
        return db.query(H5User).filter(H5User.phone == phone).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[H5User]:
        """Get H5 user by ID"""
        return db.query(H5User).filter(H5User.id == user_id).first()
    
    @staticmethod
    def check_daily_limit(db: Session, user_id: int) -> bool:
        """Check if user has exceeded daily query limit"""
        user = db.query(H5User).filter(H5User.id == user_id).first()
        if not user:
            return False
        
        today = datetime.utcnow().date()
        
        # Reset counter if it's a new day
        if user.query_date and user.query_date.date() < today:
            user.daily_query_count = 0
            user.query_date = datetime.utcnow()
            db.commit()
        
        return user.daily_query_count < settings.H5_DAILY_QUERY_LIMIT
    
    @staticmethod
    def increment_query_count(db: Session, user_id: int) -> None:
        """Increment user's daily query count"""
        user = db.query(H5User).filter(H5User.id == user_id).first()
        if user:
            user.daily_query_count += 1
            user.last_query_at = datetime.utcnow()
            if not user.query_date or user.query_date.date() < datetime.utcnow().date():
                user.query_date = datetime.utcnow()
            db.commit()


class H5DebtInfoService:
    """H5 debt information query service"""
    
    @staticmethod
    def query_debt_info(db: Session, h5_user_id: int, debtor_id_card: str) -> Tuple[Optional[dict], str]:
        """
        Query debt information for a debtor.
        Returns (debt_info_dict, error_message)
        """
        # Check daily limit
        if not H5AuthService.check_daily_limit(db, h5_user_id):
            return None, f"Daily query limit ({settings.H5_DAILY_QUERY_LIMIT}) exceeded"
        
        # Find debtor by ID card
        debtor = db.query(Debtor).filter(Debtor.id_card == debtor_id_card).first()
        if not debtor:
            return None, "No debt record found"
        
        # Increment query count
        H5AuthService.increment_query_count(db, h5_user_id)
        
        db.commit()
        
        return {
            "debtor_id": debtor.id,
            "name": debtor.name,
            "id_card": debtor.id_card,
            "phone": debtor.encrypted_phone,
            "debt_amount": debtor.overdue_amount,
            "status": debtor.status.value,
            "query_time": datetime.utcnow().isoformat()
        }, ""
    
    @staticmethod
    def get_payment_accounts(db: Session) -> List[PaymentAccount]:
        """Get all active payment accounts"""
        return db.query(PaymentAccount).filter(PaymentAccount.is_active == True).all()
