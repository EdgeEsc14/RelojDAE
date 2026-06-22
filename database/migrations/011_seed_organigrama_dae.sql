\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;
ALTER TABLE organizacion.unidades_organizacionales
    ALTER COLUMN codigo TYPE VARCHAR(80);
-- Evita reemplazar el organigrama si ya existen empleados.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM personal.empleados
    ) THEN
        RAISE EXCEPTION
            'No se puede reemplazar el organigrama porque ya existen empleados registrados.';
    END IF;
END
$$;


-- Eliminar solamente las unidades provisionales.
DELETE FROM organizacion.unidades_organizacionales;


-- Reiniciar la identidad porque todavía no existen empleados.
ALTER TABLE organizacion.unidades_organizacionales
    ALTER COLUMN id RESTART WITH 1;


-- =========================================================
-- DIRECCIÓN PRINCIPAL
-- =========================================================

INSERT INTO organizacion.unidades_organizacionales (
    codigo,
    nombre,
    descripcion,
    tipo_unidad_id,
    clave_organica,
    unidad_padre_id,
    orden_visual,
    activo
)
VALUES (
    'DAE',
    'Dirección de Administración Escolar',
    'Unidad directiva principal de la Dirección de Administración Escolar.',
    (
        SELECT id
        FROM organizacion.tipos_unidad
        WHERE codigo = 'DIRECCION'
    ),
    'M33',
    NULL,
    1,
    TRUE
);


-- =========================================================
-- UNIDADES DIRECTAMENTE DEPENDIENTES DE LA DIRECCIÓN
-- =========================================================

INSERT INTO organizacion.unidades_organizacionales (
    codigo,
    nombre,
    descripcion,
    tipo_unidad_id,
    clave_organica,
    unidad_padre_id,
    orden_visual,
    activo
)
VALUES
    (
        'COMITE_INTERNO_PROYECTOS',
        'Comité Interno de Proyectos',
        'Comité interno dependiente de la Dirección de Administración Escolar.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'COMITE'
        ),
        NULL,
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DAE'
        ),
        1,
        TRUE
    ),
    (
        'ENCARGADO_ACUERDOS',
        'Encargado de Acuerdos',
        'Unidad responsable del seguimiento de acuerdos de la Dirección.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'ENCARGADURIA'
        ),
        'O33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DAE'
        ),
        2,
        TRUE
    ),
    (
        'DIV_ADMISION_CONTROL_ESCOLAR',
        'División de Admisión y Control Escolar',
        'División responsable de los procesos de admisión y control escolar.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DIVISION'
        ),
        'N33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DAE'
        ),
        3,
        TRUE
    ),
    (
        'DIV_REGISTRO_CERTIFICACION_ESTUDIOS',
        'División de Registro y Certificación de Estudios',
        'División responsable del registro y certificación de estudios.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DIVISION'
        ),
        'N33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DAE'
        ),
        4,
        TRUE
    ),
    (
        'DEP_SERVICIOS_ADMINISTRATIVOS',
        'Departamento de Servicios Administrativos',
        'Departamento responsable de los servicios administrativos.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DEPARTAMENTO'
        ),
        'O32',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DAE'
        ),
        5,
        TRUE
    );


-- =========================================================
-- DEPARTAMENTOS DE ADMISIÓN Y CONTROL ESCOLAR
-- =========================================================

INSERT INTO organizacion.unidades_organizacionales (
    codigo,
    nombre,
    descripcion,
    tipo_unidad_id,
    clave_organica,
    unidad_padre_id,
    orden_visual,
    activo
)
VALUES
    (
        'DEP_ADMISION_ESCOLAR',
        'Departamento de Admisión Escolar',
        'Departamento adscrito a la División de Admisión y Control Escolar.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DEPARTAMENTO'
        ),
        'O33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DIV_ADMISION_CONTROL_ESCOLAR'
        ),
        1,
        TRUE
    ),
    (
        'DEP_CONTROL_DOCUMENTAL',
        'Departamento de Control Documental',
        'Departamento adscrito a la División de Admisión y Control Escolar.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DEPARTAMENTO'
        ),
        'O33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DIV_ADMISION_CONTROL_ESCOLAR'
        ),
        2,
        TRUE
    ),
    (
        'DEP_ATENCION_PLANTELES_RVOE',
        'Departamento de Atención a Planteles con RVOE',
        'Departamento responsable de la atención a planteles con RVOE.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DEPARTAMENTO'
        ),
        'O33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DIV_ADMISION_CONTROL_ESCOLAR'
        ),
        3,
        TRUE
    );


-- =========================================================
-- DEPARTAMENTOS DE REGISTRO Y CERTIFICACIÓN
-- =========================================================

INSERT INTO organizacion.unidades_organizacionales (
    codigo,
    nombre,
    descripcion,
    tipo_unidad_id,
    clave_organica,
    unidad_padre_id,
    orden_visual,
    activo
)
VALUES
    (
        'DEP_CERTIFICACION',
        'Departamento de Certificación',
        'Departamento adscrito a la División de Registro y Certificación de Estudios.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DEPARTAMENTO'
        ),
        'O33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DIV_REGISTRO_CERTIFICACION_ESTUDIOS'
        ),
        1,
        TRUE
    ),
    (
        'DEP_REGISTRO_SUPERVISION_ESCOLAR',
        'Departamento de Registro y Supervisión Escolar',
        'Departamento responsable del registro y la supervisión escolar.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DEPARTAMENTO'
        ),
        'O33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DIV_REGISTRO_CERTIFICACION_ESTUDIOS'
        ),
        2,
        TRUE
    ),
    (
        'DEP_INFORMATICA_ESTADISTICA_ESCOLAR',
        'Departamento de Informática y Estadística Escolar',
        'Departamento responsable de informática y estadística escolar.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DEPARTAMENTO'
        ),
        'O33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DIV_REGISTRO_CERTIFICACION_ESTUDIOS'
        ),
        3,
        TRUE
    ),
    (
        'DEP_EQUIVALENCIA_REVALIDACION_ESTUDIOS',
        'Departamento de Equivalencia y Revalidación de Estudios',
        'Departamento responsable de equivalencia y revalidación de estudios.',
        (
            SELECT id
            FROM organizacion.tipos_unidad
            WHERE codigo = 'DEPARTAMENTO'
        ),
        'O33',
        (
            SELECT id
            FROM organizacion.unidades_organizacionales
            WHERE codigo = 'DIV_REGISTRO_CERTIFICACION_ESTUDIOS'
        ),
        4,
        TRUE
    );


COMMIT;