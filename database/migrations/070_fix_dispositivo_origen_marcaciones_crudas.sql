-- 070_fix_dispositivo_origen_marcaciones_crudas.sql
--
-- Corrige el valor hardcodeado "ZKTeco" en marcaciones_crudas.dispositivo_origen
-- que fue insertado por versiones anteriores del endpoint POST /zk/attendance/sync.
--
-- El valor correcto es el codigo del dispositivo en dispositivos.dispositivos,
-- resuelto por coincidencia de IP. Esto habilita la resolución canónica de
-- identidad por dispositivo (Contrato §10, zk_employee_link_repo).
--
-- Es seguro ejecutar más de una vez (idempotente por el WHERE).

UPDATE asistencia.marcaciones_crudas mc
SET
    dispositivo_origen = d.codigo
FROM dispositivos.dispositivos d
WHERE mc.dispositivo_origen = 'ZKTeco'
  AND HOST(d.ip)            = mc.dispositivo_ip
  AND d.activo              = TRUE;
