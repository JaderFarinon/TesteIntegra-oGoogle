from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Appointment, Expense, Note, Reminder, Task
from app.schemas import (
    AppointmentCreate,
    AppointmentOut,
    ExpenseCreate,
    ExpenseOut,
    NoteCreate,
    NoteOut,
    ReminderCreate,
    ReminderOut,
    TaskCreate,
    TaskOut,
)

router = APIRouter(prefix="/api", tags=["modules"])


MODULES = {
    "tasks": (Task, TaskCreate, TaskOut),
    "appointments": (Appointment, AppointmentCreate, AppointmentOut),
    "notes": (Note, NoteCreate, NoteOut),
    "expenses": (Expense, ExpenseCreate, ExpenseOut),
    "reminders": (Reminder, ReminderCreate, ReminderOut),
}


def _get_module(module: str):
    if module not in MODULES:
        raise HTTPException(status_code=404, detail="Módulo não encontrado")
    return MODULES[module]


@router.get("/{module}")
def list_items(module: str, db: Session = Depends(get_db)):
    model, _, _ = _get_module(module)
    return db.query(model).order_by(model.created_at.desc()).all()


@router.post("/{module}", status_code=status.HTTP_201_CREATED)
def create_item(module: str, payload: dict, db: Session = Depends(get_db)):
    model, schema_in, _ = _get_module(module)
    validated = schema_in(**payload)
    item = model(**validated.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{module}/{item_id}")
def update_item(module: str, item_id: int, payload: dict, db: Session = Depends(get_db)):
    model, schema_in, _ = _get_module(module)
    item = db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    validated = schema_in(**payload)
    for key, value in validated.model_dump().items():
        setattr(item, key, value)

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{module}/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(module: str, item_id: int, db: Session = Depends(get_db)):
    model, _, _ = _get_module(module)
    item = db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    db.delete(item)
    db.commit()
    return None
