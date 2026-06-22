BEGIN;

CREATE SCHEMA IF NOT EXISTS asistencia
    AUTHORIZATION reloj_app;


CREATE TABLE IF NOT EXISTS asistencia.horarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(40) NOT NULL,

    nombre VARCHAR(120) NOT NULL,

    descripcion VARCHAR(500),

    tolerancia_entrada_minutos SMALLINT
        NOT NULL DEFAULT 0,

    descanso_minutos SMALLINT
        NOT NULL DEFAULT 0,

    permite_tiempo_extra BOOLEAN
        NOT NULL DEFAULT FALSE,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_horarios
        PRIMARY KEY (id),

    CONSTRAINT uq_horarios_codigo
        UNIQUE (codigo),

    CONSTRAINT ck_horarios_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_horarios_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_horarios_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_horarios_tolerancia_no_negativa
        CHECK (
            tolerancia_entrada_minutos >= 0
        ),

    CONSTRAINT ck_horarios_descanso_no_negativo
        CHECK (
            descanso_minutos >= 0
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_horarios_nombre_normalizado
ON asistencia.horarios (
    LOWER(BTRIM(nombre))
);


COMMIT;