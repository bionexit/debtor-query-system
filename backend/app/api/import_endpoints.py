from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
from app.models.database import get_db
from app.models.models import User
from app.schemas.schemas import ImportResponse
from app.services.import_service import ImportService
from app.api.deps import get_current_user, require_operator

router = APIRouter(prefix="/api/import", tags=["import"])

UPLOAD_DIR = "./imports"


@router.post("/excel", response_model=ImportResponse)
async def import_excel(
    batch_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """Import debtors from Excel file"""
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
    
    # Import debtors
    success_count, fail_count, errors = ImportService.import_debtors(
        db, batch_id, file_path, current_user.id
    )
    
    return ImportResponse(
        batch_id=batch_id,
        total_count=success_count + fail_count,
        success_count=success_count,
        fail_count=fail_count,
        errors=errors[:100]  # Limit errors to first 100
    )


@router.post("/validate")
async def validate_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate an Excel file without importing"""
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
    file_path = os.path.join(UPLOAD_DIR, f"validate_{timestamp}_{file.filename}")
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Validate
    is_valid, error, row_count = ImportService.validate_excel_file(file_path)
    
    # Clean up
    os.remove(file_path)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "valid": True,
        "row_count": row_count,
        "message": f"File is valid with {row_count} rows"
    }
