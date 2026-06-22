\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS dispositivos.sincronizaciones (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    dispositivo_id BIGINT NOT NULL,

    tipo_sincronizacion VARCHAR(40)
        NOT NULL DEFAULT 'MARCACIONES',

    fecha_inicio TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_fin TIMESTAMP WITH TIME ZONE,

    estatus VARCHAR(30)
        NOT NULL DEFAULT 'EN_PROCESO',

    registros_leidos INTEGER
        NOT NULL DEFAULT 0,

    registros_nuevos INTEGER
        NOT NULL DEFAULT 0,

    registros_duplicados INTEGER
        NOT NULL DEFAULT 0,

    registros_actualizados INTEGER
        NOT NULL DEFAULT 0,

    registros_error INTEGER
        NOT NULL DEFAULT 0,

    mensaje_error VARCHAR(1000),

    detalle JSONB,

    ejecutada_por_usuario_id BIGINT,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_sincronizaciones
        PRIMARY KEY (id),

    CONSTRAINT fk_sincronizaciones_dispositivo
        FOREIGN KEY (dispositivo_id)
        REFERENCES dispositivos.dispositivos (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_sincronizaciones_usuario
        FOREIGN KEY (ejecutada_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT ck_sincronizaciones_tipo
        CHECK (
            tipo_sincronizacion IN (
                'MARCACIONES',
                'USUARIOS',
                'CONFIGURACION',
                'COMPLETA'
            )
        ),

    CONSTRAINT ck_sincronizaciones_estatus
        CHECK (
            estatus IN (
                'EN_PROCESO',
                'EXITOSA',
                'PARCIAL',
                'ERROR',
                'CANCELADA'
            )
        ),

    CONSTRAINT ck_sincronizaciones_fechas
        CHECK (
            fecha_fin IS NULL
            OR fecha_fin >= fecha_inicio
        ),

    CONSTRAINT ck_sincronizaciones_contadores
        CHECK (
            registros_leidos >= 0
            AND registros_nuevos >= 0
            AND registros_duplicados >= 0
            AND registros_actualizados >= 0
            AND registros_error >= 0
        ),

    CONSTRAINT ck_sincronizaciones_error
        CHECK (
            (
                estatus = 'ERROR'
                AND mensaje_error IS NOT NULL
                AND BTRIM(mensaje_error) <> ''
            )
            OR
            (
                estatus <> 'ERROR'
            )
        ),

    CONSTRAINT ck_sincronizaciones_mensaje_error_no_vacio
        CHECK (
            mensaje_error IS NULL
            OR BTRIM(mensaje_error) <> ''
        )
);


CREATE INDEX IF NOT EXISTS
    ix_sincronizaciones_dispositivo
ON dispositivos.sincronizaciones (
    dispositivo_id
);


CREATE INDEX IF NOT EXISTS
    ix_sincronizaciones_tipo
ON dispositivos.sincronizaciones (
    tipo_sincronizacion
);


CREATE INDEX IF NOT EXISTS
    ix_sincronizaciones_estatus
ON dispositivos.sincronizaciones (
    estatus
);


CREATE INDEX IF NOT EXISTS
    ix_sincronizaciones_fecha_inicio
ON dispositivos.sincronizaciones (
    fecha_inicio
);


ALTER TABLE asistencia.marcaciones
    ADD COLUMN IF NOT EXISTS sincronizacion_id BIGINT;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_marcaciones_sincronizacion'
          AND conrelid = 'asistencia.marcaciones'::regclass
    ) THEN
        ALTER TABLE asistencia.marcaciones
            ADD CONSTRAINT fk_marcaciones_sincronizacion
            FOREIGN KEY (sincronizacion_id)
            REFERENCES dispositivos.sincronizaciones (id)
            ON UPDATE RESTRICT
            ON DELETE SET NULL;
    END IF;
END $$;


CREATE INDEX IF NOT EXISTS
    ix_marcaciones_sincronizacion
ON asistencia.marcaciones (
    sincronizacion_id
);


CREATE TABLE IF NOT EXISTS asistencia.descansos_obligatorios (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    empleado_id BIGINT NOT NULL,

    periodo_evaluacion_id BIGINT NOT NULL,

    resumen_periodo_empleado_id BIGINT,

    incidencia_id BIGINT,

    numero_descanso_periodo SMALLINT
        NOT NULL DEFAULT 1,

    numero_descanso_historico INTEGER,

    puntos_efectivos_periodo SMALLINT NOT NULL,

    fecha_generacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_programada DATE,

    fecha_aplicacion DATE,

    estatus VARCHAR(30)
        NOT NULL DEFAULT 'PENDIENTE',

    requiere_revision_baja BOOLEAN
        NOT NULL DEFAULT FALSE,

    motivo_revision_baja VARCHAR(700),

    generado_por_usuario_id BIGINT,

    programado_por_usuario_id BIGINT,

    aplicado_por_usuario_id BIGINT,

    cancelado_por_usuario_id BIGINT,

    fecha_cancelacion TIMESTAMP WITH TIME ZONE,

    motivo_cancelacion VARCHAR(700),

    observaciones VARCHAR(1000),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_descansos_obligatorios
        PRIMARY KEY (id),

    CONSTRAINT fk_descansos_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_descansos_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_descansos_resumen
        FOREIGN KEY (resumen_periodo_empleado_id)
        REFERENCES asistencia.resumen_periodo_empleado (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_descansos_incidencia
        FOREIGN KEY (incidencia_id)
        REFERENCES asistencia.incidencias (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_descansos_generado_por
        FOREIGN KEY (generado_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_descansos_programado_por
        FOREIGN KEY (programado_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_descansos_aplicado_por
        FOREIGN KEY (aplicado_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_descansos_cancelado_por
        FOREIGN KEY (cancelado_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT uq_descansos_empleado_periodo_numero
        UNIQUE (
            empleado_id,
            periodo_evaluacion_id,
            numero_descanso_periodo
        ),

    CONSTRAINT ck_descansos_numero_periodo
        CHECK (
            numero_descanso_periodo > 0
        ),

    CONSTRAINT ck_descansos_numero_historico
        CHECK (
            numero_descanso_historico IS NULL
            OR numero_descanso_historico > 0
        ),

    CONSTRAINT ck_descansos_puntos
        CHECK (
            puntos_efectivos_periodo >= 0
        ),

    CONSTRAINT ck_descansos_estatus
        CHECK (
            estatus IN (
                'PENDIENTE',
                'PROGRAMADO',
                'APLICADO',
                'CANCELADO'
            )
        ),

    CONSTRAINT ck_descansos_programado
        CHECK (
            (
                estatus = 'PROGRAMADO'
                AND fecha_programada IS NOT NULL
            )
            OR
            (
                estatus <> 'PROGRAMADO'
            )
        ),

    CONSTRAINT ck_descansos_aplicado
        CHECK (
            (
                estatus = 'APLICADO'
                AND fecha_aplicacion IS NOT NULL
            )
            OR
            (
                estatus <> 'APLICADO'
            )
        ),

    CONSTRAINT ck_descansos_cancelado
        CHECK (
            (
                estatus = 'CANCELADO'
                AND fecha_cancelacion IS NOT NULL
                AND motivo_cancelacion IS NOT NULL
                AND BTRIM(motivo_cancelacion) <> ''
            )
            OR
            (
                estatus <> 'CANCELADO'
            )
        ),

    CONSTRAINT ck_descansos_fecha_aplicacion
        CHECK (
            fecha_aplicacion IS NULL
            OR fecha_programada IS NULL
            OR fecha_aplicacion >= fecha_programada
        ),

    CONSTRAINT ck_descansos_motivo_revision_no_vacio
        CHECK (
            motivo_revision_baja IS NULL
            OR BTRIM(motivo_revision_baja) <> ''
        ),

    CONSTRAINT ck_descansos_motivo_cancelacion_no_vacio
        CHECK (
            motivo_cancelacion IS NULL
            OR BTRIM(motivo_cancelacion) <> ''
        ),

    CONSTRAINT ck_descansos_observaciones_no_vacias
        CHECK (
            observaciones IS NULL
            OR BTRIM(observaciones) <> ''
        )
);


CREATE INDEX IF NOT EXISTS
    ix_descansos_empleado
ON asistencia.descansos_obligatorios (
    empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_descansos_periodo
ON asistencia.descansos_obligatorios (
    periodo_evaluacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_descansos_resumen
ON asistencia.descansos_obligatorios (
    resumen_periodo_empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_descansos_incidencia
ON asistencia.descansos_obligatorios (
    incidencia_id
);


CREATE INDEX IF NOT EXISTS
    ix_descansos_estatus
ON asistencia.descansos_obligatorios (
    estatus
);


CREATE INDEX IF NOT EXISTS
    ix_descansos_fecha_programada
ON asistencia.descansos_obligatorios (
    fecha_programada
);


CREATE INDEX IF NOT EXISTS
    ix_descansos_revision_baja
ON asistencia.descansos_obligatorios (
    requiere_revision_baja
);


COMMIT;