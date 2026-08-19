\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- ============================================================
-- 059_consolidate_asistencias_diarias.sql
--
-- Objetivo:
-- Consolidar asistencia.asistencias_diarias como la única tabla
-- oficial para resultados laborales diarios.
--
-- asistencia.asistencia_diaria fue creada como una tabla técnica
-- derivada, pero no forma parte del flujo actual y está vacía.
-- ============================================================

DO $$
DECLARE
    v_registros BIGINT;
    v_referencias BIGINT;
BEGIN
    IF to_regclass(
        'asistencia.asistencia_diaria'
    ) IS NULL THEN
        RAISE NOTICE
            'La tabla asistencia.asistencia_diaria no existe.';
        RETURN;
    END IF;

    EXECUTE
        'SELECT COUNT(*)
         FROM asistencia.asistencia_diaria'
    INTO v_registros;

    IF v_registros > 0 THEN
        RAISE EXCEPTION
            'No se puede eliminar asistencia.asistencia_diaria: contiene % registros.',
            v_registros;
    END IF;

    SELECT COUNT(*)
    INTO v_referencias
    FROM pg_constraint
    WHERE confrelid =
        'asistencia.asistencia_diaria'::regclass;

    IF v_referencias > 0 THEN
        RAISE EXCEPTION
            'No se puede eliminar asistencia.asistencia_diaria: existen % restricciones que la referencian.',
            v_referencias;
    END IF;

    DROP TABLE asistencia.asistencia_diaria;

    RAISE NOTICE
        'Tabla asistencia.asistencia_diaria eliminada correctamente.';
END;
$$;

COMMENT ON TABLE asistencia.asistencias_diarias IS
'Fuente oficial del resultado laboral diario por empleado. '
'Se genera al evaluar calendario laboral, horario vigente, '
'política de asistencia y marcaciones crudas.';

COMMIT;