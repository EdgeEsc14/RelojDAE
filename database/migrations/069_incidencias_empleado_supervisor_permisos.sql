-- Migración 069: Permisos de incidencias para empleado y supervisor
--
-- Flujo: el empleado registra una solicitud de incidencia (PENDIENTE)
-- desde su propia sesión; su supervisor la aprueba o rechaza.
--
-- EMPLEADO: puede_crear = TRUE  (alcance_datos = PROPIO, ya existente)
-- SUPERVISOR: puede_aprobar = TRUE (alcance_datos = AREA, ya existente)

UPDATE seguridad.permisos_rol pr
SET puede_crear = TRUE
FROM seguridad.roles r
JOIN seguridad.modulos m ON m.codigo = 'INCIDENCIAS'
WHERE pr.rol_id = r.id
  AND pr.modulo_id = m.id
  AND r.nombre = 'Empleado';

UPDATE seguridad.permisos_rol pr
SET puede_aprobar = TRUE
FROM seguridad.roles r
JOIN seguridad.modulos m ON m.codigo = 'INCIDENCIAS'
WHERE pr.rol_id = r.id
  AND pr.modulo_id = m.id
  AND r.nombre = 'Supervisor';
