\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.aplicaciones_justificante (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    justificante_id BIGINT NOT NULL,

    incidencia_id BIGINT NOT NULL,

    empleado_id BIGINT NOT NULL,

    periodo_evaluacion_id BIGINT NOT NULL,

    fecha_incidencia DATE NOT NULL,

    puntos_descontados SMALLINT
        NOT NULL DEFAULT 0,

    dias_aplicados NUMERIC(4,2)
        NOT NULL DEFAULT 1,

    aplicado_por_usuario_id BIGINT,

    fecha_aplicacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    observaciones VARCHAR(700),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_aplicaciones_justificante
        PRIMARY KEY (id),

    CONSTRAINT fk_aplicaciones_justificante
        FOREIGN KEY (justificante_id)
        REFERENCES asistencia.justificantes (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_aplicaciones_incidencia
        FOREIGN KEY (incidencia_id)
        REFERENCES asistencia.incidencias (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_aplicaciones_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_aplicaciones_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_aplicaciones_usuario
        FOREIGN KEY (aplicado_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT uq_aplicaciones_justificante_incidencia
        UNIQUE (
            justificante_id,
            incidencia_id
        ),

    CONSTRAINT ck_aplicaciones_puntos_descontados
        CHECK (
            puntos_descontados >= 0
        ),

    CONSTRAINT ck_aplicaciones_dias_aplicados
        CHECK (
            dias_aplicados > 0
        ),

    CONSTRAINT ck_aplicaciones_observaciones_no_vacias
        CHECK (
            observaciones IS NULL
            OR BTRIM(observaciones) <> ''
        )
);


CREATE INDEX IF NOT EXISTS
    ix_aplicaciones_justificante
ON asistencia.aplicaciones_justificante (
    justificante_id
);


CREATE INDEX IF NOT EXISTS
    ix_aplicaciones_incidencia
ON asistencia.aplicaciones_justificante (
    incidencia_id
);


CREATE INDEX IF NOT EXISTS
    ix_aplicaciones_empleado_periodo
ON asistencia.aplicaciones_justificante (
    empleado_id,
    periodo_evaluacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_aplicaciones_fecha_incidencia
ON asistencia.aplicaciones_justificante (
    fecha_incidencia
);


COMMIT;