"""
Repositorio para consultas de reportes.

Proporciona queries optimizadas para reportes de asistencia
por empleado y por departamento en rangos de fechas.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope


ACCESS_SCOPE_SQL = """
(
    :access_data_scope = 'TOTAL'

    OR (
        :access_data_scope = 'PROPIO'
        AND e.id = :access_employee_id
    )

    OR (
        :access_data_scope = 'AREA'
        AND e.unidad_organizacional_id = ANY(
            CAST(:access_unit_ids AS BIGINT[])
        )
    )
)
"""


def _get_access_params(access_scope: AccessScope) -> dict:
    return {
        "access_data_scope": access_scope.data_scope,
        "access_employee_id": access_scope.employee_id,
        "access_unit_ids": list(access_scope.allowed_unit_ids),
    }


def obtener_reporte_empleado(
    db: Session,
    codigo_empleado: str,
    fecha_inicio: date,
    fecha_fin: date,
    access_scope: AccessScope,
) -> dict[str, Any] | None:
    """
    Genera datos para el reporte individual de un empleado
    en un rango de fechas.

    Retorna:
    - Información del empleado
    - Resumen del periodo (contadores)
    - Detalle diario de asistencia
    """

    access_params = _get_access_params(access_scope)

    # Obtener empleado con verificación de acceso
    empleado_row = db.execute(
        text(
            f"""
            SELECT
                e.id,
                e.codigo_empleado,
                e.nombre_completo,
                e.correo,
                e.estatus,
                p.nombre AS puesto,
                uo.nombre AS unidad_organizacional
            FROM personal.empleados e
            LEFT JOIN organizacion.puestos p ON p.id = e.puesto_id
            LEFT JOIN organizacion.unidades_organizacionales uo
                ON uo.id = e.unidad_organizacional_id
            WHERE e.codigo_empleado = :codigo_empleado
              AND {ACCESS_SCOPE_SQL}
            LIMIT 1
            """
        ),
        {"codigo_empleado": codigo_empleado, **access_params},
    ).mappings().first()

    if empleado_row is None:
        return None

    empleado = dict(empleado_row)
    empleado_id = empleado["id"]

    # Detalle diario
    dias_rows = db.execute(
        text(
            """
            SELECT
                ad.fecha,
                ad.entrada_programada,
                ad.salida_programada,
                ad.primera_entrada,
                ad.ultima_salida,
                ad.minutos_retardo,
                ad.minutos_ordinarios,
                ad.minutos_extra,
                ad.estatus,
                ad.puntos_generados,
                ad.observaciones
            FROM asistencia.asistencias_diarias ad
            WHERE ad.empleado_id = :empleado_id
              AND ad.fecha BETWEEN :fecha_inicio AND :fecha_fin
            ORDER BY ad.fecha ASC
            """
        ),
        {
            "empleado_id": empleado_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        },
    ).mappings().all()

    dias = [dict(row) for row in dias_rows]

    # Resumen calculado
    total_dias = len(dias)
    completos = sum(1 for d in dias if d["estatus"] == "COMPLETO")
    retardos_menores = sum(1 for d in dias if d["estatus"] == "RETARDO_MENOR")
    retardos_mayores = sum(1 for d in dias if d["estatus"] == "RETARDO_MAYOR")
    faltas = sum(1 for d in dias if d["estatus"] == "FALTA")
    omisiones_salida = sum(1 for d in dias if d["estatus"] == "OMISION_SALIDA")
    total_puntos = sum(d["puntos_generados"] or 0 for d in dias)
    total_minutos_retardo = sum(d["minutos_retardo"] or 0 for d in dias)
    total_minutos_ordinarios = sum(d["minutos_ordinarios"] or 0 for d in dias)
    total_minutos_extra = sum(d["minutos_extra"] or 0 for d in dias)

    resumen = {
        "dias_periodo": total_dias,
        "dias_completos": completos,
        "retardos_menores": retardos_menores,
        "retardos_mayores": retardos_mayores,
        "faltas": faltas,
        "omisiones_salida": omisiones_salida,
        "total_puntos": total_puntos,
        "total_minutos_retardo": total_minutos_retardo,
        "total_minutos_ordinarios": total_minutos_ordinarios,
        "total_minutos_extra": total_minutos_extra,
        "porcentaje_asistencia": (
            round((completos + retardos_menores + retardos_mayores) / total_dias * 100, 1)
            if total_dias > 0
            else 0
        ),
    }

    return {
        "empleado": empleado,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "resumen": resumen,
        "dias": dias,
    }


def obtener_reporte_departamental(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
    access_scope: AccessScope,
    unidad_organizacional_id: int | None = None,
) -> dict[str, Any]:
    """
    Genera datos para el reporte departamental/concentrado
    en un rango de fechas.

    Retorna resumen por unidad organizacional.
    """

    access_params = _get_access_params(access_scope)

    conditions = f"""
        ad.fecha BETWEEN :fecha_inicio AND :fecha_fin
        AND e.id IS NOT NULL
        AND {ACCESS_SCOPE_SQL}
    """

    params: dict[str, Any] = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        **access_params,
    }

    if unidad_organizacional_id is not None:
        conditions += " AND e.unidad_organizacional_id = :unidad_id"
        params["unidad_id"] = unidad_organizacional_id

    rows = db.execute(
        text(
            f"""
            SELECT
                uo.id AS unidad_id,
                uo.nombre AS unidad_nombre,
                COUNT(DISTINCT e.id) AS total_empleados,
                COUNT(ad.id) AS total_registros,
                COUNT(*) FILTER (WHERE ad.estatus = 'COMPLETO') AS dias_completos,
                COUNT(*) FILTER (WHERE ad.estatus = 'RETARDO_MENOR') AS retardos_menores,
                COUNT(*) FILTER (WHERE ad.estatus = 'RETARDO_MAYOR') AS retardos_mayores,
                COUNT(*) FILTER (WHERE ad.estatus = 'FALTA') AS faltas,
                COUNT(*) FILTER (WHERE ad.estatus = 'OMISION_SALIDA') AS omisiones_salida,
                COALESCE(SUM(ad.puntos_generados), 0) AS total_puntos,
                COALESCE(SUM(ad.minutos_retardo), 0) AS total_minutos_retardo,
                COALESCE(SUM(ad.minutos_ordinarios), 0) AS total_minutos_ordinarios,
                COALESCE(SUM(ad.minutos_extra), 0) AS total_minutos_extra
            FROM asistencia.asistencias_diarias ad
            INNER JOIN personal.empleados e ON e.id = ad.empleado_id
            LEFT JOIN organizacion.unidades_organizacionales uo
                ON uo.id = e.unidad_organizacional_id
            WHERE {conditions}
            GROUP BY uo.id, uo.nombre
            ORDER BY uo.nombre ASC NULLS LAST
            """
        ),
        params,
    ).mappings().all()

    departamentos = [dict(row) for row in rows]

    # Totales generales
    total_empleados = sum(d["total_empleados"] for d in departamentos)
    total_completos = sum(d["dias_completos"] for d in departamentos)
    total_faltas = sum(d["faltas"] for d in departamentos)
    total_retardos = sum(d["retardos_menores"] + d["retardos_mayores"] for d in departamentos)

    return {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "totales": {
            "departamentos": len(departamentos),
            "empleados": total_empleados,
            "dias_completos": total_completos,
            "faltas": total_faltas,
            "retardos": total_retardos,
        },
        "departamentos": departamentos,
    }
