\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- ============================================================
-- 064_add_estado_dispositivos.sql
--
-- Objetivo:
-- Agregar campos de estado operativo a dispositivos.dispositivos
-- para diferenciar estado lógico (activo) del estado físico
-- (conexión real con el reloj).
--
-- Campos nuevos:
--   estado_conexion       — CONECTADO/DESCONECTADO/ERROR/DESHABILITADO
--   ultima_comprobacion   — última vez que se intentó probar conexión
--   ultimo_error          — último mensaje de error de conexión
--   descripcion           — texto libre para notas del dispositivo
-- ============================================================

ALTER TABLE dispositivos.dispositivos
ADD COLUMN IF NOT EXISTS estado_conexion VARCHAR(20)
    NOT NULL DEFAULT 'DESCONECTADO';

ALTER TABLE dispositivos.dispositivos
ADD COLUMN IF NOT EXISTS ultima_comprobacion TIMESTAMP WITH TIME ZONE;

ALTER TABLE dispositivos.dispositivos
ADD COLUMN IF NOT EXISTS ultimo_error VARCHAR(500);

ALTER TABLE dispositivos.dispositivos
ADD COLUMN IF NOT EXISTS descripcion VARCHAR(500);

-- Constraint para estado_conexion
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_dispositivos_estado_conexion'
          AND conrelid = 'dispositivos.dispositivos'::regclass
    ) THEN
        ALTER TABLE dispositivos.dispositivos
        ADD CONSTRAINT ck_dispositivos_estado_conexion
        CHECK (
            estado_conexion IN (
                'CONECTADO',
                'DESCONECTADO',
                'ERROR',
                'DESHABILITADO'
            )
        );
    END IF;
END;
$$;

-- Índice para estado de conexión
CREATE INDEX IF NOT EXISTS
    ix_dispositivos_estado_conexion
ON dispositivos.dispositivos (
    estado_conexion
);

COMMIT;
