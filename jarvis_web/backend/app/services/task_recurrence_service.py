from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Task
from app.schemas import RecurringTaskCreate, TaskUpdate

MAX_RECURRING_SPAN_DAYS = 366 * 4
VALID_PATTERNS = {"daily", "weekly", "monthly", "interval"}
RecurrenceScope = Literal["single", "future", "all"]
WEEKDAY_NAME_TO_INT = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


@dataclass
class RecurrenceValidationResult:
    pattern: str
    recurrence_meta: dict


@dataclass
class ScopeSelectionResult:
    tasks: list[Task]
    recurrence_group_id: str | None
    applied_scope: RecurrenceScope


def validate_recurrence_rules(payload: RecurringTaskCreate) -> RecurrenceValidationResult:
    if payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date deve ser maior ou igual a start_date",
        )

    span_days = (payload.end_date - payload.start_date).days
    if span_days > MAX_RECURRING_SPAN_DAYS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A recorrência pode gerar no máximo 4 anos de tarefas",
        )

    pattern = payload.recurrence_pattern.strip().lower()
    if pattern not in VALID_PATTERNS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="recurrence_pattern inválido. Use: daily, weekly, monthly ou interval",
        )

    meta = payload.recurrence_meta or {}

    if pattern == "weekly":
        _validate_weekly_meta(meta)
    elif pattern == "monthly":
        _validate_monthly_meta(meta, payload.start_date)
    elif pattern == "interval":
        _validate_interval_meta(meta)

    return RecurrenceValidationResult(pattern=pattern, recurrence_meta=meta)


def expand_recurrence_dates(payload: RecurringTaskCreate, validation: RecurrenceValidationResult) -> list[date]:
    pattern = validation.pattern
    start_date = payload.start_date
    end_date = payload.end_date

    if pattern == "daily":
        return _expand_daily(start_date, end_date)
    if pattern == "weekly":
        return _expand_weekly(start_date, end_date, validation.recurrence_meta)
    if pattern == "monthly":
        return _expand_monthly(start_date, end_date, validation.recurrence_meta)
    return _expand_interval(start_date, end_date, validation.recurrence_meta)


def create_recurring_tasks_batch(db: Session, payload: RecurringTaskCreate) -> tuple[str, list[Task]]:
    validation = validate_recurrence_rules(payload)
    dates = expand_recurrence_dates(payload, validation)

    if not dates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nenhuma tarefa foi gerada para o período informado",
        )

    recurrence_group_id = str(uuid4())
    recurrence_meta_json = json.dumps(validation.recurrence_meta, ensure_ascii=False)

    tasks = [
        Task(
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            status=payload.status,
            due_date=due_date,
            is_recurring=True,
            recurrence_group_id=recurrence_group_id,
            recurrence_pattern=validation.pattern,
            recurrence_meta=recurrence_meta_json,
            original_prompt=payload.original_prompt,
        )
        for due_date in dates
    ]

    db.add_all(tasks)
    db.commit()

    for task in tasks:
        db.refresh(task)

    return recurrence_group_id, tasks


def update_tasks_by_scope(
    db: Session,
    reference_task: Task,
    recurrence_group_id: str,
    scope: RecurrenceScope,
    payload: TaskUpdate,
) -> ScopeSelectionResult:
    selection = _select_scope_tasks(db, reference_task, recurrence_group_id, scope)
    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nenhum campo para atualização foi enviado",
        )

    for task in selection.tasks:
        for key, value in changes.items():
            setattr(task, key, value)

    db.commit()
    for task in selection.tasks:
        db.refresh(task)

    return selection


def delete_tasks_by_scope(
    db: Session,
    reference_task: Task,
    recurrence_group_id: str,
    scope: RecurrenceScope,
) -> ScopeSelectionResult:
    selection = _select_scope_tasks(db, reference_task, recurrence_group_id, scope)

    for task in selection.tasks:
        db.delete(task)

    db.commit()
    return selection


