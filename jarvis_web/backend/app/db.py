from __future__ import annotations

from collections.abc import Generator
from datetime import date, datetime, time
from pathlib import Path

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import (
    Appointment,
    Base,
    Conversation,
    Expense,
    Message,
    Note,
    Reminder,
    Settings,
    Task,
)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    """Inicializa estrutura do banco e popula dados de exemplo opcionalmente."""
    _prepare_sqlite_path(settings.database_url)
    Base.metadata.create_all(bind=engine)
    _ensure_tasks_schema_compatibility()

    if settings.database_seed_enabled:
        with SessionLocal() as db:
            if _database_is_empty(db):
                _seed_initial_data(db)


def _ensure_tasks_schema_compatibility() -> None:
    """Garante colunas novas de recorrência sem migração externa."""
    inspector = inspect(engine)
    if "tasks" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("tasks")}
    column_statements = {
        "is_recurring": "ALTER TABLE tasks ADD COLUMN is_recurring BOOLEAN NOT NULL DEFAULT 0",
        "recurrence_group_id": "ALTER TABLE tasks ADD COLUMN recurrence_group_id VARCHAR(36)",
        "recurrence_pattern": "ALTER TABLE tasks ADD COLUMN recurrence_pattern VARCHAR(30)",
        "recurrence_meta": "ALTER TABLE tasks ADD COLUMN recurrence_meta TEXT",
        "original_prompt": "ALTER TABLE tasks ADD COLUMN original_prompt TEXT",
    }

    with engine.begin() as connection:
        for column_name, ddl in column_statements.items():
            if column_name not in existing_columns:
                connection.execute(text(ddl))


def _prepare_sqlite_path(database_url: str) -> None:
    if not database_url.startswith("sqlite"):
        return

    db_url: URL = make_url(database_url)
    database_name = db_url.database
    if not database_name or database_name == ":memory:":
        return

    db_file = Path(database_name)
    if not db_file.is_absolute():
        db_file = Path.cwd() / db_file

    db_file.parent.mkdir(parents=True, exist_ok=True)


def _database_is_empty(db: Session) -> bool:
    models = [
        Settings,
        Conversation,
        Message,
        Task,
        Appointment,
        Note,
        Expense,
        Reminder,
    ]
    return not any(db.scalar(select(model.id).limit(1)) is not None for model in models)


def _seed_initial_data(db: Session) -> None:
    hoje = date.today()
    agora = datetime.utcnow()

    db.add(
        Settings(
            openai_api_key=None,
            openai_model=settings.default_openai_model,
        )
    )

    conversa = Conversation(title="Boas-vindas")
    db.add(conversa)
    db.flush()

    db.add(
        Message(
            conversation_id=conversa.id,
            role="assistant",
            content="Olá! Eu sou o Jarvis. Use os módulos para organizar seu dia.",
        )
    )

    db.add_all(
        [
            Task(
                title="Revisar prioridades da semana",
                description="Definir as 3 tarefas mais importantes.",
                priority="high",
                status="pending",
                due_date=hoje,
            ),
            Appointment(
                title="Checkpoint diário",
                description="Alinhar progresso das tarefas.",
                date=hoje,
                time=time(hour=9, minute=30),
                location="Home office",
                status="scheduled",
            ),
            Note(
                title="Primeiros passos",
                content="Cadastre suas tarefas, compromissos e lembretes para começar.",
                tag="onboarding",
            ),
            Expense(
                description="Assinatura de ferramenta",
                amount=49.9,
                category="software",
                expense_date=hoje,
                payment_method="cartão",
                notes="Exemplo inicial",
            ),
            Reminder(
                title="Planejamento do dia",
                description="Separar 10 minutos para planejar as atividades.",
                remind_at=agora.replace(hour=8, minute=0, second=0, microsecond=0),
                status="pending",
            ),
        ]
    )

    db.commit()
