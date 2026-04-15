from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db
from app.models.models import User
from app.schemas.schemas import ConfigCreate, ConfigUpdate, ConfigResponse, ConfigChangeLogResponse
from app.services.config_service import ConfigService
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/configs", tags=["configs"])


@router.post("/", response_model=ConfigResponse)
def create_config(
    config: ConfigCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new configuration (admin only)"""
    result, error = ConfigService.create_config(
        db,
        config_key=config.config_key,
        config_value=config.config_value,
        description=config.description,
        changed_by=current_user.id
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.get("/{config_id}", response_model=ConfigResponse)
def get_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get configuration by ID"""
    config = ConfigService.get_config(db, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return config


@router.get("/key/{config_key}", response_model=ConfigResponse)
def get_config_by_key(
    config_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get configuration by key"""
    config = ConfigService.get_config_by_key(db, config_key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return config


@router.get("/", response_model=List[ConfigResponse])
def list_configs(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List configurations"""
    configs = ConfigService.list_configs(db, skip, limit, is_active)
    return configs


@router.put("/{config_id}", response_model=ConfigResponse)
def update_config(
    config_id: int,
    config: ConfigUpdate,
    change_reason: str = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update configuration (admin only)"""
    update_data = config.model_dump(exclude_unset=True)
    result, error = ConfigService.update_config(
        db, config_id,
        changed_by=current_user.id,
        change_reason=change_reason,
        **update_data
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.post("/switch/{config_key}")
def switch_config(
    config_key: str,
    new_value: str,
    reason: str = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Quick switch a configuration value (admin only)"""
    result, error = ConfigService.switch_config(
        db, config_key, new_value,
        changed_by=current_user.id,
        reason=reason
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )
    
    return {"message": f"Config '{config_key}' switched to '{new_value}'"}


@router.delete("/{config_id}")
def delete_config(
    config_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a configuration (admin only)"""
    success, error = ConfigService.delete_config(db, config_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Configuration deleted"}


@router.get("/{config_id}/logs", response_model=List[ConfigChangeLogResponse])
def get_config_logs(
    config_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get change history for a configuration"""
    logs = ConfigService.get_change_logs(db, config_id, skip, limit)
    return logs


@router.get("/logs/all", response_model=List[ConfigChangeLogResponse])
def get_all_config_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all configuration change logs (admin only)"""
    logs = ConfigService.get_all_change_logs(db, skip, limit)
    return logs
