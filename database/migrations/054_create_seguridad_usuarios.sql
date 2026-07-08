BEGIN;

-- ============================================================
-- 054_create_seguridad_usuarios.sql
-- Objetivo:
-- Crear o completar tabla de usuarios reales del sistema web.
--
-- Esta migración es compatible si seguridad.usuarios ya existía
-- con una estructura anterior.
--
-- Nota:
-- Estos usuarios son para iniciar sesión en la aplicación.
-- No son usuarios del reloj ZKTeco.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS seguridad;

CREATE TABLE IF NOT EXISTS seguridad.usuarios (
    id BIGSERIAL PRIMARY KEY
);

-- ============================================================
-- Columnas base
-- ============================================================

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS empleado_id INTEGER;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS correo VARCHAR(255);

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS nombre_usuario VARCHAR(100);

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS password_hash TEXT;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS rol VARCHAR(50);

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS estatus VARCHAR(50);

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS correo_verificado BOOLEAN;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS codigo_verificacion_hash TEXT;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS codigo_verificacion_expira_en TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS requiere_cambio_password BOOLEAN;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS ultimo_login TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS creado_por BIGINT;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS aprobado_por BIGINT;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS aprobado_en TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP WITHOUT TIME ZONE;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP WITHOUT TIME ZONE;

-- ============================================================
-- Valores por defecto para registros existentes
-- ============================================================

UPDATE seguridad.usuarios
SET correo = CONCAT('usuario_', id, '@pendiente.local')
WHERE correo IS NULL
   OR btrim(correo) = '';

UPDATE seguridad.usuarios
SET rol = 'empleado'
WHERE rol IS NULL
   OR btrim(rol) = '';

UPDATE seguridad.usuarios
SET estatus = 'PENDIENTE_APROBACION'
WHERE estatus IS NULL
   OR btrim(estatus) = '';

UPDATE seguridad.usuarios
SET correo_verificado = FALSE
WHERE correo_verificado IS NULL;

UPDATE seguridad.usuarios
SET requiere_cambio_password = FALSE
WHERE requiere_cambio_password IS NULL;

UPDATE seguridad.usuarios
SET fecha_creacion = NOW()
WHERE fecha_creacion IS NULL;

UPDATE seguridad.usuarios
SET fecha_modificacion = NOW()
WHERE fecha_modificacion IS NULL;

-- ============================================================
-- Defaults y NOT NULL
-- ============================================================

ALTER TABLE seguridad.usuarios
ALTER COLUMN correo SET NOT NULL;

ALTER TABLE seguridad.usuarios
ALTER COLUMN rol SET DEFAULT 'empleado';

ALTER TABLE seguridad.usuarios
ALTER COLUMN rol SET NOT NULL;

ALTER TABLE seguridad.usuarios
ALTER COLUMN estatus SET DEFAULT 'PENDIENTE_APROBACION';

ALTER TABLE seguridad.usuarios
ALTER COLUMN estatus SET NOT NULL;

ALTER TABLE seguridad.usuarios
ALTER COLUMN correo_verificado SET DEFAULT FALSE;

ALTER TABLE seguridad.usuarios
ALTER COLUMN correo_verificado SET NOT NULL;

ALTER TABLE seguridad.usuarios
ALTER COLUMN requiere_cambio_password SET DEFAULT FALSE;

ALTER TABLE seguridad.usuarios
ALTER COLUMN requiere_cambio_password SET NOT NULL;

ALTER TABLE seguridad.usuarios
ALTER COLUMN fecha_creacion SET DEFAULT NOW();

ALTER TABLE seguridad.usuarios
ALTER COLUMN fecha_creacion SET NOT NULL;

ALTER TABLE seguridad.usuarios
ALTER COLUMN fecha_modificacion SET DEFAULT NOW();

ALTER TABLE seguridad.usuarios
ALTER COLUMN fecha_modificacion SET NOT NULL;

