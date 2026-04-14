from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.db import get_db
from app.models import Appointment, Conversation, Expense, Message, Note, Reminder, Settings, Task
from app.schemas import AssistantChatIn, AssistantChatOut, AssistantContextOut
from app.services.openai_client import build_chat_completion

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def _serialize_context(db: Session) -> dict[str, Any]:
    pending_tasks = (
        db.query(Task)
        .filter(Task.status.in_(["pending", "in_progress"]))
        .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
        .limit(10)
        .all()
    )
    upcoming_appointments = (
        db.query(Appointment)
        .filter(Appointment.date >= datetime.utcnow().date())
        .order_by(Appointment.date.asc(), Appointment.time.asc())
        .limit(10)
        .all()
    )
    pending_reminders = (
        db.query(Reminder)
        .filter(Reminder.status == "pending")
        .order_by(Reminder.remind_at.asc())
        .limit(10)
        .all()
    )
    recent_expenses = db.query(Expense).order_by(Expense.expense_date.desc()).limit(10).all()

    return {
        "pending_tasks": [
            {
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "status": task.status,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            }
            for task in pending_tasks
        ],
        "upcoming_appointments": [
            {
                "id": appointment.id,
                "title": appointment.title,
                "date": appointment.date.isoformat(),
                "time": appointment.time.isoformat(),
                "status": appointment.status,
            }
            for appointment in upcoming_appointments
        ],
        "pending_reminders": [
            {
                "id": reminder.id,
                "title": reminder.title,
                "remind_at": reminder.remind_at.isoformat(),
                "status": reminder.status,
            }
            for reminder in pending_reminders
        ],
        "recent_expenses": [
            {
                "id": expense.id,
                "description": expense.description,
                "amount": expense.amount,
                "category": expense.category,
                "expense_date": expense.expense_date.isoformat(),
            }
            for expense in recent_expenses
        ],
    }


def _execute_action(db: Session, action: str | None, entity: str | None, data: dict[str, Any]) -> None:
    if action != "create" or not entity:
        return

    if entity == "task" and data.get("title"):
        task = Task(
            title=data["title"],
            description=data.get("description"),
            priority=data.get("priority", "medium"),
            status=data.get("status", "pending"),
            due_date=datetime.fromisoformat(data["due_date"]).date() if data.get("due_date") else None,
        )
        db.add(task)
    elif entity == "appointment" and data.get("title") and data.get("date") and data.get("time"):
        parsed_time = (
            datetime.strptime(data["time"], "%H:%M:%S").time()
            if len(data["time"].split(":")) == 3
            else datetime.strptime(data["time"], "%H:%M").time()
        )
        appointment = Appointment(
            title=data["title"],
            description=data.get("description"),
            date=datetime.fromisoformat(data["date"]).date(),
            time=parsed_time,
            location=data.get("location"),
            status=data.get("status", "scheduled"),
        )
        db.add(appointment)
    elif entity == "note" and data.get("title") and data.get("content"):
        note = Note(title=data["title"], content=data["content"], tag=data.get("tag"))
        db.add(note)
    elif entity == "expense" and data.get("description") and data.get("amount") and data.get("expense_date"):
        expense = Expense(
            description=data["description"],
            amount=float(data["amount"]),
            category=data.get("category"),
            expense_date=datetime.fromisoformat(data["expense_date"]).date(),
            payment_method=data.get("payment_method"),
            notes=data.get("notes"),
        )
        db.add(expense)
    elif entity == "reminder" and data.get("title") and data.get("remind_at"):
        reminder = Reminder(
            title=data["title"],
            description=data.get("description"),
            remind_at=datetime.fromisoformat(data["remind_at"]),
            status=data.get("status", "pending"),
        )
        db.add(reminder)


@router.get("/context", response_model=AssistantContextOut)
def get_assistant_context(db: Session = Depends(get_db)):
    return _serialize_context(db)


@router.post("/chat", response_model=AssistantChatOut)
def assistant_chat(payload: AssistantChatIn, db: Session = Depends(get_db)):
    config = db.query(Settings).order_by(Settings.id.desc()).first()
    if not config or not config.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configure a OpenAI API key via /api/settings antes de usar o chat.",
        )

    conversation_id = payload.conversation_id
    if conversation_id is None:
        conversation = Conversation(title=payload.message[:80] or "Nova conversa")
        db.add(conversation)
        db.flush()
        conversation_id = conversation.id
    else:
        conversation = db.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")

    user_message = Message(conversation_id=conversation_id, role="user", content=payload.message)
    db.add(user_message)

    context = _serialize_context(db)

    try:
        completion = build_chat_completion(
            api_key=config.openai_api_key,
            model=config.openai_model or app_settings.default_openai_model,
            user_message=payload.message,
            context=context,
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Resposta inválida da OpenAI: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Erro na OpenAI: {exc}") from exc

    resposta_texto = str(completion.get("resposta_texto", "Não foi possível gerar resposta."))
    acao_detectada = completion.get("acao_detectada")
    entidade = completion.get("entidade")
    dados_extraidos = completion.get("dados_extraidos") or {}
    precisa_confirmacao = bool(completion.get("precisa_confirmacao", False))

    if isinstance(dados_extraidos, dict) and not precisa_confirmacao:
        _execute_action(db, acao_detectada, entidade, dados_extraidos)

    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=resposta_texto,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return AssistantChatOut(
        resposta_texto=resposta_texto,
        acao_detectada=acao_detectada,
        entidade=entidade,
        dados_extraidos=dados_extraidos if isinstance(dados_extraidos, dict) else {},
        precisa_confirmacao=precisa_confirmacao,
        conversation_id=conversation_id,
        message_id=assistant_message.id,
    )
