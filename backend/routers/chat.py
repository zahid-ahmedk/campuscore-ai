from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import ChatRequest
from security import current_user
from services.chat_service import answer

router = APIRouter(prefix="/api", tags=["assistant"])


@router.post("/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return answer(db, user, payload.message.strip())
