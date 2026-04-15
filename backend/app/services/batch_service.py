from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime
import uuid
from app.models.models import Batch, BatchStatus, Debtor, Voucher, VoucherStatus


class BatchService:
    """Batch management service"""
    
    @staticmethod
    def create_batch(db: Session, name: str, description: str = None, 
                     created_by: int = None) -> Tuple[Batch, str]:
        """Create a new batch"""
        batch_no = f"BATCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        batch = Batch(
            batch_no=batch_no,
            name=name,
            description=description,
            status=BatchStatus.PENDING,
            created_by=created_by
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch, ""
    
    @staticmethod
    def get_batch(db: Session, batch_id: int) -> Optional[Batch]:
        """Get batch by ID"""
        return db.query(Batch).filter(Batch.id == batch_id).first()
    
    @staticmethod
    def get_batch_by_no(db: Session, batch_no: str) -> Optional[Batch]:
        """Get batch by batch number"""
        return db.query(Batch).filter(Batch.batch_no == batch_no).first()
    
    @staticmethod
    def list_batches(db: Session, skip: int = 0, limit: int = 100, 
                    status: BatchStatus = None, created_by: int = None) -> List[Batch]:
        """List batches with filters"""
        query = db.query(Batch)
        
        if status:
            query = query.filter(Batch.status == status)
        if created_by:
            query = query.filter(Batch.created_by == created_by)
        
        return query.order_by(Batch.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_batch(db: Session, batch_id: int, **kwargs) -> Tuple[Optional[Batch], str]:
        """Update batch information"""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return None, "Batch not found"
        
        # Cannot update a completed or failed batch
        if batch.status in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
            return None, f"Cannot update a {batch.status.value} batch"
        
        for key, value in kwargs.items():
            if hasattr(batch, key) and value is not None:
                setattr(batch, key, value)
        
        db.commit()
        db.refresh(batch)
        return batch, ""
    
    @staticmethod
    def update_batch_status(db: Session, batch_id: int, status: BatchStatus) -> Tuple[Optional[Batch], str]:
        """Update batch status"""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return None, "Batch not found"
        
        batch.status = status
        db.commit()
        db.refresh(batch)
        return batch, ""
    
    @staticmethod
    def delete_batch(db: Session, batch_id: int) -> Tuple[bool, str]:
        """Delete a batch"""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return False, "Batch not found"
        
        # Cannot delete a processing batch
        if batch.status == BatchStatus.PROCESSING:
            return False, "Cannot delete a processing batch"
        
        # Check if batch has debtors
        debtor_count = db.query(Debtor).filter(Debtor.batch_id == batch_id).count()
        if debtor_count > 0:
            return False, f"Batch has {debtor_count} associated debtors. Delete them first."
        
        db.delete(batch)
        db.commit()
        return True, ""
    
    @staticmethod
    def increment_batch_success(db: Session, batch_id: int) -> None:
        """Increment batch success count"""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch:
            batch.success_count += 1
            db.commit()
    
    @staticmethod
    def increment_batch_fail(db: Session, batch_id: int) -> None:
        """Increment batch fail count"""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch:
            batch.fail_count += 1
            db.commit()
