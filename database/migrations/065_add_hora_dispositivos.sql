\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- ============================================================
-- 065_add_hora_dispositivos.sql
--
-- Objetivo:
-- Agregar campos para gestión de hora por dispositivo.
-- Separar ultima_sincronizacion_hora de ultima_sincronizacion
-- (que se refiere a marcaciones).
-- ============================================================

ALTER TABLE dispositivos.dispositivos
ADD COLUMN IF NOT EXISTS ultima_sincronizacion_hora TIMESTAMP WITH TIME ZONE;

ALTER TABLE dispositivos.dispositivos
ADD COLUMN IF NOT EXISTS ultimo_desfase_segundos INTEGER;

ALTER TABLE dispositivos.dispositivos
ADD COLUMN IF NOT EXISTS ultimo_resultado_hora VARCHAR(50);

ALTER TABLE dispositivos.dispositivos
ADD COLUMN IF NOT EXISTS ultimo_error_hora VARCHAR(500);

-- Renombrar ultima_sincronizacion a ultima_sincronizacion_marcaciones
-- para claridad (si no se ha renombrado antes)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'dispositivos'
          AND table_name = 'dispositivos'
          AND column_name = 'ultima_sincronizacion'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'dispositivos'
          AND table_name = 'dispositivos'
          AND column_name = 'ultima_sincronizacion_marcaciones'
    ) THEN
        ALTER TABLE dispositivos.dispositivos
        RENAME COLUMN ultima_sincronizacion TO ultima_sincronizacion_marcaciones;
    END IF;
END;
$$;

COMMIT;
