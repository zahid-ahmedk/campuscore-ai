from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from models import FeePayment, FeeRecord


def resolve_category(category: str, custom: str | None) -> tuple[str, str | None]:
    """Return (category, custom_note). 'Custom' requires free text."""
    category = (category or "").strip()
    if category == settings.CUSTOM_CATEGORY:
        note = (custom or "").strip()
        if len(note) < 3:
            raise HTTPException(400, "Enter a fee category or note for the Custom option")
        return settings.CUSTOM_CATEGORY, note[:200]
    if category not in settings.FEE_CATEGORIES:
        raise HTTPException(400, "Select a valid fee category")
    return category, None


def status_for(total: float, paid: float) -> str:
    if paid >= total:
        return "Paid"
    return "Partial" if paid > 0 else "Pending"


def recompute_fee(db: Session, fee: FeeRecord) -> None:
    """paid_amount is always the sum of verified payments, never edited by hand."""
    db.flush()  # sessions run with autoflush off; make the new status visible to the SUM
    paid = db.query(func.coalesce(func.sum(FeePayment.amount), 0.0)).filter(
        FeePayment.fee_id == fee.id, FeePayment.status == "Verified").scalar()
    fee.paid_amount = float(paid)
    fee.status = status_for(fee.total_fee, fee.paid_amount)
    fee.updated_at = datetime.utcnow()


def serialize_fee(f: FeeRecord) -> dict:
    return {
        "id": f.id, "semester": f.semester, "category": f.category,
        "total_fee": f.total_fee, "paid_amount": f.paid_amount,
        "balance": max(f.total_fee - f.paid_amount, 0), "status": f.status,
    }


def serialize_payment(p: FeePayment, with_student: bool = False) -> dict:
    out = {
        "id": p.id, "fee_id": p.fee_id, "category": p.category, "custom_note": p.custom_note,
        "amount": p.amount, "challan_no": p.challan_no, "status": p.status, "remarks": p.remarks,
        "receipt_name": p.receipt_name, "receipt_type": p.receipt_type, "receipt_size": p.receipt_size,
        "submitted_at": p.submitted_at.isoformat(), "verified_at": p.verified_at.isoformat() if p.verified_at else None,
    }
    if with_student and p.student:
        out.update({"roll_no": p.student.roll_no, "student_name": p.student.full_name})
    return out
