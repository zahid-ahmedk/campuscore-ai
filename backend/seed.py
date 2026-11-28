"""Seed demo data.

    python seed.py                  # small demo set (IT department)
    python seed.py --students 100000  # synthetic load-test data

Demo accounts are for local development only; change or delete them in production.
"""
import argparse
import random
import struct
import zlib
from datetime import datetime, timedelta

import pandas as pd

from config import settings
from database import Base, SessionLocal, engine
from ml_engine import risk_predictor
from models import Department, FeePayment, FeeRecord, GradeRecord, Student, User
from security import hash_password

DEMO_PASSWORD = "Quest@2026"
TUITION = "Semester Tuition Fee"

DEMO_STUDENTS = [
    # roll, name, att, cgpa, paid, mid, ses, fin, grade
    ("21IT-95", "Muhammad Hassnain", 88, 3.45, 45000, 25, 17, 41, "A"),
    ("21IT-98", "Zahid Ahmed", 62, 2.15, 20000, 11, 9, 24, "D"),
    ("21IT-100", "Ibrahim Zardari", 79, 2.95, 45000, 19, 14, 34, "B"),
    ("21IT-70", "Asad Zardari", 54, 1.85, 0, 9, 8, 19, "F"),
]
FIRST = ["Ali", "Ahmed", "Hassan", "Usman", "Bilal", "Faizan", "Sana", "Ayesha", "Fatima", "Hira", "Imran", "Kashif",
         "Naveed", "Rabia", "Saad", "Zain", "Maryam", "Noman", "Owais", "Sajid"]
LAST = ["Memon", "Soomro", "Shaikh", "Chandio", "Jatoi", "Lashari", "Mangi", "Bhutto", "Khoso", "Siyal", "Abro", "Kalhoro"]
EXTRA_DEPTS = [("Civil Engineering", "CE"), ("Electrical Engineering", "EE"), ("Mechanical Engineering", "ME"),
               ("Software Engineering", "SW"), ("Computer Systems Engineering", "CS"), ("Chemical Engineering", "CH"),
               ("Electronic Engineering", "EL"), ("Textile Engineering", "TE"), ("Telecommunication Engineering", "TL"),
               ("Industrial Engineering", "IE"), ("Petroleum Engineering", "PE")]


def _png() -> bytes:
    """A valid 1x1 PNG used as the placeholder receipt for demo payments."""
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff")) + chunk(b"IEND", b""))


def seed_demo(db) -> None:
    it = Department(name="Information Technology", code="IT")
    db.add(it)
    db.commit()
    pw = hash_password(DEMO_PASSWORD)
    db.add_all([
        User(full_name="System Administrator", email="admin@quest-portal.local", hashed_password=pw, role="admin"),
        User(full_name="Dr. Suleman Memon", email="chairman@quest-portal.local", hashed_password=pw, role="chairman", department_id=it.id),
        User(full_name="IT Office Clerk", email="clerk@quest-portal.local", hashed_password=pw, role="clerk", department_id=it.id),
    ])
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (settings.UPLOAD_DIR / "demo_receipt.png").write_bytes(_png())

    for roll, name, att, cgpa, paid, mid, ses, fin, grade in DEMO_STUDENTS:
        pred = risk_predictor.predict_student_risk(att, mid, ses, paid < 45000)
        s = Student(roll_no=roll, full_name=name, email=f"{roll.lower().replace('-', '')}@quest-portal.local",
                    batch=roll[:2], semester=5, department_id=it.id, attendance_percentage=att, cgpa=cgpa,
                    risk_level=pred["risk_level"], risk_score=pred["risk_score"])
        db.add(s)
        db.flush()
        status = "Paid" if paid >= 45000 else "Partial" if paid else "Pending"
        fee = FeeRecord(student_id=s.id, semester=5, category=TUITION, total_fee=45000, paid_amount=paid, status=status,
                        due_date=datetime.utcnow() + timedelta(days=20))
        db.add(fee)
        db.add(GradeRecord(student_id=s.id, course_code="IT-301", course_name="Artificial Intelligence",
                           midterm_marks=mid, sessional_marks=ses, final_marks=fin, grade_letter=grade))
        db.flush()
        if paid:
            db.add(FeePayment(fee_id=fee.id, student_id=s.id, category=TUITION, amount=paid,
                              challan_no=f"HBL-{roll.replace('-', '')}-01", receipt_file="demo_receipt.png",
                              receipt_name="challan.png", receipt_type="image/png", receipt_size=70,
                              status="Verified", verified_at=datetime.utcnow()))
        if roll == "21IT-98":  # a submission waiting for the clerk
            db.add(FeePayment(fee_id=fee.id, student_id=s.id, category=TUITION, amount=10000,
                              challan_no="HBL-21IT98-02", receipt_file="demo_receipt.png", receipt_name="challan.png",
                              receipt_type="image/png", receipt_size=70, status="Pending"))
        if roll == "21IT-95":
            db.flush()
    db.commit()
    hs = db.query(Student).filter(Student.roll_no == "21IT-95").one()
    db.add(User(full_name=hs.full_name, email="21it95@quest-portal.local", hashed_password=pw, role="student",
                department_id=it.id, student_id=hs.id))
    db.commit()


