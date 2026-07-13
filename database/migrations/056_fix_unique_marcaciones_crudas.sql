BEGIN;

-- 1. Eliminar duplicados lógicos ya existentes.
-- Conserva el primer registro y borra copias causadas por cambio de IP.
DELETE FROM asistencia.marcaciones_crudas mc
USING (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY
                dispositivo_origen,
                COALESCE(zk_uid_registro, -1),
                zk_user_id,
                fecha_hora,
                COALESCE(punch, -1),
                COALESCE(status, -1)
            ORDER BY
                (empleado_id IS NULL),
                id
        ) AS rn
    FROM asistencia.marcaciones_crudas
) duplicados
WHERE mc.id = duplicados.id
  AND duplicados.rn > 1;

-- 2. Eliminar índice anterior porque incluía dispositivo_ip.
DROP INDEX IF EXISTS asistencia.ux_marcaciones_crudas_zk_evento;

-- 3. Crear índice único lógico sin IP.
-- La IP puede cambiar; no debe formar parte de la identidad de una marcación.
CREATE UNIQUE INDEX ux_marcaciones_crudas_zk_evento
ON asistencia.marcaciones_crudas (
    dispositivo_origen,
    COALESCE(zk_uid_registro, -1),
    zk_user_id,
    fecha_hora,
    COALESCE(punch, -1),
    COALESCE(status, -1)
);

COMMIT;