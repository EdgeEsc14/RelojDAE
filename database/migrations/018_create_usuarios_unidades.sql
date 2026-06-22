\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS seguridad.usuarios_unidades (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    usuario_id BIGINT NOT NULL,

    unidad_organizacional_id BIGINT NOT NULL,

    incluye_descendientes BOOLEAN
        NOT NULL DEFAULT TRUE,

    es_principal BOOLEAN
        NOT NULL DEFAULT FALSE,

    fecha_inicio DATE
        NOT NULL DEFAULT CURRENT_DATE,

    fecha_fin DATE,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_usuarios_unidades
        PRIMARY KEY (id),

    CONSTRAINT fk_usuarios_unidades_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_usuarios_unidades_unidad
        FOREIGN KEY (unidad_organizacional_id)
        REFERENCES organizacion.unidades_organizacionales (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT uq_usuarios_unidades_periodo
        UNIQUE (
            usuario_id,
            unidad_organizacional_id,
            fecha_inicio
        ),

    CONSTRAINT ck_usuarios_unidades_fechas
        CHECK (
            fecha_fin IS NULL
            OR fecha_fin >= fecha_inicio
        )
);


CREATE INDEX IF NOT EXISTS
    ix_usuarios_unidades_usuario
ON seguridad.usuarios_unidades (
    usuario_id
);


CREATE INDEX IF NOT EXISTS
    ix_usuarios_unidades_unidad
ON seguridad.usuarios_unidades (
    unidad_organizacional_id
);


CREATE INDEX IF NOT EXISTS
    ix_usuarios_unidades_activo
ON seguridad.usuarios_unidades (
    activo
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_usuarios_unidades_principal_activa
ON seguridad.usuarios_unidades (
    usuario_id
)
WHERE es_principal = TRUE
  AND activo = TRUE;


COMMIT;