BEGIN;

CREATE TABLE IF NOT EXISTS organizacion.puestos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(40) NOT NULL,

    nombre VARCHAR(120) NOT NULL,

    descripcion VARCHAR(500),

    nivel_jerarquico SMALLINT
        NOT NULL DEFAULT 0,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_puestos
        PRIMARY KEY (id),

    CONSTRAINT uq_puestos_codigo
        UNIQUE (codigo),

    CONSTRAINT ck_puestos_codigo_no_vacio
        CHECK (BTRIM(codigo) <> ''),

    CONSTRAINT ck_puestos_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_puestos_nombre_no_vacio
        CHECK (BTRIM(nombre) <> ''),

    CONSTRAINT ck_puestos_nivel_jerarquico
        CHECK (nivel_jerarquico >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_puestos_nombre_normalizado
ON organizacion.puestos (
    LOWER(BTRIM(nombre))
);

COMMIT;