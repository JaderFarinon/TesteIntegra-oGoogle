from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Conversation, Message
from app.schemas import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
)

router = APIRouter(prefix="/api", tags=["chat-data"])


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    conversation = Conversation(**payload.model_dump())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/messages", response_model=list[MessageOut])
def list_messages(conversation_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Message)
    if conversation_id is not None:
        query = query.filter(Message.conversation_id == conversation_id)
    return query.order_by(Message.created_at.asc()).all()


@router.post("/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def create_message(payload: MessageCreate, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, payload.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    message = Message(**payload.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
