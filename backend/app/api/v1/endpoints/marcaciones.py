from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.marcaciones_repo import listar_marcaciones
from app.schemas.marcaciones import MarcacionesListadoResponse


router = APIRouter(
    prefix="/marcaciones",
    tags=["Marcaciones"],
)


@router.get("", response_model=MarcacionesListadoResponse)
def get_marcaciones(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date | None, Query(description="Fecha de marcaciones en formato YYYY-MM-DD")] = None,
    q: Annotated[str | None, Query(description="Búsqueda por empleado, ZK user ID o dispositivo")] = None,
    dispositivo_id: Annotated[int | None, Query(description="Filtro por dispositivo")] = None,
    empleado_id: Annotated[int | None, Query(description="Filtro por empleado interno")] = None,
    procesada: Annotated[bool | None, Query(description="Filtro por estado de procesamiento")] = None,
    tipo_marcacion_codigo: Annotated[str | None, Query(description="Filtro por código de tipo de marcación")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    return listar_marcaciones(
        db=db,
        fecha=fecha,
        q=q,
        dispositivo_id=dispositivo_id,
        empleado_id=empleado_id,
        procesada=procesada,
        tipo_marcacion_codigo=tipo_marcacion_codigo,
        limit=limit,
        offset=offset,
    )