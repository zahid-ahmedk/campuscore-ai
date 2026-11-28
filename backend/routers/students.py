import math
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ai_advisor import generate_student_study_plan
from database import get_db
from ml_engine import risk_predictor
from models import AuditLog, Department, FeePayment, FeeRecord, GradeRecord, Student, User
from schemas import StudentCreate
from security import STAFF, current_user, require_roles
from services.fee_service import serialize_fee

router = APIRouter(prefix="/api", tags=["students"])

SORTS = {"roll_no": Student.roll_no, "name": Student.full_name, "cgpa": Student.cgpa,
         "attendance": Student.attendance_percentage, "risk": Student.risk_score}


def scoped(query, user: User):
    """Chairmen and clerks only see their own department."""
    if user.role in ("chairman", "clerk") and user.department_id:
        query = query.filter(Student.department_id == user.department_id)
    return query


@router.get("/students")
def list_students(
    page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
    batch: Optional[str] = None, department_id: Optional[int] = None,
    risk_level: Optional[str] = None, q: Optional[str] = Query(None, max_length=60),
    sort: str = "roll_no", desc: bool = False,
    db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF)),
):
    query = scoped(db.query(Student), user)
    if batch:
        query = query.filter(Student.batch == batch)
    if department_id:
        query = query.filter(Student.department_id == department_id)
    if risk_level in ("Low", "Medium", "High"):
        query = query.filter(Student.risk_level == risk_level)
    if q:
        like = f"{q.strip()}%"  # prefix match keeps the roll_no index usable
        query = query.filter((Student.roll_no.ilike(like)) | (Student.full_name.ilike(f"%{q.strip()}%")))

    total = query.count()
    col = SORTS.get(sort, Student.roll_no)
    rows = query.order_by(col.desc() if desc else col.asc(), Student.id).offset((page - 1) * page_size).limit(page_size).all()

    # Outstanding balance for just this page, in one aggregate query.
    ids = [s.id for s in rows]
    dues = {}
    if ids:
        for sid, billed, paid in db.query(FeeRecord.student_id, func.sum(FeeRecord.total_fee),
                                          func.sum(FeeRecord.paid_amount)).filter(
                FeeRecord.student_id.in_(ids)).group_by(FeeRecord.student_id):
            dues[sid] = float(billed - paid)
    dept_names = {d.id: d.name for d in db.query(Department)}

    return {
        "items": [{
            "id": s.id, "roll_no": s.roll_no, "full_name": s.full_name, "email": s.email,
            "batch": s.batch, "semester": s.semester, "department": dept_names.get(s.department_id, ""),
            "attendance_percentage": s.attendance_percentage, "cgpa": s.cgpa,
            "risk_level": s.risk_level, "risk_score": s.risk_score, "balance": dues.get(s.id, 0.0),
        } for s in rows],
        "page": page, "page_size": page_size, "total": total, "pages": max(1, math.ceil(total / page_size)),
    }


@router.get("/batches")
def batches(db: Session = Depends(get_db), user: User = Depends(require_roles(*STAFF))):
    rows = scoped(db.query(Student.batch).distinct(), user).order_by(Student.batch).all()
    return [b for (b,) in rows]


@router.post("/students", status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db),
                   user: User = Depends(require_roles("admin", "chairman", "clerk"))):
    dept_id = user.department_id if user.role != "admin" else payload.department_id
    if not db.get(Department, dept_id):
        raise HTTPException(400, "Unknown department")
    email = payload.email.strip().lower()
    if db.query(Student).filter((Student.roll_no == payload.roll_no) | (Student.email == email)).first():
        raise HTTPException(409, "Roll number or email already registered")
    pred = risk_predictor.predict_student_risk(payload.attendance_percentage, 20.0, 15.0, False)
    s = Student(roll_no=payload.roll_no, full_name=payload.full_name.strip(), email=email, batch=payload.batch,
                semester=payload.semester, department_id=dept_id, attendance_percentage=payload.attendance_percentage,
                cgpa=payload.cgpa, risk_level=pred["risk_level"], risk_score=pred["risk_score"])
    db.add(s)
    db.add(AuditLog(user_id=user.id, action="student.create", detail=payload.roll_no))
    db.commit()
    return {"id": s.id, "roll_no": s.roll_no, "risk": pred}


