from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.models import SmsTask, SMSTaskStatus, SmsTemplate, SmsChannel
from app.schemas.schemas import SMSTaskCreate, SMSTaskResponse, SMSTaskStatus as SMSTaskStatusEnum
from app.services.sms_service import SMSService
from datetime import datetime

router = APIRouter(prefix="/sms/tasks", tags=["SMS Tasks"])


def task_to_response(task: SmsTask) -> SMSTaskResponse:
    """Map SmsTask model to SMSTaskResponse schema."""
    # Handle template_id - it might be stored as string in DB but schema expects int
    try:
        template_id_val = int(task.template_id) if task.template_id else 0
    except (ValueError, TypeError):
        template_id_val = 0
    
    return SMSTaskResponse(
        id=task.id,
        template_id=template_id_val,
        channel_id=0,  # SmsTask doesn't have channel_id field
        recipient_count=len(task.phone_numbers) if task.phone_numbers else 0,
        scheduled_at=task.created_at,
        task_no=task.task_id,
        status=SMSTaskStatus(task.status) if isinstance(task.status, str) else task.status,
        success_count=0,
        fail_count=0,
        created_by=None,
        created_at=task.created_at
    )


@router.post("/", response_model=SMSTaskResponse)
def create_task(
    task_data: SMSTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new SMS task."""
    sms_service = SMSService(db)
    
    # Validate template exists and is active
    template = sms_service.get_template_by_id(task_data.template_id)
    if not template:
        raise HTTPException(status_code=400, detail="Template not found")
    if template.status != "active":
        raise HTTPException(status_code=400, detail="Template is not active")
    
    # Validate channel exists and is active
    channel = db.query(SmsChannel).filter(SmsChannel.id == task_data.channel_id).first()
    if not channel:
        raise HTTPException(status_code=400, detail="Channel not found")
    if channel.status != "active" or not channel.is_active:
        raise HTTPException(status_code=400, detail="Channel is not available")
    
    # Create the task
    import uuid
    task_id = f"TASK_{uuid.uuid4().hex[:12].upper()}"
    
    task = SmsTask(
        task_id=task_id,
        template_id=str(task_data.template_id),
        phone_numbers=task_data.phones,
        user_ids=[],
        variables_data={},
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task_to_response(task)


@router.get("/", response_model=List[SMSTaskResponse])
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List SMS tasks with optional status filter."""
    if not current_user.is_superadmin and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(SmsTask)
    if status:
        query = query.filter(SmsTask.status == status)
    
    tasks = query.order_by(SmsTask.created_at.desc()).offset(skip).limit(limit).all()
    return [task_to_response(t) for t in tasks]


@router.get("/{task_id}", response_model=SMSTaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SMS task by ID."""
    task = db.query(SmsTask).filter(SmsTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_response(task)


@router.post("/{task_id}/send")
def send_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send SMS task."""
    task = db.query(SmsTask).filter(SmsTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status.upper() == "SUCCESS":
        raise HTTPException(status_code=400, detail="Task has already been sent")
    
    # Update task status to sent
    task.status = "sent"
    task.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Task sent successfully"}


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete SMS task."""
    task = db.query(SmsTask).filter(SmsTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status.upper() == "SUCCESS":
        raise HTTPException(status_code=400, detail="Cannot delete a sent task")
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}
