from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.asistencia_repo import (
    listar_asistencia_diaria,
    obtener_resumen_asistencia_empleado,
)
from app.schemas.asistencia import (
    AsistenciaDiariaListadoResponse,
    AsistenciaEmpleadoResumenResponse,
)


router = APIRouter(
    prefix="/asistencia",
    tags=["Asistencia"],
)


@router.get(
    "/diaria",
    response_model=AsistenciaDiariaListadoResponse,
)
def get_asistencia_diaria(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date, Query(description="Fecha de asistencia en formato YYYY-MM-DD")],
    q: Annotated[str | None, Query(description="Búsqueda por código, nombre o correo")] = None,
    estatus: Annotated[str | None, Query(description="Filtro por estatus de asistencia")] = None,
    unidad_organizacional_id: Annotated[int | None, Query(description="Filtro por unidad organizacional")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    return listar_asistencia_diaria(
        db=db,
        fecha=fecha,
        q=q,
        estatus=estatus,
        unidad_organizacional_id=unidad_organizacional_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/empleados/{codigo_empleado}/resumen",
    response_model=AsistenciaEmpleadoResumenResponse,
)
def get_resumen_asistencia_empleado(
    codigo_empleado: str,
    db: Annotated[Session, Depends(get_db)],
    limite: Annotated[int, Query(ge=1, le=30)] = 10,
) -> dict:
    resumen = obtener_resumen_asistencia_empleado(
        db=db,
        codigo_empleado=codigo_empleado,
        limite=limite,
    )

    if resumen is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe empleado con código {codigo_empleado}",
        )

    return resumen