from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.repositories.debug_repo import (
    listar_columnas_tabla,
    listar_tablas_sistema,
    obtener_resumen_tablas_clave,
)
from app.core.auth_dependencies import require_roles

router = APIRouter(
    prefix="/debug",
    tags=["Debug"],
    dependencies=[
        Depends(require_roles("super_admin")),
    ],
)


@router.get("/schema")
def get_schema_resumen(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    settings = get_settings()

    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=403,
            detail="Endpoint disponible solo en ambiente development",
        )

    return {
        "schemas": [
            "organizacion",
            "personal",
            "seguridad",
            "asistencia",
            "dispositivos",
            "auditoria",
        ],
        "tables": obtener_resumen_tablas_clave(db),
    }


@router.get("/tables")
def get_tablas_sistema(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    settings = get_settings()

    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=403,
            detail="Endpoint disponible solo en ambiente development",
        )

    return {
        "items": listar_tablas_sistema(db),
    }


@router.get("/schema/{schema_name}/{table_name}")
def get_columnas_tabla(
    schema_name: str,
    table_name: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    settings = get_settings()

    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=403,
            detail="Endpoint disponible solo en ambiente development",
        )

    try:
        columnas = listar_columnas_tabla(
            db=db,
            schema_name=schema_name,
            table_name=table_name,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not columnas:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró la tabla {schema_name}.{table_name}",
        )

    return {
        "schema": schema_name,
        "table": table_name,
        "columns": columnas,
    }