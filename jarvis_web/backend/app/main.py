from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import init_database
from app.routers.appointments import router as appointments_router
from app.routers.assistant import router as assistant_router
from app.routers.conversations import router as conversations_router
from app.routers.expenses import router as expenses_router
from app.routers.health import router as health_router
from app.routers.notes import router as notes_router
from app.routers.reminders import router as reminders_router
from app.routers.settings import router as settings_router
from app.routers.tasks import router as tasks_router

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    init_database()


@app.get("/")
def root():
    return {"message": "Jarvis Web API online"}


app.include_router(health_router)
app.include_router(settings_router)
app.include_router(conversations_router)
app.include_router(tasks_router)
app.include_router(appointments_router)
app.include_router(notes_router)
app.include_router(expenses_router)
app.include_router(reminders_router)
app.include_router(assistant_router)
