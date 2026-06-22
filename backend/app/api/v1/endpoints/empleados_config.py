from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.empleados_config_repo import (
    asignar_dispositivo_empleado,
    asignar_horario_empleado,
    crear_usuario_sistema_empleado,
)
from app.schemas.empleados_config import (
    AsignacionHorarioEmpleadoResponse,
    AsignarDispositivoEmpleadoRequest,
    AsignarHorarioEmpleadoRequest,
    CrearUsuarioSistemaEmpleadoRequest,
    DispositivoEmpleadoResponse,
    UsuarioSistemaEmpleadoResponse,
)


router = APIRouter(
    prefix="/empleados",
    tags=["Empleados - Configuración"],
)


@router.post(
    "/{codigo_empleado}/horarios/asignar",
    response_model=AsignacionHorarioEmpleadoResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_asignar_horario_empleado(
    codigo_empleado: str,
    payload: AsignarHorarioEmpleadoRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    try:
        asignacion = asignar_horario_empleado(
            db=db,
            codigo_empleado=codigo_empleado,
            payload=payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if asignacion is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe empleado con código {codigo_empleado}",
        )

    return asignacion


@router.post(
    "/{codigo_empleado}/dispositivos/asignar",
    response_model=DispositivoEmpleadoResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_asignar_dispositivo_empleado(
    codigo_empleado: str,
    payload: AsignarDispositivoEmpleadoRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    try:
        asignacion = asignar_dispositivo_empleado(
            db=db,
            codigo_empleado=codigo_empleado,
            payload=payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if asignacion is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe empleado con código {codigo_empleado}",
        )

    return asignacion


@router.post(
    "/{codigo_empleado}/usuario-sistema",
    response_model=UsuarioSistemaEmpleadoResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_crear_usuario_sistema_empleado(
    codigo_empleado: str,
    payload: CrearUsuarioSistemaEmpleadoRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    try:
        usuario = crear_usuario_sistema_empleado(
            db=db,
            codigo_empleado=codigo_empleado,
            payload=payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe empleado con código {codigo_empleado}",
        )

    return usuario