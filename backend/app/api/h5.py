from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import verify_token
from app.schemas.debtor import DebtorQueryResponse
from app.services.debtor_service import DebtorService
from app.models.user import User
import uuid

router = APIRouter(prefix="/h5", tags=["H5 API"])

h5_tokens = {}


def verify_h5_token(token: str) -> Optional[dict]:
    """Verify H5 token."""
    payload = verify_token(token)
    if payload and payload.get("type") == "h5":
        return payload
    return None


def get_h5_user(request: Request, db: Session = Depends(get_db)) -> dict:
    """Get H5 user from token in Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_h5_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired H5 token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"phone": payload.get("phone"), "token": token}


@router.get("/query", response_model=List[DebtorQueryResponse])
def h5_query_debtors(
    request: Request,
    debtor_number: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    id_card: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Query debtors via H5 API.
    Requires H5 authentication token.
    """
    h5_user = get_h5_user(request, db)
    
    client_ip = request.client.host if request.client else None
    
    debtor_service = DebtorService(db)
    debtors, total, error = debtor_service.query_by_fields(
        debtor_number=debtor_number,
        name=name,
        id_card=id_card,
        query_type="h5_query",
        query_channel="h5",
        query_ip=client_ip,
        page=page,
        page_size=page_size
    )
    
    result = []
    for debtor in debtors:
        result.append(DebtorQueryResponse(
            debtor_number=debtor.debtor_number,
            name=debtor.name,
            id_card=debtor.id_card,
            phone=debtor_service.decrypt_phone(debtor) if debtor.encrypted_phone else None,
            email=debtor.email,
            bank_name=debtor.bank_name,
            bank_account=debtor.bank_account,
            bank_account_name=debtor.bank_account_name,
            address=debtor.address,
            status=debtor.status,
            overdue_amount=debtor.overdue_amount,
            overdue_days=debtor.overdue_days,
        ))
    
    return result


@router.get("/debtor/{debtor_number}", response_model=DebtorQueryResponse)
def h5_get_debtor(
    debtor_number: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get specific debtor by debtor number via H5 API.
    Requires H5 authentication token.
    """
    h5_user = get_h5_user(request, db)
    
    client_ip = request.client.host if request.client else None
    
    debtor_service = DebtorService(db)
    debtor = debtor_service.get_by_debtor_number(debtor_number)
    
    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")
    
    _, _ = debtor_service.query(
        debtor_id=debtor.id,
        query_type="h5_detail",
        query_channel="h5",
        query_ip=client_ip
    )
    
    return DebtorQueryResponse(
        debtor_number=debtor.debtor_number,
        name=debtor.name,
        id_card=debtor.id_card,
        phone=debtor_service.decrypt_phone(debtor) if debtor.encrypted_phone else None,
        email=debtor.email,
        bank_name=debtor.bank_name,
        bank_account=debtor.bank_account,
        bank_account_name=debtor.bank_account_name,
        address=debtor.address,
        status=debtor.status,
        overdue_amount=debtor.overdue_amount,
        overdue_days=debtor.overdue_days,
    )


@router.get("/stats")
def h5_get_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get debtor statistics via H5 API.
    Requires H5 authentication token.
    """
    h5_user = get_h5_user(request, db)
    
    debtor_service = DebtorService(db)
    return debtor_service.get_debtor_stats()
