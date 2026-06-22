from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.empleados_repo import (
    listar_empleados,
    obtener_empleado_por_codigo,
    obtener_perfil_empleado_por_codigo,
)
from app.repositories.empleados_write_repo import (
    actualizar_empleado,
    actualizar_estatus_empleado,
    crear_empleado,
    generar_siguiente_codigo_empleado,
)
from app.schemas.empleados import (
    EmpleadoPerfilResponse,
    EmpleadoResumen,
    EmpleadosListadoResponse,
)
from app.schemas.empleados_write import (
    EmpleadoCreate,
    EmpleadoEstatusUpdate,
    EmpleadoUpdate,
    SiguienteCodigoEmpleadoResponse,
)


router = APIRouter(
    prefix="/empleados",
    tags=["Empleados"],
)


@router.get("", response_model=EmpleadosListadoResponse)
def get_empleados(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(description="Búsqueda por código, nombre o correo")] = None,
    estatus: Annotated[str | None, Query(description="Filtro por estatus del empleado")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    return listar_empleados(
        db=db,
        q=q,
        estatus=estatus,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/siguiente-codigo",
    response_model=SiguienteCodigoEmpleadoResponse,
)
def get_siguiente_codigo_empleado(
    db: Annotated[Session, Depends(get_db)],
    prefijo: Annotated[str, Query(min_length=2, max_length=10)] = "EMP",
) -> dict:
    try:
        return generar_siguiente_codigo_empleado(
            db=db,
            prefijo=prefijo,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=EmpleadoResumen,
    status_code=status.HTTP_201_CREATED,
)
def post_empleado(
    payload: EmpleadoCreate,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    try:
        return crear_empleado(
            db=db,
            payload=payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/{codigo_empleado}/perfil", response_model=EmpleadoPerfilResponse)
def get_perfil_empleado_por_codigo(
    codigo_empleado: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    perfil = obtener_perfil_empleado_por_codigo(
        db=db,
        codigo_empleado=codigo_empleado,
    )

    if perfil is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe empleado con código {codigo_empleado}",
        )

    return perfil


@router.put("/{codigo_empleado}", response_model=EmpleadoResumen)
def put_empleado(
    codigo_empleado: str,
    payload: EmpleadoUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    try:
        empleado = actualizar_empleado(
            db=db,
            codigo_empleado=codigo_empleado,
            payload=payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if empleado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe empleado con código {codigo_empleado}",
        )

    return empleado


@router.patch("/{codigo_empleado}/estatus", response_model=EmpleadoResumen)
def patch_estatus_empleado(
    codigo_empleado: str,
    payload: EmpleadoEstatusUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    try:
        empleado = actualizar_estatus_empleado(
            db=db,
            codigo_empleado=codigo_empleado,
            estatus=payload.estatus,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if empleado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe empleado con código {codigo_empleado}",
        )

    return empleado


@router.get("/{codigo_empleado}", response_model=EmpleadoResumen)
def get_empleado_por_codigo(
    codigo_empleado: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    empleado = obtener_empleado_por_codigo(
        db=db,
        codigo_empleado=codigo_empleado,
    )

    if empleado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe empleado con código {codigo_empleado}",
        )

    return empleado