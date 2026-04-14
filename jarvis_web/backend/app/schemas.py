from datetime import datetime

from pydantic import BaseModel, Field


class BaseOut(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    completed: bool = False
    due_date: str | None = None


class TaskOut(BaseOut, TaskCreate):
    pass


class AppointmentCreate(BaseModel):
    title: str
    location: str | None = None
    start_time: str
    end_time: str | None = None
    notes: str | None = None


class AppointmentOut(BaseOut, AppointmentCreate):
    pass


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteOut(BaseOut, NoteCreate):
    pass


class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: str | None = None
    expense_date: str


class ExpenseOut(BaseOut, ExpenseCreate):
    pass


class ReminderCreate(BaseModel):
    message: str
    remind_at: str
    done: bool = False


class ReminderOut(BaseOut, ReminderCreate):
    pass


class ChatPrompt(BaseModel):
    message: str


class ChatMessageOut(BaseOut):
    role: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    history: list[ChatMessageOut]


class SettingsOut(BaseModel):
    app_name: str
    app_env: str
    openai_model: str
