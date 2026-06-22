\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS seguridad.modulos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(50) NOT NULL,

    nombre VARCHAR(100) NOT NULL,

    descripcion VARCHAR(300),

    modulo_padre_id BIGINT,

    orden_visual SMALLINT
        NOT NULL DEFAULT 0,

    es_visible_menu BOOLEAN
        NOT NULL DEFAULT TRUE,

    es_sistema BOOLEAN
        NOT NULL DEFAULT TRUE,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_modulos
        PRIMARY KEY (id),

    CONSTRAINT uq_modulos_codigo
        UNIQUE (codigo),

    CONSTRAINT fk_modulos_padre
        FOREIGN KEY (modulo_padre_id)
        REFERENCES seguridad.modulos (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_modulos_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_modulos_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_modulos_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_modulos_orden_visual
        CHECK (
            orden_visual >= 0
        ),

    CONSTRAINT ck_modulos_no_autorreferencia
        CHECK (
            modulo_padre_id IS NULL
            OR modulo_padre_id <> id
        )
);


CREATE INDEX IF NOT EXISTS
    ix_modulos_padre
ON seguridad.modulos (
    modulo_padre_id
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_modulos_nombre_por_padre
ON seguridad.modulos (
    LOWER(BTRIM(nombre)),
    COALESCE(modulo_padre_id, 0)
);


-- =========================================================
-- Módulos principales
-- =========================================================

INSERT INTO seguridad.modulos (
    codigo,
    nombre,
    descripcion,
    modulo_padre_id,
    orden_visual,
    es_visible_menu,
    es_sistema,
    activo
)
VALUES
    (
        'DASHBOARD',
        'Dashboard',
        'Indicadores generales y resumen de asistencia.',
        NULL,
        1,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'ASISTENCIA',
        'Asistencia',
        'Consulta y procesamiento de registros de asistencia.',
        NULL,
        2,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'EMPLEADOS',
        'Empleados',
        'Administración y consulta del personal.',
        NULL,
        3,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'DISPOSITIVOS',
        'Dispositivos',
        'Administración de relojes checadores y sincronizaciones.',
        NULL,
        4,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'REPORTES',
        'Reportes',
        'Consulta y generación de reportes.',
        NULL,
        5,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'CONFIGURACION',
        'Configuración',
        'Administración general de catálogos y seguridad.',
        NULL,
        6,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'PERFIL',
        'Perfil',
        'Consulta y configuración del perfil propio.',
        NULL,
        7,
        TRUE,
        TRUE,
        TRUE
    )
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    modulo_padre_id = EXCLUDED.modulo_padre_id,
    orden_visual = EXCLUDED.orden_visual,
    es_visible_menu = EXCLUDED.es_visible_menu,
    es_sistema = EXCLUDED.es_sistema,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;


-- =========================================================
-- Submódulos de Configuración
-- =========================================================

INSERT INTO seguridad.modulos (
    codigo,
    nombre,
    descripcion,
    modulo_padre_id,
    orden_visual,
    es_visible_menu,
    es_sistema,
    activo
)
VALUES
    (
        'ORGANIZACION',
        'Organización',
        'Administración del organigrama, unidades y puestos.',
        (
            SELECT id
            FROM seguridad.modulos
            WHERE codigo = 'CONFIGURACION'
        ),
        1,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'HORARIOS',
        'Horarios',
        'Administración de turnos, jornadas y horarios.',
        (
            SELECT id
            FROM seguridad.modulos
            WHERE codigo = 'CONFIGURACION'
        ),
        2,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'POLITICAS_ASISTENCIA',
        'Políticas de asistencia',
        'Configuración de tolerancias, puntos, sanciones y periodos.',
        (
            SELECT id
            FROM seguridad.modulos
            WHERE codigo = 'CONFIGURACION'
        ),
        3,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'SEGURIDAD',
        'Seguridad',
        'Administración de usuarios, roles y permisos.',
        (
            SELECT id
            FROM seguridad.modulos
            WHERE codigo = 'CONFIGURACION'
        ),
        4,
        TRUE,
        TRUE,
        TRUE
    )
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    modulo_padre_id = EXCLUDED.modulo_padre_id,
    orden_visual = EXCLUDED.orden_visual,
    es_visible_menu = EXCLUDED.es_visible_menu,
    es_sistema = EXCLUDED.es_sistema,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;


COMMIT;