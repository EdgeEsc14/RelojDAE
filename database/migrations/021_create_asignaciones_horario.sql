\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.asignaciones_horario (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    empleado_id BIGINT NOT NULL,

    horario_id BIGINT NOT NULL,

    fecha_inicio DATE NOT NULL,

    fecha_fin DATE,

    estatus VARCHAR(20)
        NOT NULL DEFAULT 'ACTIVA',

    motivo VARCHAR(300),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_asignaciones_horario
        PRIMARY KEY (id),

    CONSTRAINT fk_asignaciones_horario_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_asignaciones_horario_horario
        FOREIGN KEY (horario_id)
        REFERENCES asistencia.horarios (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_asignaciones_horario_estatus
        CHECK (
            estatus IN (
                'ACTIVA',
                'CERRADA',
                'CANCELADA'
            )
        ),

    CONSTRAINT ck_asignaciones_horario_fechas
        CHECK (
            fecha_fin IS NULL
            OR fecha_fin >= fecha_inicio
        ),

    CONSTRAINT ck_asignaciones_horario_motivo_no_vacio
        CHECK (
            motivo IS NULL
            OR BTRIM(motivo) <> ''
        )
);


CREATE INDEX IF NOT EXISTS
    ix_asignaciones_horario_empleado
ON asistencia.asignaciones_horario (
    empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_asignaciones_horario_horario
ON asistencia.asignaciones_horario (
    horario_id
);


CREATE INDEX IF NOT EXISTS
    ix_asignaciones_horario_fechas
ON asistencia.asignaciones_horario (
    fecha_inicio,
    fecha_fin
);


CREATE INDEX IF NOT EXISTS
    ix_asignaciones_horario_estatus
ON asistencia.asignaciones_horario (
    estatus
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_asignaciones_horario_actual_por_empleado
ON asistencia.asignaciones_horario (
    empleado_id
)
WHERE fecha_fin IS NULL
  AND estatus = 'ACTIVA';


COMMIT;