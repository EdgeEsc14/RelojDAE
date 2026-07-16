\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- ============================================================
-- 061_corregir_formatos_empleados.sql
--
-- Permite conservar empleados de prueba EMP-####
-- y utilizar DAE-#### para las nuevas altas.
--
-- También corrige la validación del RFC y sincroniza la
-- secuencia DAE con los códigos realmente existentes.
-- ============================================================


-- 1. Código de empleado: EMP-#### o DAE-####

ALTER TABLE personal.empleados
DROP CONSTRAINT IF EXISTS ck_empleados_codigo_formato;

ALTER TABLE personal.empleados
ADD CONSTRAINT ck_empleados_codigo_formato
CHECK (
    codigo_empleado = UPPER(BTRIM(codigo_empleado))
    AND codigo_empleado ~ '^(EMP|DAE)-[0-9]{4,}$'
);


-- 2. RFC de persona física o moral

ALTER TABLE personal.empleados
DROP CONSTRAINT IF EXISTS ck_empleados_rfc_formato;

ALTER TABLE personal.empleados
ADD CONSTRAINT ck_empleados_rfc_formato
CHECK (
    rfc IS NULL
    OR rfc ~ '^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$'
);


-- 3. Reajustar la secuencia DAE.
--
-- Si no existe ningún empleado DAE, el siguiente será DAE-0001.
-- Si ya existen empleados DAE, continúa después del mayor.

DO $$
DECLARE
    v_maximo BIGINT;
BEGIN
    SELECT MAX(
        (
            SUBSTRING(
                codigo_empleado
                FROM '^DAE-([0-9]+)$'
            )
        )::BIGINT
    )
    INTO v_maximo
    FROM personal.empleados
    WHERE codigo_empleado ~ '^DAE-[0-9]+$';

    IF v_maximo IS NULL THEN
        PERFORM setval(
            'personal.codigo_empleado_dae_seq',
            1,
            FALSE
        );
    ELSE
        PERFORM setval(
            'personal.codigo_empleado_dae_seq',
            v_maximo,
            TRUE
        );
    END IF;
END;
$$;


COMMIT;