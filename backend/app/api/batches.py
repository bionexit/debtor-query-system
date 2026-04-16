from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db
from app.models.models import Batch, BatchStatus, User
from app.schemas.schemas import BatchCreate, BatchUpdate, BatchResponse
from app.services.batch_service import BatchService
from app.api.deps import get_current_user, require_operator

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("/", response_model=BatchResponse)
def create_batch(
    batch: BatchCreate,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Create a new batch"""
    result, error = BatchService.create_batch(
        db,
        name=batch.name,
        description=batch.description,
        partner_id=batch.partner_id,
        created_by=current_user.id
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get batch by ID"""
    batch = BatchService.get_batch(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    return batch


@router.get("/", response_model=List[BatchResponse])
def list_batches(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    created_by: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List batches with filters"""
    batch_status = BatchStatus(status) if status else None
    batches = BatchService.list_batches(db, skip, limit, batch_status, created_by)
    return batches


@router.put("/{batch_id}", response_model=BatchResponse)
def update_batch(
    batch_id: int,
    batch: BatchUpdate,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Update batch information"""
    update_data = batch.model_dump(exclude_unset=True)
    result, error = BatchService.update_batch(db, batch_id, **update_data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return result


@router.delete("/{batch_id}")
def delete_batch(
    batch_id: int,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Delete a batch"""
    success, error = BatchService.delete_batch(db, batch_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Batch deleted successfully"}
