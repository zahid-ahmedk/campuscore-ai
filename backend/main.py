from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import bcrypt

from database import engine, get_db, Base
from models import Department, User, Student, FeeRecord, GradeRecord
from ml_engine import risk_predictor
from ai_advisor import generate_student_study_plan, answer_admin_query

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CampusCore AI Management System",
    description="v2.0 AI-Powered Academic, Fee & Predictive Risk Management API",
    version="2.0.0",
)

# Allow Next.js frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Request Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str

class DepartmentCreate(BaseModel):
    name: str
    code: str

class StaffCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str  # chairman or clerk
    department_id: int

class StudentCreate(BaseModel):
    roll_no: str
    full_name: str
    email: str
    batch: str
    department_id: int
    attendance_percentage: float = 85.0
    cgpa: float = 3.0
    total_fee: float = 45000.0
    paid_amount: float = 0.0

class FeeUpdateRequest(BaseModel):
    paid_amount: float

class GradeUpdateRequest(BaseModel):
    course_code: str
    course_name: str
    midterm_marks: float
    sessional_marks: float
    final_marks: float

class CopilotQuery(BaseModel):
    question: str


# --- 1. Authentication Endpoint ---
@app.post("/api/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not bcrypt.checkpw(
        payload.password.encode("utf-8"), user.hashed_password.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "department_id": user.department_id,
    }


# --- 2. Admin Endpoints (Departments & Chairmen) ---
@app.get("/api/departments")
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()

@app.post("/api/departments")
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    existing = db.query(Department).filter(Department.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department code already exists")
    dept = Department(name=payload.name, code=payload.code)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

@app.post("/api/staff")
def create_staff(payload: StaffCreate, db: Session = Depends(get_db)):
    if payload.role not in ["chairman", "clerk"]:
        raise HTTPException(status_code=400, detail="Role must be chairman or clerk")
    hashed = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hashed,
        role=payload.role,
        department_id=payload.department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}


# --- 3. Clerk & Chairman Endpoints (Students & Batch Fees) ---
@app.get("/api/students")
def list_students(batch: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Student)
    if batch:
        query = query.filter(Student.batch == batch)
    students = query.all()

    results = []
    for s in students:
        fee = s.fees[0] if s.fees else None
        results.append({
            "id": s.id,
            "roll_no": s.roll_no,
            "full_name": s.full_name,
            "email": s.email,
            "batch": s.batch,
            "department": s.department.name if s.department else "N/A",
            "attendance_percentage": s.attendance_percentage,
            "cgpa": s.cgpa,
            "risk_level": s.risk_level,
            "risk_score": s.risk_score,
            "fee": {
                "id": fee.id if fee else None,
                "total_fee": fee.total_fee if fee else 0,
                "paid_amount": fee.paid_amount if fee else 0,
                "balance": (fee.total_fee - fee.paid_amount) if fee else 0,
                "status": fee.status if fee else "Pending",
            },
        })
    return results

@app.post("/api/students")
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.roll_no == payload.roll_no).first():
        raise HTTPException(status_code=400, detail="Roll number already exists")

    fee_status = (
        "Paid" if payload.paid_amount >= payload.total_fee
        else ("Partial" if payload.paid_amount > 0 else "Pending")
    )
    pred = risk_predictor.predict_student_risk(
        attendance=payload.attendance_percentage,
        midterm_marks=20.0,
        sessional_marks=15.0,
        has_unpaid_fees=(fee_status != "Paid"),
    )

    student = Student(
        roll_no=payload.roll_no,
        full_name=payload.full_name,
        email=payload.email,
        batch=payload.batch,
        department_id=payload.department_id,
        attendance_percentage=payload.attendance_percentage,
        cgpa=payload.cgpa,
        risk_level=pred["risk_level"],
        risk_score=pred["risk_score"],
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    fee = FeeRecord(
        student_id=student.id,
        semester=1,
        total_fee=payload.total_fee,
        paid_amount=payload.paid_amount,
        status=fee_status,
    )
    db.add(fee)
    db.commit()
    return {"message": "Student added successfully", "student_id": student.id, "ai_risk": pred}

@app.put("/api/fees/{fee_id}")
def update_fee(fee_id: int, payload: FeeUpdateRequest, db: Session = Depends(get_db)):
    fee = db.query(FeeRecord).filter(FeeRecord.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")

    fee.paid_amount = payload.paid_amount
    if fee.paid_amount >= fee.total_fee:
        fee.status = "Paid"
    elif fee.paid_amount > 0:
        fee.status = "Partial"
    else:
        fee.status = "Pending"

    db.commit()
    return {"id": fee.id, "paid_amount": fee.paid_amount, "status": fee.status}


# --- 4. Student Portal & AI Study Advisor ---
@app.get("/api/students/{roll_no}/profile")
def get_student_profile(roll_no: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    grades_list = [
        {
            "course_code": g.course_code,
            "course_name": g.course_name,
            "credit_hours": g.credit_hours,
            "midterm_marks": g.midterm_marks,
            "sessional_marks": g.sessional_marks,
            "final_marks": g.final_marks,
            "total": g.midterm_marks + g.sessional_marks + g.final_marks,
            "grade_letter": g.grade_letter,
        }
        for g in student.grades
    ]

    first_grade = grades_list[0] if grades_list else {"midterm_marks": 20.0, "sessional_marks": 15.0}
    has_unpaid = any(f.status != "Paid" for f in student.fees)
    pred = risk_predictor.predict_student_risk(
        attendance=student.attendance_percentage,
        midterm_marks=first_grade["midterm_marks"],
        sessional_marks=first_grade["sessional_marks"],
        has_unpaid_fees=has_unpaid,
    )

    study_plan = generate_student_study_plan(
        student_name=student.full_name,
        roll_no=student.roll_no,
        attendance=student.attendance_percentage,
        cgpa=student.cgpa,
        risk_level=pred["risk_level"],
        risk_factors=pred["factors"],
        grades=grades_list,
    )

    return {
        "student": {
            "roll_no": student.roll_no,
            "full_name": student.full_name,
            "batch": student.batch,
            "department": student.department.name if student.department else "N/A",
            "attendance_percentage": student.attendance_percentage,
            "cgpa": student.cgpa,
        },
        "grades": grades_list,
        "fees": [
            {"semester": f.semester, "total_fee": f.total_fee, "paid_amount": f.paid_amount, "status": f.status}
            for f in student.fees
        ],
        "ai_risk_analysis": pred,
        "ai_study_plan": study_plan,
    }


# --- 5. Admin / Chairman AI Copilot Endpoint ---
@app.post("/api/ai/copilot")
def admin_copilot(payload: CopilotQuery, db: Session = Depends(get_db)):
    students = db.query(Student).all()
    fees = db.query(FeeRecord).all()
    depts = db.query(Department).all()

    total_billed = sum(f.total_fee for f in fees)
    total_collected = sum(f.paid_amount for f in fees)
    high_risk = [s for s in students if s.risk_level == "High"]

    stats = {
        "total_students": len(students),
        "total_departments": len(depts),
        "avg_attendance": sum(s.attendance_percentage for s in students) / len(students) if students else 0,
        "avg_cgpa": sum(s.cgpa for s in students) / len(students) if students else 0,
        "high_risk_count": len(high_risk),
        "high_risk_rolls": [s.roll_no for s in high_risk],
        "total_billed": total_billed,
        "total_collected": total_collected,
        "total_pending": total_billed - total_collected,
        "unpaid_students_count": sum(1 for f in fees if f.status != "Paid"),
    }
    return answer_admin_query(payload.question, stats)