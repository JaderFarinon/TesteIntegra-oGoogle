from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.models import Appointment, Conversation, Expense, Message, Note, Reminder, Settings, Task
from app.schemas import AssistantChatIn, AssistantChatOut
from app.services.openai_client import build_chat_completion

SUPPORTED_INTENTS = {
    "create_task",
    "list_tasks",
    "create_appointment",
    "list_appointments",
    "create_note",
    "list_notes",
    "create_expense",
    "list_expenses",
    "create_reminder",
    "list_reminders",
    "general_question",
}


def load_assistant_settings(db: Session) -> Settings:
    config = db.query(Settings).order_by(Settings.id.desc()).first()
    if not config or not config.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configure a OpenAI API key via /api/settings antes de usar o chat.",
        )
    return config


def build_db_context(db: Session) -> dict[str, Any]:
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
    future_reminders = (
        db.query(Reminder)
        .filter(Reminder.remind_at >= datetime.utcnow())
        .order_by(Reminder.remind_at.asc())
        .limit(10)
        .all()
    )
    recent_expenses = db.query(Expense).order_by(Expense.expense_date.desc()).limit(10).all()
    recent_notes = db.query(Note).order_by(Note.created_at.desc()).limit(10).all()

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
                "location": appointment.location,
            }
            for appointment in upcoming_appointments
        ],
        "future_reminders": [
            {
                "id": reminder.id,
                "title": reminder.title,
                "remind_at": reminder.remind_at.isoformat(),
                "status": reminder.status,
            }
            for reminder in future_reminders
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
        "recent_notes": [
            {
                "id": note.id,
                "title": note.title,
                "tag": note.tag,
                "created_at": note.created_at.isoformat(),
            }
            for note in recent_notes
        ],
    }


def _entity_from_intent(intent: str | None) -> str | None:
    if not intent or intent == "general_question":
        return None
    if intent.endswith("_tasks") or intent.endswith("_task"):
        return "task"
    if intent.endswith("_appointments") or intent.endswith("_appointment"):
        return "appointment"
    if intent.endswith("_notes") or intent.endswith("_note"):
        return "note"
    if intent.endswith("_expenses") or intent.endswith("_expense"):
        return "expense"
    if intent.endswith("_reminders") or intent.endswith("_reminder"):
        return "reminder"
    return None


def validate_ai_response(payload: dict[str, Any]) -> dict[str, Any]:
    required_fields = {
        "resposta_texto",
        "acao_detectada",
        "entidade",
        "dados_extraidos",
        "precisa_confirmacao",
    }
    missing = required_fields - set(payload.keys())
    if missing:
        raise HTTPException(
            status_code=502,
            detail=f"Resposta da OpenAI sem campos obrigatórios: {', '.join(sorted(missing))}",
        )

    intent = payload.get("acao_detectada")
    if intent is not None and intent not in SUPPORTED_INTENTS:
        intent = "general_question"

    dados = payload.get("dados_extraidos")
    if not isinstance(dados, dict):
        dados = {}

    resposta_texto = str(payload.get("resposta_texto") or "Não foi possível processar sua solicitação.")
    precisa_confirmacao = bool(payload.get("precisa_confirmacao", False))
    entidade = payload.get("entidade") or _entity_from_intent(intent)

    return {
        "resposta_texto": resposta_texto,
        "acao_detectada": intent,
        "entidade": entidade,
        "dados_extraidos": dados,
        "precisa_confirmacao": precisa_confirmacao,
    }


def _required_fields_for_intent(intent: str | None) -> set[str]:
    return {
        "create_task": {"title"},
        "create_appointment": {"title", "date", "time"},
        "create_note": {"title", "content"},
        "create_expense": {"description", "amount", "expense_date"},
        "create_reminder": {"title", "remind_at"},
    }.get(intent, set())


