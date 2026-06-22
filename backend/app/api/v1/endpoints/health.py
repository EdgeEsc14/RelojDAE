from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.database import probar_conexion_db


router = APIRouter(
    prefix="/health",
    tags=["Healthcheck"],
)


@router.get("")
def healthcheck() -> dict:
    settings = get_settings()

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/db")
def healthcheck_db() -> dict:
    try:
        db_info = probar_conexion_db()

        return {
            "status": "ok",
            "database": db_info,
        }

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc