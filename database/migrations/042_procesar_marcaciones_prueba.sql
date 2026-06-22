\set ON_ERROR_STOP on

BEGIN;

SELECT set_config('app.usuario_correo', 'admin.sistema@dae.local', TRUE);
SELECT set_config('app.modulo', 'PROCESAMIENTO_ASISTENCIA', TRUE);
SELECT set_config('app.accion', 'PROCESAR_MARCACIONES_PRUEBA', TRUE);


DO $$
DECLARE
    v_empleado_id BIGINT;
    v_politica_id BIGINT;
    v_periodo_id BIGINT;
    v_horario_id BIGINT;

    v_marcacion_entrada_id BIGINT;
    v_marcacion_salida_id BIGINT;

    v_tipo_incidencia_id BIGINT;
    v_asistencia_id BIGINT;
    v_incidencia_id BIGINT;

    v_fecha DATE := '2026-06-22'::DATE;

    v_entrada_programada TIMESTAMP WITH TIME ZONE := '2026-06-22 08:00:00-06'::TIMESTAMP WITH TIME ZONE;
    v_salida_programada TIMESTAMP WITH TIME ZONE := '2026-06-22 17:00:00-06'::TIMESTAMP WITH TIME ZONE;

    v_primera_entrada TIMESTAMP WITH TIME ZONE;
    v_ultima_salida TIMESTAMP WITH TIME ZONE;

    v_minutos_retardo INTEGER;
    v_minutos_segmento INTEGER;
    v_puntos_retardo SMALLINT;
