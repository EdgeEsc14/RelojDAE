\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.politicas_asistencia (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(40) NOT NULL,

    version SMALLINT
        NOT NULL DEFAULT 1,

    nombre VARCHAR(120) NOT NULL,

    descripcion VARCHAR(500),

    tipo_periodo VARCHAR(20) NOT NULL,

    limite_tolerancia_segundos INTEGER NOT NULL,

    limite_retardo_menor_segundos INTEGER NOT NULL,

    limite_retardo_mayor_segundos INTEGER NOT NULL,

    puntos_retardo_menor SMALLINT
        NOT NULL DEFAULT 1,

    puntos_retardo_mayor SMALLINT
        NOT NULL DEFAULT 2,

    puntos_para_descanso SMALLINT
        NOT NULL DEFAULT 10,

    max_dias_justificables_periodo SMALLINT
        NOT NULL DEFAULT 2,

    max_puntos_descontables_por_dia SMALLINT
        NOT NULL DEFAULT 2,

    descansos_para_revision_baja SMALLINT
        NOT NULL DEFAULT 7,

    faltas_consecutivas_revision_baja SMALLINT
        NOT NULL DEFAULT 3,

    vigencia_desde DATE NOT NULL,

    vigencia_hasta DATE,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_politicas_asistencia
        PRIMARY KEY (id),

    CONSTRAINT uq_politicas_asistencia_codigo_version
        UNIQUE (
            codigo,
            version
        ),

    CONSTRAINT ck_politicas_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_politicas_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_politicas_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_politicas_version
        CHECK (
            version > 0
        ),

    CONSTRAINT ck_politicas_tipo_periodo
        CHECK (
            tipo_periodo IN (
                'QUINCENAL',
                'MENSUAL'
            )
        ),

    CONSTRAINT ck_politicas_limites_no_negativos
        CHECK (
            limite_tolerancia_segundos >= 0
            AND limite_retardo_menor_segundos >= 0
            AND limite_retardo_mayor_segundos >= 0
        ),

    CONSTRAINT ck_politicas_orden_limites
        CHECK (
            limite_tolerancia_segundos
                < limite_retardo_menor_segundos
            AND limite_retardo_menor_segundos
                < limite_retardo_mayor_segundos
        ),

    CONSTRAINT ck_politicas_puntos
        CHECK (
            puntos_retardo_menor >= 0
            AND puntos_retardo_mayor >= puntos_retardo_menor
            AND puntos_para_descanso > 0
        ),

    CONSTRAINT ck_politicas_justificantes
        CHECK (
            max_dias_justificables_periodo >= 0
            AND max_puntos_descontables_por_dia >= 0
        ),

    CONSTRAINT ck_politicas_revision_baja
        CHECK (
            descansos_para_revision_baja > 0
            AND faltas_consecutivas_revision_baja > 0
        ),

    CONSTRAINT ck_politicas_vigencia
        CHECK (
            vigencia_hasta IS NULL
            OR vigencia_hasta >= vigencia_desde
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_politicas_asistencia_nombre_version
ON asistencia.politicas_asistencia (
    LOWER(BTRIM(nombre)),
    version
);


CREATE INDEX IF NOT EXISTS
    ix_politicas_asistencia_vigencia
ON asistencia.politicas_asistencia (
    vigencia_desde,
    vigencia_hasta
);


CREATE INDEX IF NOT EXISTS
    ix_politicas_asistencia_activo
ON asistencia.politicas_asistencia (
    activo
);


INSERT INTO asistencia.politicas_asistencia (
    codigo,
    version,
    nombre,
    descripcion,
    tipo_periodo,
    limite_tolerancia_segundos,
    limite_retardo_menor_segundos,
    limite_retardo_mayor_segundos,
    puntos_retardo_menor,
    puntos_retardo_mayor,
    puntos_para_descanso,
    max_dias_justificables_periodo,
    max_puntos_descontables_por_dia,
    descansos_para_revision_baja,
    faltas_consecutivas_revision_baja,
    vigencia_desde,
    vigencia_hasta,
    activo
)
VALUES (
    'POLITICA_DAE_GENERAL',
    1,
    'Política general DAE',
    'Política base de puntualidad, retardos, faltas, justificantes y descansos obligatorios.',
    'QUINCENAL',
    659,
    1259,
    1859,
    1,
    2,
    10,
    2,
    2,
    7,
    3,
    DATE '2026-01-01',
    NULL,
    TRUE
)
ON CONFLICT (
    codigo,
    version
)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    tipo_periodo = EXCLUDED.tipo_periodo,
    limite_tolerancia_segundos = EXCLUDED.limite_tolerancia_segundos,
    limite_retardo_menor_segundos = EXCLUDED.limite_retardo_menor_segundos,
    limite_retardo_mayor_segundos = EXCLUDED.limite_retardo_mayor_segundos,
    puntos_retardo_menor = EXCLUDED.puntos_retardo_menor,
    puntos_retardo_mayor = EXCLUDED.puntos_retardo_mayor,
    puntos_para_descanso = EXCLUDED.puntos_para_descanso,
    max_dias_justificables_periodo = EXCLUDED.max_dias_justificables_periodo,
    max_puntos_descontables_por_dia = EXCLUDED.max_puntos_descontables_por_dia,
    descansos_para_revision_baja = EXCLUDED.descansos_para_revision_baja,
    faltas_consecutivas_revision_baja = EXCLUDED.faltas_consecutivas_revision_baja,
    vigencia_desde = EXCLUDED.vigencia_desde,
    vigencia_hasta = EXCLUDED.vigencia_hasta,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;

COMMIT;