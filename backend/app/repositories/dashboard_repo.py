from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.repositories.access_repo import (
    get_allowed_employee_ids,
)
from app.repositories.organizacion_repo import DEPARTAMENTO_RESUELTO_CTE


def _iso(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    return str(value)


def _construir_asistencia_hoy(row: dict[str, Any]) -> dict[str, Any]:
    """
    Arma el bloque asistencia_hoy con todos los estatus del contrato
    y un % de puntualidad calculado sobre días laborables (excluye
    DIA_NO_LABORAL del denominador: un feriado con cero registros de
    entrada no debe leerse como una caída de puntualidad).
    """
    total = row.get("total", 0) or 0
    completos = row.get("completos", 0) or 0
    tolerancias = row.get("tolerancias", 0) or 0
    retardos_menores = row.get("retardos_menores", 0) or 0
    retardos_mayores = row.get("retardos_mayores", 0) or 0
    dias_no_laborales = row.get("dias_no_laborales", 0) or 0

    dias_laborables = total - dias_no_laborales
    dias_asistidos = completos + tolerancias + retardos_menores + retardos_mayores

    return {
        "total": total,
        "completos": completos,
        "tolerancias": tolerancias,
        "retardos_menores": retardos_menores,
        "retardos_mayores": retardos_mayores,
        "faltas": row.get("faltas", 0) or 0,
        "omisiones_entrada": row.get("omisiones_entrada", 0) or 0,
        "omisiones_salida": row.get("omisiones_salida", 0) or 0,
        "dias_no_laborales": dias_no_laborales,
        "requieren_revision": row.get("requieren_revision", 0) or 0,
        "puntos_generados": row.get("puntos_generados", 0) or 0,
        "pct_puntualidad": (
            round(completos / dias_laborables * 100, 1)
            if dias_laborables > 0
            else 0
        ),
        "pct_asistencia": (
            round(dias_asistidos / dias_laborables * 100, 1)
            if dias_laborables > 0
            else 0
        ),
    }


def obtener_dashboard_resumen(
    *,
    db: Session,
    access_scope: AccessScope,
) -> dict[str, Any]:
    allowed_employee_ids = get_allowed_employee_ids(
        db=db,
        access_scope=access_scope,
    )

    params = {
        "allowed_employee_ids": list(
            allowed_employee_ids
        ),
        "include_unlinked": (
            access_scope.has_complete_access
        ),
    }

    employee_filter = """
        e.id = ANY(
            CAST(:allowed_employee_ids AS BIGINT[])
        )
    """

    attendance_filter = """
        ad.empleado_id = ANY(
            CAST(:allowed_employee_ids AS BIGINT[])
        )
    """

    mark_filter = """
        (
            mc.empleado_id = ANY(
                CAST(:allowed_employee_ids AS BIGINT[])
            )
            OR (
                :include_unlinked = TRUE
                AND mc.empleado_id IS NULL
            )
        )
    """

    empleados_query = text(
        f"""
        SELECT
            COUNT(*) AS total,

            COUNT(*) FILTER (
                WHERE UPPER(
                    COALESCE(e.estatus, '')
                ) = 'ACTIVO'
            ) AS activos,

            COUNT(*) FILTER (
                WHERE UPPER(
                    COALESCE(e.estatus, '')
                ) <> 'ACTIVO'
            ) AS inactivos,

            COUNT(*) FILTER (
                WHERE NULLIF(
                    BTRIM(
                        COALESCE(e.zk_user_id, '')
                    ),
                    ''
                ) IS NOT NULL
            ) AS con_zk,

            COUNT(*) FILTER (
                WHERE NULLIF(
                    BTRIM(
                        COALESCE(e.zk_user_id, '')
                    ),
                    ''
                ) IS NULL
            ) AS sin_zk

        FROM personal.empleados e
        WHERE {employee_filter}
        """
    )

    marcaciones_query = text(
        f"""
        SELECT
            COUNT(*) AS total,

            COUNT(*) FILTER (
                WHERE mc.fecha = CURRENT_DATE
            ) AS hoy,

            MAX(mc.fecha_hora) AS ultima_fecha_hora

        FROM asistencia.marcaciones_crudas mc
        WHERE {mark_filter}
        """
    )

    dispositivos_query = text(
        """
        SELECT
            COUNT(*) AS total,

            COUNT(*) FILTER (
                WHERE activo = TRUE
            ) AS activos,

            COUNT(*) FILTER (
                WHERE activo = FALSE
            ) AS inactivos

        FROM dispositivos.dispositivos
        """
    )

    asistencia_hoy_query = text(
        f"""
        SELECT
            COUNT(*) AS total,

            COUNT(*) FILTER (
                WHERE ad.estatus = 'COMPLETO'
            ) AS completos,

            COUNT(*) FILTER (
                WHERE ad.estatus = 'TOLERANCIA'
            ) AS tolerancias,

            COUNT(*) FILTER (
                WHERE ad.estatus = 'RETARDO_MENOR'
            ) AS retardos_menores,

            COUNT(*) FILTER (
                WHERE ad.estatus = 'RETARDO_MAYOR'
            ) AS retardos_mayores,

            COUNT(*) FILTER (
                WHERE ad.estatus = 'FALTA'
            ) AS faltas,

            COUNT(*) FILTER (
                WHERE ad.estatus = 'OMISION_ENTRADA'
            ) AS omisiones_entrada,

            COUNT(*) FILTER (
                WHERE ad.estatus = 'OMISION_SALIDA'
            ) AS omisiones_salida,

            COUNT(*) FILTER (
                WHERE ad.estatus = 'DIA_NO_LABORAL'
            ) AS dias_no_laborales,

            COUNT(*) FILTER (
                WHERE ad.requiere_revision = TRUE
            ) AS requieren_revision,

            COALESCE(
                SUM(ad.puntos_generados),
                0
            ) AS puntos_generados

        FROM asistencia.asistencias_diarias ad
        WHERE ad.fecha = CURRENT_DATE
          AND {attendance_filter}
        """
    )

    ultimas_marcaciones_query = text(
        f"""
        SELECT
            mc.id,
            mc.zk_user_id,
            mc.codigo_empleado,

            COALESCE(
                e.nombre_completo,
                'Sin empleado vinculado'
            ) AS empleado_nombre,

            mc.fecha_hora,
            mc.fecha,
            mc.hora,
            mc.punch,
            mc.punch_label,
            mc.status,
            mc.status_label,
            mc.dispositivo_origen,
            mc.dispositivo_ip

        FROM asistencia.marcaciones_crudas mc

        LEFT JOIN personal.empleados e
            ON e.id = mc.empleado_id

        WHERE {mark_filter}

        ORDER BY
            mc.fecha_hora DESC,
            mc.id DESC

        LIMIT 10
        """
    )

    alertas_query = text(
        f"""
        SELECT
            (
                SELECT COUNT(*)
                FROM personal.empleados e
                WHERE UPPER(
                    COALESCE(e.estatus, '')
                ) = 'ACTIVO'
                  AND NULLIF(
                        BTRIM(
                            COALESCE(e.zk_user_id, '')
                        ),
                        ''
                      ) IS NULL
                  AND {employee_filter}
            ) AS empleados_sin_zk,

            (
                SELECT COUNT(*)
                FROM personal.empleados e
                WHERE UPPER(
                    COALESCE(e.estatus, '')
                ) = 'ACTIVO'
                  AND {employee_filter}
                  AND NOT EXISTS (
                      SELECT 1
                      FROM asistencia.asignaciones_horario ah
                      WHERE ah.empleado_id = e.id
                        AND ah.estatus = 'ACTIVA'
                        AND ah.fecha_inicio <= CURRENT_DATE
                        AND (
                            ah.fecha_fin IS NULL
                            OR ah.fecha_fin >= CURRENT_DATE
                        )
                  )
            ) AS empleados_sin_horario,

            (
                SELECT COUNT(*)
                FROM asistencia.marcaciones_crudas mc
                WHERE mc.fecha = CURRENT_DATE
                  AND mc.empleado_id IS NULL
                  AND :include_unlinked = TRUE
            ) AS marcaciones_sin_empleado_hoy,

            (
                SELECT COUNT(*)
                FROM asistencia.asistencias_diarias ad
                WHERE ad.fecha = CURRENT_DATE
                  AND ad.requiere_revision = TRUE
                  AND {attendance_filter}
            ) AS asistencias_revision_hoy,

            (
                SELECT COUNT(*)
                FROM asistencia.asistencias_diarias ad
                WHERE ad.fecha = CURRENT_DATE
                  AND ad.estatus = 'FALTA'
                  AND {attendance_filter}
            ) AS faltas_hoy,

            (
                SELECT COUNT(*)
                FROM asistencia.asistencias_diarias ad
                WHERE ad.fecha = CURRENT_DATE
                  AND ad.estatus = 'RETARDO_MAYOR'
                  AND {attendance_filter}
            ) AS retardos_mayores_hoy
        """
    )

    asistencia_ultimos_dias_query = text(
        """
        WITH fechas AS (
            SELECT generate_series(
                CURRENT_DATE - INTERVAL '6 days',
                CURRENT_DATE,
                INTERVAL '1 day'
            )::date AS fecha
        ),

        asistencias_permitidas AS (
            SELECT ad.*
            FROM asistencia.asistencias_diarias ad
            WHERE ad.empleado_id = ANY(
                CAST(:allowed_employee_ids AS BIGINT[])
            )
        )

        SELECT
            f.fecha::text AS fecha,

            COUNT(ad.id) AS total,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'COMPLETO'
            ) AS completos,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'TOLERANCIA'
            ) AS tolerancias,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN (
                    'RETARDO_MENOR',
                    'RETARDO_MAYOR'
                )
            ) AS retardos,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'FALTA'
            ) AS faltas,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN (
                    'OMISION_ENTRADA',
                    'OMISION_SALIDA'
                )
            ) AS omisiones,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'DIA_NO_LABORAL'
            ) AS dias_no_laborales,

            COUNT(ad.id) FILTER (
                WHERE ad.requiere_revision = TRUE
            ) AS requieren_revision

        FROM fechas f

        LEFT JOIN asistencias_permitidas ad
            ON ad.fecha = f.fecha

        GROUP BY f.fecha
        ORDER BY f.fecha
        """
    )

    top_empleados_faltas_query = text(
        f"""
        SELECT
            e.id AS empleado_id,
            e.codigo_empleado,
            e.nombre_completo AS empleado_nombre,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'FALTA'
            ) AS faltas,

            COUNT(ad.id) FILTER (
                WHERE ad.requiere_revision = TRUE
            ) AS requieren_revision,

            COUNT(ad.id) AS dias_procesados

        FROM asistencia.asistencias_diarias ad

        INNER JOIN personal.empleados e
            ON e.id = ad.empleado_id

        WHERE ad.fecha >= (
            CURRENT_DATE - INTERVAL '29 days'
        )
          AND {employee_filter}

        GROUP BY
            e.id,
            e.codigo_empleado,
            e.nombre_completo

        HAVING COUNT(ad.id) FILTER (
            WHERE ad.estatus = 'FALTA'
        ) > 0

        ORDER BY
            faltas DESC,
            requieren_revision DESC,
            e.nombre_completo ASC

        LIMIT 10
        """
    )

    top_empleados_retardos_query = text(
        f"""
        SELECT
            e.id AS empleado_id,
            e.codigo_empleado,
            e.nombre_completo AS empleado_nombre,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'RETARDO_MENOR'
            ) AS retardos_menores,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'RETARDO_MAYOR'
            ) AS retardos_mayores,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN (
                    'RETARDO_MENOR',
                    'RETARDO_MAYOR'
                )
            ) AS total_retardos,

            COALESCE(
                SUM(ad.puntos_generados),
                0
            ) AS puntos_generados,

            COUNT(ad.id) AS dias_procesados

        FROM asistencia.asistencias_diarias ad

        INNER JOIN personal.empleados e
            ON e.id = ad.empleado_id

        WHERE ad.fecha >= (
            CURRENT_DATE - INTERVAL '29 days'
        )
          AND {employee_filter}

        GROUP BY
            e.id,
            e.codigo_empleado,
            e.nombre_completo

        HAVING COUNT(ad.id) FILTER (
            WHERE ad.estatus IN (
                'RETARDO_MENOR',
                'RETARDO_MAYOR'
            )
        ) > 0

        ORDER BY
            total_retardos DESC,
            retardos_mayores DESC,
            puntos_generados DESC,
            e.nombre_completo ASC

        LIMIT 10
        """
    )

    # "Departamentos con más incidencias" solo debe listar unidades de
    # tipo DEPARTAMENTO (Contrato de jerarquía organizacional): un
    # empleado asignado directamente a una Dirección/División/Comité
    # se agrupa aparte (unidad_organizacional_id NULL), nunca bajo el
    # nombre de esa unidad superior como si fuera un departamento.
    departamentos_incidencias_query = text(
        f"""
        {DEPARTAMENTO_RESUELTO_CTE}
        SELECT
            dr.departamento_id AS unidad_organizacional_id,

            COALESCE(
                dr.departamento_nombre,
                'Sin departamento (unidad de nivel superior)'
            ) AS departamento_nombre,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'FALTA'
            ) AS faltas,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN (
                    'RETARDO_MENOR',
                    'RETARDO_MAYOR'
                )
            ) AS retardos,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'RETARDO_MENOR'
            ) AS retardos_menores,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'RETARDO_MAYOR'
            ) AS retardos_mayores,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN (
                    'OMISION_ENTRADA',
                    'OMISION_SALIDA'
                )
            ) AS omisiones,

            COUNT(ad.id) FILTER (
                WHERE ad.requiere_revision = TRUE
            ) AS requieren_revision,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN (
                    'FALTA',
                    'RETARDO_MENOR',
                    'RETARDO_MAYOR',
                    'OMISION_ENTRADA',
                    'OMISION_SALIDA'
                )
                OR ad.requiere_revision = TRUE
            ) AS total_incidencias,

            COUNT(DISTINCT e.id)
                AS empleados_involucrados

        FROM asistencia.asistencias_diarias ad

        INNER JOIN personal.empleados e
            ON e.id = ad.empleado_id

        LEFT JOIN departamento_resuelto dr
            ON dr.unidad_origen_id = e.unidad_organizacional_id

        WHERE ad.fecha >= (
            CURRENT_DATE - INTERVAL '29 days'
        )
          AND {employee_filter}

        GROUP BY
            dr.departamento_id,
            dr.departamento_nombre

        HAVING COUNT(ad.id) FILTER (
            WHERE ad.estatus IN (
                'FALTA',
                'RETARDO_MENOR',
                'RETARDO_MAYOR',
                'OMISION_ENTRADA',
                'OMISION_SALIDA'
            )
            OR ad.requiere_revision = TRUE
        ) > 0

        ORDER BY
            total_incidencias DESC,
            faltas DESC,
            retardos_mayores DESC,
            retardos_menores DESC,
            departamento_nombre ASC

        LIMIT 10
        """
    )

    empleados = (
        db.execute(
            empleados_query,
            params,
        ).mappings().first()
        or {}
    )

    marcaciones = (
        db.execute(
            marcaciones_query,
            params,
        ).mappings().first()
        or {}
    )

    if access_scope.has_complete_access:
        dispositivos = (
            db.execute(
                dispositivos_query
            ).mappings().first()
            or {}
        )
    else:
        dispositivos = {
            "total": 0,
            "activos": 0,
            "inactivos": 0,
        }

    asistencia_hoy = (
        db.execute(
            asistencia_hoy_query,
            params,
        ).mappings().first()
        or {}
    )

    ultimas_marcaciones_rows = (
        db.execute(
            ultimas_marcaciones_query,
            params,
        ).mappings().all()
    )

    alertas = (
        db.execute(
            alertas_query,
            params,
        ).mappings().first()
        or {}
    )

    asistencia_ultimos_dias = (
        db.execute(
            asistencia_ultimos_dias_query,
            params,
        ).mappings().all()
    )

    top_empleados_faltas = (
        db.execute(
            top_empleados_faltas_query,
            params,
        ).mappings().all()
    )

    top_empleados_retardos = (
        db.execute(
            top_empleados_retardos_query,
            params,
        ).mappings().all()
    )

    departamentos_incidencias = (
        db.execute(
            departamentos_incidencias_query,
            params,
        ).mappings().all()
    )

    # ============================================================
    # Tendencia de puntualidad últimos 30 días (para AreaChart)
    # ============================================================
    tendencia_puntualidad_query = text(
        """
        WITH fechas AS (
            SELECT generate_series(
                CURRENT_DATE - INTERVAL '29 days',
                CURRENT_DATE,
                INTERVAL '1 day'
            )::date AS fecha
        ),

        asistencias_permitidas AS (
            SELECT ad.*
            FROM asistencia.asistencias_diarias ad
            WHERE ad.empleado_id = ANY(
                CAST(:allowed_employee_ids AS BIGINT[])
            )
        )

        SELECT
            f.fecha::text AS fecha,
            COUNT(ad.id) AS total,
            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'COMPLETO'
            ) AS completos,
            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN ('RETARDO_MENOR', 'RETARDO_MAYOR')
            ) AS retardos,
            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'FALTA'
            ) AS faltas,
            -- Denominador = días laborables (excluye DIA_NO_LABORAL):
            -- un feriado con cero puntuales no debe leerse como una
            -- caída de puntualidad.
            CASE
                WHEN COUNT(ad.id) FILTER (WHERE ad.estatus <> 'DIA_NO_LABORAL') > 0
                THEN ROUND(
                    COUNT(ad.id) FILTER (WHERE ad.estatus = 'COMPLETO')::numeric
                    / COUNT(ad.id) FILTER (WHERE ad.estatus <> 'DIA_NO_LABORAL') * 100,
                    1
                )
                ELSE 0
            END AS pct_puntualidad,
            CASE
                WHEN COUNT(ad.id) FILTER (WHERE ad.estatus <> 'DIA_NO_LABORAL') > 0
                THEN ROUND(
                    (COUNT(ad.id) FILTER (WHERE ad.estatus IN ('COMPLETO', 'TOLERANCIA'))
                     + COUNT(ad.id) FILTER (WHERE ad.estatus IN ('RETARDO_MENOR', 'RETARDO_MAYOR'))
                    )::numeric
                    / COUNT(ad.id) FILTER (WHERE ad.estatus <> 'DIA_NO_LABORAL') * 100,
                    1
                )
                ELSE 0
            END AS pct_asistencia
        FROM fechas f
        LEFT JOIN asistencias_permitidas ad ON ad.fecha = f.fecha
        GROUP BY f.fecha
        ORDER BY f.fecha
        """
    )

    tendencia_puntualidad = (
        db.execute(
            tendencia_puntualidad_query,
            params,
        ).mappings().all()
    )

    # ============================================================
    # Distribución de incidencias por categoría (para PieChart)
    # ============================================================
    incidencias_por_categoria_query = text(
        f"""
        SELECT
            ti.categoria,
            ti.nombre AS tipo_nombre,
            COUNT(i.id) AS cantidad
        FROM asistencia.incidencias i
        INNER JOIN asistencia.tipos_incidencia ti ON ti.id = i.tipo_incidencia_id
        INNER JOIN personal.empleados e ON e.id = i.empleado_id
        WHERE i.fecha >= (CURRENT_DATE - INTERVAL '29 days')
          AND {employee_filter}
        GROUP BY ti.categoria, ti.nombre
        ORDER BY cantidad DESC
        """
    )

    incidencias_por_categoria = (
        db.execute(
            incidencias_por_categoria_query,
            params,
        ).mappings().all()
    )

    return {
        "empleados": {
            "total": empleados.get("total", 0),
            "activos": empleados.get("activos", 0),
            "inactivos": empleados.get("inactivos", 0),
            "con_zk": empleados.get("con_zk", 0),
            "sin_zk": empleados.get("sin_zk", 0),
        },
        "marcaciones": {
            "total": marcaciones.get("total", 0),
            "hoy": marcaciones.get("hoy", 0),
            "ultima_fecha_hora": _iso(
                marcaciones.get("ultima_fecha_hora")
            ),
        },
        "dispositivos": {
            "total": dispositivos.get("total", 0),
            "activos": dispositivos.get("activos", 0),
            "inactivos": dispositivos.get("inactivos", 0),
        },
        "asistencia_hoy": _construir_asistencia_hoy(asistencia_hoy),
        "ultimas_marcaciones": [
            {
                "id": row["id"],
                "zk_user_id": row["zk_user_id"],
                "codigo_empleado": row["codigo_empleado"],
                "empleado_nombre": row["empleado_nombre"],
                "fecha_hora": _iso(row["fecha_hora"]),
                "fecha": _iso(row["fecha"]),
                "hora": _iso(row["hora"]),
                "punch": row["punch"],
                "punch_label": row["punch_label"],
                "status": row["status"],
                "status_label": row["status_label"],
                "dispositivo_origen": (
                    row["dispositivo_origen"]
                ),
                "dispositivo_ip": row["dispositivo_ip"],
            }
            for row in ultimas_marcaciones_rows
        ],
        "alertas": {
            "empleados_sin_zk": alertas.get(
                "empleados_sin_zk",
                0,
            ),
            "empleados_sin_horario": alertas.get(
                "empleados_sin_horario",
                0,
            ),
            "marcaciones_sin_empleado_hoy": alertas.get(
                "marcaciones_sin_empleado_hoy",
                0,
            ),
            "asistencias_revision_hoy": alertas.get(
                "asistencias_revision_hoy",
                0,
            ),
            "faltas_hoy": alertas.get("faltas_hoy", 0),
            "retardos_mayores_hoy": alertas.get(
                "retardos_mayores_hoy",
                0,
            ),
        },
        "asistencia_ultimos_dias": [
            {
                "fecha": row["fecha"],
                "total": row["total"],
                "completos": row["completos"],
                "tolerancias": row["tolerancias"],
                "retardos": row["retardos"],
                "faltas": row["faltas"],
                "omisiones": row["omisiones"],
                "dias_no_laborales": row["dias_no_laborales"],
                "requieren_revision": (
                    row["requieren_revision"]
                ),
            }
            for row in asistencia_ultimos_dias
        ],
        "top_empleados_faltas": [
            {
                "empleado_id": row["empleado_id"],
                "codigo_empleado": row["codigo_empleado"],
                "empleado_nombre": row["empleado_nombre"],
                "faltas": row["faltas"],
                "requieren_revision": (
                    row["requieren_revision"]
                ),
                "dias_procesados": row["dias_procesados"],
            }
            for row in top_empleados_faltas
        ],
        "top_empleados_retardos": [
            {
                "empleado_id": row["empleado_id"],
                "codigo_empleado": row["codigo_empleado"],
                "empleado_nombre": row["empleado_nombre"],
                "retardos_menores": row["retardos_menores"],
                "retardos_mayores": row["retardos_mayores"],
                "total_retardos": row["total_retardos"],
                "puntos_generados": row["puntos_generados"],
                "dias_procesados": row["dias_procesados"],
            }
            for row in top_empleados_retardos
        ],
        "departamentos_incidencias": [
            {
                "unidad_organizacional_id": (
                    row["unidad_organizacional_id"]
                ),
                "departamento_nombre": (
                    row["departamento_nombre"]
                ),
                "faltas": row["faltas"],
                "retardos": row["retardos"],
                "retardos_menores": (
                    row["retardos_menores"]
                ),
                "retardos_mayores": (
                    row["retardos_mayores"]
                ),
                "omisiones": row["omisiones"],
                "requieren_revision": (
                    row["requieren_revision"]
                ),
                "total_incidencias": (
                    row["total_incidencias"]
                ),
                "empleados_involucrados": (
                    row["empleados_involucrados"]
                ),
            }
            for row in departamentos_incidencias
        ],
        "tendencia_puntualidad": [
            {
                "fecha": row["fecha"],
                "total": row["total"],
                "completos": row["completos"],
                "retardos": row["retardos"],
                "faltas": row["faltas"],
                "pct_puntualidad": float(
                    row["pct_puntualidad"]
                ),
                "pct_asistencia": float(
                    row["pct_asistencia"]
                ),
            }
            for row in tendencia_puntualidad
        ],
        "incidencias_por_categoria": [
            {
                "categoria": row["categoria"],
                "tipo_nombre": row["tipo_nombre"],
                "cantidad": row["cantidad"],
            }
            for row in incidencias_por_categoria
        ],
    }