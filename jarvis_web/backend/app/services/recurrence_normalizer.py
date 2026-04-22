from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import HTTPException, status

MAX_RECURRING_SPAN_DAYS = 366 * 4
WEEKDAY_ALIASES = {
    "mon": 0,
    "monday": 0,
    "seg": 0,
    "segunda": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "ter": 1,
    "terça": 1,
    "terca": 1,
    "wed": 2,
    "weds": 2,
    "wednesday": 2,
    "qua": 2,
    "quarta": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "qui": 3,
    "quinta": 3,
    "fri": 4,
    "friday": 4,
    "sex": 4,
    "sexta": 4,
    "sat": 5,
    "saturday": 5,
    "sab": 5,
    "sábado": 5,
    "sabado": 5,
    "sun": 6,
    "sunday": 6,
    "dom": 6,
    "domingo": 6,
}
WEEKDAY_INT_TO_NAME = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}


def normalize_recurrence_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normaliza regras de recorrência extraídas por IA para o formato do backend.

    Saída:
    {
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "recurrence_pattern": "daily|weekly|monthly|interval",
      "recurrence_meta": {...}
    }

    Exemplos de uso:
    - normalize_recurrence_input({
        "start_date": "2026-01-01", "end_date": "2026-01-31", "recurrence_pattern": "daily"
      })
    - normalize_recurrence_input({
        "start_date": "2026-01-01", "end_date": "2026-02-28", "recurrence_pattern": "weekly",
        "recurrence_meta": {"weekdays": ["mon", "wed"]}
      })
    - normalize_recurrence_input({
        "start_date": "2026-01-01", "end_date": "2026-06-01", "recurrence_pattern": "monthly",
        "day_of_month": 15
      })
    - normalize_recurrence_input({
        "start_date": "2026-01-01", "end_date": "2026-03-01", "recurrence_pattern": "interval",
        "every_n_days": 2
      })
    """

    start_date = _extract_required_date(data, "start_date")
    end_date = _extract_required_date(data, "end_date")
    _validate_date_range(start_date, end_date)

    pattern = _normalize_pattern(data.get("recurrence_pattern") or data.get("pattern"))
    recurrence_meta = _normalize_recurrence_meta(pattern, data)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "recurrence_pattern": pattern,
        "recurrence_meta": recurrence_meta,
    }


def _extract_required_date(data: dict[str, Any], field_name: str) -> date:
    value = data.get(field_name)
    if value in (None, ""):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} é obrigatório para recorrência",
        )
    return _parse_date(value, field_name)


def _parse_date(value: Any, field_name: str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field_name} deve estar em formato ISO (YYYY-MM-DD)",
            ) from exc

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"{field_name} inválido",
    )


def _validate_date_range(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date deve ser menor ou igual a end_date",
        )

    span_days = (end_date - start_date).days
    if span_days > MAX_RECURRING_SPAN_DAYS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A recorrência pode ter no máximo 4 anos",
        )


def _normalize_pattern(raw_pattern: Any) -> str:
    if not isinstance(raw_pattern, str) or not raw_pattern.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="recurrence_pattern é obrigatório",
        )

    aliases = {
        "daily": "daily",
        "day": "daily",
        "diario": "daily",
        "diária": "daily",
        "diaria": "daily",
        "weekly": "weekly",
        "week": "weekly",
        "semanal": "weekly",
        "monthly": "monthly",
        "month": "monthly",
        "mensal": "monthly",
        "interval": "interval",
        "intervalo": "interval",
        "every_n_days": "interval",
    }

    normalized = aliases.get(raw_pattern.strip().lower())
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="recurrence_pattern inválido. Use daily, weekly, monthly ou interval",
        )
    return normalized


def _normalize_recurrence_meta(pattern: str, data: dict[str, Any]) -> dict[str, Any]:
    raw_meta = data.get("recurrence_meta") if isinstance(data.get("recurrence_meta"), dict) else {}

    if pattern == "daily":
        return {}

    if pattern == "weekly":
        weekdays_value = raw_meta.get("weekdays", data.get("weekdays"))
        weekdays = _normalize_weekdays(weekdays_value)
        return {"weekdays": weekdays}

    if pattern == "monthly":
        day_of_month_value = raw_meta.get("day_of_month", data.get("day_of_month"))
        day_of_month = _validate_day_of_month(day_of_month_value)
        return {"day_of_month": day_of_month}

    every_n_days_value = raw_meta.get("every_n_days", data.get("every_n_days"))
    if every_n_days_value is None:
        every_n_days_value = raw_meta.get("every_days", data.get("every_days"))

    every_n_days = _validate_every_n_days(every_n_days_value)
    return {"every_days": every_n_days}


def _normalize_weekdays(value: Any) -> list[int]:
    if not isinstance(value, list) or not value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="weekly exige weekdays com ao menos um dia da semana",
        )

    normalized: list[int] = []
    for day in value:
        if isinstance(day, int) and 0 <= day <= 6:
            normalized.append(day)
            continue

        if isinstance(day, str):
            key = day.strip().lower()
            if key in WEEKDAY_ALIASES:
                normalized.append(WEEKDAY_ALIASES[key])
                continue
            if key.isdigit() and 0 <= int(key) <= 6:
                normalized.append(int(key))
                continue

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"weekday inválido: {day}. Use 0..6 ou nomes como mon, wed, friday",
        )

    return [WEEKDAY_INT_TO_NAME[idx] for idx in sorted(set(normalized))]


def _validate_day_of_month(value: Any) -> int:
    if not isinstance(value, int) or not (1 <= value <= 31):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="monthly exige day_of_month válido entre 1 e 31",
        )
    return value


def _validate_every_n_days(value: Any) -> int:
    if not isinstance(value, int) or value < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="interval exige every_n_days (ou every_days) inteiro maior que zero",
        )
    return value