def _select_scope_tasks(
    db: Session,
    reference_task: Task,
    recurrence_group_id: str,
    scope: RecurrenceScope,
) -> ScopeSelectionResult:
    if not reference_task.is_recurring or not reference_task.recurrence_group_id:
        return ScopeSelectionResult(tasks=[reference_task], recurrence_group_id=None, applied_scope="single")

    if reference_task.recurrence_group_id != recurrence_group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A tarefa informada não pertence ao recurrence_group_id solicitado",
        )

    query = db.query(Task).filter(Task.recurrence_group_id == recurrence_group_id)

    if scope == "single":
        tasks = query.filter(Task.id == reference_task.id).all()
    elif scope == "future":
        if reference_task.due_date is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A tarefa de referência precisa ter due_date para usar scope=future",
            )
        tasks = query.filter(Task.due_date >= reference_task.due_date).order_by(Task.due_date.asc()).all()
    else:
        tasks = query.order_by(Task.due_date.asc()).all()

    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma tarefa encontrada para o escopo informado",
        )

    return ScopeSelectionResult(tasks=tasks, recurrence_group_id=recurrence_group_id, applied_scope=scope)


def _validate_weekly_meta(meta: dict) -> None:
    days = meta.get("weekdays")
    if not isinstance(days, list) or not days:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Para weekly, informe recurrence_meta.weekdays com ao menos um dia da semana",
        )

    normalized_days: list[int] = []
    for day in days:
        if isinstance(day, int) and 0 <= day <= 6:
            normalized_days.append(day)
            continue

        if isinstance(day, str) and day.strip().lower() in WEEKDAY_NAME_TO_INT:
            normalized_days.append(WEEKDAY_NAME_TO_INT[day.strip().lower()])
            continue

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dias inválidos em recurrence_meta.weekdays. Use 0-6 ou nomes (monday..sunday)",
        )

    meta["weekdays"] = sorted(set(normalized_days))


def _validate_monthly_meta(meta: dict, start_date: date) -> None:
    day_of_month = meta.get("day_of_month", start_date.day)
    if not isinstance(day_of_month, int) or day_of_month < 1 or day_of_month > 31:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Para monthly, day_of_month deve ser um inteiro entre 1 e 31",
        )

    meta["day_of_month"] = day_of_month


def _validate_interval_meta(meta: dict) -> None:
    every_days = meta.get("every_days")
    if not isinstance(every_days, int) or every_days < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Para interval, recurrence_meta.every_days deve ser inteiro maior que zero",
        )


def _expand_daily(start_date: date, end_date: date) -> list[date]:
    occurrences: list[date] = []
    current = start_date
    while current <= end_date:
        occurrences.append(current)
        current += timedelta(days=1)
    return occurrences


def _expand_weekly(start_date: date, end_date: date, meta: dict) -> list[date]:
    weekdays = set(meta["weekdays"])
    occurrences: list[date] = []

    current = start_date
    while current <= end_date:
        if current.weekday() in weekdays:
            occurrences.append(current)
        current += timedelta(days=1)

    return occurrences


def _expand_monthly(start_date: date, end_date: date, meta: dict) -> list[date]:
    day_of_month = meta["day_of_month"]
    occurrences: list[date] = []

    year = start_date.year
    month = start_date.month

    while True:
        month_last_day = calendar.monthrange(year, month)[1]
        candidate = date(year, month, min(day_of_month, month_last_day))

        if start_date <= candidate <= end_date:
            occurrences.append(candidate)

        if (year, month) == (end_date.year, end_date.month):
            break

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    return occurrences


def _expand_interval(start_date: date, end_date: date, meta: dict) -> list[date]:
    every_days = meta["every_days"]
    occurrences: list[date] = []

    current = start_date
    while current <= end_date:
        occurrences.append(current)
        current += timedelta(days=every_days)

    return occurrences
