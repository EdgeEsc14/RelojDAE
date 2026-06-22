\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

WITH overrides (
    rol_codigo,
    modulo_codigo,
    alcance_datos,
    puede_consultar,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_aprobar,
    puede_exportar
) AS (
    VALUES
        -- =====================================================
        -- SUPER ADMIN
        -- =====================================================
        ('SUPER_ADMIN', 'DASHBOARD', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'ASISTENCIA', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'EMPLEADOS', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'DISPOSITIVOS', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'REPORTES', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'CONFIGURACION', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'ORGANIZACION', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'HORARIOS', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'POLITICAS_ASISTENCIA', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'SEGURIDAD', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'PERFIL', 'PROPIO', TRUE, FALSE, TRUE, FALSE, FALSE, FALSE),

        -- =====================================================
        -- RH / ADMIN
        -- =====================================================
        ('RH_ADMIN', 'DASHBOARD', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('RH_ADMIN', 'ASISTENCIA', 'TOTAL', TRUE, TRUE, TRUE, FALSE, TRUE, TRUE),
        ('RH_ADMIN', 'EMPLEADOS', 'TOTAL', TRUE, TRUE, TRUE, FALSE, FALSE, TRUE),
        ('RH_ADMIN', 'DISPOSITIVOS', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('RH_ADMIN', 'REPORTES', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('RH_ADMIN', 'CONFIGURACION', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('RH_ADMIN', 'ORGANIZACION', 'TOTAL', TRUE, TRUE, TRUE, FALSE, FALSE, TRUE),
        ('RH_ADMIN', 'HORARIOS', 'TOTAL', TRUE, TRUE, TRUE, FALSE, FALSE, TRUE),
        ('RH_ADMIN', 'POLITICAS_ASISTENCIA', 'TOTAL', TRUE, TRUE, TRUE, FALSE, TRUE, TRUE),
        ('RH_ADMIN', 'SEGURIDAD', 'NINGUNO', FALSE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('RH_ADMIN', 'PERFIL', 'PROPIO', TRUE, FALSE, TRUE, FALSE, FALSE, FALSE),

        -- =====================================================
        -- SUPERVISOR
        -- =====================================================
        ('SUPERVISOR', 'DASHBOARD', 'AREA', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('SUPERVISOR', 'ASISTENCIA', 'AREA', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('SUPERVISOR', 'EMPLEADOS', 'AREA', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('SUPERVISOR', 'REPORTES', 'AREA', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('SUPERVISOR', 'PERFIL', 'PROPIO', TRUE, FALSE, TRUE, FALSE, FALSE, FALSE),

        -- =====================================================
        -- EMPLEADO
        -- =====================================================
        ('EMPLEADO', 'DASHBOARD', 'PROPIO', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('EMPLEADO', 'ASISTENCIA', 'PROPIO', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('EMPLEADO', 'EMPLEADOS', 'PROPIO', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('EMPLEADO', 'REPORTES', 'PROPIO', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('EMPLEADO', 'PERFIL', 'PROPIO', TRUE, FALSE, TRUE, FALSE, FALSE, FALSE),

        -- =====================================================
        -- AUDITOR
        -- =====================================================
        ('AUDITOR', 'DASHBOARD', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('AUDITOR', 'ASISTENCIA', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('AUDITOR', 'EMPLEADOS', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('AUDITOR', 'DISPOSITIVOS', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('AUDITOR', 'REPORTES', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('AUDITOR', 'CONFIGURACION', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('AUDITOR', 'ORGANIZACION', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('AUDITOR', 'HORARIOS', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('AUDITOR', 'POLITICAS_ASISTENCIA', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('AUDITOR', 'SEGURIDAD', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('AUDITOR', 'PERFIL', 'PROPIO', TRUE, FALSE, TRUE, FALSE, FALSE, FALSE)
),
matriz AS (
    SELECT
        rol.id AS rol_id,
        modulo.id AS modulo_id,
        COALESCE(overrides.alcance_datos, 'NINGUNO') AS alcance_datos,
        COALESCE(overrides.puede_consultar, FALSE) AS puede_consultar,
        COALESCE(overrides.puede_crear, FALSE) AS puede_crear,
        COALESCE(overrides.puede_editar, FALSE) AS puede_editar,
        COALESCE(overrides.puede_eliminar, FALSE) AS puede_eliminar,
        COALESCE(overrides.puede_aprobar, FALSE) AS puede_aprobar,
        COALESCE(overrides.puede_exportar, FALSE) AS puede_exportar
    FROM seguridad.roles AS rol
    CROSS JOIN seguridad.modulos AS modulo
    LEFT JOIN overrides
        ON overrides.rol_codigo = rol.codigo
        AND overrides.modulo_codigo = modulo.codigo
)
INSERT INTO seguridad.permisos_rol (
    rol_id,
    modulo_id,
    alcance_datos,
    puede_consultar,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_aprobar,
    puede_exportar
)
SELECT
    rol_id,
    modulo_id,
    alcance_datos,
    puede_consultar,
    puede_crear,
    puede_editar,
    puede_eliminar,
    puede_aprobar,
    puede_exportar
FROM matriz
ON CONFLICT (rol_id, modulo_id)
DO UPDATE SET
    alcance_datos = EXCLUDED.alcance_datos,
    puede_consultar = EXCLUDED.puede_consultar,
    puede_crear = EXCLUDED.puede_crear,
    puede_editar = EXCLUDED.puede_editar,
    puede_eliminar = EXCLUDED.puede_eliminar,
    puede_aprobar = EXCLUDED.puede_aprobar,
    puede_exportar = EXCLUDED.puede_exportar,
    fecha_modificacion = CURRENT_TIMESTAMP;

COMMIT;