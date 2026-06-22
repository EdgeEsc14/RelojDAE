\set ON_ERROR_STOP on

BEGIN;

SELECT set_config('app.usuario_correo', 'admin.sistema@dae.local', TRUE);
SELECT set_config('app.modulo', 'PRUEBA_MARCACIONES', TRUE);
SELECT set_config('app.accion', 'INSERTAR_MARCACIONES_PRUEBA', TRUE);


DO $$
DECLARE
    v_empleado_id BIGINT;
    v_dispositivo_id BIGINT;
    v_empleado_dispositivo_id BIGINT;

    v_tipo_entrada_id BIGINT;
    v_tipo_salida_id BIGINT;

    v_sincronizacion_id BIGINT;

    v_insertados INTEGER := 0;
    v_rows INTEGER := 0;
BEGIN
    SELECT id
    INTO v_empleado_id
    FROM personal.empleados
    WHERE codigo_empleado = 'EMP-9001';

    IF v_empleado_id IS NULL THEN
        RAISE EXCEPTION 'No existe el empleado EMP-9001.';
    END IF;


    SELECT id
    INTO v_dispositivo_id
    FROM dispositivos.dispositivos
    WHERE codigo = 'ZK_PRINCIPAL';

    IF v_dispositivo_id IS NULL THEN
        RAISE EXCEPTION 'No existe el dispositivo ZK_PRINCIPAL.';
    END IF;


    SELECT id
    INTO v_empleado_dispositivo_id
    FROM dispositivos.empleado_dispositivo
    WHERE empleado_id = v_empleado_id
      AND dispositivo_id = v_dispositivo_id
      AND zk_user_id = '9001'
      AND activo = TRUE
    LIMIT 1;

    IF v_empleado_dispositivo_id IS NULL THEN
        RAISE EXCEPTION 'No existe relación empleado-dispositivo para EMP-9001 y ZK_PRINCIPAL.';
    END IF;


    SELECT id
    INTO v_tipo_entrada_id
    FROM asistencia.tipos_marcacion
    WHERE codigo = 'ENTRADA_ORDINARIA';

    SELECT id
    INTO v_tipo_salida_id
    FROM asistencia.tipos_marcacion
    WHERE codigo = 'SALIDA_ORDINARIA';

    IF v_tipo_entrada_id IS NULL OR v_tipo_salida_id IS NULL THEN
        RAISE EXCEPTION 'No existen tipos de marcación ordinaria.';
    END IF;


    INSERT INTO dispositivos.sincronizaciones (
        dispositivo_id,
        tipo_sincronizacion,
        fecha_inicio,
        estatus,
        registros_leidos,
        registros_nuevos,
        registros_duplicados,
        registros_error,
        ejecutada_por_usuario_id,
        detalle
    )
    VALUES (
        v_dispositivo_id,
        'MARCACIONES',
        CURRENT_TIMESTAMP,
        'EN_PROCESO',
        2,
        0,
        0,
        0,
        NULL,
        jsonb_build_object(
            'origen', 'seed_prueba',
            'empleado', 'EMP-9001'
        )
    )
    RETURNING id INTO v_sincronizacion_id;


    INSERT INTO asistencia.marcaciones (
        dispositivo_id,
        empleado_dispositivo_id,
        empleado_id,
        tipo_marcacion_id,
        fecha_hora,
        fecha,
        zk_user_id,
        zk_uid,
        punch_original,
        estado_verificacion,
        codigo_trabajo,
        origen,
        raw_data,
        procesada,
        sincronizacion_id
    )
    SELECT
        v_dispositivo_id,
        v_empleado_dispositivo_id,
        v_empleado_id,
        v_tipo_entrada_id,
        '2026-06-22 08:17:00-06'::TIMESTAMP WITH TIME ZONE,
        '2026-06-22'::DATE,
        '9001',
        9001,
        0,
        1,
        NULL,
        'ZKTECO',
        jsonb_build_object(
            'seed', TRUE,
            'tipo', 'entrada_ordinaria',
            'nota', 'Marcación simulada de prueba'
        ),
        FALSE,
        v_sincronizacion_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM asistencia.marcaciones
        WHERE dispositivo_id = v_dispositivo_id
          AND zk_user_id = '9001'
          AND fecha_hora = '2026-06-22 08:17:00-06'::TIMESTAMP WITH TIME ZONE
          AND COALESCE(punch_original, -1) = 0
    );

    GET DIAGNOSTICS v_rows = ROW_COUNT;
    v_insertados := v_insertados + v_rows;


    INSERT INTO asistencia.marcaciones (
        dispositivo_id,
        empleado_dispositivo_id,
        empleado_id,
        tipo_marcacion_id,
        fecha_hora,
        fecha,
        zk_user_id,
        zk_uid,
        punch_original,
        estado_verificacion,
        codigo_trabajo,
        origen,
        raw_data,
        procesada,
        sincronizacion_id
    )
    SELECT
        v_dispositivo_id,
        v_empleado_dispositivo_id,
        v_empleado_id,
        v_tipo_salida_id,
        '2026-06-22 17:00:00-06'::TIMESTAMP WITH TIME ZONE,
        '2026-06-22'::DATE,
        '9001',
        9001,
        1,
        1,
        NULL,
        'ZKTECO',
        jsonb_build_object(
            'seed', TRUE,
            'tipo', 'salida_ordinaria',
            'nota', 'Marcación simulada de prueba'
        ),
        FALSE,
        v_sincronizacion_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM asistencia.marcaciones
        WHERE dispositivo_id = v_dispositivo_id
          AND zk_user_id = '9001'
          AND fecha_hora = '2026-06-22 17:00:00-06'::TIMESTAMP WITH TIME ZONE
          AND COALESCE(punch_original, -1) = 1
    );

    GET DIAGNOSTICS v_rows = ROW_COUNT;
    v_insertados := v_insertados + v_rows;


    UPDATE dispositivos.sincronizaciones
    SET
        fecha_fin = CURRENT_TIMESTAMP,
        estatus = 'EXITOSA',
        registros_nuevos = v_insertados,
        registros_duplicados = 2 - v_insertados,
        detalle = detalle || jsonb_build_object(
            'insertados', v_insertados,
            'duplicados', 2 - v_insertados
        )
    WHERE id = v_sincronizacion_id;

END $$;


COMMIT;
