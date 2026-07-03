BEGIN;

-- ============================================================
-- 051_add_zk_user_id_to_empleados.sql
-- Objetivo:
-- Agregar el identificador de usuario ZKTeco a personal.empleados.
--
-- Este campo permite vincular:
-- personal.empleados.zk_user_id = ZKTeco User ID
--
-- Nota:
-- zk_user_id NO es el UID interno del reloj.
-- Es el User ID visible del usuario dentro del dispositivo ZKTeco.
-- ============================================================

ALTER TABLE personal.empleados
ADD COLUMN IF NOT EXISTS zk_user_id VARCHAR(50);

COMMENT ON COLUMN personal.empleados.zk_user_id IS
'Identificador User ID del empleado en el reloj ZKTeco. No corresponde al UID interno del dispositivo.';

CREATE UNIQUE INDEX IF NOT EXISTS ux_empleados_zk_user_id
ON personal.empleados (zk_user_id)
WHERE zk_user_id IS NOT NULL
  AND btrim(zk_user_id) <> '';

COMMIT;