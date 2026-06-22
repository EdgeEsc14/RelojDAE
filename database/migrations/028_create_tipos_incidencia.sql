\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.tipos_incidencia (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(50) NOT NULL,

    nombre VARCHAR(120) NOT NULL,

    descripcion VARCHAR(400),

    categoria VARCHAR(30) NOT NULL,

    genera_puntos BOOLEAN
        NOT NULL DEFAULT FALSE,

    puntos_default SMALLINT
        NOT NULL DEFAULT 0,

    requiere_justificacion BOOLEAN
        NOT NULL DEFAULT FALSE,

    requiere_aprobacion BOOLEAN
        NOT NULL DEFAULT FALSE,

    afecta_asistencia BOOLEAN
        NOT NULL DEFAULT TRUE,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    orden_visual SMALLINT
        NOT NULL DEFAULT 0,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_tipos_incidencia
        PRIMARY KEY (id),

    CONSTRAINT uq_tipos_incidencia_codigo
        UNIQUE (codigo),

    CONSTRAINT ck_tipos_incidencia_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_tipos_incidencia_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_tipos_incidencia_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_tipos_incidencia_categoria
        CHECK (
            categoria IN (
                'RETARDO',
                'FALTA',
                'OMISION',
                'TIEMPO_EXTRA',
                'SANCION',
                'REVISION',
                'ADMINISTRATIVA'
            )
        ),

    CONSTRAINT ck_tipos_incidencia_puntos
        CHECK (
            puntos_default >= 0
        ),

    CONSTRAINT ck_tipos_incidencia_puntos_generados
        CHECK (
            genera_puntos = TRUE
            OR puntos_default = 0
        ),

    CONSTRAINT ck_tipos_incidencia_orden_visual
        CHECK (
            orden_visual >= 0
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_tipos_incidencia_nombre_normalizado
ON asistencia.tipos_incidencia (
    LOWER(BTRIM(nombre))
);


INSERT INTO asistencia.tipos_incidencia (
    codigo,
    nombre,
    descripcion,
    categoria,
    genera_puntos,
    puntos_default,
    requiere_justificacion,
    requiere_aprobacion,
    afecta_asistencia,
    activo,
    orden_visual
)
VALUES
    (
        'RETARDO_MENOR',
        'Retardo menor',
        'Llegada posterior a la tolerancia y dentro del rango de retardo menor.',
        'RETARDO',
        TRUE,
        1,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        1
    ),
    (
        'RETARDO_MAYOR',
        'Retardo mayor',
        'Llegada dentro del rango de retardo mayor.',
        'RETARDO',
        TRUE,
        2,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        2
    ),
    (
        'FALTA',
        'Falta',
        'Ausencia o llegada posterior al límite permitido por la política de asistencia.',
        'FALTA',
        FALSE,
        0,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        3
    ),
    (
        'OMISION_ENTRADA',
        'Omisión de entrada',
        'No existe marcación de entrada para el día evaluado.',
        'OMISION',
        FALSE,
        0,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        4
    ),
    (
        'OMISION_SALIDA',
        'Omisión de salida',
        'No existe marcación de salida para el día evaluado.',
        'OMISION',
        FALSE,
        0,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        5
    ),
    (
        'TIEMPO_EXTRA',
        'Tiempo extra',
        'Tiempo trabajado fuera de la jornada ordinaria reconocida.',
        'TIEMPO_EXTRA',
        FALSE,
        0,
        FALSE,
        TRUE,
        TRUE,
        TRUE,
        6
    ),
    (
        'DESCANSO_OBLIGATORIO',
        'Descanso obligatorio',
        'Sanción generada al alcanzar el límite de puntos efectivos del periodo.',
        'SANCION',
        FALSE,
        0,
        FALSE,
        TRUE,
        TRUE,
        TRUE,
        7
    ),
    (
        'REVISION_BAJA',
        'Revisión de baja',
        'Alerta administrativa por acumulación de descansos obligatorios o faltas continuas.',
        'REVISION',
        FALSE,
        0,
        FALSE,
        TRUE,
        FALSE,
        TRUE,
        8
    ),
    (
        'AJUSTE_ADMINISTRATIVO',
        'Ajuste administrativo',
        'Incidencia manual creada por RH para corregir o documentar una situación especial.',
        'ADMINISTRATIVA',
        FALSE,
        0,
        FALSE,
        TRUE,
        TRUE,
        TRUE,
        9
    )
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    categoria = EXCLUDED.categoria,
    genera_puntos = EXCLUDED.genera_puntos,
    puntos_default = EXCLUDED.puntos_default,
    requiere_justificacion = EXCLUDED.requiere_justificacion,
    requiere_aprobacion = EXCLUDED.requiere_aprobacion,
    afecta_asistencia = EXCLUDED.afecta_asistencia,
    activo = EXCLUDED.activo,
    orden_visual = EXCLUDED.orden_visual,
    fecha_modificacion = CURRENT_TIMESTAMP;


COMMIT;