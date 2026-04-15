from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.db import get_db
from app.models import Settings
from app.schemas import SettingsCreate, SettingsOut

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_latest_settings(db: Session) -> Optional[Settings]:
    return db.query(Settings).order_by(Settings.id.desc()).first()


@router.get("/openai", response_model=Optional[SettingsOut])
def get_openai_settings(db: Session = Depends(get_db)):
    return _get_latest_settings(db)


@router.put("/openai", response_model=SettingsOut, status_code=status.HTTP_200_OK)
def upsert_openai_settings(payload: SettingsCreate, db: Session = Depends(get_db)):
    config = _get_latest_settings(db)
    if not config:
        config = Settings(**payload.model_dump())
        db.add(config)
    else:
        config.openai_api_key = payload.openai_api_key
        config.openai_model = payload.openai_model or app_settings.default_openai_model

    db.commit()
    db.refresh(config)
    return config


@router.get("", response_model=Optional[SettingsOut], include_in_schema=False)
def get_settings_legacy(db: Session = Depends(get_db)):
    return _get_latest_settings(db)


@router.post("", response_model=SettingsOut, status_code=status.HTTP_200_OK, include_in_schema=False)
def upsert_settings_legacy(payload: SettingsCreate, db: Session = Depends(get_db)):
    return upsert_openai_settings(payload, db)
