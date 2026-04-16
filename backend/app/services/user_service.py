from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User, UserRole, UserStatus
from app.models.sms import SMSLog, SMSType, SMSStatus
from app.core.security import get_password_hash, verify_password, create_access_token, create_h5_token, create_api_key
from app.core.config import settings
from app.plugins.sms.manager import sms_manager


class UserService:
    """
    Service for user management operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone."""
        return self.db.query(User).filter(User.phone == phone).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def get_by_role(self, role: UserRole) -> List[User]:
        """Get users by role."""
        return self.db.query(User).filter(User.role == role).all()
    
    def create(self, username: str, password: str, email: Optional[str] = None,
               phone: Optional[str] = None, full_name: Optional[str] = None,
               role: UserRole = UserRole.VIEWER, created_by_id: Optional[int] = None) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            phone=phone,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            status=UserStatus.ACTIVE,
            created_by_id=created_by_id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields."""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_password(self, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
        """Update user password."""
        user = self.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        if not verify_password(old_password, user.hashed_password):
            return False, "Current password is incorrect"
        
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True, "Password updated successfully"
    
    def reset_password_by_admin(self, user_id: int, new_password: str, admin_user_id: int) -> tuple[bool, str]:
        """Reset user password by admin."""
        admin = self.get_by_id(admin_user_id)
        if not admin or not admin.is_superadmin:
            return False, "Only superadmin can reset passwords"
        
        user = self.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True, "Password reset successfully"
    
    def authenticate(self, username: str, password: str) -> tuple[Optional[User], str]:
        """
        Authenticate user with username and password.
        
        Returns:
            Tuple of (User or None, error_message)
        """
        user = self.get_by_username(username)
        
        if not user:
            return None, "Invalid username or password"
        
        if user.status == UserStatus.LOCKED:
            if user.locked_until and user.locked_until > datetime.utcnow():
                remaining = (user.locked_until - datetime.utcnow()).seconds // 60
                return None, f"Account is locked. Try again in {remaining} minutes"
            else:
                user.status = UserStatus.ACTIVE
                user.login_attempts = 0
                self.db.commit()
        
        if user.status == UserStatus.INACTIVE:
            return None, "Account is inactive"
        
        if not verify_password(password, user.hashed_password):
            user.login_attempts += 1
            
            if user.login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.status = UserStatus.LOCKED
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
                self.db.commit()
                return None, f"Too many failed attempts. Account locked for {settings.LOCKOUT_DURATION_MINUTES} minutes"
            
            self.db.commit()
            remaining = settings.MAX_LOGIN_ATTEMPTS - user.login_attempts
            return None, f"Invalid password. {remaining} attempts remaining"
        
        user.login_attempts = 0
        user.last_login_at = datetime.utcnow()
        self.db.commit()
        
        return user, ""
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user."""
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value.lower(),
            "is_superadmin": user.is_superadmin,
        }
        return create_access_token(token_data)
    
    def create_h5_token_for_user(self, phone: str, sms_code: str) -> tuple[Optional[str], str]:
        """
        Create H5 token after verifying SMS code.
        
        Returns:
            Tuple of (token or None, error_message)
        """
        sms_log = self.db.query(SMSLog).filter(
            SMSLog.phone == phone,
            SMSLog.sms_type == SMSType.VERIFICATION,
            SMSLog.status == SMSStatus.DELIVERED,
        ).order_by(SMSLog.created_at.desc()).first()
        
        if not sms_log:
            return None, "No valid SMS code found"
        
        if not sms_log.message or sms_code != sms_log.message.strip():
            return None, "Invalid SMS code"
        
        hours_since_sent = (datetime.utcnow() - sms_log.created_at).total_seconds() / 3600
        if hours_since_sent > 1:
            return None, "SMS code has expired"
        
        token_data = {
            "sub": phone,
            "phone": phone,
            "type": "h5",
        }
        return create_h5_token(token_data), ""
    
    def send_password_reset_sms(self, phone: str) -> tuple[bool, str]:
        """
        Send password reset SMS code.
        
        Returns:
            Tuple of (success, message)
        """
        user = self.get_by_phone(phone)
        if not user:
            return False, "No user found with this phone number"
        
        code = str(random.randint(100000, 999999))
        
        result = sms_manager.send(
            phone=phone,
            message=f"Your password reset code is: {code}",
        )
        
        if result.get('success'):
            sms_log = SMSLog(
                phone=phone,
                message=code,
                sms_type=SMSType.VERIFICATION,
                status=SMSStatus.SENT,
                provider=result.get('provider', 'mock'),
                provider_message_id=result.get('message_id'),
            )
            self.db.add(sms_log)
            self.db.commit()
            return True, "SMS code sent successfully"
        
        return False, "Failed to send SMS"
    
    def reset_password_with_sms(self, phone: str, sms_code: str, new_password: str) -> tuple[bool, str]:
        """
        Reset password using SMS code.
        
        Returns:
            Tuple of (success, message)
        """
        user = self.get_by_phone(phone)
        if not user:
            return False, "No user found with this phone number"
        
        sms_log = self.db.query(SMSLog).filter(
            SMSLog.phone == phone,
            SMSLog.sms_type == SMSType.VERIFICATION,
        ).order_by(SMSLog.created_at.desc()).first()
        
        if not sms_log or sms_log.message != sms_code:
            return False, "Invalid SMS code"
        
        hours_since_sent = (datetime.utcnow() - sms_log.created_at).total_seconds() / 3600
        if hours_since_sent > 1:
            return False, "SMS code has expired"
        
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        sms_log.status = SMSStatus.DELIVERED
        self.db.commit()
        
        return True, "Password reset successfully"
    
    def delete(self, user_id: int) -> bool:
        """Soft delete a user."""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def hard_delete(self, user_id: int) -> bool:
        """Permanently delete a user."""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True


import random
