"""
Endpoints de Auditoría (solo lectura).

Expone directamente auditoria.bitacora (migración 035) y
seguridad.login_auditoria (migración 055) — no hay una tercera fuente
inventada. AUDITOR y SUPER_ADMIN son los únicos roles con acceso
(seed 062): ambos solo con consultar/exportar, nunca crear/editar/
eliminar — la bitácora es de solo lectura desde la aplicación por
diseño (solo los triggers escriben en ella).
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.core.auth_dependencies import require_module_access
from app.core.database import get_db
from app.repositories.auditoria_repo import (
    listar_bitacora,
    listar_login_auditoria,
    obtener_evento_bitacora,
    obtener_resumen_auditoria,
    obtener_valores_distintos_bitacora,
)
from app.schemas.auditoria import (
    AuditoriaResumenResponse,
    BitacoraEventoDetalle,
    BitacoraFiltrosResponse,
    BitacoraListadoResponse,
    LoginListadoResponse,
)
from app.services.auditoria_export_service import (
    generar_csv_bitacora,
    generar_csv_login,
)


router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría"],
)


def _default_rango(
    fecha_inicio: date | None,
    fecha_fin: date | None,
) -> tuple[date, date]:
    fin = fecha_fin or date.today()
    inicio = fecha_inicio or fin.replace(day=1)

    if fin < inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fecha_fin no puede ser anterior a fecha_inicio.",
        )

    return inicio, fin


@router.get("/resumen", response_model=AuditoriaResumenResponse)
def get_resumen(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("AUDITORIA", "consultar")),
    ],
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
):
    inicio, fin = _default_rango(fecha_inicio, fecha_fin)
    return obtener_resumen_auditoria(db=db, fecha_inicio=inicio, fecha_fin=fin)


@router.get("/bitacora/filtros", response_model=BitacoraFiltrosResponse)
def get_bitacora_filtros(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("AUDITORIA", "consultar")),
    ],
):
    return obtener_valores_distintos_bitacora(db=db)


@router.get("/bitacora", response_model=BitacoraListadoResponse)
def get_bitacora(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("AUDITORIA", "consultar")),
    ],
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    esquema: str | None = Query(default=None),
    tabla: str | None = Query(default=None),
    operacion: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return listar_bitacora(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        esquema=esquema,
        tabla=tabla,
        operacion=operacion,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/bitacora/export")
def get_bitacora_export(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("AUDITORIA", "exportar")),
    ],
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    esquema: str | None = Query(default=None),
    tabla: str | None = Query(default=None),
    operacion: str | None = Query(default=None),
    q: str | None = Query(default=None),
):
    data = listar_bitacora(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        esquema=esquema,
        tabla=tabla,
        operacion=operacion,
        q=q,
        limit=10000,
        offset=0,
    )

    csv_content = generar_csv_bitacora(data["items"])
    filename = f"auditoria_bitacora_{date.today().isoformat()}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/bitacora/{evento_id}", response_model=BitacoraEventoDetalle)
def get_bitacora_detalle(
    evento_id: int,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("AUDITORIA", "consultar")),
    ],
):
    evento = obtener_evento_bitacora(db=db, evento_id=evento_id)

    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el evento de bitácora {evento_id}.",
        )

    return evento


@router.get("/login", response_model=LoginListadoResponse)
def get_login(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("AUDITORIA", "consultar")),
    ],
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    resultado: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return listar_login_auditoria(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        resultado=resultado,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/login/export")
def get_login_export(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("AUDITORIA", "exportar")),
    ],
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    resultado: str | None = Query(default=None),
    q: str | None = Query(default=None),
):
    data = listar_login_auditoria(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        resultado=resultado,
        q=q,
        limit=10000,
        offset=0,
    )

    csv_content = generar_csv_login(data["items"])
    filename = f"auditoria_login_{date.today().isoformat()}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
