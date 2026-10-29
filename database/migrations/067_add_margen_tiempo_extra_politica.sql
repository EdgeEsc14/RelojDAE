\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- Contrato del Núcleo de Asistencia §19: margen de gracia antes de
-- reconocer tiempo extra (ANTES_ENTRADA / DESPUES_SALIDA según el
-- turno). El margen nunca se paga; solo el excedente sobre él cuenta
-- como minutos_extra. Configurable desde Configuraciones generales,
-- nunca hardcodeado en el motor.
ALTER TABLE asistencia.politicas_asistencia
    ADD COLUMN IF NOT EXISTS margen_tiempo_extra_segundos INTEGER
        NOT NULL DEFAULT 1800;

ALTER TABLE asistencia.politicas_asistencia
    DROP CONSTRAINT IF EXISTS ck_politicas_margen_tiempo_extra_no_negativo;

ALTER TABLE asistencia.politicas_asistencia
    ADD CONSTRAINT ck_politicas_margen_tiempo_extra_no_negativo
        CHECK (margen_tiempo_extra_segundos >= 0);

COMMIT;
