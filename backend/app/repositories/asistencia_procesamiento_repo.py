from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.zk_employee_link_repo import (
    resolver_empleado_id_para_marcacion,
)
from app.services.calendario_service import resolver_fecha_laborable
from app.services.politica_service import resolver_politica_vigente


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


def _calcular_segundos_retardo(
    entrada_programada: datetime,
    primera_entrada: datetime | None,
) -> int:
    """
    Retardo de entrada en segundos, sin truncar a minutos.

    Contrato §5: la clasificación debe usar los límites de la política
    en segundos, para no perder precisión en fronteras como 08:10:59.
    """
    if primera_entrada is None:
        return 0

    diff_seconds = (
        primera_entrada.replace(tzinfo=None)
        - entrada_programada.replace(tzinfo=None)
    ).total_seconds()

    return int(diff_seconds)


def _clasificar_retardo(
    segundos_retardo: int,
    politica: dict[str, Any],
) -> tuple[str, int]:
    """
    Clasifica el retardo de entrada usando los límites (en segundos) y
    los puntos de la política vigente (Contrato §5).

    | Condición                                    | Estatus       |
    |-----------------------------------------------|--------------|
    | <= 0 (en hora o antes)                        | COMPLETO      |
    | 0 < segundos <= limite_tolerancia_segundos     | TOLERANCIA    |
    | <= limite_retardo_menor_segundos               | RETARDO_MENOR |
    | <= limite_retardo_mayor_segundos               | RETARDO_MAYOR |
    | > limite_retardo_mayor_segundos                | FALTA         |
    """
    if segundos_retardo <= 0:
        return ("COMPLETO", 0)

    if segundos_retardo <= politica["limite_tolerancia_segundos"]:
        return ("TOLERANCIA", 0)

    if segundos_retardo <= politica["limite_retardo_menor_segundos"]:
        return ("RETARDO_MENOR", int(politica["puntos_retardo_menor"]))

    if segundos_retardo <= politica["limite_retardo_mayor_segundos"]:
        return ("RETARDO_MAYOR", int(politica["puntos_retardo_mayor"]))

    return ("FALTA", 0)


_OBSERVACIONES_ENTRADA = {
    "COMPLETO": "Llegada en hora o antes de la entrada programada.",
    "TOLERANCIA": "Entrada dentro de la tolerancia de la política.",
    "RETARDO_MENOR": "Entrada con retardo menor según la política.",
    "RETARDO_MAYOR": "Entrada con retardo mayor según la política.",
}


def _calcular_estatus_y_puntos(
    segundos_retardo: int,
    tiene_entrada: bool,
    tiene_salida: bool,
    politica: dict[str, Any],
    fecha=None,
    salida_programada=None,
) -> tuple[str, int, bool, str] | None:
    """
    Contrato §15: la jornada se considera abierta mientras el momento
    actual no haya alcanzado la salida_programada (horario efectivo ya
    resuelto con calendario/horario_dias/cruce de medianoche). No se usa
    ningún margen adicional hardcodeado: no existe en el modelo actual
    (horarios/politicas_asistencia) un campo de "ventana de salida" o
    margen de cierre, y el contrato prohíbe inventar uno. La salida
    programada es la propia frontera de la ventana válida de salida
    (ver ejemplo del contrato: turno que termina a las 16:00 no puede
    marcarse a las 14:00, es decir, antes de salida_programada).

    fecha se conserva por compatibilidad de firma pero ya no participa
    en la decisión: comparar directamente contra salida_programada es
    correcto para el día actual, días pasados (siempre cerrados) y
    turnos nocturnos (la fecha de cierre real puede ser el día
    siguiente al de la fila procesada).
    """
    jornada_abierta = (
        salida_programada is not None and datetime.now() < salida_programada
    )

    if not tiene_entrada and not tiene_salida:
        # Ausencia total (cero marcaciones). Mientras la jornada siga
        # abierta no se genera FALTA todavía (Contrato §15).
        if jornada_abierta:
            return None  # No procesar: turno aún no termina

        return (
            "FALTA",
            0,
            True,
            "No se encontró checada de entrada para el día.",
        )

    if not tiene_entrada and tiene_salida:
        # Contrato §7: existe salida pero no entrada → OMISION_ENTRADA.
        # La salida ya es un evento marcado (pasado), por lo que el
        # resultado es definitivo independientemente de la hora actual.
        return (
            "OMISION_ENTRADA",
            0,
            True,
            "Se encontró checada de salida, pero no se encontró checada de entrada.",
        )

    estatus_entrada, puntos_entrada = _clasificar_retardo(segundos_retardo, politica)

    if estatus_entrada == "FALTA":
        return (
            "FALTA",
            0,
            True,
            f"Entrada con {segundos_retardo} segundos de retardo. Se considera falta.",
        )

    if not tiene_salida:
        # Mientras la jornada siga abierta, procesar con el estatus de
        # entrada (puntual/tolerancia/retardo) pero sin cerrar como
        # OMISION_SALIDA (Contrato §15).
        if jornada_abierta:
            return (
                estatus_entrada,
                puntos_entrada,
                False,
                f"{_OBSERVACIONES_ENTRADA[estatus_entrada]} Turno en curso.",
            )

        return (
            "OMISION_SALIDA",
            0,
            True,
            "Se encontró entrada, pero no se encontró checada de salida.",
        )

    return (
        estatus_entrada,
        puntos_entrada,
        False,
        _OBSERVACIONES_ENTRADA[estatus_entrada],
    )

