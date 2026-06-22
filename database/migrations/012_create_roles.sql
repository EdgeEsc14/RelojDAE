\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE SCHEMA IF NOT EXISTS seguridad
    AUTHORIZATION reloj_app;


CREATE TABLE IF NOT EXISTS seguridad.roles (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(40) NOT NULL,

    nombre VARCHAR(80) NOT NULL,

    descripcion VARCHAR(300),

    es_sistema BOOLEAN
        NOT NULL DEFAULT FALSE,

    orden_visual SMALLINT
        NOT NULL DEFAULT 0,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_roles
        PRIMARY KEY (id),

    CONSTRAINT uq_roles_codigo
        UNIQUE (codigo),

    CONSTRAINT ck_roles_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_roles_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_roles_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_roles_orden_visual
        CHECK (
            orden_visual >= 0
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_roles_nombre_normalizado
ON seguridad.roles (
    LOWER(BTRIM(nombre))
);


INSERT INTO seguridad.roles (
    codigo,
    nombre,
    descripcion,
    es_sistema,
    orden_visual,
    activo
)
VALUES
    (
        'SUPER_ADMIN',
        'Super Admin',
        'Control total del sistema, seguridad y configuración.',
        TRUE,
        1,
        TRUE
    ),
    (
        'RH_ADMIN',
        'RH/Admin',
        'Administración de empleados, horarios, incidencias y asistencia.',
        TRUE,
        2,
        TRUE
    ),
    (
        'SUPERVISOR',
        'Supervisor',
        'Consulta y gestión limitada al ámbito organizacional asignado.',
        TRUE,
        3,
        TRUE
    ),
    (
        'EMPLEADO',
        'Empleado',
        'Consulta de información y asistencia propia.',
        TRUE,
        4,
        TRUE
    ),
    (
        'AUDITOR',
        'Auditor',
        'Consulta de información sin permisos de modificación.',
        TRUE,
        5,
        TRUE
    )
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    es_sistema = EXCLUDED.es_sistema,
    orden_visual = EXCLUDED.orden_visual,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;


COMMIT;