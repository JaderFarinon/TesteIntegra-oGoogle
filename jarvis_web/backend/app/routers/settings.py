from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.db import get_db
from app.models import Settings
from app.schemas import SettingsCreate, SettingsOut

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut | None)
def get_settings(db: Session = Depends(get_db)):
    return db.query(Settings).order_by(Settings.id.desc()).first()


@router.post("", response_model=SettingsOut, status_code=status.HTTP_201_CREATED)
def upsert_settings(payload: SettingsCreate, db: Session = Depends(get_db)):
    config = db.query(Settings).order_by(Settings.id.desc()).first()
    if not config:
        config = Settings(**payload.model_dump())
        db.add(config)
    else:
        config.openai_api_key = payload.openai_api_key
        config.openai_model = payload.openai_model or app_settings.default_openai_model

    db.commit()
    db.refresh(config)
    return config
