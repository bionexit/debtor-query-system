from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Tuple
from app.models.models import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings


class AuthService:
    """Admin authentication service"""
    
    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Tuple[Optional[User], str]:
        """
        Authenticate user with username and password.
        Returns (user, error_message)
        """
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None, "Invalid username or password"
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            return None, f"Account locked. Try again in {remaining} minutes"
        
        if not verify_password(password, user.hashed_password):
            user.login_attempts += 1
            
            if user.login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
                db.commit()
                return None, f"Account locked due to {settings.MAX_LOGIN_ATTEMPTS} failed attempts"
            
            db.commit()
            remaining = settings.MAX_LOGIN_ATTEMPTS - user.login_attempts
            return None, f"Invalid password. {remaining} attempts remaining"
        
        # Check status enum (ACTIVE/INACTIVE/LOCKED)
        from app.models.user import UserStatus
        if user.status == UserStatus.INACTIVE:
            return None, "Account is deactivated"
        
        # Reset login attempts on successful login
        user.login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return user, ""
    
    @staticmethod
    def create_token(user: User) -> str:
        """Create JWT access token for user"""
        return create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role.value.lower()}
        )
    
    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str, role: UserRole = UserRole.OPERATOR) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        if not verify_password(old_password, user.hashed_password):
            return False, "Current password is incorrect"
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True, "Password changed successfully"
    
    @staticmethod
    def unlock_user(db: Session, user_id: int) -> Tuple[bool, str]:
        """Unlock a locked user account"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        db.commit()
        return True, "User unlocked successfully"
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> list:
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True
