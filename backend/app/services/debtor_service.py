from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.models.debtor import Debtor, DebtorStatus, QueryLog, ImportBatch
from app.models.partner import Partner
from app.utils.encryption import phone_encryption
from app.utils.validators import PhoneValidator, DebtorNumberValidator, IDCardValidator


class DebtorService:
    """
    Service for debtor management operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, debtor_id: int) -> Optional[Debtor]:
        """Get debtor by ID."""
        return self.db.query(Debtor).filter(
            Debtor.id == debtor_id,
            Debtor.is_deleted == False
        ).first()
    
    def get_by_debtor_number(self, debtor_number: str) -> Optional[Debtor]:
        """Get debtor by debtor number."""
        return self.db.query(Debtor).filter(
            Debtor.debtor_number == debtor_number,
            Debtor.is_deleted == False
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, status: Optional[DebtorStatus] = None) -> List[Debtor]:
        """Get all debtors with pagination."""
        query = self.db.query(Debtor).filter(Debtor.is_deleted == False)
        if status:
            query = query.filter(Debtor.status == status)
        return query.offset(skip).limit(limit).all()
    
    def count(self, status: Optional[DebtorStatus] = None) -> int:
        """Count debtors."""
        query = self.db.query(func.count(Debtor.id)).filter(Debtor.is_deleted == False)
        if status:
            query = query.filter(Debtor.status == status)
        return query.scalar()
    
    def search(self, debtor_number: Optional[str] = None, name: Optional[str] = None,
               id_card: Optional[str] = None, phone: Optional[str] = None,
               skip: int = 0, limit: int = 100) -> List[Debtor]:
        """Search debtors by various fields."""
        query = self.db.query(Debtor).filter(Debtor.is_deleted == False)
        
        if debtor_number:
            query = query.filter(Debtor.debtor_number.contains(debtor_number))
        if name:
            query = query.filter(Debtor.name.contains(name))
        if id_card:
            query = query.filter(Debtor.id_card.contains(id_card))
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, debtor_number: str, name: str, id_card: Optional[str] = None,
               phone: Optional[str] = None, email: Optional[str] = None,
               bank_name: Optional[str] = None, bank_account: Optional[str] = None,
               bank_account_name: Optional[str] = None, address: Optional[str] = None,
               remark: Optional[str] = None, status: DebtorStatus = DebtorStatus.ACTIVE,
               overdue_amount: int = 0, overdue_days: int = 0,
               created_by_id: Optional[int] = None) -> Tuple[Optional[Debtor], str]:
        """Create a new debtor."""
        
        existing = self.get_by_debtor_number(debtor_number)
        if existing:
            return None, f"Debtor with number {debtor_number} already exists"
        
        encrypted_phone_data = None
        if phone:
            is_valid, result = PhoneValidator.validate(phone)
            if not is_valid:
                return None, f"Invalid phone number: {result}"
            
            encrypted_phone_data = phone_encryption.encrypt_to_storage(phone)
        
        debtor = Debtor(
            debtor_number=debtor_number,
            name=name,
            id_card=id_card,
            encrypted_phone=encrypted_phone_data[0] if encrypted_phone_data else None,
            phone_nonce=encrypted_phone_data[1] if encrypted_phone_data else None,
            phone_tag=encrypted_phone_data[2] if encrypted_phone_data else None,
            email=email,
            bank_name=bank_name,
            bank_account=bank_account,
            bank_account_name=bank_account_name,
            address=address,
            remark=remark,
            status=status,
            overdue_amount=overdue_amount,
            overdue_days=overdue_days,
            created_by_id=created_by_id,
        )
        
        self.db.add(debtor)
        self.db.commit()
        self.db.refresh(debtor)
        
        return debtor, ""
    
    def update(self, debtor_id: int, updated_by_id: Optional[int] = None, **kwargs) -> Tuple[Optional[Debtor], str]:
        """Update debtor fields."""
        debtor = self.get_by_id(debtor_id)
        if not debtor:
            return None, "Debtor not found"
        
        if 'phone' in kwargs and kwargs['phone']:
            phone = kwargs['phone']
            is_valid, result = PhoneValidator.validate(phone)
            if not is_valid:
                return None, f"Invalid phone number: {result}"
            encrypted_phone_data = phone_encryption.encrypt_to_storage(phone)
            kwargs['encrypted_phone'] = encrypted_phone_data[0]
            kwargs['phone_nonce'] = encrypted_phone_data[1]
            kwargs['phone_tag'] = encrypted_phone_data[2]
            del kwargs['phone']
        
        for key, value in kwargs.items():
            if hasattr(debtor, key) and value is not None:
                setattr(debtor, key, value)
        
        debtor.updated_by_id = updated_by_id
        debtor.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(debtor)
        
        return debtor, ""
    
    def delete(self, debtor_id: int) -> bool:
        """Soft delete a debtor."""
        debtor = self.get_by_id(debtor_id)
        if not debtor:
            return False
        
        debtor.is_deleted = True
        debtor.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def query(self, debtor_id: int, query_type: str, query_channel: str,
              user_id: Optional[int] = None, partner_id: Optional[int] = None,
              query_ip: Optional[str] = None) -> Tuple[Optional[Debtor], str]:
        """
        Query a debtor with logging.
        
        Returns:
            Tuple of (Debtor or None, error_message)
        """
        debtor = self.get_by_id(debtor_id)
        
        query_log = QueryLog(
            debtor_id=debtor_id if debtor else 0,
            query_type=query_type,
            query_channel=query_channel,
            user_id=user_id,
            partner_id=partner_id,
            query_ip=query_ip,
            success=debtor is not None,
        )
        
        if debtor:
            debtor.last_query_at = datetime.utcnow()
            debtor.query_count += 1
            
            if debtor.query_count >= 100:
                debtor.status = DebtorStatus.OVERDUE
        
        self.db.add(query_log)
        self.db.commit()
        
        return debtor, "" if debtor else "Debtor not found"
    
    def query_by_fields(self, debtor_number: Optional[str] = None,
                        name: Optional[str] = None, id_card: Optional[str] = None,
                        phone: Optional[str] = None, query_type: str = "detail",
                        query_channel: str = "h5", user_id: Optional[int] = None,
                        partner_id: Optional[int] = None, query_ip: Optional[str] = None,
                        page: int = 1, page_size: int = 20) -> Tuple[List[Debtor], int, str]:
        """
        Query debtors by fields with pagination.
        
        Returns:
            Tuple of (list of debtors, total count, error message)
        """
        query = self.db.query(Debtor).filter(Debtor.is_deleted == False)
        
        if debtor_number:
            query = query.filter(Debtor.debtor_number == debtor_number)
        if name:
            query = query.filter(Debtor.name.contains(name))
        if id_card:
            query = query.filter(Debtor.id_card.contains(id_card))
        
        total = query.count()
        debtors = query.offset((page - 1) * page_size).limit(page_size).all()
        
        for debtor in debtors:
            log = QueryLog(
                debtor_id=debtor.id,
                query_type=query_type,
                query_channel=query_channel,
                user_id=user_id,
                partner_id=partner_id,
                query_ip=query_ip,
                query_phone=phone,
                success=True,
            )
            self.db.add(log)
            
            debtor.last_query_at = datetime.utcnow()
            debtor.query_count += 1
        
        self.db.commit()
        
        return debtors, total, ""
    
    def decrypt_phone(self, debtor: Debtor) -> Optional[str]:
        """Decrypt and return debtor's phone number."""
        if not debtor.encrypted_phone or not debtor.phone_nonce or not debtor.phone_tag:
            return None
        
        try:
            return phone_encryption.decrypt_from_storage(
                debtor.encrypted_phone,
                debtor.phone_nonce,
                debtor.phone_tag
            )
        except Exception:
            return None
    
    def get_query_logs(self, debtor_id: int, skip: int = 0, limit: int = 100) -> List[QueryLog]:
        """Get query logs for a debtor."""
        return self.db.query(QueryLog).filter(
            QueryLog.debtor_id == debtor_id
        ).order_by(QueryLog.created_at.desc()).offset(skip).limit(limit).all()
    
    def import_from_batch(self, batch_id: int) -> Tuple[int, int, List[str]]:
        """
        Import debtors from a batch.
        
        Returns:
            Tuple of (success_count, fail_count, error_messages)
        """
        batch = self.db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
        if not batch:
            return 0, 0, ["Batch not found"]
        
        from app.utils.excel import ExcelImporter
        importer = ExcelImporter(file_path=batch.file_path)
        
        if not importer.load():
            return 0, 0, importer.errors
        
        valid_rows, invalid_rows = importer.parse_rows()
        
        success_count = 0
        fail_count = 0
        errors = []
        
        for row_data in valid_rows:
            _, error = self.create(
                debtor_number=row_data['debtor_number'],
                name=row_data['name'],
                id_card=row_data.get('id_card'),
                phone=row_data.get('phone'),
                email=row_data.get('email'),
                bank_name=row_data.get('bank_name'),
                bank_account=row_data.get('bank_account'),
                bank_account_name=row_data.get('bank_account_name'),
                address=row_data.get('address'),
                remark=row_data.get('remark'),
                status=DebtorStatus(row_data.get('status', 'active')),
                overdue_amount=row_data.get('overdue_amount', 0),
                overdue_days=row_data.get('overdue_days', 0),
                created_by_id=batch.created_by_id,
            )
            
            if error:
                fail_count += 1
                errors.append(f"Row {row_data.get('row_number')}: {error}")
            else:
                success_count += 1
        
        batch.total_count = len(valid_rows) + len(invalid_rows)
        batch.success_count = success_count
        batch.fail_count = fail_count + len(invalid_rows)
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        batch.error_log = "\n".join(errors) if errors else None
        
        self.db.commit()
        
        return success_count, fail_count + len(invalid_rows), errors
    
    def create_import_batch(self, filename: str, file_path: str, created_by_id: int) -> ImportBatch:
        """Create an import batch record."""
        batch = ImportBatch(
            filename=filename,
            file_path=file_path,
            created_by_id=created_by_id,
            status="pending",
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch
    
    def get_import_batches(self, skip: int = 0, limit: int = 100) -> List[ImportBatch]:
        """Get all import batches."""
        return self.db.query(ImportBatch).order_by(
            ImportBatch.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_debtor_stats(self) -> Dict[str, Any]:
        """Get debtor statistics."""
        total = self.db.query(func.count(Debtor.id)).filter(Debtor.is_deleted == False).scalar()
        active = self.db.query(func.count(Debtor.id)).filter(
            Debtor.is_deleted == False,
            Debtor.status == DebtorStatus.ACTIVE
        ).scalar()
        overdue = self.db.query(func.count(Debtor.id)).filter(
            Debtor.is_deleted == False,
            Debtor.status == DebtorStatus.OVERDUE
        ).scalar()
        cleared = self.db.query(func.count(Debtor.id)).filter(
            Debtor.is_deleted == False,
            Debtor.status == DebtorStatus.CLEARED
        ).scalar()
        legal = self.db.query(func.count(Debtor.id)).filter(
            Debtor.is_deleted == False,
            Debtor.status == DebtorStatus.LEGAL
        ).scalar()
        
        return {
            "total": total,
            "active": active,
            "overdue": overdue,
            "cleared": cleared,
            "legal": legal,
        }
