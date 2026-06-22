\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- Eliminar el índice asociado al modelo anterior.
DROP INDEX IF EXISTS seguridad.ix_permisos_rol_nivel;


-- Eliminar la restricción y columna anteriores.
ALTER TABLE seguridad.permisos_rol
    DROP CONSTRAINT IF EXISTS
        ck_permisos_rol_nivel_acceso;


ALTER TABLE seguridad.permisos_rol
    DROP COLUMN IF EXISTS nivel_acceso;


-- =========================================================
-- Alcance de la información
-- =========================================================

ALTER TABLE seguridad.permisos_rol
    ADD COLUMN alcance_datos VARCHAR(20)
        NOT NULL DEFAULT 'NINGUNO';


-- =========================================================
-- Acciones permitidas
-- =========================================================

ALTER TABLE seguridad.permisos_rol
    ADD COLUMN puede_consultar BOOLEAN
        NOT NULL DEFAULT FALSE,

    ADD COLUMN puede_crear BOOLEAN
        NOT NULL DEFAULT FALSE,

    ADD COLUMN puede_editar BOOLEAN
        NOT NULL DEFAULT FALSE,

    ADD COLUMN puede_eliminar BOOLEAN
        NOT NULL DEFAULT FALSE,

    ADD COLUMN puede_aprobar BOOLEAN
        NOT NULL DEFAULT FALSE,

    ADD COLUMN puede_exportar BOOLEAN
        NOT NULL DEFAULT FALSE;


-- =========================================================
-- Validaciones
-- =========================================================

ALTER TABLE seguridad.permisos_rol
    ADD CONSTRAINT ck_permisos_rol_alcance
    CHECK (
        alcance_datos IN (
            'TOTAL',
            'AREA',
            'PROPIO',
            'NINGUNO'
        )
    );


ALTER TABLE seguridad.permisos_rol
    ADD CONSTRAINT ck_permisos_rol_acciones_requieren_consulta
    CHECK (
        puede_consultar = TRUE
        OR (
            puede_crear = FALSE
            AND puede_editar = FALSE
            AND puede_eliminar = FALSE
            AND puede_aprobar = FALSE
            AND puede_exportar = FALSE
        )
    );


ALTER TABLE seguridad.permisos_rol
    ADD CONSTRAINT ck_permisos_rol_sin_alcance
    CHECK (
        alcance_datos <> 'NINGUNO'
        OR (
            puede_consultar = FALSE
            AND puede_crear = FALSE
            AND puede_editar = FALSE
            AND puede_eliminar = FALSE
            AND puede_aprobar = FALSE
            AND puede_exportar = FALSE
        )
    );


CREATE INDEX ix_permisos_rol_alcance
    ON seguridad.permisos_rol (
        alcance_datos
    );


COMMIT;