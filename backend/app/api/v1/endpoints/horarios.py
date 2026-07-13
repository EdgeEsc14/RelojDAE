from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.repositories.horarios_repo import (
    actualizar_estatus_horario,
    crear_horario,
    listar_horarios_admin,
    obtener_horario_por_id,
)
from app.schemas.horarios import (
    HorarioCreate,
    HorarioEstatusUpdate,
    HorarioResponse,
    HorariosListadoResponse,
)


router = APIRouter(
    prefix="/horarios",
    tags=["Horarios"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.get("", response_model=HorariosListadoResponse)
def get_horarios(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return listar_horarios_admin(db=db)


@router.get("/{horario_id}", response_model=HorarioResponse)
def get_horario_por_id(
    horario_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    horario = obtener_horario_por_id(
        db=db,
        horario_id=horario_id,
    )

    if horario is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe horario con id {horario_id}.",
        )

    return horario


@router.post(
    "",
    response_model=HorarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_horario(
    payload: HorarioCreate,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[
        dict,
        Depends(require_roles("super_admin", "rh_admin")),
    ] = None,
) -> dict:
    try:
        return crear_horario(
            db=db,
            payload=payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.patch("/{horario_id}/estatus", response_model=HorarioResponse)
def patch_estatus_horario(
    horario_id: int,
    payload: HorarioEstatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[
        dict,
        Depends(require_roles("super_admin", "rh_admin")),
    ] = None,
) -> dict:
    horario = actualizar_estatus_horario(
        db=db,
        horario_id=horario_id,
        activo=payload.activo,
    )

    if horario is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe horario con id {horario_id}.",
        )

    return horario