BEGIN
    SELECT id
    INTO v_empleado_id
    FROM personal.empleados
    WHERE codigo_empleado = 'EMP-9001';

    IF v_empleado_id IS NULL THEN
        RAISE EXCEPTION 'No existe el empleado EMP-9001.';
    END IF;


    SELECT id
    INTO v_politica_id
    FROM asistencia.politicas_asistencia
    WHERE codigo = 'POLITICA_DAE_GENERAL'
      AND activo = TRUE
    ORDER BY version DESC
    LIMIT 1;

    IF v_politica_id IS NULL THEN
        RAISE EXCEPTION 'No existe política activa POLITICA_DAE_GENERAL.';
    END IF;


    SELECT puntos_retardo_menor
    INTO v_puntos_retardo
    FROM asistencia.politicas_asistencia
    WHERE id = v_politica_id;


    INSERT INTO asistencia.periodos_evaluacion (
        politica_asistencia_id,
        codigo,
        nombre,
        tipo_periodo,
        anio,
        numero_periodo,
        fecha_inicio,
        fecha_fin,
        estatus,
        observaciones
    )
    VALUES (
        v_politica_id,
        'PERIODO_2026_Q12',
        'Segunda quincena de junio 2026',
        'QUINCENAL',
        2026,
        12,
        '2026-06-16',
        '2026-06-30',
        'ABIERTO',
        'Periodo creado para prueba funcional de asistencia.'
    )
    ON CONFLICT (codigo)
    DO UPDATE SET
        politica_asistencia_id = EXCLUDED.politica_asistencia_id,
        nombre = EXCLUDED.nombre,
        tipo_periodo = EXCLUDED.tipo_periodo,
        anio = EXCLUDED.anio,
        numero_periodo = EXCLUDED.numero_periodo,
        fecha_inicio = EXCLUDED.fecha_inicio,
        fecha_fin = EXCLUDED.fecha_fin,
        fecha_modificacion = CURRENT_TIMESTAMP
    RETURNING id INTO v_periodo_id;


    SELECT ah.horario_id
    INTO v_horario_id
    FROM asistencia.asignaciones_horario ah
    WHERE ah.empleado_id = v_empleado_id
      AND ah.estatus = 'ACTIVA'
      AND ah.fecha_inicio <= v_fecha
      AND (
            ah.fecha_fin IS NULL
            OR ah.fecha_fin >= v_fecha
          )
    ORDER BY ah.fecha_inicio DESC
    LIMIT 1;

    IF v_horario_id IS NULL THEN
        RAISE EXCEPTION 'El empleado EMP-9001 no tiene horario activo para la fecha %.', v_fecha;
    END IF;


    SELECT m.id, m.fecha_hora
    INTO v_marcacion_entrada_id, v_primera_entrada
    FROM asistencia.marcaciones m
    JOIN asistencia.tipos_marcacion tm
        ON tm.id = m.tipo_marcacion_id
    WHERE m.empleado_id = v_empleado_id
      AND m.fecha = v_fecha
      AND tm.codigo = 'ENTRADA_ORDINARIA'
    ORDER BY m.fecha_hora
    LIMIT 1;

    IF v_marcacion_entrada_id IS NULL THEN
        RAISE EXCEPTION 'No existe marcación de entrada ordinaria para EMP-9001 en fecha %.', v_fecha;
    END IF;


    SELECT m.id, m.fecha_hora
    INTO v_marcacion_salida_id, v_ultima_salida
    FROM asistencia.marcaciones m
    JOIN asistencia.tipos_marcacion tm
        ON tm.id = m.tipo_marcacion_id
    WHERE m.empleado_id = v_empleado_id
      AND m.fecha = v_fecha
      AND tm.codigo = 'SALIDA_ORDINARIA'
    ORDER BY m.fecha_hora DESC
    LIMIT 1;

    IF v_marcacion_salida_id IS NULL THEN
        RAISE EXCEPTION 'No existe marcación de salida ordinaria para EMP-9001 en fecha %.', v_fecha;
    END IF;


    v_minutos_retardo :=
        GREATEST(
            FLOOR(
                EXTRACT(
                    EPOCH FROM (
                        v_primera_entrada - v_entrada_programada
                    )
                ) / 60
            )::INTEGER,
            0
        );

    v_minutos_segmento :=
        GREATEST(
            FLOOR(
                EXTRACT(
                    EPOCH FROM (
                        v_ultima_salida - v_primera_entrada
                    )
                ) / 60
            )::INTEGER,
            0
        );


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
        v_empleado_id,
        v_periodo_id,
        v_politica_id,
        v_horario_id,
        v_fecha,
        v_entrada_programada,
        v_salida_programada,
        v_primera_entrada,
        v_ultima_salida,
        v_minutos_retardo,
        v_minutos_segmento,
        0,
        'RETARDO_MENOR',
        v_puntos_retardo,
        TRUE,
        FALSE,
        'Asistencia generada desde marcaciones simuladas.',
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (empleado_id, fecha)
    DO UPDATE SET
        periodo_evaluacion_id = EXCLUDED.periodo_evaluacion_id,
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
        procesada = TRUE,
        requiere_revision = FALSE,
        observaciones = EXCLUDED.observaciones,
        fecha_procesamiento = CURRENT_TIMESTAMP,
        fecha_modificacion = CURRENT_TIMESTAMP
    RETURNING id INTO v_asistencia_id;


    DELETE FROM asistencia.segmentos_trabajo
    WHERE asistencia_diaria_id = v_asistencia_id;


    INSERT INTO asistencia.segmentos_trabajo (
        asistencia_diaria_id,
        empleado_id,
        fecha,
        tipo_segmento,
        marcacion_entrada_id,
        marcacion_salida_id,
        inicio,
        fin,
        minutos,
        es_valido,
        requiere_revision,
        observaciones
    )
    VALUES (
        v_asistencia_id,
        v_empleado_id,
        v_fecha,
        'ORDINARIO',
        v_marcacion_entrada_id,
        v_marcacion_salida_id,
        v_primera_entrada,
        v_ultima_salida,
        v_minutos_segmento,
        TRUE,
        FALSE,
        'Segmento ordinario generado desde marcaciones simuladas.'
    );


    SELECT id
    INTO v_tipo_incidencia_id
    FROM asistencia.tipos_incidencia
    WHERE codigo = 'RETARDO_MENOR';

    IF v_tipo_incidencia_id IS NULL THEN
        RAISE EXCEPTION 'No existe tipo de incidencia RETARDO_MENOR.';
    END IF;


    DELETE FROM asistencia.movimientos_puntos
    WHERE incidencia_id IN (
        SELECT id
        FROM asistencia.incidencias
        WHERE asistencia_diaria_id = v_asistencia_id
          AND tipo_incidencia_id = v_tipo_incidencia_id
    );


    SELECT id
    INTO v_incidencia_id
    FROM asistencia.incidencias
    WHERE asistencia_diaria_id = v_asistencia_id
      AND tipo_incidencia_id = v_tipo_incidencia_id
      AND estatus <> 'CANCELADA'
    LIMIT 1;

    IF v_incidencia_id IS NULL THEN

        INSERT INTO asistencia.incidencias (
            empleado_id,
            asistencia_diaria_id,
            periodo_evaluacion_id,
            tipo_incidencia_id,
            fecha,
            fecha_inicio,
            fecha_fin,
            descripcion,
            puntos_originales,
            puntos_justificados,
            estatus,
            origen,
            requiere_revision
        )
        VALUES (
            v_empleado_id,
            v_asistencia_id,
            v_periodo_id,
            v_tipo_incidencia_id,
            v_fecha,
            v_primera_entrada,
            NULL,
            'Retardo menor generado desde prueba de procesamiento.',
            v_puntos_retardo,
            0,
            'PENDIENTE',
            'PROCESAMIENTO',
            FALSE
        )
        RETURNING id INTO v_incidencia_id;

    ELSE

        UPDATE asistencia.incidencias
        SET
            empleado_id = v_empleado_id,
            periodo_evaluacion_id = v_periodo_id,
            fecha = v_fecha,
            fecha_inicio = v_primera_entrada,
            fecha_fin = NULL,
            descripcion = 'Retardo menor generado desde prueba de procesamiento.',
            puntos_originales = v_puntos_retardo,
            puntos_justificados = 0,
            estatus = 'PENDIENTE',
            origen = 'PROCESAMIENTO',
            requiere_revision = FALSE,
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE id = v_incidencia_id;

    END IF;


    INSERT INTO asistencia.movimientos_puntos (
        empleado_id,
        periodo_evaluacion_id,
        incidencia_id,
        justificante_id,
        aplicacion_justificante_id,
        fecha,
        tipo_movimiento,
        concepto,
        puntos,
        descripcion,
        origen,
        creado_por_usuario_id
    )
    VALUES (
        v_empleado_id,
        v_periodo_id,
        v_incidencia_id,
        NULL,
        NULL,
        v_fecha,
        'CARGO',
        'Retardo menor',
        v_puntos_retardo,
        'Movimiento de puntos generado desde prueba de procesamiento.',
        'SISTEMA',
        NULL
    );


    UPDATE asistencia.marcaciones
    SET
        procesada = TRUE,
        fecha_procesamiento = CURRENT_TIMESTAMP
    WHERE id IN (
        v_marcacion_entrada_id,
        v_marcacion_salida_id
    );

END $$;


COMMIT;