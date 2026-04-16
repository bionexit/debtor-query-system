from sqlalchemy.orm import Session
from typing import Optional, Tuple, List
from datetime import datetime
import uuid
from app.models.models import Config, ConfigChangeLog


class ConfigService:
    """System configuration management service"""
    
    @staticmethod
    def create_config(db: Session, config_key: str, config_value: str, 
                      description: str = None, changed_by: int = None) -> Tuple[Optional[Config], str]:
        """Create a new configuration"""
        # Check if key already exists
        existing = db.query(Config).filter(Config.config_key == config_key).first()
        if existing:
            return None, f"Configuration key '{config_key}' already exists"
        
        # Generate config_id from UUID
        config_id = f"CFG-{uuid.uuid4().hex[:8].upper()}"
        
        config = Config(
            config_id=config_id,
            config_key=config_key,
            config_value=config_value,
            description=description,
            changed_by=changed_by,
            is_active=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config, ""
    
    @staticmethod
    def get_config(db: Session, config_id: int) -> Optional[Config]:
        """Get configuration by ID"""
        return db.query(Config).filter(Config.id == config_id).first()
    
    @staticmethod
    def get_config_by_key(db: Session, config_key: str) -> Optional[Config]:
        """Get configuration by key"""
        return db.query(Config).filter(Config.config_key == config_key).first()
    
    @staticmethod
    def list_configs(db: Session, skip: int = 0, limit: int = 100,
                     is_active: bool = None) -> List[Config]:
        """List configurations"""
        query = db.query(Config)
        
        if is_active is not None:
            query = query.filter(Config.is_active == is_active)
        
        return query.order_by(Config.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_config(db: Session, config_id: int, config_value: str = None,
                      description: str = None, is_active: bool = None,
                      changed_by: int = None, change_reason: str = None) -> Tuple[Optional[Config], str]:
        """Update configuration and create change log"""
        config = db.query(Config).filter(Config.id == config_id).first()
        if not config:
            return None, "Configuration not found"
        
        old_value = config.config_value
        
        if config_value is not None:
            config.config_value = config_value
        if description is not None:
            config.description = description
        if is_active is not None:
            config.is_active = is_active
        
        config.changed_by = changed_by
        
        # Create change log
        change_log = ConfigChangeLog(
            config_id=config.id,
            config_name=config.config_key,  # Use config_key as config_name
            config_key=config.config_key,
            old_value=old_value,
            new_value=config_value,
            changed_by=changed_by,
            change_reason=change_reason
        )
        db.add(change_log)
        
        db.commit()
        db.refresh(config)
        return config, ""
    
    @staticmethod
    def delete_config(db: Session, config_id: int) -> Tuple[bool, str]:
        """Delete a configuration (soft delete by setting is_active=False)"""
        config = db.query(Config).filter(Config.id == config_id).first()
        if not config:
            return False, "Configuration not found"
        
        config.is_active = False
        db.commit()
        return True, ""
    
    @staticmethod
    def get_change_logs(db: Session, config_id: int, skip: int = 0, 
                        limit: int = 100) -> List[ConfigChangeLog]:
        """Get change history for a configuration"""
        return db.query(ConfigChangeLog).filter(
            ConfigChangeLog.config_id == config_id
        ).order_by(ConfigChangeLog.changed_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_all_change_logs(db: Session, skip: int = 0, 
                            limit: int = 100) -> List[ConfigChangeLog]:
        """Get all configuration change logs"""
        return db.query(ConfigChangeLog).order_by(
            ConfigChangeLog.changed_at.desc()
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def switch_config(db: Session, config_key: str, new_value: str,
                      changed_by: int = None, reason: str = None) -> Tuple[Optional[Config], str]:
        """Quick switch a config value by key"""
        config = db.query(Config).filter(Config.config_key == config_key).first()
        if not config:
            return None, f"Configuration key '{config_key}' not found"
        
        if not config.is_active:
            return None, f"Configuration '{config_key}' is not active"
        
        old_value = config.config_value
        config.config_value = new_value
        config.changed_by = changed_by
        
        # Create change log
        change_log = ConfigChangeLog(
            config_id=config.id,
            config_name=config.config_key,  # Use config_key as config_name
            config_key=config.config_key,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            change_reason=reason
        )
        db.add(change_log)
        
        db.commit()
        db.refresh(config)
        return config, ""
