\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.periodos_evaluacion (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    politica_asistencia_id BIGINT NOT NULL,

    codigo VARCHAR(60) NOT NULL,

    nombre VARCHAR(150) NOT NULL,

    tipo_periodo VARCHAR(20) NOT NULL,

    anio SMALLINT NOT NULL,

    numero_periodo SMALLINT NOT NULL,

    fecha_inicio DATE NOT NULL,

    fecha_fin DATE NOT NULL,

    estatus VARCHAR(20)
        NOT NULL DEFAULT 'ABIERTO',

    fecha_cierre TIMESTAMP WITH TIME ZONE,

    observaciones VARCHAR(500),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_periodos_evaluacion
        PRIMARY KEY (id),

    CONSTRAINT fk_periodos_politica
        FOREIGN KEY (politica_asistencia_id)
        REFERENCES asistencia.politicas_asistencia (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT uq_periodos_codigo
        UNIQUE (codigo),

    CONSTRAINT uq_periodos_politica_fechas
        UNIQUE (
            politica_asistencia_id,
            fecha_inicio,
            fecha_fin
        ),

    CONSTRAINT uq_periodos_politica_anio_numero
        UNIQUE (
            politica_asistencia_id,
            tipo_periodo,
            anio,
            numero_periodo
        ),

    CONSTRAINT ck_periodos_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_periodos_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_periodos_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_periodos_tipo_periodo
        CHECK (
            tipo_periodo IN (
                'QUINCENAL',
                'MENSUAL'
            )
        ),

    CONSTRAINT ck_periodos_anio
        CHECK (
            anio >= 2000
        ),

    CONSTRAINT ck_periodos_numero_periodo
        CHECK (
            (
                tipo_periodo = 'MENSUAL'
                AND numero_periodo BETWEEN 1 AND 12
            )
            OR
            (
                tipo_periodo = 'QUINCENAL'
                AND numero_periodo BETWEEN 1 AND 24
            )
        ),

    CONSTRAINT ck_periodos_fechas
        CHECK (
            fecha_fin >= fecha_inicio
        ),

    CONSTRAINT ck_periodos_estatus
        CHECK (
            estatus IN (
                'ABIERTO',
                'CERRADO',
                'CANCELADO'
            )
        ),

    CONSTRAINT ck_periodos_fecha_cierre
        CHECK (
            (
                estatus = 'CERRADO'
                AND fecha_cierre IS NOT NULL
            )
            OR
            (
                estatus <> 'CERRADO'
            )
        ),

    CONSTRAINT ck_periodos_observaciones_no_vacias
        CHECK (
            observaciones IS NULL
            OR BTRIM(observaciones) <> ''
        )
);


CREATE INDEX IF NOT EXISTS
    ix_periodos_evaluacion_politica
ON asistencia.periodos_evaluacion (
    politica_asistencia_id
);


CREATE INDEX IF NOT EXISTS
    ix_periodos_evaluacion_fechas
ON asistencia.periodos_evaluacion (
    fecha_inicio,
    fecha_fin
);


CREATE INDEX IF NOT EXISTS
    ix_periodos_evaluacion_estatus
ON asistencia.periodos_evaluacion (
    estatus
);


COMMIT;