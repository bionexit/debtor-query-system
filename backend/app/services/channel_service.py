from sqlalchemy.orm import Session
from typing import Optional, Tuple, List
from datetime import datetime
import httpx
from app.models.models import SMSChannel, ChannelStatus
from app.core.config import settings


class ChannelService:
    """SMS Channel management service"""
    
    @staticmethod
    def create_channel(db: Session, name: str, provider: str, endpoint: str = None,
                      api_key: str = None, priority: int = 1) -> SMSChannel:
        """Create a new SMS channel"""
        import uuid
        channel = SMSChannel(
            channel_id=f"CH{uuid.uuid4().hex[:8].upper()}",
            channel_code=f"CHANNEL_{uuid.uuid4().hex[:8].upper()}",
            channel_name=name,
            name=name,
            provider=provider,
            endpoint=endpoint,
            api_key=api_key,
            priority=priority,
            status=ChannelStatus.TESTING
        )
        db.add(channel)
        db.commit()
        db.refresh(channel)
        return channel
    
    @staticmethod
    def get_channel(db: Session, channel_id: int) -> Optional[SMSChannel]:
        """Get channel by ID"""
        return db.query(SMSChannel).filter(SMSChannel.id == channel_id).first()
    
    @staticmethod
    def list_channels(db: Session, skip: int = 0, limit: int = 100,
                      status: ChannelStatus = None, is_active: bool = None) -> List[SMSChannel]:
        """List channels with filters"""
        query = db.query(SMSChannel)
        
        if status:
            query = query.filter(SMSChannel.status == status)
        if is_active is not None:
            query = query.filter(SMSChannel.is_active == is_active)
        
        return query.order_by(SMSChannel.priority.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_channel(db: Session, channel_id: int, **kwargs) -> Tuple[Optional[SMSChannel], str]:
        """Update channel information"""
        channel = db.query(SMSChannel).filter(SMSChannel.id == channel_id).first()
        if not channel:
            return None, "Channel not found"
        
        for key, value in kwargs.items():
            if hasattr(channel, key) and value is not None:
                setattr(channel, key, value)
        
        db.commit()
        db.refresh(channel)
        return channel, ""
    
    @staticmethod
    async def test_channel(db: Session, channel_id: int, test_phone: str) -> Tuple[bool, str]:
        """Test SMS channel connectivity"""
        channel = db.query(SMSChannel).filter(SMSChannel.id == channel_id).first()
        if not channel:
            return False, "Channel not found"
        
        if not channel.endpoint:
            return False, "Channel endpoint not configured"
        
        start_time = datetime.utcnow()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.SMS_GATEWAY_URL}/api/test",
                    json={"phone": test_phone, "channel_id": channel_id},
                    timeout=10.0
                )
                
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    # Update channel stats
                    channel.success_rate = (channel.success_rate * 0.7 + 100 * 0.3)  # Rolling average
                    channel.avg_response_time = (channel.avg_response_time * 0.7 + response_time * 0.3)
                    channel.status = ChannelStatus.ACTIVE
                    channel.is_active = True
                    db.commit()
                    return True, f"Test successful (response time: {response_time:.2f}ms)"
                else:
                    channel.success_rate = channel.success_rate * 0.7  # Decrease success rate
                    db.commit()
                    return False, f"Test failed with status {response.status_code}"
                    
        except httpx.TimeoutException:
            channel.success_rate = channel.success_rate * 0.7
            db.commit()
            return False, "Test timed out"
        except Exception as e:
            channel.success_rate = channel.success_rate * 0.7
            db.commit()
            return False, f"Test failed: {str(e)}"
    
    @staticmethod
    def enable_channel(db: Session, channel_id: int) -> Tuple[Optional[SMSChannel], str]:
        """Enable a channel"""
        channel = db.query(SMSChannel).filter(SMSChannel.id == channel_id).first()
        if not channel:
            return None, "Channel not found"
        
        channel.is_active = True
        channel.status = ChannelStatus.ACTIVE
        db.commit()
        db.refresh(channel)
        return channel, ""
    
    @staticmethod
    def disable_channel(db: Session, channel_id: int) -> Tuple[Optional[SMSChannel], str]:
        """Disable a channel"""
        channel = db.query(SMSChannel).filter(SMSChannel.id == channel_id).first()
        if not channel:
            return None, "Channel not found"
        
        channel.is_active = False
        channel.status = ChannelStatus.INACTIVE
        db.commit()
        db.refresh(channel)
        return channel, ""
    
    @staticmethod
    def delete_channel(db: Session, channel_id: int) -> Tuple[bool, str]:
        """Delete a channel"""
        channel = db.query(SMSChannel).filter(SMSChannel.id == channel_id).first()
        if not channel:
            return False, "Channel not found"
        
        if channel.status == ChannelStatus.TESTING:
            db.delete(channel)
            db.commit()
            return True, ""
        
        return False, "Can only delete channels in testing status"
    
    @staticmethod
    def get_active_channels(db: Session) -> List[SMSChannel]:
        """Get all active channels ordered by priority"""
        return db.query(SMSChannel).filter(
            SMSChannel.status == ChannelStatus.ACTIVE,
            SMSChannel.is_active == True
        ).order_by(SMSChannel.priority.desc()).all()