def _mark_confirmation_if_needed(result: dict[str, Any]) -> dict[str, Any]:
    required = _required_fields_for_intent(result["acao_detectada"])
    if required and not required.issubset(result["dados_extraidos"].keys()):
        result["precisa_confirmacao"] = True
    return result


def execute_detected_action(db: Session, result: dict[str, Any]) -> None:
    intent = result["acao_detectada"]
    data = result["dados_extraidos"]

    if not intent or intent == "general_question" or result["precisa_confirmacao"]:
        return

    if intent == "create_task":
        db.add(
            Task(
                title=data["title"],
                description=data.get("description"),
                priority=data.get("priority", "medium"),
                status=data.get("status", "pending"),
                due_date=datetime.fromisoformat(data["due_date"]).date() if data.get("due_date") else None,
            )
        )
        return

    if intent == "create_appointment":
        parsed_time = (
            datetime.strptime(data["time"], "%H:%M:%S").time()
            if len(data["time"].split(":")) == 3
            else datetime.strptime(data["time"], "%H:%M").time()
        )
        db.add(
            Appointment(
                title=data["title"],
                description=data.get("description"),
                date=datetime.fromisoformat(data["date"]).date(),
                time=parsed_time,
                location=data.get("location"),
                status=data.get("status", "scheduled"),
            )
        )
        return

    if intent == "create_note":
        db.add(Note(title=data["title"], content=data["content"], tag=data.get("tag")))
        return

    if intent == "create_expense":
        db.add(
            Expense(
                description=data["description"],
                amount=float(data["amount"]),
                category=data.get("category"),
                expense_date=datetime.fromisoformat(data["expense_date"]).date(),
                payment_method=data.get("payment_method"),
                notes=data.get("notes"),
            )
        )
        return

    if intent == "create_reminder":
        db.add(
            Reminder(
                title=data["title"],
                description=data.get("description"),
                remind_at=datetime.fromisoformat(data["remind_at"]),
                status=data.get("status", "pending"),
            )
        )


def save_chat_messages(
    db: Session,
    *,
    conversation_id: int,
    user_text: str,
    assistant_text: str,
) -> Message:
    db.add(Message(conversation_id=conversation_id, role="user", content=user_text))
    assistant_message = Message(conversation_id=conversation_id, role="assistant", content=assistant_text)
    db.add(assistant_message)
    db.flush()
    return assistant_message


def ensure_conversation(db: Session, conversation_id: int | None, initial_user_message: str) -> Conversation:
    if conversation_id is None:
        conversation = Conversation(title=initial_user_message[:80] or "Nova conversa")
        db.add(conversation)
        db.flush()
        return conversation

    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return conversation


def process_assistant_chat(db: Session, payload: AssistantChatIn) -> AssistantChatOut:
    config = load_assistant_settings(db)
    conversation = ensure_conversation(db, payload.conversation_id, payload.message)
    context = build_db_context(db)

    try:
        completion = build_chat_completion(
            api_key=config.openai_api_key,
            model=config.openai_model or app_settings.default_openai_model,
            user_message=payload.message,
            context=context,
            now_iso=datetime.utcnow().isoformat(),
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Resposta inválida da OpenAI: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Erro na OpenAI: {exc}") from exc

    normalized = validate_ai_response(completion)
    normalized = _mark_confirmation_if_needed(normalized)

    execute_detected_action(db, normalized)
    assistant_message = save_chat_messages(
        db,
        conversation_id=conversation.id,
        user_text=payload.message,
        assistant_text=normalized["resposta_texto"],
    )

    db.commit()

    return AssistantChatOut(
        resposta_texto=normalized["resposta_texto"],
        acao_detectada=normalized["acao_detectada"],
        entidade=normalized["entidade"],
        dados_extraidos=normalized["dados_extraidos"],
        precisa_confirmacao=normalized["precisa_confirmacao"],
        conversation_id=conversation.id,
        message_id=assistant_message.id,
    )
