from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings():
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "openai_model": settings.openai_model,
    }
