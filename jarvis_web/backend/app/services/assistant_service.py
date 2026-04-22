from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.models import Appointment, Conversation, Expense, Message, Note, Reminder, Settings, Task
from app.schemas import AssistantChatIn, AssistantChatOut, RecurringTaskCreate, TaskUpdate
from app.services.openai_client import build_chat_completion
from app.services.task_recurrence_service import create_recurring_tasks_batch, delete_tasks_by_scope, update_tasks_by_scope

SUPPORTED_INTENTS = {
    "create_task",
    "create_recurring_task",
    "list_tasks",
    "update_task",
    "update_recurring_task",
    "delete_task",
    "delete_recurring_task",
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
VALID_SCOPES = {"single", "future", "all"}


def load_assistant_settings(db: Session) -> Settings:
    config = db.query(Settings).order_by(Settings.id.desc()).first()
    if not config or not config.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configure a OpenAI API key via /api/settings/openai antes de usar o chat.",
        )
    return config


def _compact_text(value: Optional[str], *, limit: int = 140) -> Optional[str]:
    if value is None:
        return None
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def build_db_context(db: Session) -> dict[str, Any]:
    now_utc = datetime.utcnow()
    pending_tasks = (
        db.query(Task)
        .filter(Task.status.in_(["pending", "in_progress"]))
        .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
        .limit(10)
        .all()
    )
    upcoming_appointments = (
        db.query(Appointment)
        .filter(Appointment.date >= now_utc.date())
        .order_by(Appointment.date.asc(), Appointment.time.asc())
        .limit(10)
        .all()
    )
    future_reminders = (
        db.query(Reminder)
        .filter(Reminder.remind_at >= now_utc)
        .order_by(Reminder.remind_at.asc())
        .limit(10)
        .all()
    )
    recent_expenses = db.query(Expense).order_by(Expense.expense_date.desc()).limit(10).all()
    recent_notes = db.query(Note).order_by(Note.created_at.desc()).limit(10).all()

    return {
        "tarefas_pendentes": [
            {
                "id": task.id,
                "title": task.title,
                "description": _compact_text(task.description),
                "priority": task.priority,
                "status": task.status,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "is_recurring": task.is_recurring,
                "recurrence_group_id": task.recurrence_group_id,
            }
            for task in pending_tasks
        ],
        "proximos_compromissos": [
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
        "lembretes": [
            {
                "id": reminder.id,
                "title": reminder.title,
                "description": _compact_text(reminder.description),
                "remind_at": reminder.remind_at.isoformat(),
                "status": reminder.status,
            }
            for reminder in future_reminders
        ],
        "gastos_recentes": [
            {
                "id": expense.id,
                "description": expense.description,
                "amount": expense.amount,
                "category": expense.category,
                "expense_date": expense.expense_date.isoformat(),
            }
            for expense in recent_expenses
        ],
        "notas_recentes": [
            {
                "id": note.id,
                "title": note.title,
                "tag": note.tag,
                "created_at": note.created_at.isoformat(),
            }
            for note in recent_notes
        ],
    }


def _entity_from_intent(intent: Optional[str]) -> Optional[str]:
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


def _required_fields_for_intent(intent: Optional[str]) -> set[str]:
    return {
        "create_task": {"title"},
        "create_recurring_task": {"title", "start_date", "end_date", "recurrence_pattern"},
        "update_task": {"fields"},
        "update_recurring_task": {"fields"},
        "delete_task": set(),
        "delete_recurring_task": set(),
        "create_appointment": {"title", "date", "time"},
        "create_note": {"title", "content"},
        "create_expense": {"description", "amount", "expense_date"},
        "create_reminder": {"title", "remind_at"},
    }.get(intent, set())


def _mark_confirmation_if_needed(result: dict[str, Any]) -> dict[str, Any]:
    intent = result["acao_detectada"]
    data = result["dados_extraidos"]

    required = _required_fields_for_intent(intent)
    if required and not required.issubset(data.keys()):
        result["precisa_confirmacao"] = True

    if intent == "create_recurring_task" and not data.get("end_date"):
        result["precisa_confirmacao"] = True

    if intent in {"update_recurring_task", "delete_recurring_task"}:
        scope = data.get("scope")
        if scope not in VALID_SCOPES:
            result["precisa_confirmacao"] = True
            if not result.get("resposta_texto"):
                result["resposta_texto"] = (
                    "Você quer mudar só esta tarefa, esta e as futuras, ou todas da recorrência?"
                )

    return result


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        return datetime.fromisoformat(value).date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} deve estar em formato ISO (YYYY-MM-DD)") from exc


