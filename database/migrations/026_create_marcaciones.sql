\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.marcaciones (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    dispositivo_id BIGINT NOT NULL,

    empleado_dispositivo_id BIGINT,

    empleado_id BIGINT,

    tipo_marcacion_id BIGINT NOT NULL,

    fecha_hora TIMESTAMP WITH TIME ZONE NOT NULL,

    fecha DATE NOT NULL,

    zk_user_id VARCHAR(50) NOT NULL,

    zk_uid INTEGER,

    punch_original INTEGER,

    estado_verificacion INTEGER,

    codigo_trabajo VARCHAR(80),

    origen VARCHAR(30)
        NOT NULL DEFAULT 'ZKTECO',

    raw_data JSONB,

    procesada BOOLEAN
        NOT NULL DEFAULT FALSE,

    fecha_procesamiento TIMESTAMP WITH TIME ZONE,

    observaciones VARCHAR(500),

    fecha_sincronizacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_marcaciones
        PRIMARY KEY (id),

    CONSTRAINT fk_marcaciones_dispositivo
        FOREIGN KEY (dispositivo_id)
        REFERENCES dispositivos.dispositivos (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_marcaciones_empleado_dispositivo
        FOREIGN KEY (empleado_dispositivo_id)
        REFERENCES dispositivos.empleado_dispositivo (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_marcaciones_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_marcaciones_tipo_marcacion
        FOREIGN KEY (tipo_marcacion_id)
        REFERENCES asistencia.tipos_marcacion (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_marcaciones_zk_user_id_no_vacio
        CHECK (
            BTRIM(zk_user_id) <> ''
        ),

    CONSTRAINT ck_marcaciones_zk_uid
        CHECK (
            zk_uid IS NULL
            OR zk_uid > 0
        ),

    CONSTRAINT ck_marcaciones_punch_original
        CHECK (
            punch_original IS NULL
            OR punch_original >= 0
        ),

    CONSTRAINT ck_marcaciones_estado_verificacion
        CHECK (
            estado_verificacion IS NULL
            OR estado_verificacion >= 0
        ),

    CONSTRAINT ck_marcaciones_origen
        CHECK (
            origen IN (
                'ZKTECO',
                'MANUAL',
                'IMPORTACION',
                'API'
            )
        ),

    CONSTRAINT ck_marcaciones_codigo_trabajo_no_vacio
        CHECK (
            codigo_trabajo IS NULL
            OR BTRIM(codigo_trabajo) <> ''
        ),

    CONSTRAINT ck_marcaciones_observaciones_no_vacias
        CHECK (
            observaciones IS NULL
            OR BTRIM(observaciones) <> ''
        ),

    CONSTRAINT ck_marcaciones_procesamiento
        CHECK (
            (
                procesada = TRUE
                AND fecha_procesamiento IS NOT NULL
            )
            OR
            (
                procesada = FALSE
            )
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_marcaciones_dispositivo_usuario_fecha_punch
ON asistencia.marcaciones (
    dispositivo_id,
    zk_user_id,
    fecha_hora,
    COALESCE(punch_original, -1)
);


CREATE INDEX IF NOT EXISTS
    ix_marcaciones_dispositivo
ON asistencia.marcaciones (
    dispositivo_id
);


CREATE INDEX IF NOT EXISTS
    ix_marcaciones_empleado
ON asistencia.marcaciones (
    empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_marcaciones_empleado_dispositivo
ON asistencia.marcaciones (
    empleado_dispositivo_id
);


CREATE INDEX IF NOT EXISTS
    ix_marcaciones_tipo
ON asistencia.marcaciones (
    tipo_marcacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_marcaciones_fecha
ON asistencia.marcaciones (
    fecha
);


CREATE INDEX IF NOT EXISTS
    ix_marcaciones_fecha_hora
ON asistencia.marcaciones (
    fecha_hora
);


CREATE INDEX IF NOT EXISTS
    ix_marcaciones_procesada
ON asistencia.marcaciones (
    procesada
);


COMMIT;