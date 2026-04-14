from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AssistantChatIn, AssistantChatOut, AssistantContextOut
from app.services.assistant_service import build_db_context, process_assistant_chat

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.get("/context", response_model=AssistantContextOut)
def get_assistant_context(db: Session = Depends(get_db)):
    return build_db_context(db)


@router.post("/chat", response_model=AssistantChatOut)
def assistant_chat(payload: AssistantChatIn, db: Session = Depends(get_db)):
    return process_assistant_chat(db, payload)
