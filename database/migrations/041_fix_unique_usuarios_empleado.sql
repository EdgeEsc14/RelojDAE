\set ON_ERROR_STOP on

BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM (
            SELECT
                empleado_id
            FROM seguridad.usuarios
            WHERE empleado_id IS NOT NULL
            GROUP BY empleado_id
            HAVING COUNT(*) > 1
        ) duplicados
    ) THEN
        RAISE EXCEPTION
            'No se puede crear UNIQUE: hay empleados con más de un usuario.';
    END IF;
END $$;


DROP INDEX IF EXISTS seguridad.uq_usuarios_empleado;


CREATE UNIQUE INDEX uq_usuarios_empleado
ON seguridad.usuarios (
    empleado_id
)
WHERE empleado_id IS NOT NULL;


COMMIT;