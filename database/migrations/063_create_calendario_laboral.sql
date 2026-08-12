\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- ============================================================
-- 063_create_calendario_laboral.sql
--
-- Objetivo:
-- Crear las tablas del módulo Calendario Laboral.
-- Fuente de verdad para determinar si una fecha es laborable
-- antes de procesar asistencia (faltas, retardos, omisiones).
--
-- Tablas:
--   asistencia.calendarios         — catálogo de calendarios
--   asistencia.calendario_eventos  — eventos/fechas del calendario
--
-- No incluye seed de festivos. Los eventos se cargan desde la
-- aplicación o mediante un seed independiente.
-- ============================================================


-- ============================================================
-- 1. Catálogo de calendarios
-- ============================================================

CREATE TABLE IF NOT EXISTS asistencia.calendarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(40) NOT NULL,

    nombre VARCHAR(150) NOT NULL,

    descripcion VARCHAR(500),

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_calendarios
        PRIMARY KEY (id),

    CONSTRAINT uq_calendarios_codigo
        UNIQUE (codigo),

    CONSTRAINT ck_calendarios_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_calendarios_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_calendarios_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_calendarios_nombre_normalizado
ON asistencia.calendarios (
    LOWER(BTRIM(nombre))
);


-- ============================================================
-- 2. Eventos del calendario
-- ============================================================

CREATE TABLE IF NOT EXISTS asistencia.calendario_eventos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    calendario_id BIGINT NOT NULL,

    nombre VARCHAR(200) NOT NULL,

    descripcion VARCHAR(700),

    -- Clasificación del evento
    tipo_evento VARCHAR(40) NOT NULL,

    -- Tipo de recurrencia
    tipo_recurrencia VARCHAR(30) NOT NULL,

    -- Fechas: usadas por FECHA_ESPECIFICA y PERIODO
    fecha_inicio DATE,
    fecha_fin DATE,

    -- Para ANUAL_FIJA (mes + dia se repiten todos los años)
    mes SMALLINT,
    dia SMALLINT,

    -- Control de asistencia
    afecta_asistencia BOOLEAN
        NOT NULL DEFAULT TRUE,

    es_laborable BOOLEAN
        NOT NULL DEFAULT FALSE,

    -- Prioridad de resolución (menor número = mayor prioridad)
    -- Permite resolver conflictos cuando coinciden múltiples eventos
    prioridad SMALLINT
        NOT NULL DEFAULT 50,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_calendario_eventos
        PRIMARY KEY (id),

    CONSTRAINT fk_calendario_eventos_calendario
        FOREIGN KEY (calendario_id)
        REFERENCES asistencia.calendarios (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_calendario_eventos_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_calendario_eventos_descripcion_no_vacia
        CHECK (
            descripcion IS NULL
            OR BTRIM(descripcion) <> ''
        ),

    CONSTRAINT ck_calendario_eventos_tipo_evento
        CHECK (
            tipo_evento IN (
                'FESTIVO_OFICIAL',
                'DESCANSO_INSTITUCIONAL',
                'DESCANSO_SINDICAL',
                'VACACIONES',
                'INHABIL_ADMINISTRATIVO',
                'SUSPENSION_LABORES',
                'LABORABLE_EXTRAORDINARIO',
                'OTRO'
            )
        ),

    CONSTRAINT ck_calendario_eventos_tipo_recurrencia
        CHECK (
            tipo_recurrencia IN (
                'FECHA_ESPECIFICA',
                'ANUAL_FIJA',
                'PERIODO'
            )
        ),

    CONSTRAINT ck_calendario_eventos_fechas_coherentes
        CHECK (
            (
                tipo_recurrencia = 'FECHA_ESPECIFICA'
                AND fecha_inicio IS NOT NULL
                AND fecha_fin IS NULL
                AND mes IS NULL
                AND dia IS NULL
            )
            OR
            (
                tipo_recurrencia = 'ANUAL_FIJA'
                AND mes IS NOT NULL
                AND dia IS NOT NULL
                AND fecha_inicio IS NULL
                AND fecha_fin IS NULL
            )
            OR
            (
                tipo_recurrencia = 'PERIODO'
                AND fecha_inicio IS NOT NULL
                AND fecha_fin IS NOT NULL
                AND fecha_fin >= fecha_inicio
                AND mes IS NULL
                AND dia IS NULL
            )
        ),

    CONSTRAINT ck_calendario_eventos_mes
        CHECK (
            mes IS NULL
            OR mes BETWEEN 1 AND 12
        ),

    CONSTRAINT ck_calendario_eventos_dia
        CHECK (
            dia IS NULL
            OR dia BETWEEN 1 AND 31
        ),

    CONSTRAINT ck_calendario_eventos_prioridad
        CHECK (
            prioridad BETWEEN 1 AND 100
        )
);


-- ============================================================
-- 3. Índices para consultas frecuentes
-- ============================================================

CREATE INDEX IF NOT EXISTS
    ix_calendario_eventos_calendario
ON asistencia.calendario_eventos (
    calendario_id
);

CREATE INDEX IF NOT EXISTS
    ix_calendario_eventos_tipo_evento
ON asistencia.calendario_eventos (
    tipo_evento
);

CREATE INDEX IF NOT EXISTS
    ix_calendario_eventos_tipo_recurrencia
ON asistencia.calendario_eventos (
    tipo_recurrencia
);

-- Para consultas de FECHA_ESPECIFICA y PERIODO por rango
CREATE INDEX IF NOT EXISTS
    ix_calendario_eventos_fecha_inicio
ON asistencia.calendario_eventos (
    fecha_inicio
)
WHERE fecha_inicio IS NOT NULL;

CREATE INDEX IF NOT EXISTS
    ix_calendario_eventos_fecha_fin
ON asistencia.calendario_eventos (
    fecha_fin
)
WHERE fecha_fin IS NOT NULL;

-- Para consultas de ANUAL_FIJA por mes+dia
CREATE INDEX IF NOT EXISTS
    ix_calendario_eventos_mes_dia
ON asistencia.calendario_eventos (
    mes,
    dia
)
WHERE mes IS NOT NULL AND dia IS NOT NULL;

-- Para filtrar solo eventos activos que afectan asistencia
CREATE INDEX IF NOT EXISTS
    ix_calendario_eventos_activo_afecta
ON asistencia.calendario_eventos (
    activo,
    afecta_asistencia
);

-- Prioridad para resolución de conflictos
CREATE INDEX IF NOT EXISTS
    ix_calendario_eventos_prioridad
ON asistencia.calendario_eventos (
    prioridad
);


-- ============================================================
-- 4. Insertar calendario institucional base (contenedor vacío)
-- ============================================================
-- Se crea un calendario vacío como contenedor.
-- Los eventos se cargan posteriormente desde la aplicación.

INSERT INTO asistencia.calendarios (
    codigo,
    nombre,
    descripcion,
    activo
)
VALUES (
    'CALENDARIO_DAE',
    'Calendario Laboral DAE',
    'Calendario institucional de la Dirección de Administración Escolar. Contiene festivos, vacaciones, días inhábiles y excepciones laborales.',
    TRUE
)
ON CONFLICT (codigo) DO NOTHING;


COMMIT;
