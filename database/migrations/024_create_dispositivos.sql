\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE SCHEMA IF NOT EXISTS dispositivos
    AUTHORIZATION reloj_app;


CREATE TABLE IF NOT EXISTS dispositivos.dispositivos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo VARCHAR(40) NOT NULL,

    nombre VARCHAR(120) NOT NULL,

    ip INET NOT NULL,

    puerto INTEGER NOT NULL DEFAULT 4370,

    password_comunicacion INTEGER NOT NULL DEFAULT 0,

    numero_serie VARCHAR(100),

    modelo VARCHAR(100),

    firmware VARCHAR(150),

    ubicacion VARCHAR(200),

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    ultima_conexion TIMESTAMP WITH TIME ZONE,

    ultima_sincronizacion TIMESTAMP WITH TIME ZONE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_dispositivos
        PRIMARY KEY (id),

    CONSTRAINT uq_dispositivos_codigo
        UNIQUE (codigo),

    CONSTRAINT uq_dispositivos_ip_puerto
        UNIQUE (ip, puerto),

    CONSTRAINT uq_dispositivos_numero_serie
        UNIQUE (numero_serie),

    CONSTRAINT ck_dispositivos_codigo_no_vacio
        CHECK (
            BTRIM(codigo) <> ''
        ),

    CONSTRAINT ck_dispositivos_codigo_formato
        CHECK (
            codigo = UPPER(BTRIM(codigo))
            AND codigo ~ '^[A-Z0-9_]+$'
        ),

    CONSTRAINT ck_dispositivos_nombre_no_vacio
        CHECK (
            BTRIM(nombre) <> ''
        ),

    CONSTRAINT ck_dispositivos_puerto
        CHECK (
            puerto BETWEEN 1 AND 65535
        ),

    CONSTRAINT ck_dispositivos_password_comunicacion
        CHECK (
            password_comunicacion >= 0
        ),

    CONSTRAINT ck_dispositivos_numero_serie_no_vacio
        CHECK (
            numero_serie IS NULL
            OR BTRIM(numero_serie) <> ''
        )
);


CREATE INDEX IF NOT EXISTS
    ix_dispositivos_activo
ON dispositivos.dispositivos (
    activo
);


CREATE TABLE IF NOT EXISTS dispositivos.empleado_dispositivo (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    empleado_id BIGINT NOT NULL,

    dispositivo_id BIGINT NOT NULL,

    zk_uid INTEGER,

    zk_user_id VARCHAR(50) NOT NULL,

    nombre_en_dispositivo VARCHAR(150),

    privilegio INTEGER,

    password_reloj VARCHAR(100),

    grupo VARCHAR(50),

    tarjeta VARCHAR(80),

    sincronizado BOOLEAN
        NOT NULL DEFAULT FALSE,

    fecha_ultima_sincronizacion TIMESTAMP WITH TIME ZONE,

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_empleado_dispositivo
        PRIMARY KEY (id),

    CONSTRAINT fk_empleado_dispositivo_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_empleado_dispositivo_dispositivo
        FOREIGN KEY (dispositivo_id)
        REFERENCES dispositivos.dispositivos (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_empleado_dispositivo_zk_user_id_no_vacio
        CHECK (
            BTRIM(zk_user_id) <> ''
        ),

    CONSTRAINT ck_empleado_dispositivo_zk_uid
        CHECK (
            zk_uid IS NULL
            OR zk_uid > 0
        ),

    CONSTRAINT ck_empleado_dispositivo_privilegio
        CHECK (
            privilegio IS NULL
            OR privilegio >= 0
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_empleado_dispositivo_zk_user_id_activo
ON dispositivos.empleado_dispositivo (
    dispositivo_id,
    zk_user_id
)
WHERE activo = TRUE;


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_empleado_dispositivo_zk_uid_activo
ON dispositivos.empleado_dispositivo (
    dispositivo_id,
    zk_uid
)
WHERE activo = TRUE
  AND zk_uid IS NOT NULL;


CREATE INDEX IF NOT EXISTS
    ix_empleado_dispositivo_empleado
ON dispositivos.empleado_dispositivo (
    empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_empleado_dispositivo_dispositivo
ON dispositivos.empleado_dispositivo (
    dispositivo_id
);


CREATE INDEX IF NOT EXISTS
    ix_empleado_dispositivo_activo
ON dispositivos.empleado_dispositivo (
    activo
);


INSERT INTO dispositivos.dispositivos (
    codigo,
    nombre,
    ip,
    puerto,
    password_comunicacion,
    modelo,
    firmware,
    ubicacion,
    activo
)
VALUES (
    'ZK_PRINCIPAL',
    'Reloj checador principal',
    INET '10.254.26.251',
    4370,
    0,
    'ZKTeco',
    'Ver 6.60 May 14 2018',
    'Acceso principal',
    TRUE
)
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    ip = EXCLUDED.ip,
    puerto = EXCLUDED.puerto,
    password_comunicacion = EXCLUDED.password_comunicacion,
    modelo = EXCLUDED.modelo,
    firmware = EXCLUDED.firmware,
    ubicacion = EXCLUDED.ubicacion,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;


COMMIT;