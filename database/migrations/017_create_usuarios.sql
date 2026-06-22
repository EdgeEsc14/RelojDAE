\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS seguridad.usuarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    empleado_id BIGINT,

    rol_id BIGINT NOT NULL,

    correo_electronico VARCHAR(150) NOT NULL,

    password_hash TEXT,

    nombre_usuario VARCHAR(80),

    requiere_cambio_password BOOLEAN
        NOT NULL DEFAULT TRUE,

    ultimo_acceso TIMESTAMP WITH TIME ZONE,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_usuarios
        PRIMARY KEY (id),

    CONSTRAINT fk_usuarios_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_usuarios_rol
        FOREIGN KEY (rol_id)
        REFERENCES seguridad.roles (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_usuarios_correo_no_vacio
        CHECK (
            BTRIM(correo_electronico) <> ''
        ),

    CONSTRAINT ck_usuarios_correo_formato_basico
        CHECK (
            correo_electronico ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
        ),

    CONSTRAINT ck_usuarios_nombre_usuario_no_vacio
        CHECK (
            nombre_usuario IS NULL
            OR BTRIM(nombre_usuario) <> ''
        ),

    CONSTRAINT ck_usuarios_password_hash_no_vacio
        CHECK (
            password_hash IS NULL
            OR BTRIM(password_hash) <> ''
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_usuarios_correo
ON seguridad.usuarios (
    LOWER(BTRIM(correo_electronico))
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_usuarios_nombre_usuario
ON seguridad.usuarios (
    LOWER(BTRIM(nombre_usuario))
)
WHERE nombre_usuario IS NOT NULL;


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_usuarios_empleado
ON seguridad.usuarios (
    empleado_id
)
WHERE empleado_id IS NOT NULL;


CREATE INDEX IF NOT EXISTS
    ix_usuarios_rol
ON seguridad.usuarios (
    rol_id
);


CREATE INDEX IF NOT EXISTS
    ix_usuarios_activo
ON seguridad.usuarios (
    activo
);


COMMIT;