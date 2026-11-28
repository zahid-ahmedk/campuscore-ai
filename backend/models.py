from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Index, Integer, String, Boolean, Text,
)
from sqlalchemy.orm import relationship

from database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)

    users = relationship("User", back_populates="department")
    students = relationship("Student", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # admin | chairman | clerk | student
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)

    department = relationship("Department", back_populates="users")
    student = relationship("Student", foreign_keys=[student_id])


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    roll_no = Column(String(20), unique=True, index=True, nullable=False)  # 21IT-95
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False)
    batch = Column(String(4), nullable=False)  # "21" = admitted 2021
    semester = Column(Integer, default=1, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    attendance_percentage = Column(Float, default=100.0)
    cgpa = Column(Float, default=0.0)
    risk_level = Column(String(10), default="Low")  # Low | Medium | High
    risk_score = Column(Float, default=0.0)

    department = relationship("Department", back_populates="students")
    fees = relationship("FeeRecord", back_populates="student", cascade="all, delete-orphan")
    grades = relationship("GradeRecord", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_students_batch_dept", "batch", "department_id"),
        Index("ix_students_risk", "risk_level", "batch"),
        Index("ix_students_name", "full_name"),
    )


class FeeRecord(Base):
    """A fee due raised against a student (one row per semester and category)."""
    __tablename__ = "fee_records"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    category = Column(String(80), nullable=False, default="Semester Tuition Fee")
    total_fee = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0, nullable=False)  # sum of VERIFIED payments
    status = Column(String(10), default="Pending", nullable=False)  # Pending | Partial | Paid
    due_date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="fees")
    payments = relationship("FeePayment", back_populates="fee")

    __table_args__ = (Index("ix_fee_status_student", "status", "student_id"),)


class FeePayment(Base):
    """A challan/receipt submission that a clerk verifies or rejects."""
    __tablename__ = "fee_payments"

    id = Column(Integer, primary_key=True)
    fee_id = Column(Integer, ForeignKey("fee_records.id"), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    category = Column(String(80), nullable=False)
    custom_note = Column(String(200), nullable=True)
    amount = Column(Float, nullable=False)
    challan_no = Column(String(40), nullable=False, index=True)
    receipt_file = Column(String(120), nullable=False)   # stored filename (uuid)
    receipt_name = Column(String(200), nullable=False)   # original filename
    receipt_type = Column(String(60), nullable=False)
    receipt_size = Column(Integer, nullable=False)
    status = Column(String(10), default="Pending", nullable=False, index=True)  # Pending | Verified | Rejected
    remarks = Column(String(300), nullable=True)
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    verified_at = Column(DateTime, nullable=True)

    fee = relationship("FeeRecord", back_populates="payments")
    student = relationship("Student")


class GradeRecord(Base):
    __tablename__ = "grade_records"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    course_code = Column(String(20), nullable=False)
    course_name = Column(String(120), nullable=False)
    credit_hours = Column(Integer, default=3)
    midterm_marks = Column(Float, default=0.0)    # out of 30
    sessional_marks = Column(Float, default=0.0)  # out of 20
    final_marks = Column(Float, default=0.0)      # out of 50
    grade_letter = Column(String(3), default="N/A")

    student = relationship("Student", back_populates="grades")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(60), nullable=False)
    entity = Column(String(40), nullable=True)
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
