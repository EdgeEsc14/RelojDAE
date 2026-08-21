"""
Servicio de acumulación de puntos y detección de condiciones disciplinarias.

Reglas de negocio:
    - 10 puntos acumulados en un periodo → 1 DO (Día de Omisión / Descanso Obligatorio)
    - 7 DO en un periodo → condición de revisión de baja
    - 3 faltas consecutivas → condición de revisión de baja

Este servicio se ejecuta después del procesamiento de asistencia diaria
para mantener actualizada la acumulación de puntos y detectar condiciones.

asistencia.movimientos_puntos.periodo_evaluacion_id es NOT NULL con FK
a asistencia.periodos_evaluacion: nunca se inserta un movimiento sin
resolver primero un periodo ABIERTO real y único para la fecha
correspondiente (ver periodo_evaluacion_service). Si no hay ninguno o
hay más de uno, esa fecha/detección se omite y se reporta explícitamente
en "periodos_no_resueltos" — nunca se inventa un id ni se elige uno
arbitrariamente entre varios.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.periodo_evaluacion_service import (
    ResolucionPeriodo,
    resolver_periodo_vigente,
)


PUNTOS_POR_DO = 10
DOS_PARA_REVISION_BAJA = 7
FALTAS_CONSECUTIVAS_PARA_BAJA = 3


def _problema_periodo(
    resolucion: ResolucionPeriodo,
    contexto: str,
) -> dict[str, Any]:
    """Representación explícita y auditable de una fecha sin periodo
    resoluble (0 o >1 periodos ABIERTO aplicables)."""
    return {
        "fecha": resolucion.fecha.isoformat(),
        "contexto": contexto,
        "estado": resolucion.estado,
        "candidatos": [c["id"] for c in resolucion.candidatos],
    }


def acumular_puntos_periodo(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
) -> dict[str, Any]:
    """
    Procesa la acumulación de puntos para empleados con asistencia
    procesada en el rango de fechas dado.

    Pasos:
    1. Identifica empleados con puntos_generados > 0 en asistencias_diarias.
    2. Inserta movimientos de puntos (tipo CARGO) si no existen ya,
       resolviendo el periodo de evaluación real por fecha.
    3. Calcula DOs generados cuando se acumulan 10 puntos, en el
       periodo vigente a fecha_fin.
    4. Detecta 3 faltas consecutivas.
    5. Actualiza resumen_periodo_empleado si existe.

    Retorna resumen de la operación, incluyendo cualquier fecha para
    la que no fue posible resolver un único periodo de evaluación
    (periodos_no_resueltos): esas fechas no generan movimientos ni
    detecciones, pero tampoco impiden el resto del procesamiento.
    """

    problemas_periodo: list[dict[str, Any]] = []

    # Paso 1-2: Insertar movimientos de puntos por asistencias procesadas
    movimientos_insertados, problemas_insercion = _insertar_movimientos_puntos(
        db, fecha_inicio, fecha_fin
    )
    problemas_periodo.extend(problemas_insercion)

    # Pasos 3-4 dependen del periodo vigente a fecha_fin ("el periodo
    # activo" del rango procesado). Si no se puede resolver de forma
    # única, se omiten sin abortar el resto de la acumulación.
    resolucion_fin = resolver_periodo_vigente(db, fecha_fin)

    if resolucion_fin.estado == "OK":
        periodo_id = resolucion_fin.periodo["id"]
        dos_generados = _generar_dos_por_acumulacion(
            db, fecha_inicio, fecha_fin, periodo_id
        )
        alertas_faltas = _detectar_faltas_consecutivas(
            db, fecha_inicio, fecha_fin, periodo_id
        )
    else:
        dos_generados = []
        alertas_faltas = []
        problemas_periodo.append(
            _problema_periodo(resolucion_fin, contexto="deteccion_dos_y_bajas")
        )

    # Paso 5: no depende de resolver un periodo aquí (solo actualiza
    # resúmenes ya existentes con estatus ABIERTO), por lo que corre
    # siempre.
    resumenes_actualizados = _actualizar_resumenes_periodo(db, fecha_inicio, fecha_fin)

    db.commit()

    return {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "movimientos_puntos_insertados": movimientos_insertados,
        "dos_generados": dos_generados,
        "alertas_faltas_consecutivas": alertas_faltas,
        "resumenes_actualizados": resumenes_actualizados,
        "periodos_no_resueltos": problemas_periodo,
    }


def _obtener_fechas_con_puntos_pendientes(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
) -> list[date]:
    """Fechas del rango con asistencias procesadas con puntos > 0 que
    todavía no tienen su movimiento CARGO registrado."""
    rows = db.execute(
        text(
            """
            SELECT DISTINCT ad.fecha
            FROM asistencia.asistencias_diarias ad
            WHERE ad.fecha BETWEEN :fecha_inicio AND :fecha_fin
              AND ad.puntos_generados > 0
              AND ad.procesada = true
              AND NOT EXISTS (
                  SELECT 1
                  FROM asistencia.movimientos_puntos mp
                  WHERE mp.empleado_id = ad.empleado_id
                    AND mp.fecha = ad.fecha
                    AND mp.tipo_movimiento = 'CARGO'
                    AND mp.origen = 'SISTEMA'
              )
            ORDER BY ad.fecha
            """
        ),
        {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    ).scalars().all()

    return list(rows)


def _insertar_movimientos_puntos(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
) -> tuple[int, list[dict[str, Any]]]:
    """
    Inserta movimientos de puntos (CARGO) para asistencias con puntos > 0
    que aún no tienen movimiento registrado, resolviendo el periodo de
    evaluación real para cada fecha (nunca un id fijo).

    Retorna (movimientos_insertados, problemas_periodo).
    """

    fechas_pendientes = _obtener_fechas_con_puntos_pendientes(db, fecha_inicio, fecha_fin)

    total_insertados = 0
    problemas: list[dict[str, Any]] = []

    for fecha in fechas_pendientes:
        resolucion = resolver_periodo_vigente(db, fecha)

        if resolucion.estado != "OK":
            problemas.append(_problema_periodo(resolucion, contexto="insercion_movimientos"))
            continue

        result = db.execute(
            text(
                """
                INSERT INTO asistencia.movimientos_puntos (
                    empleado_id,
                    periodo_evaluacion_id,
                    fecha,
                    tipo_movimiento,
                    concepto,
                    puntos,
                    descripcion,
                    origen
                )
                SELECT
                    ad.empleado_id,
                    :periodo_id,
                    ad.fecha,
                    'CARGO',
                    CASE ad.estatus
                        WHEN 'RETARDO_MENOR' THEN 'Retardo menor'
                        WHEN 'RETARDO_MAYOR' THEN 'Retardo mayor'
                        ELSE 'Puntos por ' || ad.estatus
                    END,
                    ad.puntos_generados,
                    ad.observaciones,
                    'SISTEMA'
                FROM asistencia.asistencias_diarias ad
                WHERE ad.fecha = :fecha
                  AND ad.puntos_generados > 0
                  AND ad.procesada = true
                  AND NOT EXISTS (
                      SELECT 1
                      FROM asistencia.movimientos_puntos mp
                      WHERE mp.empleado_id = ad.empleado_id
                        AND mp.fecha = ad.fecha
                        AND mp.tipo_movimiento = 'CARGO'
                        AND mp.origen = 'SISTEMA'
                  )
                """
            ),
            {"fecha": fecha, "periodo_id": resolucion.periodo["id"]},
        )

        total_insertados += result.rowcount

    return total_insertados, problemas


def _generar_dos_por_acumulacion(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
    periodo_id: int,
) -> list[dict[str, Any]]:
    """
    Para cada empleado con puntos procesados en el rango, verifica si
    alcanzó múltiplos de 10 puntos acumulados en el periodo vigente
    (periodo_id, ya resuelto de forma única por el llamador). Si sí,
    registra el DO correspondiente.

    Retorna lista de DOs generados.
    """

    # Obtener empleados con puntos en el rango
    empleados_con_puntos = db.execute(
        text(
            """
            SELECT DISTINCT ad.empleado_id
            FROM asistencia.asistencias_diarias ad
            WHERE ad.fecha BETWEEN :fecha_inicio AND :fecha_fin
              AND ad.puntos_generados > 0
              AND ad.empleado_id IS NOT NULL
            """
        ),
        {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    ).scalars().all()

    dos_generados = []

    for empleado_id in empleados_con_puntos:
        # Calcular puntos acumulados en el periodo vigente
        row = db.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(
                        CASE WHEN mp.tipo_movimiento = 'CARGO' THEN mp.puntos
                             WHEN mp.tipo_movimiento = 'DESCUENTO' THEN mp.puntos
                             WHEN mp.tipo_movimiento = 'AJUSTE' THEN mp.puntos
                             ELSE 0
                        END
                    ), 0) AS puntos_acumulados,
                    COUNT(*) FILTER (
                        WHERE mp.concepto = 'Día de Omisión (DO)'
                    ) AS dos_existentes
                FROM asistencia.movimientos_puntos mp
                WHERE mp.empleado_id = :empleado_id
                  AND mp.periodo_evaluacion_id = :periodo_id
                """
            ),
            {"empleado_id": empleado_id, "periodo_id": periodo_id},
        ).mappings().first()

        if row is None:
            continue

        puntos_acumulados = int(row["puntos_acumulados"])
        dos_existentes = int(row["dos_existentes"])

        # Cuántos DOs deberían existir según los puntos
        dos_esperados = puntos_acumulados // PUNTOS_POR_DO

        # Si faltan DOs por generar
        dos_faltantes = dos_esperados - dos_existentes

        for _ in range(dos_faltantes):
            db.execute(
                text(
                    """
                    INSERT INTO asistencia.movimientos_puntos (
                        empleado_id,
                        periodo_evaluacion_id,
                        fecha,
                        tipo_movimiento,
                        concepto,
                        puntos,
                        descripcion,
                        origen
                    )
                    VALUES (
                        :empleado_id,
                        :periodo_id,
                        :fecha,
                        'CARGO',
                        'Día de Omisión (DO)',
                        0,
                        :descripcion,
                        'SISTEMA'
                    )
                    """
                ),
                {
                    "empleado_id": empleado_id,
                    "periodo_id": periodo_id,
                    "fecha": fecha_fin,
                    "descripcion": (
                        f"DO generado por acumulación de {PUNTOS_POR_DO} puntos. "
                        f"Puntos acumulados: {puntos_acumulados}."
                    ),
                },
            )

            dos_generados.append({
                "empleado_id": empleado_id,
                "puntos_acumulados": puntos_acumulados,
                "do_numero": dos_existentes + 1,
            })

            # Verificar si se alcanzaron 7 DOs → condición de baja
            total_dos = dos_existentes + dos_faltantes
            if total_dos >= DOS_PARA_REVISION_BAJA:
                _marcar_revision_baja(
                    db,
                    empleado_id=empleado_id,
                    periodo_id=periodo_id,
                    motivo=(
                        f"Empleado acumuló {total_dos} Días de Omisión (DO) "
                        f"en el periodo. Requiere revisión conforme a política institucional."
                    ),
                )

    return dos_generados


