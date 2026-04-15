from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user
from app.schemas.debtor import (
    DebtorCreate, DebtorUpdate, DebtorResponse, DebtorQueryRequest, DebtorQueryResponse,
    DebtorImportResult, QueryLogResponse, ImportBatchResponse
)
from app.services.debtor_service import DebtorService
from app.models.user import User
import tempfile
import os
import shutil

router = APIRouter(prefix="/debtors", tags=["Debtors"])


@router.get("/", response_model=List[DebtorResponse])
def list_debtors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all debtors with pagination."""
    debtor_service = DebtorService(db)
    
    from app.models.debtor import DebtorStatus
    status_enum = DebtorStatus(status) if status else None
    
    debtors = debtor_service.get_all(skip=skip, limit=limit, status=status_enum)
    return [DebtorResponse.model_validate(d) for d in debtors]


@router.get("/stats")
def get_debtor_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get debtor statistics."""
    debtor_service = DebtorService(db)
    return debtor_service.get_debtor_stats()


@router.get("/{debtor_id}", response_model=DebtorResponse)
def get_debtor(
    debtor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get debtor by ID."""
    debtor_service = DebtorService(db)
    debtor = debtor_service.get_by_id(debtor_id)
    
    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")
    
    return DebtorResponse.model_validate(debtor)


@router.get("/{debtor_id}/phone")
def get_debtor_phone(
    debtor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get decrypted debtor phone number."""
    debtor_service = DebtorService(db)
    debtor = debtor_service.get_by_id(debtor_id)
    
    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")
    
    phone = debtor_service.decrypt_phone(debtor)
    
    return {"phone": phone}


@router.post("/", response_model=DebtorResponse, status_code=status.HTTP_201_CREATED)
def create_debtor(
    debtor_data: DebtorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new debtor."""
    debtor_service = DebtorService(db)
    debtor, error = debtor_service.create(
        debtor_number=debtor_data.debtor_number,
        name=debtor_data.name,
        id_card=debtor_data.id_card,
        phone=debtor_data.phone,
        email=debtor_data.email,
        bank_name=debtor_data.bank_name,
        bank_account=debtor_data.bank_account,
        bank_account_name=debtor_data.bank_account_name,
        address=debtor_data.address,
        remark=debtor_data.remark,
        status=debtor_data.status,
        overdue_amount=debtor_data.overdue_amount,
        overdue_days=debtor_data.overdue_days,
        created_by_id=current_user.id
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return DebtorResponse.model_validate(debtor)


@router.put("/{debtor_id}", response_model=DebtorResponse)
def update_debtor(
    debtor_id: int,
    debtor_data: DebtorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update debtor information."""
    debtor_service = DebtorService(db)
    
    update_data = debtor_data.model_dump(exclude_unset=True)
    
    debtor, error = debtor_service.update(debtor_id, updated_by_id=current_user.id, **update_data)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return DebtorResponse.model_validate(debtor)


@router.delete("/{debtor_id}")
def delete_debtor(
    debtor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a debtor."""
    debtor_service = DebtorService(db)
    success = debtor_service.delete(debtor_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Debtor not found")
    
    return {"message": "Debtor deleted successfully"}


@router.get("/{debtor_id}/query-logs", response_model=List[QueryLogResponse])
def get_debtor_query_logs(
    debtor_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get query logs for a debtor."""
    debtor_service = DebtorService(db)
    logs = debtor_service.get_query_logs(debtor_id, skip=skip, limit=limit)
    return [QueryLogResponse.model_validate(log) for log in logs]


@router.post("/import")
async def import_debtors(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import debtors from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        debtor_service = DebtorService(db)
        
        batch = debtor_service.create_import_batch(
            filename=file.filename,
            file_path=temp_file_path,
            created_by_id=current_user.id
        )
        
        background_tasks.add_task(debtor_service.import_from_batch, batch.id)
        
        return {
            "message": "Import started in background",
            "batch_id": batch.id,
            "filename": file.filename
        }
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/imports/history", response_model=List[ImportBatchResponse])
def get_import_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get import batch history."""
    debtor_service = DebtorService(db)
    batches = debtor_service.get_import_batches(skip=skip, limit=limit)
    return [ImportBatchResponse.model_validate(b) for b in batches]
