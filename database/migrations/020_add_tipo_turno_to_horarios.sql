\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

ALTER TABLE asistencia.horarios
    ADD COLUMN IF NOT EXISTS tipo_turno_id BIGINT;


ALTER TABLE asistencia.horarios
    ADD CONSTRAINT fk_horarios_tipo_turno
    FOREIGN KEY (tipo_turno_id)
    REFERENCES asistencia.tipos_turno (id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT;


CREATE INDEX IF NOT EXISTS
    ix_horarios_tipo_turno
ON asistencia.horarios (
    tipo_turno_id
);


-- Asignamos el horario administrativo existente al turno matutino.
UPDATE asistencia.horarios AS horario
SET tipo_turno_id = (
    SELECT id
    FROM asistencia.tipos_turno
    WHERE codigo = 'MATUTINO'
)
WHERE horario.codigo = 'ADMINISTRATIVO'
  AND horario.tipo_turno_id IS NULL;


-- Después de actualizar los horarios existentes,
-- hacemos obligatoria la relación.
ALTER TABLE asistencia.horarios
    ALTER COLUMN tipo_turno_id SET NOT NULL;


COMMIT;