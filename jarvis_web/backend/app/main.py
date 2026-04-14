from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import engine
from app.models import Base
from app.routers.chat import router as chat_router
from app.routers.modules import router as modules_router
from app.routers.settings import router as settings_router

app = FastAPI(title=settings.app_name)

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Jarvis Web API online"}


app.include_router(chat_router)
app.include_router(modules_router)
app.include_router(settings_router)
