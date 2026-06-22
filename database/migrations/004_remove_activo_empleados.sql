BEGIN;

ALTER TABLE personal.empleados
    DROP COLUMN IF EXISTS activo;

COMMIT;