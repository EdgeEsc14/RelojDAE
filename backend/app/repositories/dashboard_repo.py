from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _iso(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    return str(value)


def obtener_dashboard_resumen(db: Session) -> dict[str, Any]:
    empleados_query = text(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (
                WHERE UPPER(COALESCE(e.estatus, '')) = 'ACTIVO'
            ) AS activos,
            COUNT(*) FILTER (
                WHERE UPPER(COALESCE(e.estatus, '')) <> 'ACTIVO'
            ) AS inactivos,
            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(COALESCE(e.zk_user_id, '')), '') IS NOT NULL
            ) AS con_zk,
            COUNT(*) FILTER (
                WHERE NULLIF(BTRIM(COALESCE(e.zk_user_id, '')), '') IS NULL
            ) AS sin_zk
        FROM personal.empleados e
        """
    )

    marcaciones_query = text(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (
                WHERE mc.fecha = CURRENT_DATE
            ) AS hoy,
            MAX(mc.fecha_hora) AS ultima_fecha_hora
        FROM asistencia.marcaciones_crudas mc
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
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (
                WHERE estatus = 'COMPLETO'
            ) AS completos,
            COUNT(*) FILTER (
                WHERE estatus = 'RETARDO_MENOR'
            ) AS retardos_menores,
            COUNT(*) FILTER (
                WHERE estatus = 'RETARDO_MAYOR'
            ) AS retardos_mayores,
            COUNT(*) FILTER (
                WHERE estatus = 'FALTA'
            ) AS faltas,
            COUNT(*) FILTER (
                WHERE requiere_revision = TRUE
            ) AS requieren_revision,
            COALESCE(SUM(puntos_generados), 0) AS puntos_generados
        FROM asistencia.asistencias_diarias
        WHERE fecha = CURRENT_DATE
        """
    )
    ultimas_marcaciones_query = text(
        """
        SELECT
            mc.id,
            mc.zk_user_id,
            mc.codigo_empleado,
            COALESCE(e.nombre_completo, 'Sin empleado vinculado') AS empleado_nombre,
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
        ORDER BY mc.fecha_hora DESC, mc.id DESC
        LIMIT 10
        """
    )


    alertas_query = text(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM personal.empleados e
                WHERE UPPER(COALESCE(e.estatus, '')) = 'ACTIVO'
                AND NULLIF(BTRIM(COALESCE(e.zk_user_id, '')), '') IS NULL
            ) AS empleados_sin_zk,

            (
                SELECT COUNT(*)
                FROM personal.empleados e
                WHERE UPPER(COALESCE(e.estatus, '')) = 'ACTIVO'
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
            ) AS marcaciones_sin_empleado_hoy,

            (
                SELECT COUNT(*)
                FROM asistencia.asistencias_diarias ad
                WHERE ad.fecha = CURRENT_DATE
                AND ad.requiere_revision = TRUE
            ) AS asistencias_revision_hoy,

            (
                SELECT COUNT(*)
                FROM asistencia.asistencias_diarias ad
                WHERE ad.fecha = CURRENT_DATE
                AND ad.estatus = 'FALTA'
            ) AS faltas_hoy,

            (
                SELECT COUNT(*)
                FROM asistencia.asistencias_diarias ad
                WHERE ad.fecha = CURRENT_DATE
                AND ad.estatus = 'RETARDO_MAYOR'
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

            COUNT(ad.id) FILTER (
                WHERE ad.requiere_revision = TRUE
            ) AS requieren_revision

        FROM fechas f
        LEFT JOIN asistencia.asistencias_diarias ad
            ON ad.fecha = f.fecha

        GROUP BY f.fecha
        ORDER BY f.fecha
        """
    )



    top_empleados_faltas_query = text(
        """
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

        WHERE ad.fecha >= CURRENT_DATE - INTERVAL '29 days'

        GROUP BY
            e.id,
            e.codigo_empleado,
            e.nombre_completo

        HAVING
            COUNT(ad.id) FILTER (
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
        """
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
                WHERE ad.estatus IN ('RETARDO_MENOR', 'RETARDO_MAYOR')
            ) AS total_retardos,

            COALESCE(SUM(ad.puntos_generados), 0) AS puntos_generados,

            COUNT(ad.id) AS dias_procesados

        FROM asistencia.asistencias_diarias ad
        INNER JOIN personal.empleados e
            ON e.id = ad.empleado_id

        WHERE ad.fecha >= CURRENT_DATE - INTERVAL '29 days'

        GROUP BY
            e.id,
            e.codigo_empleado,
            e.nombre_completo

        HAVING
            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN ('RETARDO_MENOR', 'RETARDO_MAYOR')
            ) > 0

        ORDER BY
            total_retardos DESC,
            retardos_mayores DESC,
            puntos_generados DESC,
            e.nombre_completo ASC

        LIMIT 10
        """
    )


    departamentos_incidencias_query = text(
        """
        SELECT
            uo.id AS unidad_organizacional_id,
            COALESCE(uo.nombre, 'Sin departamento') AS departamento_nombre,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'FALTA'
            ) AS faltas,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN ('RETARDO_MENOR', 'RETARDO_MAYOR')
            ) AS retardos,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'RETARDO_MENOR'
            ) AS retardos_menores,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus = 'RETARDO_MAYOR'
            ) AS retardos_mayores,

            COUNT(ad.id) FILTER (
                WHERE ad.estatus IN ('OMISION_ENTRADA', 'OMISION_SALIDA')
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

            COUNT(DISTINCT e.id) AS empleados_involucrados

        FROM asistencia.asistencias_diarias ad
        INNER JOIN personal.empleados e
            ON e.id = ad.empleado_id

        LEFT JOIN organizacion.unidades_organizacionales uo
            ON uo.id = e.unidad_organizacional_id

        WHERE ad.fecha >= CURRENT_DATE - INTERVAL '29 days'

        GROUP BY
            uo.id,
            uo.nombre

        HAVING
            COUNT(ad.id) FILTER (
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

    empleados = db.execute(empleados_query).mappings().first() or {}
    marcaciones = db.execute(marcaciones_query).mappings().first() or {}
    dispositivos = db.execute(dispositivos_query).mappings().first() or {}
    asistencia_hoy = db.execute(
        asistencia_hoy_query
    ).mappings().first() or {}
    ultimas_marcaciones_rows = db.execute(
        ultimas_marcaciones_query
    ).mappings().all()
    alertas = db.execute(
        alertas_query
    ).mappings().first() or {}
    asistencia_ultimos_dias = db.execute(
        asistencia_ultimos_dias_query
    ).mappings().all()
    top_empleados_faltas = db.execute(
        top_empleados_faltas_query
    ).mappings().all()

    top_empleados_retardos = db.execute(
        top_empleados_retardos_query
    ).mappings().all()

    departamentos_incidencias = db.execute(
        departamentos_incidencias_query
    ).mappings().all()

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
        "asistencia_hoy": {
            "total": asistencia_hoy.get("total", 0),
            "completos": asistencia_hoy.get("completos", 0),
            "retardos_menores": asistencia_hoy.get("retardos_menores", 0),
            "retardos_mayores": asistencia_hoy.get("retardos_mayores", 0),
            "faltas": asistencia_hoy.get("faltas", 0),
            "requieren_revision": asistencia_hoy.get("requieren_revision", 0),
            "puntos_generados": asistencia_hoy.get("puntos_generados", 0),
        },
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
                "dispositivo_origen": row["dispositivo_origen"],
                "dispositivo_ip": row["dispositivo_ip"],
            }
            for row in ultimas_marcaciones_rows
        ],

        "alertas": {
        "empleados_sin_zk": alertas.get("empleados_sin_zk", 0),
        "empleados_sin_horario": alertas.get("empleados_sin_horario", 0),
        "marcaciones_sin_empleado_hoy": alertas.get(
            "marcaciones_sin_empleado_hoy",
            0,
        ),
        "asistencias_revision_hoy": alertas.get(
            "asistencias_revision_hoy",
            0,
        ),
        "faltas_hoy": alertas.get("faltas_hoy", 0),
        "retardos_mayores_hoy": alertas.get("retardos_mayores_hoy", 0),
    },
    "asistencia_ultimos_dias": [
        {
            "fecha": row["fecha"],
            "total": row["total"],
            "completos": row["completos"],
            "retardos": row["retardos"],
            "faltas": row["faltas"],
            "requieren_revision": row["requieren_revision"],
        }
        for row in asistencia_ultimos_dias
    ],
    "top_empleados_faltas": [
        {
            "empleado_id": row["empleado_id"],
            "codigo_empleado": row["codigo_empleado"],
            "empleado_nombre": row["empleado_nombre"],
            "faltas": row["faltas"],
            "requieren_revision": row["requieren_revision"],
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
            "unidad_organizacional_id": row["unidad_organizacional_id"],
            "departamento_nombre": row["departamento_nombre"],
            "faltas": row["faltas"],
            "retardos": row["retardos"],
            "retardos_menores": row["retardos_menores"],
            "retardos_mayores": row["retardos_mayores"],
            "omisiones": row["omisiones"],
            "requieren_revision": row["requieren_revision"],
            "total_incidencias": row["total_incidencias"],
            "empleados_involucrados": row["empleados_involucrados"],
        }
        for row in departamentos_incidencias
    ],
}