def seed_bulk(db, n: int) -> None:
    rng = random.Random(7)
    depts = [Department(name=nm, code=c) for nm, c in EXTRA_DEPTS]
    db.add_all(depts)
    db.commit()
    dept_ids = [d.id for d in db.query(Department)]
    codes = {d.id: d.code for d in db.query(Department)}
    combos = [(d, str(b)) for d in dept_ids for b in range(17, 27)]
    rng.shuffle(combos)
    made, chunk = 0, 5000
    while made < n:
        rows = []
        for i in range(made, min(made + chunk, n)):
            did, batch = combos[i % len(combos)]
            serial = 101 + i // len(combos)  # 1-100 are reserved for the demo roll numbers
            rows.append({
                "roll_no": f"{batch}{codes[did]}-{serial}", "full_name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                "email": f"{batch}{codes[did].lower()}{serial}@bulk.local", "batch": batch,
                "semester": rng.randint(1, 8), "department_id": did,
                "attendance_percentage": round(rng.uniform(45, 100), 1), "cgpa": round(rng.uniform(1.5, 4.0), 2),
            })
        db.bulk_insert_mappings(Student, rows)
        db.commit()
        made += len(rows)
    ids = [i for (i,) in db.query(Student.id).filter(Student.email.like("%@bulk.local")).order_by(Student.id)]
    for i in range(0, len(ids), chunk):
        part = ids[i:i + chunk]
        att = dict(db.query(Student.id, Student.attendance_percentage).filter(Student.id.in_(part)))
        fees, unpaid = [], {}
        for sid in part:
            paid = rng.choice([0, 0, 22500, 45000, 45000, 45000])
            unpaid[sid] = paid < 45000
            fees.append({"student_id": sid, "semester": 1, "category": TUITION, "total_fee": 45000, "paid_amount": paid,
                         "status": "Paid" if paid >= 45000 else "Partial" if paid else "Pending"})
        db.bulk_insert_mappings(FeeRecord, fees)
        frame = pd.DataFrame({"attendance": [att[s] for s in part],
                              "midterm_pct": [rng.uniform(20, 100) for _ in part],
                              "sessional_pct": [rng.uniform(30, 100) for _ in part],
                              "unpaid_fees": [int(unpaid[s]) for s in part]})
        out = risk_predictor.predict_batch(frame)
        db.bulk_update_mappings(Student, [{"id": s, "risk_score": float(out.risk_score[j]), "risk_level": out.risk_level[j]}
                                          for j, s in enumerate(part)])
        db.commit()
    print(f"Inserted {made:,} synthetic students.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--students", type=int, default=0, help="also insert N synthetic students (load test)")
    args = ap.parse_args()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not db.query(Department).first():
        seed_demo(db)
        print(f"Demo accounts created (password: {DEMO_PASSWORD}):")
        print("  admin@quest-portal.local | chairman@quest-portal.local | clerk@quest-portal.local | 21it95@quest-portal.local")
    else:
        print("Database already seeded.")
    if args.students:
        seed_bulk(db, args.students)
    db.close()