@router.get("/dashboard/summary")
def summary(batch: Optional[str] = None, db: Session = Depends(get_db),
            user: User = Depends(require_roles(*STAFF))):
    """All figures are SQL aggregates: constant memory regardless of student count."""
    sq = scoped(db.query(Student), user)
    if batch:
        sq = sq.filter(Student.batch == batch)
    total, att, cgpa = sq.with_entities(func.count(Student.id), func.avg(Student.attendance_percentage),
                                        func.avg(Student.cgpa)).one()
    risk = dict(sq.with_entities(Student.risk_level, func.count()).group_by(Student.risk_level).all())

    fq = db.query(FeeRecord).join(Student, Student.id == FeeRecord.student_id)
    fq = scoped(fq, user)
    if batch:
        fq = fq.filter(Student.batch == batch)
    billed, collected = fq.with_entities(func.coalesce(func.sum(FeeRecord.total_fee), 0),
                                         func.coalesce(func.sum(FeeRecord.paid_amount), 0)).one()
    fstat = dict(fq.with_entities(FeeRecord.status, func.count()).group_by(FeeRecord.status).all())

    pq = db.query(func.count(FeePayment.id)).join(Student, Student.id == FeePayment.student_id)
    pending = scoped(pq, user).filter(FeePayment.status == "Pending").scalar()

    return {
        "students": total, "avg_attendance": round(att or 0, 1), "avg_cgpa": round(cgpa or 0, 2),
        "risk": {k: risk.get(k, 0) for k in ("Low", "Medium", "High")},
        "fees": {"billed": float(billed), "collected": float(collected), "outstanding": float(billed - collected),
                 "paid": fstat.get("Paid", 0), "partial": fstat.get("Partial", 0), "pending": fstat.get("Pending", 0)},
        "pending_verifications": pending,
    }


def _profile(db: Session, s: Student) -> dict:
    grades = [{"course_code": g.course_code, "course_name": g.course_name, "credit_hours": g.credit_hours,
               "midterm_marks": g.midterm_marks, "sessional_marks": g.sessional_marks,
               "final_marks": g.final_marks, "total": g.midterm_marks + g.sessional_marks + g.final_marks,
               "grade_letter": g.grade_letter} for g in s.grades]
    n = max(len(grades), 1)
    mid = sum(g["midterm_marks"] for g in grades) / n if grades else 20.0
    ses = sum(g["sessional_marks"] for g in grades) / n if grades else 15.0
    unpaid = any(f.status != "Paid" for f in s.fees)
    pred = risk_predictor.predict_student_risk(s.attendance_percentage, mid, ses, unpaid)
    plan = generate_student_study_plan(s.full_name, s.roll_no, s.attendance_percentage, s.cgpa,
                                       pred["risk_level"], pred["factors"], grades)
    return {
        "student": {"roll_no": s.roll_no, "full_name": s.full_name, "batch": s.batch, "semester": s.semester,
                    "department": s.department.name if s.department else "", "email": s.email,
                    "attendance_percentage": s.attendance_percentage, "cgpa": s.cgpa},
        "grades": grades, "fees": [serialize_fee(f) for f in s.fees],
        "risk_analysis": pred, "study_plan": plan,
    }


@router.get("/students/{roll_no}/profile")
def profile(roll_no: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    roll_no = roll_no.upper()
    if user.role == "student" and (not user.student or user.student.roll_no != roll_no):
        raise HTTPException(403, "You can only view your own profile")
    s = scoped(db.query(Student), user).filter(Student.roll_no == roll_no).first()
    if not s:
        raise HTTPException(404, "Student not found")
    return _profile(db, s)


@router.post("/risk/recompute")
def recompute_risk(db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "chairman"))):
    """Re-score every student in chunks with the vectorised model (safe for 100k+ rows)."""
    avg_marks = dict(db.query(GradeRecord.student_id,
                              func.avg(GradeRecord.midterm_marks / 30.0 * 100.0)).group_by(GradeRecord.student_id).all())
    avg_ses = dict(db.query(GradeRecord.student_id,
                            func.avg(GradeRecord.sessional_marks / 20.0 * 100.0)).group_by(GradeRecord.student_id).all())
    unpaid = {sid for (sid,) in db.query(FeeRecord.student_id).filter(FeeRecord.status != "Paid").distinct()}

    updated, chunk = 0, 5000
    base = scoped(db.query(Student.id, Student.attendance_percentage), user).order_by(Student.id)
    last = 0
    while True:
        rows = base.filter(Student.id > last).limit(chunk).all()
        if not rows:
            break
        frame = pd.DataFrame({
            "attendance": [r[1] for r in rows],
            "midterm_pct": [avg_marks.get(r[0], 66.7) for r in rows],
            "sessional_pct": [avg_ses.get(r[0], 75.0) for r in rows],
            "unpaid_fees": [1 if r[0] in unpaid else 0 for r in rows],
        })
        out = risk_predictor.predict_batch(frame)
        db.bulk_update_mappings(Student, [
            {"id": r[0], "risk_score": float(out.risk_score[i]), "risk_level": out.risk_level[i]}
            for i, r in enumerate(rows)])
        db.commit()
        updated += len(rows)
        last = rows[-1][0]
    db.add(AuditLog(user_id=user.id, action="risk.recompute", detail=str(updated)))
    db.commit()
    return {"updated": updated}
