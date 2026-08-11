\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- ============================================================
-- 062_add_modulos_permisos_faltantes.sql
--
-- Objetivo:
-- Crear módulos que el frontend utiliza pero no existían en
-- seguridad.modulos, y poblar sus permisos por rol.
--
-- Módulos nuevos:
--   CHECADAS_CRUDAS  — Visualización de marcaciones crudas ZKTeco
--   INCIDENCIAS      — Gestión de incidencias laborales
--   AUDITORIA        — Consulta de logs y auditoría del sistema
--
-- Decisiones de diseño:
--   - HORARIOS se mantiene como submódulo de CONFIGURACION (ya funciona)
--   - USUARIOS_SISTEMA del frontend se mapea a SEGURIDAD existente
--   - CHECADAS_CRUDAS, INCIDENCIAS y AUDITORIA son top-level
--
-- Esta migración NO modifica endpoints ni código Python.
-- Solo agrega registros a seguridad.modulos y seguridad.permisos_rol.
-- ============================================================


-- =========================================================
-- 1. Insertar módulos nuevos
-- =========================================================

INSERT INTO seguridad.modulos (
    codigo,
    nombre,
    descripcion,
    modulo_padre_id,
    orden_visual,
    es_visible_menu,
    es_sistema,
    activo
)
VALUES
    (
        'CHECADAS_CRUDAS',
        'Checadas crudas',
        'Visualización y sincronización de marcaciones crudas desde dispositivos ZKTeco.',
        NULL,
        3,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'INCIDENCIAS',
        'Incidencias',
        'Gestión de incidencias laborales, justificantes y solicitudes.',
        NULL,
        4,
        TRUE,
        TRUE,
        TRUE
    ),
    (
        'AUDITORIA',
        'Auditoría',
        'Consulta de registros de auditoría, logs de acceso y trazabilidad.',
        NULL,
        8,
        TRUE,
        TRUE,
        TRUE
    )
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    modulo_padre_id = EXCLUDED.modulo_padre_id,
    orden_visual = EXCLUDED.orden_visual,
    es_visible_menu = EXCLUDED.es_visible_menu,
    es_sistema = EXCLUDED.es_sistema,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;


-- =========================================================
-- 2. Insertar permisos por rol para los módulos nuevos
--
-- Lógica:
--   SUPER_ADMIN  → TOTAL, todas las capacidades
--   RH_ADMIN     → TOTAL en CHECADAS_CRUDAS e INCIDENCIAS
--                   (consultar + crear + editar + aprobar + exportar)
--                   NINGUNO en AUDITORIA
--   SUPERVISOR   → AREA en INCIDENCIAS (consultar + exportar)
--                   NINGUNO en CHECADAS_CRUDAS y AUDITORIA
--   EMPLEADO     → PROPIO en INCIDENCIAS (solo consultar)
--                   NINGUNO en CHECADAS_CRUDAS y AUDITORIA
--   AUDITOR      → TOTAL en los tres (solo consultar + exportar)
-- =========================================================

WITH permisos_nuevos (
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
        -- SUPER_ADMIN
        ('SUPER_ADMIN', 'CHECADAS_CRUDAS', 'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'INCIDENCIAS',     'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),
        ('SUPER_ADMIN', 'AUDITORIA',       'TOTAL', TRUE, TRUE, TRUE, TRUE, TRUE, TRUE),

        -- RH_ADMIN
        ('RH_ADMIN', 'CHECADAS_CRUDAS', 'TOTAL',   TRUE, TRUE, TRUE, FALSE, FALSE, TRUE),
        ('RH_ADMIN', 'INCIDENCIAS',     'TOTAL',   TRUE, TRUE, TRUE, FALSE, TRUE, TRUE),
        ('RH_ADMIN', 'AUDITORIA',       'NINGUNO', FALSE, FALSE, FALSE, FALSE, FALSE, FALSE),

        -- SUPERVISOR
        ('SUPERVISOR', 'CHECADAS_CRUDAS', 'NINGUNO', FALSE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('SUPERVISOR', 'INCIDENCIAS',     'AREA',    TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('SUPERVISOR', 'AUDITORIA',       'NINGUNO', FALSE, FALSE, FALSE, FALSE, FALSE, FALSE),

        -- EMPLEADO
        ('EMPLEADO', 'CHECADAS_CRUDAS', 'NINGUNO', FALSE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('EMPLEADO', 'INCIDENCIAS',     'PROPIO',  TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
        ('EMPLEADO', 'AUDITORIA',       'NINGUNO', FALSE, FALSE, FALSE, FALSE, FALSE, FALSE),

        -- AUDITOR
        ('AUDITOR', 'CHECADAS_CRUDAS', 'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('AUDITOR', 'INCIDENCIAS',     'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE),
        ('AUDITOR', 'AUDITORIA',       'TOTAL', TRUE, FALSE, FALSE, FALSE, FALSE, TRUE)
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
    r.id AS rol_id,
    m.id AS modulo_id,
    pn.alcance_datos,
    pn.puede_consultar,
    pn.puede_crear,
    pn.puede_editar,
    pn.puede_eliminar,
    pn.puede_aprobar,
    pn.puede_exportar
FROM permisos_nuevos pn
INNER JOIN seguridad.roles r
    ON r.codigo = pn.rol_codigo
INNER JOIN seguridad.modulos m
    ON m.codigo = pn.modulo_codigo
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
