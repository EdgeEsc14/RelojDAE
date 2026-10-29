\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- ============================================================
-- 066_normalizar_puestos_dropdown.sql
--
-- Objetivo:
-- Reducir el catálogo de organizacion.puestos a las opciones
-- vigentes para el dropdown de "Puesto" del formulario de
-- empleados: Jefe de departamento, Jefe de división, Director,
-- Empleado, Asistente y Servicio Social.
--
-- Los puestos que ya no aplican (Auxiliar administrativo,
-- Capturista, Coordinador, Encargado de área) no se eliminan:
-- sus empleados se reasignan a "Empleado" y los puestos viejos
-- se desactivan (activo = false) para que dejen de listarse en
-- altas nuevas, preservando trazabilidad histórica.
-- ============================================================

-- 1. Renombrar puestos existentes que ya corresponden 1:1
UPDATE organizacion.puestos
SET nombre = 'Director',
    fecha_modificacion = CURRENT_TIMESTAMP
WHERE codigo = 'DIRECTOR_DAE';

UPDATE organizacion.puestos
SET nombre = 'Asistente',
    fecha_modificacion = CURRENT_TIMESTAMP
WHERE codigo = 'ASISTENTE_ADMINISTRATIVO';

-- 2. Crear los puestos faltantes
INSERT INTO organizacion.puestos (codigo, nombre, descripcion, nivel_jerarquico, activo)
SELECT 'EMPLEADO', 'Empleado', 'Puesto operativo general.', 0, true
WHERE NOT EXISTS (
    SELECT 1 FROM organizacion.puestos WHERE codigo = 'EMPLEADO'
);

INSERT INTO organizacion.puestos (codigo, nombre, descripcion, nivel_jerarquico, activo)
SELECT 'SERVICIO_SOCIAL', 'Servicio Social', 'Prestador de servicio social.', 0, true
WHERE NOT EXISTS (
    SELECT 1 FROM organizacion.puestos WHERE codigo = 'SERVICIO_SOCIAL'
);

-- 3. Reasignar empleados de los puestos que se retiran hacia "Empleado"
UPDATE personal.empleados e
SET puesto_id = (SELECT id FROM organizacion.puestos WHERE codigo = 'EMPLEADO')
FROM organizacion.puestos p
WHERE e.puesto_id = p.id
  AND p.codigo IN (
      'AUXILIAR_ADMINISTRATIVO',
      'CAPTURISTA',
      'COORDINADOR',
      'ENCARGADO_AREA'
  );

-- 4. Desactivar los puestos que ya no deben listarse
UPDATE organizacion.puestos
SET activo = false,
    fecha_modificacion = CURRENT_TIMESTAMP
WHERE codigo IN (
    'AUXILIAR_ADMINISTRATIVO',
    'CAPTURISTA',
    'COORDINADOR',
    'ENCARGADO_AREA'
);

COMMIT;