def _detectar_faltas_consecutivas(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
    periodo_id: int,
) -> list[dict[str, Any]]:
    """
    Detecta empleados con 3 o más faltas consecutivas dentro del rango procesado.

    Busca secuencias de días consecutivos con estatus FALTA.
    """

    alertas = []

    # Buscar empleados con faltas en el rango
    rows = db.execute(
        text(
            """
            WITH faltas_ordenadas AS (
                SELECT
                    ad.empleado_id,
                    ad.fecha,
                    ad.fecha - (
                        ROW_NUMBER() OVER (
                            PARTITION BY ad.empleado_id
                            ORDER BY ad.fecha
                        )
                    )::integer AS grupo_consecutivo
                FROM asistencia.asistencias_diarias ad
                WHERE ad.estatus = 'FALTA'
                  AND ad.empleado_id IS NOT NULL
                  AND ad.fecha BETWEEN :fecha_inicio AND :fecha_fin
            ),
            secuencias AS (
                SELECT
                    empleado_id,
                    grupo_consecutivo,
                    COUNT(*) AS faltas_consecutivas,
                    MIN(fecha) AS desde,
                    MAX(fecha) AS hasta
                FROM faltas_ordenadas
                GROUP BY empleado_id, grupo_consecutivo
                HAVING COUNT(*) >= :min_faltas
            )
            SELECT
                empleado_id,
                faltas_consecutivas,
                desde,
                hasta
            FROM secuencias
            ORDER BY empleado_id, desde
            """
        ),
        {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "min_faltas": FALTAS_CONSECUTIVAS_PARA_BAJA,
        },
    ).mappings().all()

    for row in rows:
        empleado_id = row["empleado_id"]
        faltas = row["faltas_consecutivas"]
        desde = row["desde"]
        hasta = row["hasta"]

        _marcar_revision_baja(
            db,
            empleado_id=empleado_id,
            periodo_id=periodo_id,
            motivo=(
                f"Empleado acumuló {faltas} faltas consecutivas "
                f"del {desde} al {hasta}. "
                f"Requiere revisión conforme a política institucional."
            ),
        )

        alertas.append({
            "empleado_id": empleado_id,
            "faltas_consecutivas": faltas,
            "desde": desde.isoformat() if desde else None,
            "hasta": hasta.isoformat() if hasta else None,
        })

    return alertas


