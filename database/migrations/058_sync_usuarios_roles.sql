\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

UPDATE seguridad.usuarios AS usuario
SET
    rol = LOWER(rol.codigo),
    fecha_modificacion = CURRENT_TIMESTAMP
FROM seguridad.roles AS rol
WHERE rol.id = usuario.rol_id
  AND usuario.rol IS DISTINCT FROM LOWER(rol.codigo);

COMMIT;