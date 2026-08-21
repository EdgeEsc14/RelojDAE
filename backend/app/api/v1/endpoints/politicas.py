"""
Endpoints para la Política de Asistencia (asistencia.politicas_asistencia).

Fuente canónica para la pantalla de Configuración: no existe una
segunda copia de estas reglas en el backend ni en el frontend.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.core.auth_dependencies import require_module_access
from app.core.database import get_db
from app.schemas.politicas import (
    PoliticaAsistenciaResponse,
    PoliticaAsistenciaUpdate,
)
from app.services.politica_service import (
    PoliticaSinResolucionUnica,
    actualizar_politica_activa,
    obtener_politica_activa,
)


router = APIRouter(
    prefix="/politicas-asistencia",
    tags=["PoliticasAsistencia"],
)


def _resolucion_a_http(exc: PoliticaSinResolucionUnica) -> HTTPException:
    if exc.estado == "SIN_POLITICA":
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No existe una política de asistencia ACTIVA vigente "
                f"para {exc.resolucion.fecha}. Debe configurarse una "
                "política en asistencia.politicas_asistencia."
            ),
        )

    # MULTIPLES_POLITICAS: nunca se elige una candidata silenciosamente
    # (Contrato §5). Se reporta explícitamente para que un administrador
    # corrija el solapamiento de vigencias.
    candidatos = [
        {
            "id": p["id"],
            "codigo": p["codigo"],
            "version": p["version"],
            "vigencia_desde": str(p["vigencia_desde"]),
            "vigencia_hasta": (
                str(p["vigencia_hasta"]) if p["vigencia_hasta"] else None
            ),
        }
        for p in exc.resolucion.candidatos
    ]

    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "message": (
                "Existen múltiples políticas ACTIVAS con vigencia "
                f"solapada para {exc.resolucion.fecha}. Corrija la "
                "configuración antes de continuar."
            ),
            "candidatos": candidatos,
        },
    )


@router.get("/activa", response_model=PoliticaAsistenciaResponse)
def get_politica_activa(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "CONFIGURACION",
                "consultar",
            )
        ),
    ],
) -> dict:
    try:
        return obtener_politica_activa(db)
    except PoliticaSinResolucionUnica as exc:
        raise _resolucion_a_http(exc) from exc


@router.put("/activa", response_model=PoliticaAsistenciaResponse)
def put_politica_activa(
    payload: PoliticaAsistenciaUpdate,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "CONFIGURACION",
                "editar",
            )
        ),
    ],
) -> dict:
    try:
        return actualizar_politica_activa(db, payload)
    except PoliticaSinResolucionUnica as exc:
        raise _resolucion_a_http(exc) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
