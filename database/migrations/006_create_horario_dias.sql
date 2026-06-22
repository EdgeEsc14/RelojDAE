BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.horario_dias (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    horario_id BIGINT NOT NULL,

    dia_semana SMALLINT NOT NULL,

    es_laboral BOOLEAN
        NOT NULL DEFAULT TRUE,

    hora_entrada TIME WITHOUT TIME ZONE,

    hora_salida TIME WITHOUT TIME ZONE,

    cruza_medianoche BOOLEAN
        GENERATED ALWAYS AS (
            es_laboral
            AND hora_salida < hora_entrada
        ) STORED,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_horario_dias
        PRIMARY KEY (id),

    CONSTRAINT fk_horario_dias_horario
        FOREIGN KEY (horario_id)
        REFERENCES asistencia.horarios (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT uq_horario_dias_horario_dia
        UNIQUE (
            horario_id,
            dia_semana
        ),

    CONSTRAINT ck_horario_dias_dia_semana
        CHECK (
            dia_semana BETWEEN 1 AND 7
        ),

    CONSTRAINT ck_horario_dias_horas
        CHECK (
            (
                es_laboral = TRUE
                AND hora_entrada IS NOT NULL
                AND hora_salida IS NOT NULL
                AND hora_entrada <> hora_salida
            )
            OR
            (
                es_laboral = FALSE
                AND hora_entrada IS NULL
                AND hora_salida IS NULL
            )
        )
);


CREATE INDEX IF NOT EXISTS
    ix_horario_dias_horario
ON asistencia.horario_dias (
    horario_id
);


COMMIT;