BEGIN;

-- ============================================================
-- 052_create_marcaciones_crudas.sql
-- Objetivo:
-- Guardar una copia cruda de las marcaciones leídas desde el reloj ZKTeco.
--
-- Esta tabla representa evidencia original descargada del dispositivo.
-- No debe editarse manualmente para corregir asistencia.
-- Las correcciones deben hacerse mediante incidencias o reprocesamiento.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS asistencia;

CREATE TABLE IF NOT EXISTS asistencia.marcaciones_crudas (
    id BIGSERIAL PRIMARY KEY,

    -- Identificación del dispositivo origen
    dispositivo_origen VARCHAR(100) NOT NULL DEFAULT 'ZKTeco',
    dispositivo_ip VARCHAR(50),

    -- Identificadores crudos del reloj
    zk_uid_registro INTEGER,
    zk_user_id VARCHAR(50) NOT NULL,

    -- Fecha y hora original de la marcación
    fecha_hora TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    fecha DATE GENERATED ALWAYS AS (fecha_hora::date) STORED,
    hora TIME WITHOUT TIME ZONE GENERATED ALWAYS AS (fecha_hora::time) STORED,

    -- Códigos originales del reloj
    punch INTEGER,
    punch_label VARCHAR(100),
    status INTEGER,
    status_label VARCHAR(150),

    -- Relación lógica opcional contra empleados
    empleado_id INTEGER,
    codigo_empleado VARCHAR(50),

    -- Payload original normalizado para auditoría
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Control de sincronización
    sync_run_id VARCHAR(100),
    sincronizado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE asistencia.marcaciones_crudas IS
'Marcaciones crudas leídas desde relojes ZKTeco. Evidencia original para procesamiento de asistencia.';

COMMENT ON COLUMN asistencia.marcaciones_crudas.zk_uid_registro IS
'Identificador interno del registro/marcación devuelto por pyzk. No es el UID del usuario.';

COMMENT ON COLUMN asistencia.marcaciones_crudas.zk_user_id IS
'User ID del usuario en el reloj ZKTeco. Se vincula contra personal.empleados.zk_user_id.';

COMMENT ON COLUMN asistencia.marcaciones_crudas.fecha_hora IS
'Fecha y hora original de la marcación registrada por el reloj.';

COMMENT ON COLUMN asistencia.marcaciones_crudas.raw_payload IS
'Payload crudo normalizado leído desde el reloj para auditoría.';

-- Índice único para evitar duplicados.
-- Se usa índice único con expresiones porque PostgreSQL no permite COALESCE()
-- dentro de un UNIQUE CONSTRAINT tradicional en CREATE TABLE.
CREATE UNIQUE INDEX IF NOT EXISTS ux_marcaciones_crudas_zk_evento
ON asistencia.marcaciones_crudas (
    dispositivo_origen,
    (COALESCE(dispositivo_ip, '')),
    (COALESCE(zk_uid_registro, -1)),
    zk_user_id,
    fecha_hora,
    (COALESCE(punch, -1)),
    (COALESCE(status, -1))
);

CREATE INDEX IF NOT EXISTS ix_marcaciones_crudas_fecha_hora
ON asistencia.marcaciones_crudas (fecha_hora DESC);

CREATE INDEX IF NOT EXISTS ix_marcaciones_crudas_zk_user_id
ON asistencia.marcaciones_crudas (zk_user_id);

CREATE INDEX IF NOT EXISTS ix_marcaciones_crudas_fecha
ON asistencia.marcaciones_crudas (fecha);

CREATE INDEX IF NOT EXISTS ix_marcaciones_crudas_codigo_empleado
ON asistencia.marcaciones_crudas (codigo_empleado);

COMMIT;