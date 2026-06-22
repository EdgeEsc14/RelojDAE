\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.asistencias_diarias (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    empleado_id BIGINT NOT NULL,

    periodo_evaluacion_id BIGINT,

    politica_asistencia_id BIGINT NOT NULL,

    horario_id BIGINT NOT NULL,

    fecha DATE NOT NULL,

    entrada_programada TIMESTAMP WITH TIME ZONE,

    salida_programada TIMESTAMP WITH TIME ZONE,

    primera_entrada TIMESTAMP WITH TIME ZONE,

    ultima_salida TIMESTAMP WITH TIME ZONE,

    minutos_retardo INTEGER
        NOT NULL DEFAULT 0,

    minutos_ordinarios INTEGER
        NOT NULL DEFAULT 0,

    minutos_extra INTEGER
        NOT NULL DEFAULT 0,

    estatus VARCHAR(40)
        NOT NULL DEFAULT 'SIN_PROCESAR',

    puntos_generados SMALLINT
        NOT NULL DEFAULT 0,

    procesada BOOLEAN
        NOT NULL DEFAULT FALSE,

    requiere_revision BOOLEAN
        NOT NULL DEFAULT FALSE,

    observaciones VARCHAR(500),

    fecha_procesamiento TIMESTAMP WITH TIME ZONE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_asistencias_diarias
        PRIMARY KEY (id),

    CONSTRAINT fk_asistencias_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_asistencias_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_asistencias_politica
        FOREIGN KEY (politica_asistencia_id)
        REFERENCES asistencia.politicas_asistencia (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_asistencias_horario
        FOREIGN KEY (horario_id)
        REFERENCES asistencia.horarios (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT uq_asistencias_empleado_fecha
        UNIQUE (
            empleado_id,
            fecha
        ),

    CONSTRAINT ck_asistencias_minutos_no_negativos
        CHECK (
            minutos_retardo >= 0
            AND minutos_ordinarios >= 0
            AND minutos_extra >= 0
        ),

    CONSTRAINT ck_asistencias_puntos_no_negativos
        CHECK (
            puntos_generados >= 0
        ),

    CONSTRAINT ck_asistencias_estatus
        CHECK (
            estatus IN (
                'SIN_PROCESAR',
                'COMPLETO',
                'COMPLETO_CON_TIEMPO_EXTRA',
                'TOLERANCIA',
                'RETARDO_MENOR',
                'RETARDO_MAYOR',
                'FALTA',
                'OMISION_ENTRADA',
                'OMISION_SALIDA',
                'DIA_NO_LABORAL',
                'JUSTIFICADA',
                'CANCELADA'
            )
        ),

    CONSTRAINT ck_asistencias_programacion
        CHECK (
            entrada_programada IS NULL
            OR salida_programada IS NULL
            OR salida_programada <> entrada_programada
        ),

    CONSTRAINT ck_asistencias_observaciones_no_vacias
        CHECK (
            observaciones IS NULL
            OR BTRIM(observaciones) <> ''
        ),

    CONSTRAINT ck_asistencias_procesamiento
        CHECK (
            (
                procesada = TRUE
                AND fecha_procesamiento IS NOT NULL
            )
            OR
            (
                procesada = FALSE
            )
        )
);


CREATE INDEX IF NOT EXISTS
    ix_asistencias_empleado
ON asistencia.asistencias_diarias (
    empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_asistencias_fecha
ON asistencia.asistencias_diarias (
    fecha
);


CREATE INDEX IF NOT EXISTS
    ix_asistencias_periodo
ON asistencia.asistencias_diarias (
    periodo_evaluacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_asistencias_estatus
ON asistencia.asistencias_diarias (
    estatus
);


CREATE INDEX IF NOT EXISTS
    ix_asistencias_procesada
ON asistencia.asistencias_diarias (
    procesada
);


CREATE TABLE IF NOT EXISTS asistencia.segmentos_trabajo (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    asistencia_diaria_id BIGINT NOT NULL,

    empleado_id BIGINT NOT NULL,

    fecha DATE NOT NULL,

    tipo_segmento VARCHAR(20) NOT NULL,

    marcacion_entrada_id BIGINT,

    marcacion_salida_id BIGINT,

    inicio TIMESTAMP WITH TIME ZONE NOT NULL,

    fin TIMESTAMP WITH TIME ZONE NOT NULL,

    minutos INTEGER NOT NULL,

    es_valido BOOLEAN
        NOT NULL DEFAULT TRUE,

    requiere_revision BOOLEAN
        NOT NULL DEFAULT FALSE,

    observaciones VARCHAR(500),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_segmentos_trabajo
        PRIMARY KEY (id),

    CONSTRAINT fk_segmentos_asistencia
        FOREIGN KEY (asistencia_diaria_id)
        REFERENCES asistencia.asistencias_diarias (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_segmentos_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_segmentos_marcacion_entrada
        FOREIGN KEY (marcacion_entrada_id)
        REFERENCES asistencia.marcaciones (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_segmentos_marcacion_salida
        FOREIGN KEY (marcacion_salida_id)
        REFERENCES asistencia.marcaciones (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT ck_segmentos_tipo
        CHECK (
            tipo_segmento IN (
                'ORDINARIO',
                'EXTRA',
                'NO_RECONOCIDO'
            )
        ),

    CONSTRAINT ck_segmentos_fechas
        CHECK (
            fin > inicio
        ),

    CONSTRAINT ck_segmentos_minutos
        CHECK (
            minutos > 0
        ),

    CONSTRAINT ck_segmentos_observaciones_no_vacias
        CHECK (
            observaciones IS NULL
            OR BTRIM(observaciones) <> ''
        ),

    CONSTRAINT ck_segmentos_marcaciones_diferentes
        CHECK (
            marcacion_entrada_id IS NULL
            OR marcacion_salida_id IS NULL
            OR marcacion_entrada_id <> marcacion_salida_id
        )
);


CREATE INDEX IF NOT EXISTS
    ix_segmentos_asistencia
ON asistencia.segmentos_trabajo (
    asistencia_diaria_id
);


CREATE INDEX IF NOT EXISTS
    ix_segmentos_empleado_fecha
ON asistencia.segmentos_trabajo (
    empleado_id,
    fecha
);


CREATE INDEX IF NOT EXISTS
    ix_segmentos_tipo
ON asistencia.segmentos_trabajo (
    tipo_segmento
);


CREATE INDEX IF NOT EXISTS
    ix_segmentos_marcacion_entrada
ON asistencia.segmentos_trabajo (
    marcacion_entrada_id
);


CREATE INDEX IF NOT EXISTS
    ix_segmentos_marcacion_salida
ON asistencia.segmentos_trabajo (
    marcacion_salida_id
);


COMMIT;