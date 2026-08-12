from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.calendario_service import resolver_fecha_laborable


def _combinar_fecha_hora(fecha: date, hora: time) -> datetime:
    """Combina fecha con hora para generar un datetime."""
    return datetime.combine(fecha, hora)


def _calcular_salida_programada(
    fecha: date,
    hora_entrada: time,
    hora_salida: time,
) -> datetime:
    """
    Calcula la salida programada considerando cruce de medianoche.

    Si hora_salida < hora_entrada, el turno cruza medianoche y la salida
    corresponde al día siguiente.

    Ejemplo:
        entrada 22:00, salida 06:00 → salida = fecha + 1 día a las 06:00
        entrada 08:00, salida 15:00 → salida = misma fecha a las 15:00
    """
    if hora_salida < hora_entrada:
        return datetime.combine(fecha + timedelta(days=1), hora_salida)

    return datetime.combine(fecha, hora_salida)


def _calcular_minutos_retardo(
    entrada_programada: datetime,
    primera_entrada: datetime | None,
) -> int:
    if primera_entrada is None:
        return 0

    diff_seconds = (
        primera_entrada.replace(tzinfo=None)
        - entrada_programada.replace(tzinfo=None)
    ).total_seconds()

    return max(0, int(diff_seconds // 60))


def _calcular_estatus_y_puntos(
    minutos_retardo: int,
    tiene_entrada: bool,
    tiene_salida: bool,
) -> tuple[str, int, bool, str]:
    if not tiene_entrada:
        return (
            "FALTA",
            0,
            True,
            "No se encontró checada de entrada para el día.",
        )

    if minutos_retardo > 30:
        return (
            "FALTA",
            0,
            True,
            f"Entrada con {minutos_retardo} minutos de retardo. Se considera falta.",
        )

    if not tiene_salida:
        return (
            "OMISION_SALIDA",
            0,
            True,
            "Se encontró entrada, pero no se encontró checada de salida.",
        )

    if minutos_retardo <= 10:
        return (
            "COMPLETO",
            0,
            False,
            "Asistencia dentro de tolerancia.",
        )

    if minutos_retardo <= 20:
        return (
            "RETARDO_MENOR",
            1,
            False,
            f"Entrada con {minutos_retardo} minutos de retardo.",
        )

    return (
        "RETARDO_MAYOR",
        2,
        False,
        f"Entrada con {minutos_retardo} minutos de retardo.",
    )

def _calcular_minutos_extra(
    modalidad_tiempo_extra: str,
    entrada_programada: datetime,
    salida_programada: datetime,
    primera_entrada: datetime | None,
    ultima_salida: datetime | None,
    permite_tiempo_extra: bool,
) -> int:
    if not permite_tiempo_extra:
        return 0

    modalidad = str(modalidad_tiempo_extra or "").upper()

    if modalidad == "ANTES_ENTRADA" and primera_entrada:
        diff_seconds = (
            entrada_programada.replace(tzinfo=None)
            - primera_entrada.replace(tzinfo=None)
        ).total_seconds()

        return max(0, int(diff_seconds // 60))

    if modalidad == "DESPUES_SALIDA" and ultima_salida:
        diff_seconds = (
            ultima_salida.replace(tzinfo=None)
            - salida_programada.replace(tzinfo=None)
        ).total_seconds()

        return max(0, int(diff_seconds // 60))

    return 0


def _calcular_minutos_ordinarios(
    primera_entrada: datetime | None,
    ultima_salida: datetime | None,
    duracion_jornada_minutos: int,
    descanso_minutos: int,
    minutos_extra: int,
) -> int:
    if primera_entrada is None or ultima_salida is None:
        return 0

    diff_seconds = (
        ultima_salida.replace(tzinfo=None)
        - primera_entrada.replace(tzinfo=None)
    ).total_seconds()

    minutos_trabajados = max(0, int(diff_seconds // 60))
    minutos_netos = max(
        0,
        minutos_trabajados - int(descanso_minutos or 0) - minutos_extra,
    )

    return min(
        int(duracion_jornada_minutos or 0),
        minutos_netos,
    )


def _registrar_dia_no_laboral(
    db: Session,
    *,
    empleado_id: int,
    horario_id: int,
    fecha: date,
    hora_entrada: time,
    hora_salida: time,
    primera_entrada: datetime | None,
    ultima_salida: datetime | None,
    eventos: list[dict[str, Any]],
) -> None:
    """
    Registra un día no laborable en asistencias_diarias.

    No genera puntos, no marca como falta, no penaliza.
    Usa el estatus DIA_NO_LABORAL que ya existe en el CHECK constraint.
    """

    entrada_programada = _combinar_fecha_hora(fecha, hora_entrada)
    salida_programada = _calcular_salida_programada(fecha, hora_entrada, hora_salida)

    # Construir observación con nombres de eventos
    nombres_eventos = [e.get("nombre", "Evento") for e in eventos if e.get("afecta_asistencia")]
    observaciones = (
        "Día no laborable según calendario: " + ", ".join(nombres_eventos)
        if nombres_eventos
        else "Día no laborable según calendario laboral."
    )

    db.execute(
        text(
            """
            INSERT INTO asistencia.asistencias_diarias (
                empleado_id,
                periodo_evaluacion_id,
                politica_asistencia_id,
                horario_id,
                fecha,
                entrada_programada,
                salida_programada,
                primera_entrada,
                ultima_salida,
                minutos_retardo,
                minutos_ordinarios,
                minutos_extra,
                estatus,
                puntos_generados,
                procesada,
                requiere_revision,
                observaciones,
                fecha_procesamiento
            )
            VALUES (
                :empleado_id,
                NULL,
                1,
                :horario_id,
                :fecha,
                :entrada_programada,
                :salida_programada,
                :primera_entrada,
                :ultima_salida,
                0,
                0,
                0,
                'DIA_NO_LABORAL',
                0,
                true,
                false,
                :observaciones,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (empleado_id, fecha)
            DO UPDATE SET
                politica_asistencia_id = EXCLUDED.politica_asistencia_id,
                horario_id = EXCLUDED.horario_id,
                entrada_programada = EXCLUDED.entrada_programada,
                salida_programada = EXCLUDED.salida_programada,
                primera_entrada = EXCLUDED.primera_entrada,
                ultima_salida = EXCLUDED.ultima_salida,
                minutos_retardo = 0,
                minutos_ordinarios = 0,
                minutos_extra = 0,
                estatus = 'DIA_NO_LABORAL',
                puntos_generados = 0,
                procesada = true,
                requiere_revision = false,
                observaciones = EXCLUDED.observaciones,
                fecha_procesamiento = CURRENT_TIMESTAMP,
                fecha_modificacion = CURRENT_TIMESTAMP
            """
        ),
        {
            "empleado_id": empleado_id,
            "horario_id": horario_id,
            "fecha": fecha,
            "entrada_programada": entrada_programada,
            "salida_programada": salida_programada,
            "primera_entrada": primera_entrada,
            "ultima_salida": ultima_salida,
            "observaciones": observaciones,
        },
    )


def procesar_asistencia_diaria(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
) -> dict[str, Any]:
    """
    Procesa asistencia diaria para empleados con marcaciones en el rango.

    Para turnos que cruzan medianoche (hora_salida < hora_entrada), la salida
    se busca en el día siguiente. La fecha del registro de asistencia corresponde
    al día de ENTRADA del turno.
    """
    rows = db.execute(
        text(
            """
            WITH horarios_empleado AS (
                SELECT
                    mc.empleado_id,
                    mc.codigo_empleado,
                    mc.fecha AS fecha_entrada,

                    ah.horario_id,

                    h.hora_entrada,
                    h.hora_salida,
                    h.tolerancia_entrada_minutos,
                    h.descanso_minutos,
                    h.permite_tiempo_extra,

                    tt.duracion_jornada_minutos,
                    tt.modalidad_tiempo_extra,

                    -- Detectar si el turno cruza medianoche
                    (h.hora_salida < h.hora_entrada) AS cruza_medianoche

                FROM asistencia.marcaciones_crudas mc

                INNER JOIN asistencia.asignaciones_horario ah
                    ON ah.empleado_id = mc.empleado_id
                   AND ah.estatus = 'ACTIVA'
                   AND ah.fecha_inicio <= mc.fecha
                   AND (
                        ah.fecha_fin IS NULL
                        OR ah.fecha_fin >= mc.fecha
                   )

                INNER JOIN asistencia.horarios h
                    ON h.id = ah.horario_id
                   AND h.activo = true

                INNER JOIN asistencia.tipos_turno tt
                    ON tt.id = h.tipo_turno_id
                   AND tt.activo = true

                WHERE mc.fecha BETWEEN :fecha_inicio AND :fecha_fin
                  AND mc.empleado_id IS NOT NULL
                  AND mc.punch = 0

                GROUP BY
                    mc.empleado_id,
                    mc.codigo_empleado,
                    mc.fecha,
                    ah.horario_id,
                    h.hora_entrada,
                    h.hora_salida,
                    h.tolerancia_entrada_minutos,
                    h.descanso_minutos,
                    h.permite_tiempo_extra,
                    tt.duracion_jornada_minutos,
                    tt.modalidad_tiempo_extra
            )
            SELECT
                he.empleado_id,
                he.codigo_empleado,
                he.fecha_entrada AS fecha,
                he.horario_id,
                he.hora_entrada,
                he.hora_salida,
                he.tolerancia_entrada_minutos,
                he.descanso_minutos,
                he.permite_tiempo_extra,
                he.duracion_jornada_minutos,
                he.modalidad_tiempo_extra,
                he.cruza_medianoche,

                -- Primera entrada del día de entrada
                (
                    SELECT MIN(m.fecha_hora)
                    FROM asistencia.marcaciones_crudas m
                    WHERE m.empleado_id = he.empleado_id
                      AND m.fecha = he.fecha_entrada
                      AND m.punch = 0
                ) AS primera_entrada,

                -- Última salida: mismo día O día siguiente si cruza medianoche
                (
                    SELECT MAX(m.fecha_hora)
                    FROM asistencia.marcaciones_crudas m
                    WHERE m.empleado_id = he.empleado_id
                      AND m.punch = 1
                      AND (
                          -- Salida el mismo día
                          (NOT he.cruza_medianoche AND m.fecha = he.fecha_entrada)
                          OR
                          -- Salida el día siguiente (turno nocturno)
                          (he.cruza_medianoche AND m.fecha IN (he.fecha_entrada, he.fecha_entrada + 1))
                      )
                ) AS ultima_salida

            FROM horarios_empleado he
            ORDER BY he.fecha_entrada, he.empleado_id
            """
        ),
        {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        },
    ).mappings().all()

    procesadas = 0
    dias_no_laborables = 0
    errores: list[dict[str, Any]] = []

    for row in rows:
        try:
            fecha = row["fecha"]
            empleado_id = row["empleado_id"]

            # ============================================================
            # PASO PREVIO: Verificar si la fecha es laborable
            # según el Calendario Laboral.
            #
            # Si no hay eventos de calendario configurados, el
            # comportamiento por defecto es considerar el día como
            # laborable (opt-in).
            # ============================================================
            resolucion = resolver_fecha_laborable(
                db, fecha, empleado_id
            )

            if not resolucion.es_laborable:
                # Registrar como DIA_NO_LABORAL sin penalización
                _registrar_dia_no_laboral(
                    db=db,
                    empleado_id=empleado_id,
                    horario_id=row["horario_id"],
                    fecha=fecha,
                    hora_entrada=row["hora_entrada"],
                    hora_salida=row["hora_salida"],
                    primera_entrada=row["primera_entrada"],
                    ultima_salida=row["ultima_salida"],
                    eventos=resolucion.eventos,
                )
                dias_no_laborables += 1
                procesadas += 1
                continue

            # ============================================================
            # Procesamiento normal de asistencia (día laborable)
            # ============================================================

            entrada_programada = _combinar_fecha_hora(
                fecha,
                row["hora_entrada"],
            )

            salida_programada = _calcular_salida_programada(
                fecha,
                row["hora_entrada"],
                row["hora_salida"],
            )

            primera_entrada = row["primera_entrada"]
            ultima_salida = row["ultima_salida"]

            minutos_retardo = _calcular_minutos_retardo(
                entrada_programada=entrada_programada,
                primera_entrada=primera_entrada,
            )

            estatus, puntos, requiere_revision, observaciones = (
                _calcular_estatus_y_puntos(
                    minutos_retardo=minutos_retardo,
                    tiene_entrada=primera_entrada is not None,
                    tiene_salida=ultima_salida is not None,
                )
            )

            minutos_extra = _calcular_minutos_extra(
                modalidad_tiempo_extra=row["modalidad_tiempo_extra"],
                entrada_programada=entrada_programada,
                salida_programada=salida_programada,
                primera_entrada=primera_entrada,
                ultima_salida=ultima_salida,
                permite_tiempo_extra=row["permite_tiempo_extra"],
            )

            minutos_ordinarios = _calcular_minutos_ordinarios(
                primera_entrada=primera_entrada,
                ultima_salida=ultima_salida,
                duracion_jornada_minutos=row["duracion_jornada_minutos"],
                descanso_minutos=row["descanso_minutos"],
                minutos_extra=minutos_extra,
            )

            db.execute(
                text(
                    """
                    INSERT INTO asistencia.asistencias_diarias (
                        empleado_id,
                        periodo_evaluacion_id,
                        politica_asistencia_id,
                        horario_id,
                        fecha,
                        entrada_programada,
                        salida_programada,
                        primera_entrada,
                        ultima_salida,
                        minutos_retardo,
                        minutos_ordinarios,
                        minutos_extra,
                        estatus,
                        puntos_generados,
                        procesada,
                        requiere_revision,
                        observaciones,
                        fecha_procesamiento
                    )
                    VALUES (
                        :empleado_id,
                        NULL,
                        1,
                        :horario_id,
                        :fecha,
                        :entrada_programada,
                        :salida_programada,
                        :primera_entrada,
                        :ultima_salida,
                        :minutos_retardo,
                        :minutos_ordinarios,
                        :minutos_extra,
                        :estatus,
                        :puntos_generados,
                        true,
                        :requiere_revision,
                        :observaciones,
                        CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (empleado_id, fecha)
                    DO UPDATE SET
                        politica_asistencia_id = EXCLUDED.politica_asistencia_id,
                        horario_id = EXCLUDED.horario_id,
                        entrada_programada = EXCLUDED.entrada_programada,
                        salida_programada = EXCLUDED.salida_programada,
                        primera_entrada = EXCLUDED.primera_entrada,
                        ultima_salida = EXCLUDED.ultima_salida,
                        minutos_retardo = EXCLUDED.minutos_retardo,
                        minutos_ordinarios = EXCLUDED.minutos_ordinarios,
                        minutos_extra = EXCLUDED.minutos_extra,
                        estatus = EXCLUDED.estatus,
                        puntos_generados = EXCLUDED.puntos_generados,
                        procesada = true,
                        requiere_revision = EXCLUDED.requiere_revision,
                        observaciones = EXCLUDED.observaciones,
                        fecha_procesamiento = CURRENT_TIMESTAMP,
                        fecha_modificacion = CURRENT_TIMESTAMP
                    """
                ),
                {
                    "empleado_id": row["empleado_id"],
                    "horario_id": row["horario_id"],
                    "fecha": fecha,
                    "entrada_programada": entrada_programada,
                    "salida_programada": salida_programada,
                    "primera_entrada": primera_entrada,
                    "ultima_salida": ultima_salida,
                    "minutos_retardo": minutos_retardo,
                    "minutos_ordinarios": minutos_ordinarios,
                    "minutos_extra": minutos_extra,
                    "estatus": estatus,
                    "puntos_generados": puntos,
                    "requiere_revision": requiere_revision,
                    "observaciones": observaciones,
                },
            )

            procesadas += 1

        except Exception as exc:
            errores.append(
                {
                    "empleado_id": row.get("empleado_id"),
                    "fecha": str(row.get("fecha")),
                    "error": str(exc),
                }
            )

    db.commit()

    return {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "registros_encontrados": len(rows),
        "procesadas": procesadas,
        "dias_no_laborables": dias_no_laborables,
        "errores": errores,
    }