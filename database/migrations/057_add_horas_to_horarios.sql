BEGIN;

ALTER TABLE asistencia.horarios
ADD COLUMN IF NOT EXISTS hora_entrada TIME;

ALTER TABLE asistencia.horarios
ADD COLUMN IF NOT EXISTS hora_salida TIME;

UPDATE asistencia.horarios
SET
    hora_entrada = COALESCE(hora_entrada, TIME '08:00'),
    hora_salida = COALESCE(hora_salida, TIME '15:00')
WHERE codigo = 'ADMINISTRATIVO';

ALTER TABLE asistencia.horarios
ALTER COLUMN hora_entrada SET NOT NULL;

ALTER TABLE asistencia.horarios
ALTER COLUMN hora_salida SET NOT NULL;

COMMIT;