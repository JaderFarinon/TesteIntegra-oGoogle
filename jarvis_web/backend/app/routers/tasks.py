from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Task
from app.schemas import RecurringTaskCreate, RecurringTaskCreateOut, TaskCreate, TaskOut, TaskUpdate
from app.services.task_recurrence_service import create_recurring_tasks_batch

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.created_at.desc()).all()


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.post("/recurring", response_model=RecurringTaskCreateOut, status_code=status.HTTP_201_CREATED)
def create_recurring_tasks(payload: RecurringTaskCreate, db: Session = Depends(get_db)):
    recurrence_group_id, tasks = create_recurring_tasks_batch(db, payload)
    return RecurringTaskCreateOut(
        recurrence_group_id=recurrence_group_id,
        total_created=len(tasks),
        tasks=tasks,
    )


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")

    db.delete(task)
    db.commit()
    return None
