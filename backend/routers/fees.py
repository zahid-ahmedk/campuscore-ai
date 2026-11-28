import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import AuditLog, FeePayment, FeeRecord, Student, User
from routers.students import scoped
from schemas import FeeDueCreate, VerifyRequest
from security import STAFF, current_user, require_roles
from services.fee_service import (
    recompute_fee, resolve_category, serialize_fee, serialize_payment,
)
from storage import receipt_path, save_receipt

router = APIRouter(prefix="/api/fees", tags=["fees"])
FEE_STAFF = ("admin", "chairman", "clerk")


@router.get("/categories")
def categories(_: User = Depends(current_user)):
    return {"categories": settings.FEE_CATEGORIES, "custom": settings.CUSTOM_CATEGORY}


def _student_for(db: Session, user: User, roll_no: Optional[str]) -> Student:
    """Students act on themselves; staff must name a student inside their department."""
    if user.role == "student":
        if not user.student:
            raise HTTPException(403, "No student record is linked to this account")
        if roll_no and roll_no.upper() != user.student.roll_no:
            raise HTTPException(403, "You can only act on your own fee record")
        return user.student
    if not roll_no:
        raise HTTPException(400, "roll_no is required")
    s = scoped(db.query(Student), user).filter(Student.roll_no == roll_no.strip().upper()).first()
    if not s:
        raise HTTPException(404, "Student not found")
    return s


@router.get("")
def list_dues(
    page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = None, batch: Optional[str] = None,
    q: Optional[str] = Query(None, max_length=40),
    db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF)),
):
    query = scoped(db.query(FeeRecord, Student).join(Student, Student.id == FeeRecord.student_id), user)
    if status in ("Pending", "Partial", "Paid"):
        query = query.filter(FeeRecord.status == status)
    if batch:
        query = query.filter(Student.batch == batch)
    if q:
        query = query.filter(Student.roll_no.ilike(f"{q.strip()}%") | Student.full_name.ilike(f"%{q.strip()}%"))
    total = query.count()
    rows = query.order_by(Student.roll_no, FeeRecord.semester).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{**serialize_fee(f), "roll_no": s.roll_no, "student_name": s.full_name, "batch": s.batch}
                  for f, s in rows],
        "page": page, "page_size": page_size, "total": total, "pages": max(1, math.ceil(total / page_size)),
    }


@router.post("/dues", status_code=201)
def create_due(payload: FeeDueCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(*FEE_STAFF))):
    category, note = resolve_category(payload.category, payload.custom_category)
    label = note or category
    if payload.batch:
        ids = [i for (i,) in scoped(db.query(Student.id), user).filter(Student.batch == payload.batch)]
    else:
        ids = [_student_for(db, user, payload.roll_no).id]
    if not ids:
        raise HTTPException(404, "No students matched")
    db.bulk_insert_mappings(FeeRecord, [
        {"student_id": i, "semester": payload.semester, "category": label[:80],
         "total_fee": payload.amount, "paid_amount": 0.0, "status": "Pending", "updated_at": datetime.utcnow()}
        for i in ids])
    db.add(AuditLog(user_id=user.id, action="fee.due.create", detail=f"{label} x{len(ids)}"))
    db.commit()
    return {"created": len(ids)}