def _resolve_task_reference(db: Session, data: dict[str, Any]) -> Task:
    task_id = data.get("task_id")
    title = data.get("title")

    if task_id is not None:
        task = db.get(Task, int(task_id))
        if not task:
            raise HTTPException(status_code=404, detail="Task de referência não encontrada")
        return task

    if isinstance(title, str) and title.strip():
        matches = db.query(Task).filter(Task.title.ilike(title.strip())).order_by(Task.created_at.desc()).all()
        if not matches:
            raise HTTPException(status_code=404, detail="Nenhuma task encontrada com esse título")
        if len(matches) > 1:
            raise HTTPException(
                status_code=422,
                detail="Há múltiplas tasks com esse título. Informe task_id para evitar ambiguidade",
            )
        return matches[0]

    raise HTTPException(status_code=422, detail="Informe task_id ou title para identificar a task")


def _build_task_update_fields(data: dict[str, Any]) -> dict[str, Any]:
    fields = data.get("fields") or {}
    if not isinstance(fields, dict) or not fields:
        raise HTTPException(status_code=422, detail="Informe fields com os campos que deseja atualizar")

    allowed = {
        "title",
        "description",
        "priority",
        "status",
        "due_date",
        "is_recurring",
        "recurrence_group_id",
        "recurrence_pattern",
        "recurrence_meta",
        "original_prompt",
    }
    unknown = set(fields.keys()) - allowed
    if unknown:
        raise HTTPException(status_code=422, detail=f"Campos inválidos para update: {', '.join(sorted(unknown))}")

    if "due_date" in fields and fields["due_date"] is not None:
        fields["due_date"] = _parse_iso_date(fields["due_date"], "due_date")

    return fields


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
                due_date=_parse_iso_date(data["due_date"], "due_date") if data.get("due_date") else None,
            )
        )
        return

    if intent == "create_recurring_task":
        create_recurring_tasks_batch(
            db,
            RecurringTaskCreate(
                title=data["title"],
                description=data.get("description"),
                priority=data.get("priority", "medium"),
                status=data.get("status", "pending"),
                start_date=data["start_date"],
                end_date=data["end_date"],
                recurrence_pattern=data["recurrence_pattern"],
                recurrence_meta=data.get("recurrence_meta", {}),
                original_prompt=data.get("original_prompt"),
            ),
        )
        return

    if intent == "update_task":
        task = _resolve_task_reference(db, data)
        fields = _build_task_update_fields(data)
        for key, value in fields.items():
            setattr(task, key, value)
        return

    if intent == "update_recurring_task":
        task = _resolve_task_reference(db, data)
        scope = data.get("scope", "single")
        fields = _build_task_update_fields(data)

        if scope not in VALID_SCOPES:
            raise HTTPException(status_code=422, detail="scope inválido. Use single, future ou all")

        update_tasks_by_scope(
            db=db,
            reference_task=task,
            recurrence_group_id=task.recurrence_group_id or "",
            scope=scope,
            payload=TaskUpdate(**fields),
        )
        return

    if intent == "delete_task":
        task = _resolve_task_reference(db, data)
        db.delete(task)
        return

    if intent == "delete_recurring_task":
        task = _resolve_task_reference(db, data)
        scope = data.get("scope", "single")

        if scope not in VALID_SCOPES:
            raise HTTPException(status_code=422, detail="scope inválido. Use single, future ou all")

        delete_tasks_by_scope(
            db=db,
            reference_task=task,
            recurrence_group_id=task.recurrence_group_id or "",
            scope=scope,
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


def ensure_conversation(db: Session, conversation_id: Optional[int], initial_user_message: str) -> Conversation:
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
