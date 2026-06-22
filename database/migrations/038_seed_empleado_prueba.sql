\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE personal.empleados
    ADD COLUMN IF NOT EXISTS correo VARCHAR(320);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_empleados_correo_normalizado
ON personal.empleados (
    LOWER(BTRIM(correo))
)
WHERE correo IS NOT NULL;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_empleados_correo_no_vacio'
          AND conrelid = 'personal.empleados'::regclass
    ) THEN
        ALTER TABLE personal.empleados
            ADD CONSTRAINT ck_empleados_correo_no_vacio
            CHECK (
                correo IS NULL
                OR BTRIM(correo) <> ''
            );
    END IF;
END $$;

SELECT set_config('app.usuario_correo', 'admin.sistema@dae.local', TRUE);
SELECT set_config('app.modulo', 'SEED_INICIAL', TRUE);
SELECT set_config('app.accion', 'CREAR_EMPLEADO_PRUEBA', TRUE);


DO $$
DECLARE
    v_unidad_id BIGINT;
    v_puesto_id BIGINT;
    v_horario_id BIGINT;
    v_rol_empleado_id BIGINT;
    v_empleado_id BIGINT;
    v_usuario_id BIGINT;
    v_dispositivo_id BIGINT;
    v_password_hash TEXT;
BEGIN
    SELECT id
    INTO v_unidad_id
    FROM organizacion.unidades_organizacionales
    WHERE nombre ILIKE '%Inform%'
      AND nombre ILIKE '%Estad%'
      AND nombre ILIKE '%Escolar%'
    ORDER BY id
    LIMIT 1;

    IF v_unidad_id IS NULL THEN
        SELECT id
        INTO v_unidad_id
        FROM organizacion.unidades_organizacionales
        WHERE unidad_padre_id IS NULL
        ORDER BY id
        LIMIT 1;
    END IF;

    IF v_unidad_id IS NULL THEN
        RAISE EXCEPTION 'No existe ninguna unidad organizacional.';
    END IF;


    INSERT INTO organizacion.puestos (
        codigo,
        nombre,
        descripcion,
        nivel_jerarquico,
        activo
    )
    VALUES (
        'AUXILIAR_ADMINISTRATIVO',
        'Auxiliar administrativo',
        'Puesto de prueba para validar el flujo inicial del sistema.',
        1,
        TRUE
    )
    ON CONFLICT (codigo)
    DO UPDATE SET
        nombre = EXCLUDED.nombre,
        descripcion = EXCLUDED.descripcion,
        nivel_jerarquico = EXCLUDED.nivel_jerarquico,
        activo = TRUE,
        fecha_modificacion = CURRENT_TIMESTAMP;

    SELECT id
    INTO v_puesto_id
    FROM organizacion.puestos
    WHERE codigo = 'AUXILIAR_ADMINISTRATIVO';


    SELECT id
    INTO v_horario_id
    FROM asistencia.horarios
    WHERE codigo = 'ADMINISTRATIVO';

    IF v_horario_id IS NULL THEN
        RAISE EXCEPTION 'No existe el horario ADMINISTRATIVO.';
    END IF;


    SELECT id
    INTO v_rol_empleado_id
    FROM seguridad.roles
    WHERE codigo = 'EMPLEADO';

    IF v_rol_empleado_id IS NULL THEN
        RAISE EXCEPTION 'No existe el rol EMPLEADO.';
    END IF;


    SELECT id
    INTO v_dispositivo_id
    FROM dispositivos.dispositivos
    WHERE codigo = 'ZK_PRINCIPAL';

    IF v_dispositivo_id IS NULL THEN
        RAISE EXCEPTION 'No existe el dispositivo ZK_PRINCIPAL.';
    END IF;


    IF EXISTS (
        SELECT 1
        FROM personal.empleados
        WHERE codigo_empleado = 'EMP-9001'
    ) THEN

        UPDATE personal.empleados
        SET
            nombres = 'Empleado',
            apellido_paterno = 'Prueba',
            apellido_materno = 'Sistema',
            rfc = 'PEPS900101ABC',
            correo = 'empleado.prueba@dae.local',
            unidad_organizacional_id = v_unidad_id,
            puesto_id = v_puesto_id,
            supervisor_id = NULL,
            fecha_ingreso = CURRENT_DATE,
            fecha_baja = NULL,
            estatus = 'ACTIVO',
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE codigo_empleado = 'EMP-9001';

    ELSE

        INSERT INTO personal.empleados (
            codigo_empleado,
            nombres,
            apellido_paterno,
            apellido_materno,
            rfc,
            correo,
            unidad_organizacional_id,
            puesto_id,
            supervisor_id,
            fecha_ingreso,
            fecha_baja,
            estatus
        )
        VALUES (
            'EMP-9001',
            'Empleado',
            'Prueba',
            'Sistema',
            'PEPS900101ABC',
            'empleado.prueba@dae.local',
            v_unidad_id,
            v_puesto_id,
            NULL,
            CURRENT_DATE,
            NULL,
            'ACTIVO'
        );

    END IF;


    SELECT id
    INTO v_empleado_id
    FROM personal.empleados
    WHERE codigo_empleado = 'EMP-9001';


    IF EXISTS (
        SELECT 1
        FROM asistencia.asignaciones_horario
        WHERE empleado_id = v_empleado_id
          AND estatus = 'ACTIVA'
          AND fecha_fin IS NULL
    ) THEN

        UPDATE asistencia.asignaciones_horario
        SET
            horario_id = v_horario_id,
            motivo = 'Asignación inicial de prueba.',
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE empleado_id = v_empleado_id
          AND estatus = 'ACTIVA'
          AND fecha_fin IS NULL;

    ELSE

        INSERT INTO asistencia.asignaciones_horario (
            empleado_id,
            horario_id,
            fecha_inicio,
            fecha_fin,
            estatus,
            motivo
        )
        VALUES (
            v_empleado_id,
            v_horario_id,
            CURRENT_DATE,
            NULL,
            'ACTIVA',
            'Asignación inicial de prueba.'
        );

    END IF;


    v_password_hash :=
        crypt(
            'EmpleadoDAE2026!',
            gen_salt('bf', 10)
        );


    IF EXISTS (
        SELECT 1
        FROM seguridad.usuarios
        WHERE LOWER(correo_electronico) = LOWER('empleado.prueba@dae.local')
    ) THEN

        UPDATE seguridad.usuarios
        SET
            empleado_id = v_empleado_id,
            rol_id = v_rol_empleado_id,
            password_hash = v_password_hash,
            nombre_usuario = 'empleado.prueba',
            requiere_cambio_password = TRUE,
            activo = TRUE,
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE LOWER(correo_electronico) = LOWER('empleado.prueba@dae.local');

    ELSE

        INSERT INTO seguridad.usuarios (
            empleado_id,
            rol_id,
            correo_electronico,
            password_hash,
            nombre_usuario,
            requiere_cambio_password,
            activo
        )
        VALUES (
            v_empleado_id,
            v_rol_empleado_id,
            'empleado.prueba@dae.local',
            v_password_hash,
            'empleado.prueba',
            TRUE,
            TRUE
        );

    END IF;


    SELECT id
    INTO v_usuario_id
    FROM seguridad.usuarios
    WHERE LOWER(correo_electronico) = LOWER('empleado.prueba@dae.local');


    UPDATE seguridad.usuarios_unidades
    SET
        es_principal = FALSE,
        fecha_modificacion = CURRENT_TIMESTAMP
    WHERE usuario_id = v_usuario_id
      AND activo = TRUE
      AND es_principal = TRUE
      AND unidad_organizacional_id <> v_unidad_id;


    IF EXISTS (
        SELECT 1
        FROM seguridad.usuarios_unidades
        WHERE usuario_id = v_usuario_id
          AND unidad_organizacional_id = v_unidad_id
          AND activo = TRUE
    ) THEN

        UPDATE seguridad.usuarios_unidades
        SET
            incluye_descendientes = FALSE,
            es_principal = TRUE,
            fecha_fin = NULL,
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE usuario_id = v_usuario_id
          AND unidad_organizacional_id = v_unidad_id
          AND activo = TRUE;

    ELSE

        INSERT INTO seguridad.usuarios_unidades (
            usuario_id,
            unidad_organizacional_id,
            incluye_descendientes,
            es_principal,
            fecha_inicio,
            fecha_fin,
            activo
        )
        VALUES (
            v_usuario_id,
            v_unidad_id,
            FALSE,
            TRUE,
            CURRENT_DATE,
            NULL,
            TRUE
        );

    END IF;


    IF EXISTS (
        SELECT 1
        FROM dispositivos.empleado_dispositivo
        WHERE dispositivo_id = v_dispositivo_id
          AND zk_user_id = '9001'
          AND activo = TRUE
    ) THEN

        UPDATE dispositivos.empleado_dispositivo
        SET
            empleado_id = v_empleado_id,
            zk_uid = 9001,
            nombre_en_dispositivo = 'EMPLEADO PRUEBA',
            privilegio = 0,
            grupo = '1',
            sincronizado = FALSE,
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE dispositivo_id = v_dispositivo_id
          AND zk_user_id = '9001'
          AND activo = TRUE;

    ELSIF EXISTS (
        SELECT 1
        FROM dispositivos.empleado_dispositivo
        WHERE dispositivo_id = v_dispositivo_id
          AND empleado_id = v_empleado_id
          AND activo = TRUE
    ) THEN

        UPDATE dispositivos.empleado_dispositivo
        SET
            zk_uid = 9001,
            zk_user_id = '9001',
            nombre_en_dispositivo = 'EMPLEADO PRUEBA',
            privilegio = 0,
            grupo = '1',
            sincronizado = FALSE,
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE dispositivo_id = v_dispositivo_id
          AND empleado_id = v_empleado_id
          AND activo = TRUE;

    ELSE

        INSERT INTO dispositivos.empleado_dispositivo (
            empleado_id,
            dispositivo_id,
            zk_uid,
            zk_user_id,
            nombre_en_dispositivo,
            privilegio,
            grupo,
            sincronizado,
            activo
        )
        VALUES (
            v_empleado_id,
            v_dispositivo_id,
            9001,
            '9001',
            'EMPLEADO PRUEBA',
            0,
            '1',
            FALSE,
            TRUE
        );

    END IF;

END $$;


COMMIT;