import bcrypt
from database import engine, SessionLocal, Base
from models import Department, User, Student, FeeRecord, GradeRecord
from ml_engine import risk_predictor

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def seed_database():
    # Create all tables in campuscore.db
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Prevent duplicate seeding
    if db.query(Department).first():
        print("Database already seeded!")
        db.close()
        return

    # 1. Create Department (matching thesis screenshot IT1)
    it_dept = Department(name="Information Technology", code="IT1")
    cs_dept = Department(name="Computer Science", code="CS1")
    db.add_all([it_dept, cs_dept])
    db.commit()
    db.refresh(it_dept)

    # 2. Create Role Accounts (Admin, Chairman, Clerk, Student)
    users = [
        User(
            full_name="System Administrator",
            email="admin@campuscore.edu",
            hashed_password=hash_password("admin123"),
            role="admin",
            department_id=None,
        ),
        User(
            full_name="Dr. Baqar Ali Zardari",
            email="chairman@campuscore.edu",
            hashed_password=hash_password("chair123"),
            role="chairman",
            department_id=it_dept.id,
        ),
        User(
            full_name="Department Clerk",
            email="clerk@campuscore.edu",
            hashed_password=hash_password("clerk123"),
            role="clerk",
            department_id=it_dept.id,
        ),
        User(
            full_name="Muhammad Hassnain",
            email="21it95@student.campuscore.edu",
            hashed_password=hash_password("student123"),
            role="student",
            department_id=it_dept.id,
        ),
    ]
    db.add_all(users)
    db.commit()

    # 3. Create Batch 21 Students with Grades, Fees & ML Risk Scores
    sample_students = [
        {
            "roll_no": "21IT-95",
            "full_name": "Muhammad Hassnain",
            "email": "21it95@student.campuscore.edu",
            "batch": "21",
            "attendance": 88.0,
            "cgpa": 3.45,
            "total_fee": 45000,
            "paid_amount": 45000,
            "fee_status": "Paid",
            "midterm": 25.0,
            "sessional": 17.0,
            "final": 41.0,
            "grade": "A",
        },
        {
            "roll_no": "21IT-98",
            "full_name": "Zahid Ahmed",
            "email": "21it98@student.campuscore.edu",
            "batch": "21",
            "attendance": 62.0,
            "cgpa": 2.15,
            "total_fee": 45000,
            "paid_amount": 20000,
            "fee_status": "Partial",
            "midterm": 11.0,
            "sessional": 9.0,
            "final": 24.0,
            "grade": "D",
        },
        {
            "roll_no": "21IT-100",
            "full_name": "Ibrahim Zardari",
            "email": "21it100@student.campuscore.edu",
            "batch": "21",
            "attendance": 79.0,
            "cgpa": 2.95,
            "total_fee": 45000,
            "paid_amount": 45000,
            "fee_status": "Paid",
            "midterm": 19.0,
            "sessional": 14.0,
            "final": 34.0,
            "grade": "B",
        },
        {
            "roll_no": "21IT-70",
            "full_name": "Asad Zardari",
            "email": "21it70@student.campuscore.edu",
            "batch": "21",
            "attendance": 54.0,
            "cgpa": 1.85,
            "total_fee": 45000,
            "paid_amount": 0,
            "fee_status": "Pending",
            "midterm": 9.0,
            "sessional": 8.0,
            "final": 19.0,
            "grade": "F",
        },
    ]

    for s in sample_students:
        prediction = risk_predictor.predict_student_risk(
            attendance=s["attendance"],
            midterm_marks=s["midterm"],
            sessional_marks=s["sessional"],
            has_unpaid_fees=(s["fee_status"] != "Paid"),
        )

        student = Student(
            roll_no=s["roll_no"],
            full_name=s["full_name"],
            email=s["email"],
            batch=s["batch"],
            department_id=it_dept.id,
            attendance_percentage=s["attendance"],
            cgpa=s["cgpa"],
            risk_level=prediction["risk_level"],
            risk_score=prediction["risk_score"],
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        fee = FeeRecord(
            student_id=student.id,
            semester=7,
            total_fee=s["total_fee"],
            paid_amount=s["paid_amount"],
            status=s["fee_status"],
        )
        grade = GradeRecord(
            student_id=student.id,
            course_code="IT-401",
            course_name="Artificial Intelligence & Data Science",
            credit_hours=3,
            midterm_marks=s["midterm"],
            sessional_marks=s["sessional"],
            final_marks=s["final"],
            grade_letter=s["grade"],
        )
        db.add_all([fee, grade])
        db.commit()

        print(
            f"Seeded {student.roll_no} ({student.full_name}) -> "
            f"AI Risk: {student.risk_level} ({student.risk_score * 100:.0f}%)"
        )

    db.close()
    print("\nSuccess! campuscore.db created and populated.")

if __name__ == "__main__":
    seed_database()