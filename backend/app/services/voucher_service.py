from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime
import os
from app.models.models import Voucher, VoucherStatus


class VoucherService:
    """Voucher (file upload) management service"""
    
    @staticmethod
    def create_voucher(db: Session, file_name: str, file_path: str, file_size: int,
                      uploaded_by: int, total_count: int = 0) -> Voucher:
        """Create a new voucher record"""
        voucher = Voucher(
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            status=VoucherStatus.PENDING,
            total_count=total_count,
            uploaded_by=uploaded_by
        )
        db.add(voucher)
        db.commit()
        db.refresh(voucher)
        return voucher
    
    @staticmethod
    def get_voucher(db: Session, voucher_id: int) -> Optional[Voucher]:
        """Get voucher by ID"""
        return db.query(Voucher).filter(Voucher.id == voucher_id).first()
    
    @staticmethod
    def list_vouchers(db: Session, skip: int = 0, limit: int = 100,
                      status: VoucherStatus = None, uploaded_by: int = None) -> List[Voucher]:
        """List vouchers with filters"""
        query = db.query(Voucher)
        
        if status:
            query = query.filter(Voucher.status == status)
        if uploaded_by:
            query = query.filter(Voucher.uploaded_by == uploaded_by)
        
        return query.order_by(Voucher.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_voucher_count(db: Session, voucher_id: int, success_count: int, 
                             fail_count: int, error_details: str = None) -> Tuple[Optional[Voucher], str]:
        """Update voucher counts after file processing"""
        voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
        if not voucher:
            return None, "Voucher not found"
        
        voucher.success_count = success_count
        voucher.fail_count = fail_count
        voucher.total_count = success_count + fail_count
        if error_details:
            voucher.error_details = error_details
        
        db.commit()
        db.refresh(voucher)
        return voucher, ""
    
    @staticmethod
    def approve_voucher(db: Session, voucher_id: int, reviewed_by: int, 
                        comment: str = None) -> Tuple[Optional[Voucher], str]:
        """Approve a voucher"""
        voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
        if not voucher:
            return None, "Voucher not found"
        
        if voucher.status != VoucherStatus.PENDING:
            return None, f"Voucher is already {voucher.status.value}"
        
        voucher.status = VoucherStatus.APPROVED
        voucher.reviewed_by = reviewed_by
        voucher.reviewed_at = datetime.utcnow()
        voucher.review_comment = comment
        
        db.commit()
        db.refresh(voucher)
        return voucher, ""
    
    @staticmethod
    def reject_voucher(db: Session, voucher_id: int, reviewed_by: int,
                       comment: str = None) -> Tuple[Optional[Voucher], str]:
        """Reject a voucher"""
        voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
        if not voucher:
            return None, "Voucher not found"
        
        if voucher.status != VoucherStatus.PENDING:
            return None, f"Voucher is already {voucher.status.value}"
        
        voucher.status = VoucherStatus.REJECTED
        voucher.reviewed_by = reviewed_by
        voucher.reviewed_at = datetime.utcnow()
        voucher.review_comment = comment
        
        db.commit()
        db.refresh(voucher)
        return voucher, ""
    
    @staticmethod
    def delete_voucher(db: Session, voucher_id: int) -> Tuple[bool, str]:
        """Delete a voucher"""
        voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
        if not voucher:
            return False, "Voucher not found"
        
        # Delete physical file if exists
        if voucher.file_path and os.path.exists(voucher.file_path):
            try:
                os.remove(voucher.file_path)
            except OSError:
                pass
        
        db.delete(voucher)
        db.commit()
        return True, ""
