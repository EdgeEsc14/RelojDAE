from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_user
from app.core.database import get_db
from app.repositories.dashboard_repo import obtener_dashboard_resumen
from app.schemas.dashboard import DashboardResumenResponse


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.get("/resumen", response_model=DashboardResumenResponse)
def get_dashboard_resumen(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return obtener_dashboard_resumen(db=db)