@router.get("/student/{roll_no}")
def student_fees(roll_no: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    s = _student_for(db, user, roll_no)
    fees = db.query(FeeRecord).filter(FeeRecord.student_id == s.id).order_by(FeeRecord.semester, FeeRecord.id).all()
    pays = db.query(FeePayment).filter(FeePayment.student_id == s.id).order_by(FeePayment.id.desc()).all()
    billed = sum(f.total_fee for f in fees)
    paid = sum(f.paid_amount for f in fees)
    return {
        "student": {"roll_no": s.roll_no, "full_name": s.full_name, "batch": s.batch},
        "totals": {"billed": billed, "paid": paid, "balance": max(billed - paid, 0),
                   "pending_verification": sum(p.amount for p in pays if p.status == "Pending")},
        "dues": [serialize_fee(f) for f in fees],
        "payments": [serialize_payment(p) for p in pays],
    }


@router.post("/payments", status_code=201)
async def submit_payment(
    category: str = Form(...), custom_category: Optional[str] = Form(None),
    amount: float = Form(..., gt=0, le=10_000_000), challan_no: str = Form(...),
    fee_id: Optional[int] = Form(None), roll_no: Optional[str] = Form(None),
    receipt: UploadFile = File(...),
    db: Session = Depends(get_db), user: User = Depends(current_user),
):
    s = _student_for(db, user, roll_no)
    category, note = resolve_category(category, custom_category)
    challan = challan_no.strip().upper()
    if not settings.CHALLAN_PATTERN.match(challan):
        raise HTTPException(400, "Challan No. may contain letters, digits, '-' and '/' (3 to 40 characters)")
    if db.query(FeePayment.id).filter(FeePayment.challan_no == challan, FeePayment.status != "Rejected").first():
        raise HTTPException(409, "This challan number has already been submitted")

    fee = None
    if fee_id:
        fee = db.get(FeeRecord, fee_id)
        if not fee or fee.student_id != s.id:
            raise HTTPException(404, "Fee record not found for this student")
    else:  # auto-link to the oldest open due in the same category
        fee = (db.query(FeeRecord).filter(FeeRecord.student_id == s.id, FeeRecord.category == (note or category),
                                          FeeRecord.status != "Paid").order_by(FeeRecord.semester).first())
    if not fee and db.query(FeeRecord.id).filter(
            FeeRecord.student_id == s.id, FeeRecord.category == (note or category), FeeRecord.status == "Paid").first():
        raise HTTPException(400, f"{note or category} is already fully paid")
    if fee:
        in_review = db.query(func.coalesce(func.sum(FeePayment.amount), 0.0)).filter(
            FeePayment.fee_id == fee.id, FeePayment.status == "Pending").scalar()
        if amount > fee.total_fee - fee.paid_amount - in_review + 0.001:
            raise HTTPException(400, "Amount exceeds the outstanding balance for this fee")

    stored = await save_receipt(receipt)
    p = FeePayment(fee_id=fee.id if fee else None, student_id=s.id, category=category, custom_note=note,
                   amount=amount, challan_no=challan, receipt_file=stored["file"], receipt_name=stored["name"],
                   receipt_type=stored["type"], receipt_size=stored["size"], submitted_by=user.id)
    db.add(p)
    db.add(AuditLog(user_id=user.id, action="payment.submit", detail=f"{s.roll_no} {challan}"))
    db.commit()
    db.refresh(p)
    return serialize_payment(p, with_student=True)


@router.get("/payments")
def list_payments(
    page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = None, q: Optional[str] = Query(None, max_length=40),
    db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF)),
):
    query = scoped(db.query(FeePayment).join(Student, Student.id == FeePayment.student_id), user)
    if status in ("Pending", "Verified", "Rejected"):
        query = query.filter(FeePayment.status == status)
    if q:
        like = f"{q.strip()}%"
        query = query.filter(Student.roll_no.ilike(like) | FeePayment.challan_no.ilike(like.upper()))
    total = query.count()
    rows = query.order_by(FeePayment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_payment(p, True) for p in rows], "page": page, "page_size": page_size,
            "total": total, "pages": max(1, math.ceil(total / page_size))}


def _get_payment(db: Session, user: User, pid: int) -> FeePayment:
    p = db.get(FeePayment, pid)
    if not p:
        raise HTTPException(404, "Payment not found")
    if user.role == "student":
        if not user.student or p.student_id != user.student.id:
            raise HTTPException(403, "Not your payment")
    elif user.role != "admin" and user.department_id and p.student.department_id != user.department_id:
        raise HTTPException(403, "Outside your department")
    return p


@router.patch("/payments/{pid}/verify")
def verify_payment(pid: int, payload: VerifyRequest, db: Session = Depends(get_db),
                   user: User = Depends(require_roles(*FEE_STAFF))):
    p = _get_payment(db, user, pid)
    if payload.status not in ("Verified", "Rejected"):
        raise HTTPException(400, "Status must be Verified or Rejected")
    if p.status != "Pending":
        raise HTTPException(409, f"Payment already {p.status.lower()}")
    if payload.status == "Rejected" and not (payload.remarks or "").strip():
        raise HTTPException(400, "Give a reason when rejecting a receipt")
    p.status, p.remarks = payload.status, (payload.remarks or "").strip() or None
    p.verified_by, p.verified_at = user.id, datetime.utcnow()
    if p.fee_id:
        recompute_fee(db, db.get(FeeRecord, p.fee_id))
    db.add(AuditLog(user_id=user.id, action=f"payment.{payload.status.lower()}", entity="fee_payment", entity_id=p.id))
    db.commit()
    return serialize_payment(p, True)


@router.get("/payments/{pid}/receipt")
def get_receipt(pid: int, download: bool = False, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = _get_payment(db, user, pid)
    return FileResponse(receipt_path(p.receipt_file), media_type=p.receipt_type, filename=p.receipt_name,
                        content_disposition_type="attachment" if download else "inline")
