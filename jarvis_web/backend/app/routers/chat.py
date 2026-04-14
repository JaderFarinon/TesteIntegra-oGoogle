from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChatMessage
from app.schemas import ChatPrompt, ChatResponse
from app.services.openai_client import ask_openai

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/history")
def history(db: Session = Depends(get_db)):
    return db.query(ChatMessage).order_by(ChatMessage.created_at.asc()).all()


@router.post("", response_model=ChatResponse)
def chat(payload: ChatPrompt, db: Session = Depends(get_db)):
    user_msg = ChatMessage(role="user", message=payload.message)
    db.add(user_msg)

    answer = ask_openai(payload.message)
    assistant_msg = ChatMessage(role="assistant", message=answer)
    db.add(assistant_msg)

    db.commit()

    history_data = db.query(ChatMessage).order_by(ChatMessage.created_at.asc()).all()
    return {"answer": answer, "history": history_data}
