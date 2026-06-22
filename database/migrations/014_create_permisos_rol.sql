\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS seguridad.permisos_rol (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    rol_id BIGINT NOT NULL,

    modulo_id BIGINT NOT NULL,

    nivel_acceso VARCHAR(20)
        NOT NULL DEFAULT 'NINGUNO',

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_permisos_rol
        PRIMARY KEY (id),

    CONSTRAINT fk_permisos_rol_rol
        FOREIGN KEY (rol_id)
        REFERENCES seguridad.roles (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_permisos_rol_modulo
        FOREIGN KEY (modulo_id)
        REFERENCES seguridad.modulos (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT uq_permisos_rol_rol_modulo
        UNIQUE (
            rol_id,
            modulo_id
        ),

    CONSTRAINT ck_permisos_rol_nivel_acceso
        CHECK (
            nivel_acceso IN (
                'TOTAL',
                'AREA',
                'PROPIO',
                'LECTURA',
                'NINGUNO'
            )
        )
);


CREATE INDEX IF NOT EXISTS
    ix_permisos_rol_rol
ON seguridad.permisos_rol (
    rol_id
);


CREATE INDEX IF NOT EXISTS
    ix_permisos_rol_modulo
ON seguridad.permisos_rol (
    modulo_id
);


CREATE INDEX IF NOT EXISTS
    ix_permisos_rol_nivel
ON seguridad.permisos_rol (
    nivel_acceso
);


COMMIT;