from datetime import date, datetime, time
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampOut(ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class SettingsCreate(BaseModel):
    openai_api_key: Optional[str] = Field(default=None, max_length=255)
    openai_model: str = Field(default="gpt-4.1-mini", max_length=100)


class SettingsOut(TimestampOut):
    openai_api_key: Optional[str] = Field(default=None, max_length=255)
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
    description: Optional[str] = Field(default=None)
    priority: str = Field(default="medium", max_length=20)
    status: str = Field(default="pending", max_length=30)
    due_date: Optional[date] = None
    is_recurring: bool = False
    recurrence_group_id: Optional[str] = Field(default=None, max_length=36)
    recurrence_pattern: Optional[str] = Field(default=None, max_length=30)
    recurrence_meta: Optional[str] = None
    original_prompt: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None)
    priority: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=30)
    due_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    recurrence_group_id: Optional[str] = Field(default=None, max_length=36)
    recurrence_pattern: Optional[str] = Field(default=None, max_length=30)
    recurrence_meta: Optional[str] = None
    original_prompt: Optional[str] = None


class TaskOut(TimestampOut, TaskBase):
    pass


class RecurringTaskCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    priority: str = Field(default="medium", max_length=20)
    status: str = Field(default="pending", max_length=30)
    start_date: date
    end_date: date
    recurrence_pattern: str = Field(..., max_length=30)
    recurrence_meta: dict[str, Any] = Field(default_factory=dict)
    original_prompt: Optional[str] = None


class RecurringTaskCreateOut(BaseModel):
    recurrence_group_id: str
    total_created: int
    tasks: list[TaskOut]



RecurrenceScope = Literal["single", "future", "all"]


class TaskBulkOperationOut(BaseModel):
    recurrence_group_id: Optional[str] = None
    scope: RecurrenceScope
    affected_count: int
    message: str


class TaskBulkUpdateOut(TaskBulkOperationOut):
    tasks: list[TaskOut]


class AppointmentBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    date: date
    time: time
    location: Optional[str] = Field(default=None, max_length=200)
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
    tag: Optional[str] = Field(default=None, max_length=100)


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


class NoteOut(TimestampOut, NoteBase):
    pass


class ExpenseBase(BaseModel):
    description: str = Field(..., max_length=200)
    amount: float
    category: Optional[str] = Field(default=None, max_length=100)
    expense_date: date
    payment_method: Optional[str] = Field(default=None, max_length=80)
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    pass


class ExpenseOut(TimestampOut, ExpenseBase):
    pass


class ReminderBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(default=None)
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
    conversation_id: Optional[int] = Field(default=None)


class AssistantContextOut(BaseModel):
    tarefas_pendentes: list[dict[str, Any]]
    proximos_compromissos: list[dict[str, Any]]
    lembretes: list[dict[str, Any]]
    gastos_recentes: list[dict[str, Any]]
    notas_recentes: list[dict[str, Any]]


class AssistantChatOut(BaseModel):
    resposta_texto: str
    acao_detectada: Optional[str] = None
    entidade: Optional[str] = None
    dados_extraidos: dict[str, Any] = Field(default_factory=dict)
    precisa_confirmacao: bool = False
    conversation_id: int
    message_id: int
