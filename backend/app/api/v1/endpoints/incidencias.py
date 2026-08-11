"""
Endpoints para gestión de incidencias.

CRUD con control de acceso por módulo INCIDENCIAS.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.core.auth_dependencies import get_current_user, require_module_access
from app.core.database import get_db
from app.repositories.incidencias_repo import (
    contar_incidencias_por_estatus,
    crear_incidencia,
    listar_incidencias,
    obtener_incidencia_por_id,
    revisar_incidencia,
)
from app.schemas.incidencias import (
    IncidenciaCreateRequest,
    IncidenciaDetailResponse,
    IncidenciaListResponse,
    IncidenciaReviewRequest,
    IncidenciasContadoresResponse,
)


router = APIRouter(
    prefix="/incidencias",
    tags=["Incidencias"],
)


# ============================================================
# GET /incidencias — Listar incidencias
# ============================================================


@router.get("", response_model=IncidenciaListResponse)
def get_incidencias(
    db: Annotated[Session, Depends(get_db)],
    access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("INCIDENCIAS", "consultar")),
    ],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    estatus: str | None = Query(default=None),
    tipo_incidencia_id: int | None = Query(default=None),
    empleado_id: int | None = Query(default=None),
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    busqueda: str | None = Query(default=None, max_length=100),
) -> dict:
    """Lista incidencias con filtros y paginación."""

    return listar_incidencias(
        db,
        access_scope,
        page=page,
        page_size=page_size,
        estatus=estatus,
        tipo_incidencia_id=tipo_incidencia_id,
        empleado_id=empleado_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        busqueda=busqueda,
    )


# ============================================================
# GET /incidencias/contadores — Métricas por estatus
# ============================================================


@router.get("/contadores", response_model=IncidenciasContadoresResponse)
def get_contadores(
    db: Annotated[Session, Depends(get_db)],
    access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("INCIDENCIAS", "consultar")),
    ],
) -> dict:
    """Retorna contadores de incidencias agrupados por estatus."""

    return contar_incidencias_por_estatus(db, access_scope)


# ============================================================
# GET /incidencias/{id} — Detalle
# ============================================================


@router.get("/{incidencia_id}", response_model=IncidenciaDetailResponse)
def get_incidencia(
    incidencia_id: int,
    db: Annotated[Session, Depends(get_db)],
    access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("INCIDENCIAS", "consultar")),
    ],
) -> dict:
    """Obtiene detalle completo de una incidencia."""

    incidencia = obtener_incidencia_por_id(db, incidencia_id, access_scope)

    if incidencia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe incidencia con id {incidencia_id} o no tienes acceso.",
        )

    return incidencia


# ============================================================
# POST /incidencias — Crear incidencia manual
# ============================================================


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def post_crear_incidencia(
    payload: IncidenciaCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("INCIDENCIAS", "crear")),
    ],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Crea una incidencia manual."""

    try:
        result = crear_incidencia(
            db,
            empleado_id=payload.empleado_id,
            tipo_incidencia_id=payload.tipo_incidencia_id,
            fecha=payload.fecha,
            descripcion=payload.descripcion,
            puntos_originales=payload.puntos_originales,
            creada_por_usuario_id=current_user["id"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return result


# ============================================================
# PATCH /incidencias/{id}/revisar — Aprobar/Rechazar
# ============================================================


@router.patch("/{incidencia_id}/revisar")
def patch_revisar_incidencia(
    incidencia_id: int,
    payload: IncidenciaReviewRequest,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("INCIDENCIAS", "aprobar")),
    ],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Aprueba, rechaza o cancela una incidencia."""

    try:
        result = revisar_incidencia(
            db,
            incidencia_id,
            estatus=payload.estatus,
            comentario_revision=payload.comentario_revision,
            revisada_por_usuario_id=current_user["id"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe incidencia con id {incidencia_id}.",
        )

    return result
