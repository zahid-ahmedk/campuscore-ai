from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # e.g., Information Technology
    code = Column(String, unique=True, nullable=False)  # e.g., IT1

    users = relationship("User", back_populates="department")
    students = relationship("Student", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # Roles from thesis + Student portal: admin, chairman, clerk, student
    role = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    department = relationship("Department", back_populates="users")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, unique=True, index=True, nullable=False)  # e.g., 21IT-95
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    batch = Column(String, index=True, nullable=False)  # e.g., "21"
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    # Academic & AI Tracking Metrics
    attendance_percentage = Column(Float, default=100.0)
    cgpa = Column(Float, default=0.0)
    risk_level = Column(String, default="Low")  # Low, Medium, High (ML Predicted)
    risk_score = Column(Float, default=0.0)     # 0.0 to 1.0 probability

    department = relationship("Department", back_populates="students")
    fees = relationship("FeeRecord", back_populates="student")
    grades = relationship("GradeRecord", back_populates="student")


class FeeRecord(Base):
    __tablename__ = "fee_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    total_fee = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    status = Column(String, default="Pending")  # Paid, Partial, Pending
    updated_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="fees")


class GradeRecord(Base):
    __tablename__ = "grade_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_code = Column(String, nullable=False)  # e.g., IT-301
    course_name = Column(String, nullable=False)  # e.g., Artificial Intelligence
    credit_hours = Column(Integer, default=3)
    midterm_marks = Column(Float, default=0.0)    # Out of 30
    sessional_marks = Column(Float, default=0.0)  # Out of 20
    final_marks = Column(Float, default=0.0)      # Out of 50
    grade_letter = Column(String, default="N/A")

    student = relationship("Student", back_populates="grades")