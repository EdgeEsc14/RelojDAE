BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.tipos_turno (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(30) NOT NULL,

    nombre VARCHAR(80) NOT NULL,

    hora_entrada_desde TIME WITHOUT TIME ZONE,

    hora_entrada_hasta TIME WITHOUT TIME ZONE,

    duracion_jornada_minutos SMALLINT NOT NULL,

    modalidad_tiempo_extra VARCHAR(30) NOT NULL,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_tipos_turno
        PRIMARY KEY (id),

    CONSTRAINT uq_tipos_turno_codigo
        UNIQUE (codigo),

    CONSTRAINT ck_tipos_turno_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_tipos_turno_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_tipos_turno_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_tipos_turno_rango_entrada
        CHECK (
            hora_entrada_desde IS NOT NULL
            OR hora_entrada_hasta IS NOT NULL
        ),

    CONSTRAINT ck_tipos_turno_duracion
        CHECK (
            duracion_jornada_minutos > 0
        ),

    CONSTRAINT ck_tipos_turno_modalidad_extra
        CHECK (
            modalidad_tiempo_extra IN (
                'ANTES_ENTRADA',
                'DESPUES_SALIDA',
                'NO_APLICA'
            )
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_tipos_turno_nombre_normalizado
ON asistencia.tipos_turno (
    LOWER(BTRIM(nombre))
);


INSERT INTO asistencia.tipos_turno (
    codigo,
    nombre,
    hora_entrada_desde,
    hora_entrada_hasta,
    duracion_jornada_minutos,
    modalidad_tiempo_extra,
    activo
)
VALUES
    (
        'MATUTINO',
        'Turno matutino',
        NULL,
        TIME '13:00',
        420,
        'DESPUES_SALIDA',
        TRUE
    ),
    (
        'VESPERTINO',
        'Turno vespertino',
        TIME '14:00',
        NULL,
        360,
        'ANTES_ENTRADA',
        TRUE
    )
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    hora_entrada_desde =
        EXCLUDED.hora_entrada_desde,
    hora_entrada_hasta =
        EXCLUDED.hora_entrada_hasta,
    duracion_jornada_minutos =
        EXCLUDED.duracion_jornada_minutos,
    modalidad_tiempo_extra =
        EXCLUDED.modalidad_tiempo_extra,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;


COMMIT;