from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampOut(ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class SettingsCreate(BaseModel):
    openai_api_key: str | None = Field(default=None, max_length=255)
    openai_model: str = Field(default="gpt-4.1-mini", max_length=100)


class SettingsOut(TimestampOut):
    openai_api_key: str | None = None
    openai_model: str


class ConversationCreate(BaseModel):
    title: str = Field(..., max_length=200)


class ConversationOut(TimestampOut):
    title: str


class MessageCreate(BaseModel):
    conversation_id: int
    role: str = Field(..., max_length=20)
    content: str


class MessageOut(ORMModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime


class TaskBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    priority: str = Field(default="medium", max_length=20)
    status: str = Field(default="pending", max_length=30)
    due_date: date | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    pass


class TaskOut(TimestampOut, TaskBase):
    pass


class AppointmentBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    date: date
    time: time
    location: str | None = Field(default=None, max_length=200)
    status: str = Field(default="scheduled", max_length=30)


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(AppointmentBase):
    pass


class AppointmentOut(TimestampOut, AppointmentBase):
    pass


class NoteBase(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    tag: str | None = Field(default=None, max_length=100)


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


class NoteOut(TimestampOut, NoteBase):
    pass


class ExpenseBase(BaseModel):
    description: str = Field(..., max_length=200)
    amount: float
    category: str | None = Field(default=None, max_length=100)
    expense_date: date
    payment_method: str | None = Field(default=None, max_length=80)
    notes: str | None = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    pass


class ExpenseOut(TimestampOut, ExpenseBase):
    pass


class ReminderBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    remind_at: datetime
    status: str = Field(default="pending", max_length=30)


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(ReminderBase):
    pass


class ReminderOut(TimestampOut, ReminderBase):
    pass


class AssistantChatIn(BaseModel):
    message: str
    conversation_id: int | None = None


class AssistantContextOut(BaseModel):
    pending_tasks: list[dict[str, Any]]
    upcoming_appointments: list[dict[str, Any]]
    future_reminders: list[dict[str, Any]]
    recent_expenses: list[dict[str, Any]]
    recent_notes: list[dict[str, Any]]


class AssistantChatOut(BaseModel):
    resposta_texto: str
    acao_detectada: str | None = None
    entidade: str | None = None
    dados_extraidos: dict[str, Any] = Field(default_factory=dict)
    precisa_confirmacao: bool = False
    conversation_id: int
    message_id: int
