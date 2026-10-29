\set ON_ERROR_STOP on
\encoding UTF8

-- ============================================================
-- 068_seed_usuarios_prueba_roles.sql
--
-- Crea usuarios de prueba para los roles RH_ADMIN, SUPERVISOR
-- y AUDITOR, que no tienen seed en migraciones anteriores.
--
-- Solo aplica si el usuario no existe aún; es idempotente.
-- NUNCA ejecutar en producción con estas credenciales.
-- ============================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

SELECT set_config('app.usuario_correo', 'seed@sistema.local', TRUE);
SELECT set_config('app.modulo', 'SEED_PRUEBA_ROLES', TRUE);
SELECT set_config('app.accion', 'CREAR_USUARIOS_PRUEBA', TRUE);


-- ============================================================
-- RH / Admin
-- Correo:     rh.admin@dae.local
-- Contraseña: RhAdminDAE2026!
-- ============================================================

DO $$
DECLARE
    v_rol_id BIGINT;
    v_password_hash TEXT;
BEGIN
    SELECT id INTO v_rol_id
    FROM seguridad.roles
    WHERE codigo = 'RH_ADMIN';

    IF v_rol_id IS NULL THEN
        RAISE EXCEPTION 'No existe el rol RH_ADMIN.';
    END IF;

    v_password_hash := crypt('RhAdminDAE2026!', gen_salt('bf', 10));

    IF EXISTS (
        SELECT 1 FROM seguridad.usuarios
        WHERE LOWER(correo_electronico) = 'rh.admin@dae.local'
    ) THEN
        UPDATE seguridad.usuarios
        SET
            rol_id                  = v_rol_id,
            password_hash           = v_password_hash,
            nombre_usuario          = 'rh.admin',
            requiere_cambio_password = TRUE,
            activo                  = TRUE,
            fecha_modificacion      = CURRENT_TIMESTAMP
        WHERE LOWER(correo_electronico) = 'rh.admin@dae.local';
    ELSE
        INSERT INTO seguridad.usuarios (
            empleado_id, rol_id, correo_electronico,
            password_hash, nombre_usuario,
            requiere_cambio_password, activo
        ) VALUES (
            NULL, v_rol_id, 'rh.admin@dae.local',
            v_password_hash, 'rh.admin',
            TRUE, TRUE
        );
    END IF;
END $$;


-- ============================================================
-- Supervisor
-- Correo:     supervisor.prueba@dae.local
-- Contraseña: SupervisorDAE2026!
--
-- Se le asigna la primera unidad organizacional activa como
-- área de alcance, para que el filtro AREA devuelva datos.
-- ============================================================

DO $$
DECLARE
    v_rol_id      BIGINT;
    v_usuario_id  BIGINT;
    v_unidad_id   BIGINT;
    v_password_hash TEXT;
BEGIN
    SELECT id INTO v_rol_id
    FROM seguridad.roles
    WHERE codigo = 'SUPERVISOR';

    IF v_rol_id IS NULL THEN
        RAISE EXCEPTION 'No existe el rol SUPERVISOR.';
    END IF;

    -- Preferir la unidad raíz (sin padre); si no, la primera activa.
    SELECT id INTO v_unidad_id
    FROM organizacion.unidades_organizacionales
    WHERE activo = TRUE
    ORDER BY (unidad_padre_id IS NULL) DESC, id
    LIMIT 1;

    IF v_unidad_id IS NULL THEN
        RAISE EXCEPTION 'No existe ninguna unidad organizacional activa.';
    END IF;

    v_password_hash := crypt('SupervisorDAE2026!', gen_salt('bf', 10));

    IF EXISTS (
        SELECT 1 FROM seguridad.usuarios
        WHERE LOWER(correo_electronico) = 'supervisor.prueba@dae.local'
    ) THEN
        UPDATE seguridad.usuarios
        SET
            rol_id                  = v_rol_id,
            password_hash           = v_password_hash,
            nombre_usuario          = 'supervisor.prueba',
            requiere_cambio_password = TRUE,
            activo                  = TRUE,
            fecha_modificacion      = CURRENT_TIMESTAMP
        WHERE LOWER(correo_electronico) = 'supervisor.prueba@dae.local';
    ELSE
        INSERT INTO seguridad.usuarios (
            empleado_id, rol_id, correo_electronico,
            password_hash, nombre_usuario,
            requiere_cambio_password, activo
        ) VALUES (
            NULL, v_rol_id, 'supervisor.prueba@dae.local',
            v_password_hash, 'supervisor.prueba',
            TRUE, TRUE
        );
    END IF;

    SELECT id INTO v_usuario_id
    FROM seguridad.usuarios
    WHERE LOWER(correo_electronico) = 'supervisor.prueba@dae.local';

    -- Asignar unidad de alcance si no existe ya
    IF NOT EXISTS (
        SELECT 1 FROM seguridad.usuarios_unidades
        WHERE usuario_id = v_usuario_id
          AND unidad_organizacional_id = v_unidad_id
          AND activo = TRUE
    ) THEN
        INSERT INTO seguridad.usuarios_unidades (
            usuario_id, unidad_organizacional_id,
            incluye_descendientes, es_principal,
            fecha_inicio, fecha_fin, activo
        ) VALUES (
            v_usuario_id, v_unidad_id,
            TRUE, TRUE,
            CURRENT_DATE, NULL, TRUE
        );
    END IF;
END $$;


-- ============================================================
-- Auditor
-- Correo:     auditor.prueba@dae.local
-- Contraseña: AuditorDAE2026!
-- ============================================================

DO $$
DECLARE
    v_rol_id BIGINT;
    v_password_hash TEXT;
BEGIN
    SELECT id INTO v_rol_id
    FROM seguridad.roles
    WHERE codigo = 'AUDITOR';

    IF v_rol_id IS NULL THEN
        RAISE EXCEPTION 'No existe el rol AUDITOR.';
    END IF;

    v_password_hash := crypt('AuditorDAE2026!', gen_salt('bf', 10));

    IF EXISTS (
        SELECT 1 FROM seguridad.usuarios
        WHERE LOWER(correo_electronico) = 'auditor.prueba@dae.local'
    ) THEN
        UPDATE seguridad.usuarios
        SET
            rol_id                  = v_rol_id,
            password_hash           = v_password_hash,
            nombre_usuario          = 'auditor.prueba',
            requiere_cambio_password = TRUE,
            activo                  = TRUE,
            fecha_modificacion      = CURRENT_TIMESTAMP
        WHERE LOWER(correo_electronico) = 'auditor.prueba@dae.local';
    ELSE
        INSERT INTO seguridad.usuarios (
            empleado_id, rol_id, correo_electronico,
            password_hash, nombre_usuario,
            requiere_cambio_password, activo
        ) VALUES (
            NULL, v_rol_id, 'auditor.prueba@dae.local',
            v_password_hash, 'auditor.prueba',
            TRUE, TRUE
        );
    END IF;
END $$;


COMMIT;
