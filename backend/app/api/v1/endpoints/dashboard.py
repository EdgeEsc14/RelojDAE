from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.core.auth_dependencies import require_module_access
from app.core.database import get_db
from app.repositories.dashboard_repo import (
    obtener_dashboard_resumen,
)
from app.schemas.dashboard import DashboardResumenResponse


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/resumen",
    response_model=DashboardResumenResponse,
)
def get_dashboard_resumen(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "DASHBOARD",
                "consultar",
            )
        ),
    ],
) -> dict:
    return obtener_dashboard_resumen(
        db=db,
        access_scope=access_scope,
    )