-- ============================================================
-- Constraints
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_usuarios_empleado'
          AND conrelid = 'seguridad.usuarios'::regclass
    ) THEN
        ALTER TABLE seguridad.usuarios
        ADD CONSTRAINT fk_usuarios_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados(id)
        ON DELETE SET NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_usuarios_creado_por'
          AND conrelid = 'seguridad.usuarios'::regclass
    ) THEN
        ALTER TABLE seguridad.usuarios
        ADD CONSTRAINT fk_usuarios_creado_por
        FOREIGN KEY (creado_por)
        REFERENCES seguridad.usuarios(id)
        ON DELETE SET NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_usuarios_aprobado_por'
          AND conrelid = 'seguridad.usuarios'::regclass
    ) THEN
        ALTER TABLE seguridad.usuarios
        ADD CONSTRAINT fk_usuarios_aprobado_por
        FOREIGN KEY (aprobado_por)
        REFERENCES seguridad.usuarios(id)
        ON DELETE SET NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_usuarios_rol'
          AND conrelid = 'seguridad.usuarios'::regclass
    ) THEN
        ALTER TABLE seguridad.usuarios
        ADD CONSTRAINT ck_usuarios_rol CHECK (
            rol IN (
                'super_admin',
                'rh_admin',
                'supervisor',
                'empleado',
                'auditor'
            )
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_usuarios_estatus'
          AND conrelid = 'seguridad.usuarios'::regclass
    ) THEN
        ALTER TABLE seguridad.usuarios
        ADD CONSTRAINT ck_usuarios_estatus CHECK (
            estatus IN (
                'ACTIVO',
                'INACTIVO',
                'PENDIENTE_VERIFICACION',
                'PENDIENTE_APROBACION',
                'RECHAZADO',
                'BLOQUEADO'
            )
        );
    END IF;
END $$;

-- ============================================================
-- Índices
-- ============================================================

CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_correo_lower
ON seguridad.usuarios (LOWER(correo));

CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_nombre_usuario_lower
ON seguridad.usuarios (LOWER(nombre_usuario))
WHERE nombre_usuario IS NOT NULL
  AND btrim(nombre_usuario) <> '';

CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_empleado_activo
ON seguridad.usuarios (empleado_id)
WHERE empleado_id IS NOT NULL
  AND estatus IN ('ACTIVO', 'PENDIENTE_APROBACION', 'PENDIENTE_VERIFICACION');

CREATE INDEX IF NOT EXISTS ix_usuarios_rol
ON seguridad.usuarios (rol);

CREATE INDEX IF NOT EXISTS ix_usuarios_estatus
ON seguridad.usuarios (estatus);

CREATE INDEX IF NOT EXISTS ix_usuarios_empleado_id
ON seguridad.usuarios (empleado_id);

-- ============================================================
-- Comentarios
-- ============================================================

COMMENT ON TABLE seguridad.usuarios IS
'Usuarios del sistema web Reloj DAE. No corresponden a usuarios internos del reloj ZKTeco.';

COMMENT ON COLUMN seguridad.usuarios.empleado_id IS
'Empleado vinculado al usuario web. Puede ser NULL para cuentas técnicas o pendientes.';

COMMENT ON COLUMN seguridad.usuarios.correo IS
'Correo usado para login y verificación.';

COMMENT ON COLUMN seguridad.usuarios.password_hash IS
'Contraseña hasheada. Nunca guardar contraseña en texto plano.';

COMMENT ON COLUMN seguridad.usuarios.rol IS
'Rol del sistema: super_admin, rh_admin, supervisor, empleado o auditor.';

COMMENT ON COLUMN seguridad.usuarios.estatus IS
'Estatus operativo de la cuenta web.';



ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS ultimo_login_ip INET;

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS ultimo_login_ip_raw VARCHAR(255);

ALTER TABLE seguridad.usuarios
ADD COLUMN IF NOT EXISTS ultimo_login_user_agent TEXT;
COMMIT;