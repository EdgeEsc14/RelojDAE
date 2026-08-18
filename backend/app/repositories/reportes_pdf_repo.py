"""
Repositorio para obtener datos completos de un empleado
necesarios para generar el reporte PDF de incidencias/asistencia.

Consulta:
- Datos del empleado (personal.empleados)
- Horario asignado (asistencia.asignaciones_horario + asistencia.horarios)
- Tipo de turno (asistencia.tipos_turno)
- Asistencia diaria procesada (asistencia.asistencias_diarias)
- Incidencias del periodo (asistencia.incidencias)
- Unidad organizacional y puesto
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def obtener_datos_reporte_empleado(
    db: Session,
    *,
    codigo_empleado: str,
    fecha_inicio: date,
    fecha_fin: date,
) -> dict[str, Any] | None:
    """
    Obtiene todos los datos necesarios para generar el reporte PDF
    de un empleado en un rango de fechas.

    Retorna None si el empleado no existe.
    """

    # 1. Datos del empleado
    empleado = _obtener_empleado(db, codigo_empleado)
    if empleado is None:
        return None

    empleado_id = empleado["id"]

    # 2. Horario asignado vigente
    horario = _obtener_horario_vigente(db, empleado_id, fecha_inicio)

    # 3. Asistencia diaria del periodo
    asistencias = _obtener_asistencias_periodo(
        db, empleado_id, fecha_inicio, fecha_fin
    )

    # 4. Incidencias del periodo
    incidencias = _obtener_incidencias_periodo(
        db, empleado_id, fecha_inicio, fecha_fin
    )

    # 5. Resumen calculado
    resumen = _calcular_resumen(asistencias, incidencias)

    return {
        "empleado": empleado,
        "horario": horario,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "asistencias": asistencias,
        "incidencias": incidencias,
        "resumen": resumen,
    }


def _obtener_empleado(
    db: Session,
    codigo_empleado: str,
) -> dict[str, Any] | None:
    """Obtiene datos completos del empleado para el encabezado del reporte."""

    query = text(
        """
        SELECT
            e.id,
            e.codigo_empleado,
            e.nombres,
            e.apellido_paterno,
            e.apellido_materno,
            e.nombre_completo,
            e.rfc,
            e.correo,
            e.estatus,
            e.fecha_ingreso,
            e.zk_user_id,

            uo.id AS unidad_organizacional_id,
            uo.nombre AS unidad_organizacional,

            p.id AS puesto_id,
            p.nombre AS puesto

        FROM personal.empleados e

        LEFT JOIN organizacion.unidades_organizacionales uo
            ON uo.id = e.unidad_organizacional_id

        LEFT JOIN organizacion.puestos p
            ON p.id = e.puesto_id

        WHERE e.codigo_empleado = :codigo_empleado
        LIMIT 1
        """
    )

    row = db.execute(query, {"codigo_empleado": codigo_empleado}).mappings().first()

    if row is None:
        return None

    return dict(row)


def _obtener_horario_vigente(
    db: Session,
    empleado_id: int,
    fecha_referencia: date,
) -> dict[str, Any] | None:
    """Obtiene el horario asignado vigente para el empleado en la fecha dada."""

    query = text(
        """
        SELECT
            h.id AS horario_id,
            h.codigo AS horario_codigo,
            h.nombre AS horario_nombre,
            h.hora_entrada,
            h.hora_salida,
            h.tolerancia_entrada_minutos,
            h.descanso_minutos,

            tt.id AS tipo_turno_id,
            tt.codigo AS tipo_turno_codigo,
            tt.nombre AS tipo_turno_nombre,
            tt.duracion_jornada_minutos

        FROM asistencia.asignaciones_horario ah

        INNER JOIN asistencia.horarios h
            ON h.id = ah.horario_id

        LEFT JOIN asistencia.tipos_turno tt
            ON tt.id = h.tipo_turno_id

        WHERE ah.empleado_id = :empleado_id
          AND ah.estatus = 'ACTIVA'
          AND ah.fecha_inicio <= :fecha_referencia
          AND (ah.fecha_fin IS NULL OR ah.fecha_fin >= :fecha_referencia)

        ORDER BY ah.fecha_inicio DESC
        LIMIT 1
        """
    )

    row = db.execute(
        query,
        {
            "empleado_id": empleado_id,
            "fecha_referencia": fecha_referencia,
        },
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def _obtener_asistencias_periodo(
    db: Session,
    empleado_id: int,
    fecha_inicio: date,
    fecha_fin: date,
) -> list[dict[str, Any]]:
    """Obtiene registros de asistencia diaria procesada en el rango."""

    query = text(
        """
        SELECT
            ad.id,
            ad.fecha,
            ad.estatus,
            ad.entrada_programada,
            ad.salida_programada,
            ad.primera_entrada,
            ad.ultima_salida,
            ad.minutos_retardo,
            ad.minutos_ordinarios,
            ad.minutos_extra,
            ad.puntos_generados,
            ad.procesada,
            ad.requiere_revision,
            ad.observaciones

        FROM asistencia.asistencias_diarias ad

        WHERE ad.empleado_id = :empleado_id
          AND ad.fecha BETWEEN :fecha_inicio AND :fecha_fin

        ORDER BY ad.fecha ASC
        """
    )

    rows = db.execute(
        query,
        {
            "empleado_id": empleado_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        },
    ).mappings().all()

    return [dict(row) for row in rows]


def _obtener_incidencias_periodo(
    db: Session,
    empleado_id: int,
    fecha_inicio: date,
    fecha_fin: date,
) -> list[dict[str, Any]]:
    """Obtiene incidencias del empleado en el rango de fechas."""

    query = text(
        """
        SELECT
            i.id,
            i.fecha,
            i.descripcion,
            i.puntos_originales,
            i.puntos_justificados,
            i.puntos_efectivos,
            i.estatus,
            i.origen,
            i.comentario_revision,

            ti.codigo AS tipo_codigo,
            ti.nombre AS tipo_nombre,
            ti.categoria AS tipo_categoria

        FROM asistencia.incidencias i

        INNER JOIN asistencia.tipos_incidencia ti
            ON ti.id = i.tipo_incidencia_id

        WHERE i.empleado_id = :empleado_id
          AND i.fecha BETWEEN :fecha_inicio AND :fecha_fin

        ORDER BY i.fecha ASC, i.id ASC
        """
    )

    rows = db.execute(
        query,
        {
            "empleado_id": empleado_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        },
    ).mappings().all()

    return [dict(row) for row in rows]


def _calcular_resumen(
    asistencias: list[dict[str, Any]],
    incidencias: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calcula el resumen estadístico del periodo."""

    total_dias = len(asistencias)
    total_minutos_ordinarios = 0
    total_minutos_extra = 0
    total_minutos_retardo = 0
    dias_completos = 0
    retardos_menores = 0
    retardos_mayores = 0
    faltas = 0
    omisiones = 0
    puntos_totales = 0

    for a in asistencias:
        estatus = (a.get("estatus") or "").upper()
        total_minutos_ordinarios += int(a.get("minutos_ordinarios") or 0)
        total_minutos_extra += int(a.get("minutos_extra") or 0)
        total_minutos_retardo += int(a.get("minutos_retardo") or 0)
        puntos_totales += int(a.get("puntos_generados") or 0)

        if estatus == "COMPLETO":
            dias_completos += 1
        elif estatus == "RETARDO_MENOR":
            retardos_menores += 1
        elif estatus == "RETARDO_MAYOR":
            retardos_mayores += 1
        elif estatus == "FALTA":
            faltas += 1
        elif estatus in ("OMISION_ENTRADA", "OMISION_SALIDA"):
            omisiones += 1

    total_incidencias = len(incidencias)
    incidencias_justificadas = sum(
        1 for i in incidencias if (i.get("estatus") or "").upper() in ("JUSTIFICADA", "APROBADA")
    )
    incidencias_pendientes = sum(
        1 for i in incidencias if (i.get("estatus") or "").upper() in ("PENDIENTE", "SIN_JUSTIFICAR")
    )

    return {
        "total_dias": total_dias,
        "dias_completos": dias_completos,
        "retardos_menores": retardos_menores,
        "retardos_mayores": retardos_mayores,
        "faltas": faltas,
        "omisiones": omisiones,
        "total_minutos_ordinarios": total_minutos_ordinarios,
        "total_horas_ordinarias": round(total_minutos_ordinarios / 60, 1),
        "total_minutos_extra": total_minutos_extra,
        "total_horas_extra": round(total_minutos_extra / 60, 1),
        "total_minutos_retardo": total_minutos_retardo,
        "puntos_totales": puntos_totales,
        "total_incidencias": total_incidencias,
        "incidencias_justificadas": incidencias_justificadas,
        "incidencias_pendientes": incidencias_pendientes,
    }
