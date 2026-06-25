BEGIN;

UPDATE organizacion.puestos
SET
    nivel_jerarquico = 0,
    fecha_modificacion = CURRENT_TIMESTAMP
WHERE codigo = 'AUXILIAR_ADMINISTRATIVO';

WITH nuevos_puestos (
    codigo,
    nombre,
    descripcion,
    nivel_jerarquico,
    activo
) AS (
    VALUES
        (
            'ASISTENTE_ADMINISTRATIVO',
            'Asistente administrativo',
            'Puesto operativo de apoyo administrativo.',
            0,
            true
        ),
        (
            'CAPTURISTA',
            'Capturista',
            'Puesto operativo para captura y validación de información.',
            0,
            true
        ),
        (
            'ENCARGADO_AREA',
            'Encargado de área',
            'Responsable operativo de un área específica.',
            1,
            true
        ),
        (
            'COORDINADOR',
            'Coordinador',
            'Responsable de coordinación operativa o administrativa.',
            2,
            true
        ),
        (
            'JEFE_DEPARTAMENTO',
            'Jefe de departamento',
            'Responsable jerárquico de un departamento.',
            3,
            true
        ),
        (
            'JEFE_DIVISION',
            'Jefe de división',
            'Responsable jerárquico de una división.',
            4,
            true
        ),
        (
            'DIRECTOR_DAE',
            'Director DAE',
            'Responsable principal de la Dirección de Administración Escolar.',
            5,
            true
        )
)
INSERT INTO organizacion.puestos (
    id,
    codigo,
    nombre,
    descripcion,
    nivel_jerarquico,
    activo
)
SELECT
    (
        SELECT COALESCE(MAX(id), 0)
        FROM organizacion.puestos
    ) + ROW_NUMBER() OVER (ORDER BY np.codigo) AS id,
    np.codigo,
    np.nombre,
    np.descripcion,
    np.nivel_jerarquico,
    np.activo
FROM nuevos_puestos np
WHERE NOT EXISTS (
    SELECT 1
    FROM organizacion.puestos p
    WHERE p.codigo = np.codigo
);

COMMIT;
