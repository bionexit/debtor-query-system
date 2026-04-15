from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db
from app.models.models import User, ChannelStatus
from app.schemas.schemas import ChannelCreate, ChannelUpdate, ChannelResponse, ChannelTestRequest
from app.services.channel_service import ChannelService
from app.api.deps import get_current_user, require_operator

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.post("/", response_model=ChannelResponse)
def create_channel(
    channel: ChannelCreate,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Create a new SMS channel"""
    result = ChannelService.create_channel(
        db,
        name=channel.name,
        provider=channel.provider,
        endpoint=channel.endpoint,
        api_key=channel.api_key,
        priority=channel.priority
    )
    return result


@router.get("/{channel_id}", response_model=ChannelResponse)
def get_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get channel by ID"""
    channel = ChannelService.get_channel(db, channel_id)
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    return channel


@router.get("/", response_model=List[ChannelResponse])
def list_channels(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List channels with filters"""
    channel_status = ChannelStatus(status) if status else None
    channels = ChannelService.list_channels(db, skip, limit, channel_status, is_active)
    return channels


@router.put("/{channel_id}", response_model=ChannelResponse)
def update_channel(
    channel_id: int,
    channel: ChannelUpdate,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Update channel information"""
    update_data = channel.model_dump(exclude_unset=True)
    result, error = ChannelService.update_channel(db, channel_id, **update_data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.post("/{channel_id}/test")
def test_channel(
    channel_id: int,
    request: ChannelTestRequest,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Test SMS channel connectivity"""
    from app.services.channel_service import ChannelService
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success, message = loop.run_until_complete(
        ChannelService.test_channel(db, channel_id, request.phone)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message}


@router.post("/{channel_id}/enable")
def enable_channel(
    channel_id: int,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Enable a channel"""
    result, error = ChannelService.enable_channel(db, channel_id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )
    
    return {"message": "Channel enabled", "channel": result}


@router.post("/{channel_id}/disable")
def disable_channel(
    channel_id: int,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Disable a channel"""
    result, error = ChannelService.disable_channel(db, channel_id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )
    
    return {"message": "Channel disabled", "channel": result}


@router.delete("/{channel_id}")
def delete_channel(
    channel_id: int,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Delete a channel"""
    success, error = ChannelService.delete_channel(db, channel_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Channel deleted successfully"}
