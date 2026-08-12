"""
Endpoints para el módulo de Calendario Laboral.

CRUD de eventos + consulta de fecha laborable.
Protegido con módulo HORARIOS (reutiliza permisos existentes).
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.core.auth_dependencies import require_module_access
from app.core.database import get_db
from app.repositories.calendario_repo import (
    actualizar_evento,
    crear_evento,
    desactivar_evento,
    listar_calendarios,
    listar_eventos,
    obtener_calendario_activo,
    obtener_evento_por_id,
    obtener_eventos_en_rango,
)
from app.schemas.calendario import (
    CalendarioEventoCreateRequest,
    CalendarioEventoListResponse,
    CalendarioEventoResponse,
    CalendarioEventoUpdateRequest,
    ConsultaDiaResponse,
)
from app.services.calendario_service import consultar_dia


router = APIRouter(
    prefix="/calendario",
    tags=["Calendario Laboral"],
)


# ============================================================
# GET /calendario/calendarios — Listar calendarios disponibles
# ============================================================


@router.get("/calendarios")
def get_calendarios(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("HORARIOS", "consultar")),
    ],
) -> list[dict]:
    """Lista calendarios disponibles."""
    return listar_calendarios(db)


# ============================================================
# GET /calendario/eventos — Listar eventos
# ============================================================


@router.get("/eventos", response_model=CalendarioEventoListResponse)
def get_eventos(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("HORARIOS", "consultar")),
    ],
    anio: int | None = Query(default=None, description="Filtrar por año"),
    mes: int | None = Query(default=None, ge=1, le=12, description="Filtrar por mes"),
    tipo_evento: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
) -> dict:
    """Lista eventos del calendario con filtros opcionales."""
    return listar_eventos(
        db,
        anio=anio,
        mes=mes,
        tipo_evento=tipo_evento,
        page=page,
        page_size=page_size,
    )


# ============================================================
# GET /calendario/eventos/{id} — Detalle de evento
# ============================================================


@router.get("/eventos/{evento_id}", response_model=CalendarioEventoResponse)
def get_evento(
    evento_id: int,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("HORARIOS", "consultar")),
    ],
) -> dict:
    """Obtiene detalle de un evento específico."""
    evento = obtener_evento_por_id(db, evento_id)

    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe evento con id {evento_id}.",
        )

    return evento


# ============================================================
# POST /calendario/eventos — Crear evento
# ============================================================


@router.post(
    "/eventos",
    response_model=CalendarioEventoResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_crear_evento(
    payload: CalendarioEventoCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("HORARIOS", "crear")),
    ],
) -> dict:
    """Crea un nuevo evento en el calendario."""

    # Resolver calendario_id
    calendario_id = payload.calendario_id
    if calendario_id is None:
        cal = obtener_calendario_activo(db)
        if cal is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No existe un calendario activo. Crea uno primero.",
            )
        calendario_id = cal["id"]

    try:
        evento = crear_evento(
            db,
            calendario_id=calendario_id,
            nombre=payload.nombre,
            descripcion=payload.descripcion,
            tipo_evento=payload.tipo_evento,
            tipo_recurrencia=payload.tipo_recurrencia,
            fecha_inicio=payload.fecha_inicio,
            fecha_fin=payload.fecha_fin,
            mes=payload.mes,
            dia=payload.dia,
            afecta_asistencia=payload.afecta_asistencia,
            es_laborable=payload.es_laborable,
            prioridad=payload.prioridad,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return evento


# ============================================================
# PATCH /calendario/eventos/{id} — Actualizar evento
# ============================================================


@router.patch("/eventos/{evento_id}", response_model=CalendarioEventoResponse)
def patch_evento(
    evento_id: int,
    payload: CalendarioEventoUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("HORARIOS", "editar")),
    ],
) -> dict:
    """Actualiza campos de un evento existente."""

    evento = actualizar_evento(
        db,
        evento_id,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        tipo_evento=payload.tipo_evento,
        tipo_recurrencia=payload.tipo_recurrencia,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
        mes=payload.mes,
        dia=payload.dia,
        afecta_asistencia=payload.afecta_asistencia,
        es_laborable=payload.es_laborable,
        prioridad=payload.prioridad,
        activo=payload.activo,
    )

    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe evento con id {evento_id}.",
        )

    return evento


# ============================================================
# DELETE /calendario/eventos/{id} — Desactivar evento
# ============================================================


@router.delete("/eventos/{evento_id}", response_model=CalendarioEventoResponse)
def delete_evento(
    evento_id: int,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("HORARIOS", "eliminar")),
    ],
) -> dict:
    """Desactiva un evento (soft delete)."""

    evento = desactivar_evento(db, evento_id)

    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe evento con id {evento_id}.",
        )

    return evento


# ============================================================
# GET /calendario/dia/{fecha} — Consultar si fecha es laborable
# ============================================================


@router.get("/dia/{fecha}", response_model=ConsultaDiaResponse)
def get_dia(
    fecha: date,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("HORARIOS", "consultar")),
    ],
    empleado_id: int | None = Query(
        default=None,
        description="ID del empleado para verificar horario_dias como fallback.",
    ),
) -> dict:
    """
    Consulta si una fecha es laborable.

    Aplica reglas de prioridad:
    1. Eventos de calendario (por prioridad).
    2. horario_dias del empleado (si se envía empleado_id).
    3. Default: laborable.
    """
    return consultar_dia(db, fecha, empleado_id)


# ============================================================
# GET /calendario/rango — Eventos en rango de fechas
# ============================================================


@router.get("/rango")
def get_eventos_rango(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("HORARIOS", "consultar")),
    ],
    fecha_inicio: date = Query(description="Fecha inicial YYYY-MM-DD"),
    fecha_fin: date = Query(description="Fecha final YYYY-MM-DD"),
) -> list[dict]:
    """Retorna eventos que aplican en un rango de fechas (para vista mensual)."""

    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fecha_fin no puede ser anterior a fecha_inicio.",
        )

    return obtener_eventos_en_rango(db, fecha_inicio, fecha_fin)