def _calcular_minutos_extra(
    modalidad_tiempo_extra: str,
    entrada_programada: datetime,
    salida_programada: datetime,
    primera_entrada: datetime | None,
    ultima_salida: datetime | None,
    permite_tiempo_extra: bool,
    margen_tiempo_extra_segundos: int,
) -> int:
    """
    Contrato §19: el margen es una franja de gracia que nunca se paga.
    Solo el excedente que supera el margen cuenta como tiempo extra.
    """
    if not permite_tiempo_extra:
        return 0

    margen = max(0, int(margen_tiempo_extra_segundos or 0))
    modalidad = str(modalidad_tiempo_extra or "").upper()

    if modalidad == "ANTES_ENTRADA" and primera_entrada:
        diff_seconds = (
            entrada_programada.replace(tzinfo=None)
            - primera_entrada.replace(tzinfo=None)
        ).total_seconds()

        excedente_segundos = max(0, diff_seconds - margen)
        return int(excedente_segundos // 60)

    if modalidad == "DESPUES_SALIDA" and ultima_salida:
        diff_seconds = (
            ultima_salida.replace(tzinfo=None)
            - salida_programada.replace(tzinfo=None)
        ).total_seconds()

        excedente_segundos = max(0, diff_seconds - margen)
        return int(excedente_segundos // 60)

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
    politica_id: int,
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
                :politica_id,
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
            "politica_id": politica_id,
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
    Procesa asistencia diaria para el universo de empleados activos con
    asignación de horario vigente en el rango (Contrato §2), tengan o no
    marcaciones. Un empleado con cero marcaciones entra al universo y
    puede resultar en FALTA o DIA_NO_LABORAL según el calendario.

    Para turnos que cruzan medianoche (hora_salida < hora_entrada), la salida
    se busca en el día siguiente. La fecha del registro de asistencia corresponde
    al día de ENTRADA del turno.
    """

    # Paso previo: vincular marcaciones huérfanas con sus empleados.
    # Prioriza dispositivos.empleado_dispositivo (fuente canónica,
    # Contrato §10) sobre personal.empleados.zk_user_id (fallback legacy
    # temporal), usando la misma resolución que la descarga de
    # marcaciones (resolver_empleado_id_para_marcacion) para que ambos
    # flujos compartan un único criterio. Si (dispositivo, zk_user_id) —
    # o zk_user_id solo, cuando el dispositivo no se identifica —
    # apunta ambiguamente a más de un empleado, no se elige ninguno: se
    # reporta como conflicto explícito en el resultado.
    marcaciones_huerfanas = db.execute(
        text(
            """
            SELECT id, dispositivo_origen, zk_user_id
            FROM asistencia.marcaciones_crudas
            WHERE empleado_id IS NULL
              AND zk_user_id IS NOT NULL
              AND zk_user_id != ''
              AND fecha BETWEEN :fecha_inicio AND :fecha_fin
            """
        ),
        {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    ).mappings().all()

    conflictos_identidad_zk: list[dict[str, Any]] = []

    for marcacion in marcaciones_huerfanas:
        resolucion = resolver_empleado_id_para_marcacion(
            db=db,
            dispositivo_origen=marcacion["dispositivo_origen"],
            zk_user_id=marcacion["zk_user_id"],
        )

        if resolucion["conflicto"]:
            conflictos_identidad_zk.append(
                {
                    "marcacion_id": marcacion["id"],
                    "dispositivo_origen": marcacion["dispositivo_origen"],
                    "zk_user_id": marcacion["zk_user_id"],
                    "detalle": resolucion["detalle"],
                }
            )
            continue

        if resolucion["empleado_id"] is None:
            continue

        db.execute(
            text(
                """
                UPDATE asistencia.marcaciones_crudas
                SET
                    empleado_id = :empleado_id,
                    codigo_empleado = :codigo_empleado
                WHERE id = :id
                """
            ),
            {
                "id": marcacion["id"],
                "empleado_id": resolucion["empleado_id"],
                "codigo_empleado": resolucion["codigo_empleado"],
            },
        )

    # El paso previo se confirma de forma independiente de la atomicidad
    # por fecha (Contrato §14): es mantenimiento de datos de marcaciones,
    # no parte de ninguna fecha concreta, y no debe deshacerse si una
    # fecha posterior falla técnicamente y se le hace rollback.
    db.commit()

    rows = db.execute(
        text(
            """
            WITH dias_rango AS (
                SELECT generate_series(
                    CAST(:fecha_inicio AS DATE),
                    CAST(:fecha_fin AS DATE),
                    INTERVAL '1 day'
                )::date AS fecha
            ),

            empleados_activos AS (
                SELECT
                    e.id AS empleado_id,
                    e.codigo_empleado
                FROM personal.empleados e
                WHERE UPPER(COALESCE(e.estatus, '')) = 'ACTIVO'
            ),

            -- Universo: empleado activo + asignación de horario vigente + fecha.
            -- No parte de marcaciones_crudas: un empleado con cero marcaciones
            -- debe existir en este universo (Contrato §2).
            universo AS (
                SELECT
                    ea.empleado_id,
                    ea.codigo_empleado,
                    dr.fecha,

                    ah.horario_id,

                    -- Contrato §4: horario_dias puede sobrescribir la
                    -- entrada/salida del horario base para el día de la
                    -- semana correspondiente. Solo sobrescribe cuando hay
                    -- una fila vigente para ese (horario_id, dia_semana)
                    -- con es_laboral=TRUE (el CHECK de horario_dias
                    -- garantiza que en ese caso ambas horas vienen no
                    -- nulas). Si no hay fila, o es_laboral=FALSE, se usa
                    -- el horario base sin cambios.
                    COALESCE(hd.hora_entrada, h.hora_entrada) AS hora_entrada,
                    COALESCE(hd.hora_salida, h.hora_salida) AS hora_salida,
                    h.tolerancia_entrada_minutos,
                    h.descanso_minutos,
                    h.permite_tiempo_extra,

                    tt.duracion_jornada_minutos,
                    tt.modalidad_tiempo_extra,

                    -- Detectar si el turno cruza medianoche, ya con la
                    -- hora efectiva (horario_dias si aplica, si no base).
                    (
                        COALESCE(hd.hora_salida, h.hora_salida)
                        < COALESCE(hd.hora_entrada, h.hora_entrada)
                    ) AS cruza_medianoche,

                    -- Cuántas asignaciones ACTIVA vigentes hay para este
                    -- (empleado, fecha). Si es > 1 existen asignaciones
                    -- solapadas: no se elige una automáticamente, se
                    -- reporta como error/deuda en Python.
                    COUNT(*) OVER (
                        PARTITION BY ea.empleado_id, dr.fecha
                    ) AS asignaciones_vigentes

                FROM empleados_activos ea

                CROSS JOIN dias_rango dr

                INNER JOIN asistencia.asignaciones_horario ah
                    ON ah.empleado_id = ea.empleado_id
                   AND ah.estatus = 'ACTIVA'
                   AND ah.fecha_inicio <= dr.fecha
                   AND (
                        ah.fecha_fin IS NULL
                        OR ah.fecha_fin >= dr.fecha
                   )

                INNER JOIN asistencia.horarios h
                    ON h.id = ah.horario_id
                   AND h.activo = true

                INNER JOIN asistencia.tipos_turno tt
                    ON tt.id = h.tipo_turno_id
                   AND tt.activo = true

                LEFT JOIN asistencia.horario_dias hd
                    ON hd.horario_id = h.id
                   AND hd.dia_semana = EXTRACT(ISODOW FROM dr.fecha)::smallint
                   AND hd.es_laboral = true
            )

            SELECT
                u.empleado_id,
                u.codigo_empleado,
                u.fecha,
                u.horario_id,
                u.hora_entrada,
                u.hora_salida,
                u.tolerancia_entrada_minutos,
                u.descanso_minutos,
                u.permite_tiempo_extra,
                u.duracion_jornada_minutos,
                u.modalidad_tiempo_extra,
                u.cruza_medianoche,
                u.asignaciones_vigentes,

                marcas.primera_entrada,
                marcas.ultima_salida

            FROM universo u

            -- ¿El reloj mandó al menos una marcación de SALIDA real
            -- (punch=1) dentro de la ventana de esta jornada? Si sí, se
            -- confía en esa clasificación del dispositivo (compatibilidad
            -- con el comportamiento de siempre). Si no —reloj que manda
            -- todo con el mismo punch, caso real detectado desde
            -- 2026-08-21 por mala configuración del dispositivo físico—
            -- se clasifica por orden cronológico en vez de por el código
            -- reportado (Contrato §11: el punch es un detalle de
            -- adaptador/mapeo ZKTeco, no del núcleo; el motor puede
            -- trabajar con marcaciones clasificadas independientemente
            -- del protocolo de origen).
            CROSS JOIN LATERAL (
                SELECT EXISTS (
                    SELECT 1
                    FROM asistencia.marcaciones_crudas ms
                    WHERE ms.empleado_id = u.empleado_id
                      AND ms.punch = 1
                      AND (
                          (NOT u.cruza_medianoche AND ms.fecha = u.fecha)
                          OR (u.cruza_medianoche AND ms.fecha IN (u.fecha, u.fecha + 1))
                      )
                ) AS existe
            ) hay_salida_marcada

            CROSS JOIN LATERAL (
                SELECT
                    CASE
                        WHEN hay_salida_marcada.existe THEN (
                            -- Por dispositivo: primera marcación de ENTRADA (punch=0).
                            SELECT MIN(m.fecha_hora)
                            FROM asistencia.marcaciones_crudas m
                            WHERE m.empleado_id = u.empleado_id
                              AND m.fecha = u.fecha
                              AND m.punch = 0
                        )
                        ELSE (
                            -- Por orden: primera marcación del día, sin importar punch.
                            SELECT MIN(m.fecha_hora)
                            FROM asistencia.marcaciones_crudas m
                            WHERE m.empleado_id = u.empleado_id
                              AND m.fecha = u.fecha
                        )
                    END AS primera_entrada,

                    CASE
                        WHEN hay_salida_marcada.existe THEN (
                            -- Por dispositivo: última marcación de SALIDA (punch=1).
                            SELECT MAX(m.fecha_hora)
                            FROM asistencia.marcaciones_crudas m
                            WHERE m.empleado_id = u.empleado_id
                              AND m.punch = 1
                              AND (
                                  (NOT u.cruza_medianoche AND m.fecha = u.fecha)
                                  OR (u.cruza_medianoche AND m.fecha IN (u.fecha, u.fecha + 1))
                              )
                        )
                        ELSE (
                            -- Por orden: última marcación de la ventana, siempre que
                            -- sea POSTERIOR a la entrada. Si solo hay una marcación en
                            -- el día, no cuenta como salida de sí misma -> NULL.
                            SELECT MAX(m.fecha_hora)
                            FROM asistencia.marcaciones_crudas m
                            WHERE m.empleado_id = u.empleado_id
                              AND (
                                  (NOT u.cruza_medianoche AND m.fecha = u.fecha)
                                  OR (u.cruza_medianoche AND m.fecha IN (u.fecha, u.fecha + 1))
                              )
                              AND m.fecha_hora > COALESCE(
                                  (
                                      SELECT MIN(m2.fecha_hora)
                                      FROM asistencia.marcaciones_crudas m2
                                      WHERE m2.empleado_id = u.empleado_id
                                        AND m2.fecha = u.fecha
                                  ),
                                  '-infinity'::timestamp
                              )
                        )
                    END AS ultima_salida
            ) marcas

            ORDER BY u.fecha, u.empleado_id
            """
        ),
        {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        },
    ).mappings().all()

    procesadas = 0
    dias_no_laborables = 0
    faltas_generadas = 0
    errores: list[dict[str, Any]] = []

    # ============================================================
    # Contrato §14: la unidad transaccional es la FECHA completa.
    # Se agrupan las filas por fecha y cada fecha se procesa y se
    # confirma (o se revierte) de forma independiente: un fallo técnico
    # en un empleado no puede dejar a otros empleados de la MISMA fecha
    # parcialmente insertados, pero tampoco debe impedir procesar las
    # demás fechas del rango.
    # ============================================================
    filas_por_fecha: dict[date, list[Any]] = {}
    for row in rows:
        filas_por_fecha.setdefault(row["fecha"], []).append(row)

    for fecha, filas_fecha in filas_por_fecha.items():
        # Contadores y set de dedupe locales a la fecha: solo se suman a
        # los totales globales si la transacción de esta fecha confirma.
        # Si la fecha falla técnicamente, se descartan junto con el
        # rollback — no deben reflejar trabajo que ya no existe en BD.
        procesadas_fecha = 0
        dias_no_laborables_fecha = 0
        faltas_generadas_fecha = 0
        claves_asignacion_duplicada: set[Any] = set()
        empleado_actual: Any = None

        try:
            for row in filas_fecha:
                empleado_id = row["empleado_id"]
                empleado_actual = empleado_id

                # ============================================================
                # Universo: como máximo una fila lógica por (empleado, fecha).
                # Si hay asignaciones_horario ACTIVA solapadas para el mismo
                # (empleado, fecha), no se elige una automáticamente: se
                # reporta como error de DOMINIO (no aborta la fecha) y no
                # se procesa ese empleado.
                # ============================================================
                if row["asignaciones_vigentes"] > 1:
                    if empleado_id not in claves_asignacion_duplicada:
                        errores.append(
                            {
                                "empleado_id": empleado_id,
                                "fecha": str(fecha),
                                "error": (
                                    "Múltiples asignaciones de horario ACTIVA "
                                    "solapadas para este empleado y fecha. No se "
                                    "puede determinar automáticamente cuál aplica. "
                                    "Corregir asistencia.asignaciones_horario."
                                ),
                            }
                        )
                        claves_asignacion_duplicada.add(empleado_id)
                    continue

                # ============================================================
                # Resolver política de asistencia vigente para la fecha.
                # Contrato §5: debe existir EXACTAMENTE una política aplicable.
                # Se resuelve antes del calendario porque incluso un día
                # DIA_NO_LABORAL requiere un politica_asistencia_id válido
                # (columna NOT NULL con FK) — no hay una "política nula".
                # SIN_POLITICA / MULTIPLES_POLITICAS son errores de DOMINIO:
                # se reportan y se sigue con los demás empleados de la fecha.
                # ============================================================
                resolucion_politica = resolver_politica_vigente(db, fecha)

                if resolucion_politica.estado == "SIN_POLITICA":
                    errores.append(
                        {
                            "empleado_id": empleado_id,
                            "fecha": str(fecha),
                            "error": (
                                "No hay política de asistencia vigente para la "
                                "fecha. No se puede procesar sin política "
                                "(Contrato §5)."
                            ),
                        }
                    )
                    continue

                if resolucion_politica.estado == "MULTIPLES_POLITICAS":
                    codigos = ", ".join(
                        f"{p.get('codigo')} v{p.get('version')}"
                        for p in resolucion_politica.candidatos
                    )
                    errores.append(
                        {
                            "empleado_id": empleado_id,
                            "fecha": str(fecha),
                            "error": (
                                "Múltiples políticas de asistencia vigentes y "
                                "activas para esta fecha, con rangos de vigencia "
                                f"solapados ({codigos}). No se elige una "
                                "automáticamente. Corregir "
                                "asistencia.politicas_asistencia."
                            ),
                        }
                    )
                    continue

                politica = resolucion_politica.politica

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
                        politica_id=politica["id"],
                        horario_id=row["horario_id"],
                        fecha=fecha,
                        hora_entrada=row["hora_entrada"],
                        hora_salida=row["hora_salida"],
                        primera_entrada=row["primera_entrada"],
                        ultima_salida=row["ultima_salida"],
                        eventos=resolucion.eventos,
                    )
                    dias_no_laborables_fecha += 1
                    procesadas_fecha += 1
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

                segundos_retardo = _calcular_segundos_retardo(
                    entrada_programada=entrada_programada,
                    primera_entrada=primera_entrada,
                )

                resultado_estatus = _calcular_estatus_y_puntos(
                    segundos_retardo=segundos_retardo,
                    tiene_entrada=primera_entrada is not None,
                    tiene_salida=ultima_salida is not None,
                    politica=politica,
                    fecha=fecha,
                    salida_programada=salida_programada,
                )

                # Si retorna None, el turno aún no termina — saltar sin grabar
                if resultado_estatus is None:
                    continue

                estatus, puntos, requiere_revision, observaciones = resultado_estatus

                minutos_extra = _calcular_minutos_extra(
                    modalidad_tiempo_extra=row["modalidad_tiempo_extra"],
                    entrada_programada=entrada_programada,
                    salida_programada=salida_programada,
                    primera_entrada=primera_entrada,
                    ultima_salida=ultima_salida,
                    permite_tiempo_extra=row["permite_tiempo_extra"],
                    margen_tiempo_extra_segundos=politica[
                        "margen_tiempo_extra_segundos"
                    ],
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
                            :politica_id,
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
                        "politica_id": politica["id"],
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

                procesadas_fecha += 1
                if estatus == "FALTA":
                    faltas_generadas_fecha += 1

            # Fin de la fecha sin errores técnicos: confirma en BD todo lo
            # de ESTA fecha únicamente, y recién ahora se suman los
            # contadores locales a los totales globales.
            db.commit()
            procesadas += procesadas_fecha
            dias_no_laborables += dias_no_laborables_fecha
            faltas_generadas += faltas_generadas_fecha

        except Exception as exc:
            # Error TÉCNICO (no es uno de los estados de dominio manejados
            # arriba, que resuelven con `continue` y sin levantar excepción):
            # revierte TODA la fecha —ningún insert parcial de otros
            # empleados de esta misma fecha queda persistido— y se continúa
            # con la siguiente fecha del rango.
            db.rollback()
            errores.append(
                {
                    "empleado_id": empleado_actual,
                    "fecha": str(fecha),
                    "error": (
                        "Error técnico procesando la fecha, se revirtió "
                        f"completa (Contrato §14): {exc}"
                    ),
                }
            )
            continue

    return {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "registros_encontrados": len(rows),
        "procesadas": procesadas,
        "faltas_generadas": faltas_generadas,
        "dias_no_laborables": dias_no_laborables,
        "errores": errores,
        "conflictos_identidad_zk": conflictos_identidad_zk,
    }