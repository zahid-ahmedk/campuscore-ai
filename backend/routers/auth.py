from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import LoginRequest
from security import create_token, current_user, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def user_out(u: User) -> dict:
    return {
        "id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role,
        "department_id": u.department_id,
        "roll_no": u.student.roll_no if u.student else None,
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if not user or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_token(user), "token_type": "bearer", "user": user_out(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_out(user)
