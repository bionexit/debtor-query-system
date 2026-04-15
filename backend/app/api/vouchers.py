from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
from app.models.database import get_db
from app.models.models import Voucher, VoucherStatus, User
from app.schemas.schemas import VoucherUploadResponse, VoucherReviewRequest, VoucherResponse
from app.services.voucher_service import VoucherService
from app.api.deps import get_current_user, require_operator, require_admin

router = APIRouter(prefix="/api/vouchers", tags=["vouchers"])

UPLOAD_DIR = "./uploads"


@router.post("/upload", response_model=VoucherUploadResponse)
async def upload_voucher(
    file: UploadFile = File(...),
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Upload a voucher file (Excel)"""
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are allowed"
        )
    
    # Create upload directory if not exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{file.filename}")
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(file_path)
    
    # Create voucher record
    voucher = VoucherService.create_voucher(
        db,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        uploaded_by=current_user.id
    )
    
    return VoucherUploadResponse(
        id=voucher.id,
        file_name=voucher.file_name,
        total_count=voucher.total_count,
        status=voucher.status,
        message="File uploaded successfully. Pending review."
    )


@router.get("/{voucher_id}", response_model=VoucherResponse)
def get_voucher(
    voucher_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get voucher by ID"""
    voucher = VoucherService.get_voucher(db, voucher_id)
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )
    return voucher


@router.get("/", response_model=List[VoucherResponse])
def list_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    uploaded_by: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List vouchers with filters"""
    voucher_status = VoucherStatus(status) if status else None
    vouchers = VoucherService.list_vouchers(db, skip, limit, voucher_status, uploaded_by)
    return vouchers


@router.post("/{voucher_id}/approve")
def approve_voucher(
    voucher_id: int,
    review: VoucherReviewRequest = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Approve a voucher (admin only)"""
    comment = review.comment if review else None
    result, error = VoucherService.approve_voucher(db, voucher_id, current_user.id, comment)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Voucher approved successfully", "voucher": result}


@router.post("/{voucher_id}/reject")
def reject_voucher(
    voucher_id: int,
    review: VoucherReviewRequest = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Reject a voucher (admin only)"""
    comment = review.comment if review else None
    result, error = VoucherService.reject_voucher(db, voucher_id, current_user.id, comment)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Voucher rejected", "voucher": result}


@router.delete("/{voucher_id}")
def delete_voucher(
    voucher_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a voucher (admin only)"""
    success, error = VoucherService.delete_voucher(db, voucher_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Voucher deleted successfully"}
