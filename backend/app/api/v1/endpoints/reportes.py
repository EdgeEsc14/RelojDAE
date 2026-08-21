"""
Endpoints para generación y exportación de reportes.

Soporta formatos: JSON (preview), CSV y PDF.
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
from app.repositories.reportes_repo import (
    obtener_reporte_departamental,
    obtener_reporte_empleado,
)
from app.repositories.reportes_pdf_repo import (
    obtener_datos_reporte_empleado as obtener_datos_pdf,
)
from app.services.reportes_export_service import (
    generar_csv_reporte_departamental,
    generar_csv_reporte_empleado,
    generar_pdf_reporte_departamental,
)
from app.services.reporte_pdf_service import (
    generar_reporte_pdf_empleado as generar_pdf_profesional,
)


def _require_exportar(access_scope: AccessScope) -> None:
    """
    CSV/PDF requieren el permiso 'exportar' del módulo REPORTES,
    distinto de 'consultar' (que solo habilita la vista previa JSON).
    """
    if not access_scope.allows("exportar"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para exportar reportes.",
        )


router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
)


# ============================================================
# Reporte Individual por Empleado
# ============================================================


@router.get("/empleado/{codigo_empleado}")
def get_reporte_empleado(
    codigo_empleado: str,
    db: Annotated[Session, Depends(get_db)],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("REPORTES", "consultar")
        ),
    ],
    fecha_inicio: date = Query(description="Fecha inicial YYYY-MM-DD"),
    fecha_fin: date = Query(description="Fecha final YYYY-MM-DD"),
    formato: str = Query(
        default="json",
        description="Formato de salida: json, csv, pdf",
    ),
):
    """
    Genera reporte de asistencia para un empleado específico, usando
    asistencia.asistencias_diarias como fuente oficial.

    Formatos soportados:
    - json: Datos estructurados para preview en frontend (requiere consultar)
    - csv: Archivo CSV descargable (requiere exportar)
    - pdf: Documento PDF descargable (requiere exportar)
    """

    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fecha_fin no puede ser anterior a fecha_inicio.",
        )

    data = obtener_reporte_empleado(
        db=db,
        codigo_empleado=codigo_empleado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        access_scope=access_scope,
    )

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado o sin permiso de acceso.",
        )

    formato_lower = formato.strip().lower()

    if formato_lower == "csv":
        _require_exportar(access_scope)

        csv_content = generar_csv_reporte_empleado(data)
        filename = f"reporte_empleado_{codigo_empleado}_{fecha_inicio}_{fecha_fin}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    if formato_lower == "pdf":
        _require_exportar(access_scope)

        # Un único generador de PDF por empleado (reportlab,
        # institucional): evita mantener dos plantillas distintas
        # para el mismo reporte.
        datos_pdf = obtener_datos_pdf(
            db=db,
            codigo_empleado=codigo_empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            access_scope=access_scope,
        )

        if datos_pdf is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleado no encontrado.",
            )

        try:
            pdf_content = generar_pdf_profesional(datos_pdf)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generando PDF: {type(exc).__name__}: {str(exc)}",
            ) from exc

        filename = f"reporte_empleado_{codigo_empleado}_{fecha_inicio}_{fecha_fin}.pdf"

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    # Default: JSON
    return data


# ============================================================
# Reporte Departamental
# ============================================================


@router.get("/departamental")
def get_reporte_departamental(
    db: Annotated[Session, Depends(get_db)],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("REPORTES", "consultar")
        ),
    ],
    fecha_inicio: date = Query(description="Fecha inicial YYYY-MM-DD"),
    fecha_fin: date = Query(description="Fecha final YYYY-MM-DD"),
    formato: str = Query(
        default="json",
        description="Formato de salida: json, csv, pdf",
    ),
    unidad_organizacional_id: int | None = Query(
        default=None,
        description="Filtrar por departamento específico (debe ser una "
        "unidad de tipo DEPARTAMENTO).",
    ),
):
    """
    Genera reporte concentrado de asistencia por departamento,
    respetando la jerarquía organizacional (no mezcla Dirección ni
    División con Departamento).

    Formatos soportados:
    - json: Datos estructurados para preview en frontend (requiere consultar)
    - csv: Archivo CSV descargable (requiere exportar)
    - pdf: Documento PDF descargable (requiere exportar)
    """

    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fecha_fin no puede ser anterior a fecha_inicio.",
        )

    try:
        data = obtener_reporte_departamental(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            access_scope=access_scope,
            unidad_organizacional_id=unidad_organizacional_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    formato_lower = formato.strip().lower()

    if formato_lower == "csv":
        _require_exportar(access_scope)

        csv_content = generar_csv_reporte_departamental(data)
        filename = f"reporte_departamental_{fecha_inicio}_{fecha_fin}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    if formato_lower == "pdf":
        _require_exportar(access_scope)

        try:
            pdf_content = generar_pdf_reporte_departamental(data)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generando PDF: {type(exc).__name__}: {str(exc)}",
            ) from exc

        filename = f"reporte_departamental_{fecha_inicio}_{fecha_fin}.pdf"

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    # Default: JSON
    return data


# ============================================================
# Reporte PDF Profesional por Empleado (nuevo, con reportlab)
# ============================================================


@router.get("/empleado/{codigo_empleado}/pdf")
def get_reporte_empleado_pdf(
    codigo_empleado: str,
    db: Annotated[Session, Depends(get_db)],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("REPORTES", "exportar")
        ),
    ],
    fecha_inicio: date = Query(description="Fecha inicial YYYY-MM-DD"),
    fecha_fin: date = Query(description="Fecha final YYYY-MM-DD"),
):
    """
    Genera reporte PDF profesional de asistencia/incidencias
    para un empleado específico.

    Diseño institucional con:
    - Logo configurable
    - Encabezado institucional
    - Datos del empleado
    - Tabla diaria detallada
    - Resumen estadístico
    - Pie de página con paginación
    """

    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fecha_fin no puede ser anterior a fecha_inicio.",
        )

    datos = obtener_datos_pdf(
        db=db,
        codigo_empleado=codigo_empleado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        access_scope=access_scope,
    )

    if datos is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado.",
        )

    try:
        pdf_bytes = generar_pdf_profesional(datos)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando PDF: {type(exc).__name__}: {str(exc)}",
        ) from exc

    filename = f"reporte_{codigo_empleado}_{fecha_inicio}_{fecha_fin}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
