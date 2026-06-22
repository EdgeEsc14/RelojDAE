\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.tipos_marcacion (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(40) NOT NULL,

    nombre VARCHAR(100) NOT NULL,

    descripcion VARCHAR(300),

    categoria VARCHAR(30) NOT NULL,

    es_entrada BOOLEAN NOT NULL,

    es_salida BOOLEAN NOT NULL,

    es_tiempo_extra BOOLEAN
        NOT NULL DEFAULT FALSE,

    requiere_pareja BOOLEAN
        NOT NULL DEFAULT TRUE,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_tipos_marcacion
        PRIMARY KEY (id),

    CONSTRAINT uq_tipos_marcacion_codigo
        UNIQUE (codigo),

    CONSTRAINT ck_tipos_marcacion_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_tipos_marcacion_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_tipos_marcacion_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_tipos_marcacion_categoria
        CHECK (
            categoria IN (
                'ORDINARIA',
                'EXTRA',
                'DESCONOCIDA'
            )
        ),

    CONSTRAINT ck_tipos_marcacion_direccion
        CHECK (
            (
                es_entrada = TRUE
                AND es_salida = FALSE
            )
            OR
            (
                es_entrada = FALSE
                AND es_salida = TRUE
            )
            OR
            (
                categoria = 'DESCONOCIDA'
                AND es_entrada = FALSE
                AND es_salida = FALSE
            )
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_tipos_marcacion_nombre_normalizado
ON asistencia.tipos_marcacion (
    LOWER(BTRIM(nombre))
);


INSERT INTO asistencia.tipos_marcacion (
    codigo,
    nombre,
    descripcion,
    categoria,
    es_entrada,
    es_salida,
    es_tiempo_extra,
    requiere_pareja,
    activo
)
VALUES
    (
        'ENTRADA_ORDINARIA',
        'Entrada ordinaria',
        'Marcación de entrada correspondiente a la jornada ordinaria.',
        'ORDINARIA',
        TRUE,
        FALSE,
        FALSE,
        TRUE,
        TRUE
    ),
    (
        'SALIDA_ORDINARIA',
        'Salida ordinaria',
        'Marcación de salida correspondiente a la jornada ordinaria.',
        'ORDINARIA',
        FALSE,
        TRUE,
        FALSE,
        TRUE,
        TRUE
    ),
    (
        'ENTRADA_EXTRA',
        'Entrada extra',
        'Marcación de entrada correspondiente a tiempo extra.',
        'EXTRA',
        TRUE,
        FALSE,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'SALIDA_EXTRA',
        'Salida extra',
        'Marcación de salida correspondiente a tiempo extra.',
        'EXTRA',
        FALSE,
        TRUE,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'DESCONOCIDA',
        'Desconocida',
        'Marcación cuyo tipo no pudo interpretarse desde el dispositivo.',
        'DESCONOCIDA',
        FALSE,
        FALSE,
        FALSE,
        FALSE,
        TRUE
    )
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    categoria = EXCLUDED.categoria,
    es_entrada = EXCLUDED.es_entrada,
    es_salida = EXCLUDED.es_salida,
    es_tiempo_extra = EXCLUDED.es_tiempo_extra,
    requiere_pareja = EXCLUDED.requiere_pareja,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;


COMMIT;