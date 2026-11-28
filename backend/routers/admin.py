from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import AuditLog, Department, User
from schemas import DepartmentCreate, StaffCreate
from security import current_user, hash_password, require_roles

router = APIRouter(prefix="/api", tags=["administration"])


@router.get("/departments")
def list_departments(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return [{"id": d.id, "name": d.name, "code": d.code} for d in db.query(Department).order_by(Department.name)]


@router.post("/departments", status_code=201)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db),
                      admin: User = Depends(require_roles("admin"))):
    code = payload.code.strip().upper()
    if db.query(Department).filter((Department.code == code) | (Department.name == payload.name.strip())).first():
        raise HTTPException(409, "A department with this name or code already exists")
    dept = Department(name=payload.name.strip(), code=code)
    db.add(dept)
    db.add(AuditLog(user_id=admin.id, action="department.create", detail=code))
    db.commit()
    return {"id": dept.id, "name": dept.name, "code": dept.code}


@router.get("/staff")
def list_staff(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    rows = db.query(User).filter(User.role.in_(["chairman", "clerk"])).order_by(User.full_name).all()
    return [{"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role,
             "department": u.department.name if u.department else None} for u in rows]


@router.post("/staff", status_code=201)
def create_staff(payload: StaffCreate, db: Session = Depends(get_db),
                 admin: User = Depends(require_roles("admin"))):
    if payload.role not in ("chairman", "clerk"):
        raise HTTPException(400, "Role must be chairman or clerk")
    if not db.get(Department, payload.department_id):
        raise HTTPException(400, "Unknown department")
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "A user with this email already exists")
    user = User(full_name=payload.full_name.strip(), email=email, hashed_password=hash_password(payload.password),
                role=payload.role, department_id=payload.department_id)
    db.add(user)
    db.add(AuditLog(user_id=admin.id, action="staff.create", detail=f"{email} ({payload.role})"))
    db.commit()
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}


@router.get("/audit")
def audit(limit: int = 50, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 200)).all()
    return [{"id": r.id, "user_id": r.user_id, "action": r.action, "detail": r.detail,
             "created_at": r.created_at.isoformat()} for r in rows]
