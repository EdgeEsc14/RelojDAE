\set ON_ERROR_STOP on

BEGIN;

-- =========================================================
-- 1. Catálogo de tipos de unidad organizacional
-- =========================================================

CREATE TABLE IF NOT EXISTS organizacion.tipos_unidad (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(30) NOT NULL,

    nombre VARCHAR(80) NOT NULL,

    descripcion VARCHAR(300),

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_tipos_unidad
        PRIMARY KEY (id),

    CONSTRAINT uq_tipos_unidad_codigo
        UNIQUE (codigo),

    CONSTRAINT ck_tipos_unidad_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_tipos_unidad_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_tipos_unidad_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_tipos_unidad_nombre_normalizado
ON organizacion.tipos_unidad (
    LOWER(BTRIM(nombre))
);


-- =========================================================
-- 2. Tipos iniciales
-- =========================================================

INSERT INTO organizacion.tipos_unidad (
    codigo,
    nombre,
    descripcion
)
VALUES
    (
        'DIRECCION',
        'Dirección',
        'Unidad organizacional de nivel directivo.'
    ),
    (
        'DIVISION',
        'División',
        'Unidad organizacional que agrupa departamentos.'
    ),
    (
        'DEPARTAMENTO',
        'Departamento',
        'Unidad operativa o administrativa.'
    ),
    (
        'COMITE',
        'Comité',
        'Órgano colegiado o grupo institucional.'
    ),
    (
        'ENCARGADURIA',
        'Encargaduría',
        'Unidad o función bajo responsabilidad de una persona encargada.'
    )
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    activo = TRUE,
    fecha_modificacion = CURRENT_TIMESTAMP;


-- =========================================================
-- 3. Renombrar departamentos
-- =========================================================

ALTER TABLE organizacion.departamentos
    RENAME TO unidades_organizacionales;


ALTER SEQUENCE IF EXISTS
    organizacion.departamentos_id_seq
RENAME TO unidades_organizacionales_id_seq;


ALTER TABLE organizacion.unidades_organizacionales
    RENAME COLUMN departamento_padre_id
    TO unidad_padre_id;


-- =========================================================
-- 4. Nuevas columnas organizacionales
-- =========================================================

ALTER TABLE organizacion.unidades_organizacionales
    ADD COLUMN tipo_unidad_id BIGINT;


ALTER TABLE organizacion.unidades_organizacionales
    ADD COLUMN clave_organica VARCHAR(20);


ALTER TABLE organizacion.unidades_organizacionales
    ADD COLUMN orden_visual SMALLINT
        NOT NULL DEFAULT 0;


-- =========================================================
-- 5. Clasificación provisional de datos existentes
-- =========================================================

UPDATE organizacion.unidades_organizacionales AS unidad
SET tipo_unidad_id = tipo.id
FROM organizacion.tipos_unidad AS tipo
WHERE tipo.codigo = CASE
    WHEN unidad.codigo = 'DIRECCION_GENERAL'
        THEN 'DIRECCION'

    WHEN unidad.codigo = 'ADMINISTRACION'
        THEN 'DIVISION'

    ELSE 'DEPARTAMENTO'
END;


ALTER TABLE organizacion.unidades_organizacionales
    ALTER COLUMN tipo_unidad_id SET NOT NULL;


-- =========================================================
-- 6. Restricciones nuevas
-- =========================================================

ALTER TABLE organizacion.unidades_organizacionales
    ADD CONSTRAINT fk_unidades_tipo
    FOREIGN KEY (tipo_unidad_id)
    REFERENCES organizacion.tipos_unidad (id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT;


ALTER TABLE organizacion.unidades_organizacionales
    ADD CONSTRAINT ck_unidades_clave_organica_no_vacia
    CHECK (
        clave_organica IS NULL
        OR BTRIM(clave_organica) <> ''
    );


ALTER TABLE organizacion.unidades_organizacionales
    ADD CONSTRAINT ck_unidades_orden_visual
    CHECK (
        orden_visual >= 0
    );


-- =========================================================
-- 7. Renombrar restricciones existentes
-- =========================================================

ALTER TABLE organizacion.unidades_organizacionales
    RENAME CONSTRAINT pk_departamentos
    TO pk_unidades_organizacionales;


ALTER TABLE organizacion.unidades_organizacionales
    RENAME CONSTRAINT uq_departamentos_codigo
    TO uq_unidades_codigo;


ALTER TABLE organizacion.unidades_organizacionales
    RENAME CONSTRAINT fk_departamentos_padre
    TO fk_unidades_padre;


ALTER TABLE organizacion.unidades_organizacionales
    RENAME CONSTRAINT ck_departamentos_codigo_no_vacio
    TO ck_unidades_codigo_no_vacio;


ALTER TABLE organizacion.unidades_organizacionales
    RENAME CONSTRAINT ck_departamentos_nombre_no_vacio
    TO ck_unidades_nombre_no_vacio;


ALTER TABLE organizacion.unidades_organizacionales
    RENAME CONSTRAINT ck_departamentos_no_autorreferencia
    TO ck_unidades_no_autorreferencia;


-- =========================================================
-- 8. Renombrar índices existentes
-- =========================================================

ALTER INDEX organizacion.ix_departamentos_padre
    RENAME TO ix_unidades_padre;


ALTER INDEX organizacion.uq_departamentos_nombre_por_padre
    RENAME TO uq_unidades_nombre_por_padre;


CREATE INDEX ix_unidades_tipo
    ON organizacion.unidades_organizacionales (
        tipo_unidad_id
    );


CREATE INDEX ix_unidades_clave_organica
    ON organizacion.unidades_organizacionales (
        clave_organica
    )
    WHERE clave_organica IS NOT NULL;


-- =========================================================
-- 9. Actualizar relación de empleados
-- =========================================================

ALTER TABLE personal.empleados
    RENAME COLUMN departamento_id
    TO unidad_organizacional_id;


ALTER TABLE personal.empleados
    RENAME CONSTRAINT fk_empleados_departamento
    TO fk_empleados_unidad_organizacional;


ALTER INDEX personal.ix_empleados_departamento
    RENAME TO ix_empleados_unidad_organizacional;


COMMIT;