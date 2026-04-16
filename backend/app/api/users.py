from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user, require_superadmin
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserPasswordUpdate, PasswordResetByAdminRequest
)
from app.services.user_service import UserService
from app.models.user import User, UserRole

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users (admin/operator access)."""
    if not current_user.is_superadmin and current_user.role not in (UserRole.ADMIN, UserRole.OPERATOR):
        raise HTTPException(status_code=403, detail="Admin or Operator access required")
    
    user_service = UserService(db)
    
    if role:
        users = user_service.get_by_role(role)
    else:
        users = user_service.get_all(skip=skip, limit=limit)
    
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID."""
    if not current_user.is_superadmin and current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user_service = UserService(db)
    user = user_service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)


@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Create a new user (superadmin only)."""
    user_service = UserService(db)
    
    existing = user_service.get_by_username(user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if user_data.email:
        existing = user_service.get_by_email(user_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    if user_data.phone:
        existing = user_service.get_by_phone(user_data.phone)
        if existing:
            raise HTTPException(status_code=400, detail="Phone already exists")
    
    user = user_service.create(
        username=user_data.username,
        password=user_data.password,
        email=user_data.email,
        phone=user_data.phone,
        full_name=user_data.full_name,
        role=user_data.role,
        created_by_id=current_user.id
    )
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user information."""
    if not current_user.is_superadmin and current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user_service = UserService(db)
    
    update_data = user_data.model_dump(exclude_unset=True)
    
    user = user_service.update(user_id, **update_data)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}/password")
def change_password(
    user_id: int,
    password_data: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change own password."""
    if current_user.id != user_id and not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Cannot change other user's password")
    
    user_service = UserService(db)
    success, message = user_service.update_password(user_id, password_data.old_password, password_data.new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


@router.post("/{user_id}/password/reset")
def reset_user_password(
    user_id: int,
    password_data: PasswordResetByAdminRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Reset user password (superadmin only)."""
    user_service = UserService(db)
    success, message = user_service.reset_password_by_admin(user_id, password_data.new_password, current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Delete a user (superadmin only)."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    user_service = UserService(db)
    success = user_service.delete(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}


@router.put("/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user role (admin only)."""
    if not current_user.is_superadmin and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if "role" not in role_data:
        raise HTTPException(status_code=400, detail="Role is required")
    
    # Convert role to uppercase if it's a string
    role_value = role_data["role"]
    if isinstance(role_value, str):
        role_value = role_value.upper()
        try:
            role_value = UserRole(role_value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role_value}")
    
    user_service = UserService(db)
    user = user_service.update(user_id, role=role_value)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user status (admin only)."""
    if not current_user.is_superadmin and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if "status" not in status_data:
        raise HTTPException(status_code=400, detail="Status is required")
    
    # Prevent self-deactivation
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    # Convert status to uppercase if it's a string
    from app.schemas.user import UserStatus
    status_value = status_data["status"]
    if isinstance(status_value, str):
        status_value = status_value.upper()
        try:
            status_value = UserStatus(status_value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_value}")
    
    user_service = UserService(db)
    user = user_service.update(user_id, status=status_value)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)
