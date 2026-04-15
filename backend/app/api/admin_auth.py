from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.schemas.schemas import LoginRequest, LoginResponse, ChangePasswordRequest
from app.services.auth_service import AuthService
from app.api.deps import get_current_user, require_admin
from app.models.models import User

router = APIRouter(prefix="/api/admin/auth", tags=["admin_auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Admin login endpoint"""
    user, error = AuthService.authenticate(db, request.username, request.password)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    token = AuthService.create_token(user)
    
    return LoginResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        role=user.role.value
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Admin logout endpoint"""
    return {"message": "Logged out successfully"}


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    success, message = AuthService.change_password(
        db, current_user.id, request.old_password, request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}


@router.post("/unlock/{user_id}")
def unlock_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Unlock a user account"""
    success, message = AuthService.unlock_user(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    
    return {"message": message}


@router.get("/users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: List all users"""
    users = AuthService.list_users(db, skip, limit)
    return {"users": users, "total": len(users)}


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Get user details"""
    user = AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/users")
def create_user(
    username: str,
    email: str,
    password: str,
    role: str = "operator",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Create a new user"""
    from app.models.models import UserRole
    
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
        )
    
    user = AuthService.create_user(db, username, email, password, user_role)
    return {"id": user.id, "username": user.username, "message": "User created successfully"}


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    email: str = None,
    role: str = None,
    is_active: bool = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Update user"""
    from app.models.models import UserRole
    
    update_data = {}
    if email is not None:
        update_data["email"] = email
    if role is not None:
        try:
            update_data["role"] = UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role"
            )
    if is_active is not None:
        update_data["is_active"] = is_active
    
    user = AuthService.update_user(db, user_id, **update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: Delete a user"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    success = AuthService.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}
