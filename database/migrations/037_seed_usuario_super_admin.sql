\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

SELECT set_config('app.usuario_correo', 'seed@sistema.local', TRUE);
SELECT set_config('app.modulo', 'SEED_INICIAL', TRUE);
SELECT set_config('app.accion', 'CREAR_USUARIO_SUPER_ADMIN', TRUE);


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM seguridad.roles
        WHERE codigo = 'SUPER_ADMIN'
    ) THEN
        RAISE EXCEPTION 'No existe el rol SUPER_ADMIN. Ejecuta primero las migraciones de roles.';
    END IF;
END $$;

DO $$
DECLARE
    v_rol_id BIGINT;
    v_password_hash TEXT;
BEGIN
    SELECT id
    INTO v_rol_id
    FROM seguridad.roles
    WHERE codigo = 'SUPER_ADMIN';

    v_password_hash :=
        crypt(
            'AdminDAE2026!',
            gen_salt('bf', 10)
        );

    IF EXISTS (
        SELECT 1
        FROM seguridad.usuarios
        WHERE LOWER(correo_electronico) = LOWER('admin.sistema@dae.local')
    ) THEN

        UPDATE seguridad.usuarios
        SET
            rol_id = v_rol_id,
            password_hash = v_password_hash,
            nombre_usuario = 'superadmin',
            requiere_cambio_password = TRUE,
            activo = TRUE,
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE LOWER(correo_electronico) = LOWER('admin.sistema@dae.local');

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
            NULL,
            v_rol_id,
            'admin.sistema@dae.local',
            v_password_hash,
            'superadmin',
            TRUE,
            TRUE
        );

    END IF;
END $$;

COMMIT;