def _marcar_revision_baja(
    db: Session,
    empleado_id: int,
    periodo_id: int,
    motivo: str,
) -> None:
    """
    Marca un resumen de periodo como requiere_revision_baja.
    Si no existe un resumen de periodo, no se crea uno nuevo: el
    resumen se crea al abrir/cerrar periodos de evaluación.
    """

    db.execute(
        text(
            """
            UPDATE asistencia.resumen_periodo_empleado
            SET
                requiere_revision_baja = TRUE,
                motivo_revision_baja = COALESCE(
                    motivo_revision_baja || E'\n' || :motivo,
                    :motivo
                ),
                fecha_modificacion = CURRENT_TIMESTAMP
            WHERE empleado_id = :empleado_id
              AND periodo_evaluacion_id = :periodo_id
              AND requiere_revision_baja = FALSE
            """
        ),
        {
            "empleado_id": empleado_id,
            "periodo_id": periodo_id,
            "motivo": motivo,
        },
    )


def _actualizar_resumenes_periodo(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
) -> int:
    """
    Actualiza los contadores de resumen_periodo_empleado para los empleados
    con asistencia procesada en el rango, si tienen resumen de periodo abierto.

    Solo actualiza filas ya existentes (rpe.estatus = 'ABIERTO'); no
    inserta ninguna, por lo que no depende de resolver un periodo aquí.
    """

    result = db.execute(
        text(
            """
            UPDATE asistencia.resumen_periodo_empleado rpe
            SET
                retardos_menores = sub.retardos_menores,
                retardos_mayores = sub.retardos_mayores,
                faltas = sub.faltas,
                dias_completos = sub.dias_completos,
                puntos_brutos = sub.puntos_brutos,
                minutos_retardo = sub.minutos_retardo,
                minutos_ordinarios = sub.minutos_ordinarios,
                minutos_extra = sub.minutos_extra,
                faltas_consecutivas_max = sub.faltas_consecutivas_max,
                descansos_obligatorios_generados = sub.dos_generados,
                fecha_calculo = CURRENT_TIMESTAMP,
                fecha_modificacion = CURRENT_TIMESTAMP
            FROM (
                SELECT
                    ad.empleado_id,
                    COUNT(*) FILTER (WHERE ad.estatus = 'RETARDO_MENOR') AS retardos_menores,
                    COUNT(*) FILTER (WHERE ad.estatus = 'RETARDO_MAYOR') AS retardos_mayores,
                    COUNT(*) FILTER (WHERE ad.estatus = 'FALTA') AS faltas,
                    COUNT(*) FILTER (WHERE ad.estatus = 'COMPLETO') AS dias_completos,
                    COALESCE(SUM(ad.puntos_generados), 0) AS puntos_brutos,
                    COALESCE(SUM(ad.minutos_retardo), 0) AS minutos_retardo,
                    COALESCE(SUM(ad.minutos_ordinarios), 0) AS minutos_ordinarios,
                    COALESCE(SUM(ad.minutos_extra), 0) AS minutos_extra,
                    -- Faltas consecutivas máximas (simplificado)
                    COALESCE((
                        SELECT MAX(cnt) FROM (
                            SELECT COUNT(*) AS cnt
                            FROM (
                                SELECT
                                    ad2.fecha,
                                    ad2.fecha - (
                                        ROW_NUMBER() OVER (ORDER BY ad2.fecha)
                                    )::integer AS grp
                                FROM asistencia.asistencias_diarias ad2
                                WHERE ad2.empleado_id = ad.empleado_id
                                  AND ad2.estatus = 'FALTA'
                                  AND ad2.fecha BETWEEN :fecha_inicio AND :fecha_fin
                            ) fg
                            GROUP BY grp
                        ) maxf
                    ), 0) AS faltas_consecutivas_max,
                    -- DOs generados
                    (
                        SELECT COUNT(*)
                        FROM asistencia.movimientos_puntos mp
                        WHERE mp.empleado_id = ad.empleado_id
                          AND mp.concepto = 'Día de Omisión (DO)'
                          AND mp.fecha BETWEEN :fecha_inicio AND :fecha_fin
                    ) AS dos_generados
                FROM asistencia.asistencias_diarias ad
                WHERE ad.fecha BETWEEN :fecha_inicio AND :fecha_fin
                  AND ad.empleado_id IS NOT NULL
                  AND ad.procesada = true
                GROUP BY ad.empleado_id
            ) sub
            WHERE rpe.empleado_id = sub.empleado_id
              AND rpe.estatus = 'ABIERTO'
              AND rpe.fecha_inicio <= :fecha_fin
              AND rpe.fecha_fin >= :fecha_inicio
            """
        ),
        {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        },
    )

    return result.rowcount
