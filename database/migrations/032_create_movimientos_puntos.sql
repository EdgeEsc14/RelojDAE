\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.movimientos_puntos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    empleado_id BIGINT NOT NULL,

    periodo_evaluacion_id BIGINT NOT NULL,

    incidencia_id BIGINT,

    justificante_id BIGINT,

    aplicacion_justificante_id BIGINT,

    fecha DATE NOT NULL,

    tipo_movimiento VARCHAR(30) NOT NULL,

    concepto VARCHAR(150) NOT NULL,

    puntos SMALLINT NOT NULL,

    descripcion VARCHAR(700),

    origen VARCHAR(30)
        NOT NULL DEFAULT 'SISTEMA',

    creado_por_usuario_id BIGINT,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_movimientos_puntos
        PRIMARY KEY (id),

    CONSTRAINT fk_movimientos_puntos_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_movimientos_puntos_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_movimientos_puntos_incidencia
        FOREIGN KEY (incidencia_id)
        REFERENCES asistencia.incidencias (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_movimientos_puntos_justificante
        FOREIGN KEY (justificante_id)
        REFERENCES asistencia.justificantes (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_movimientos_puntos_aplicacion
        FOREIGN KEY (aplicacion_justificante_id)
        REFERENCES asistencia.aplicaciones_justificante (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_movimientos_puntos_usuario
        FOREIGN KEY (creado_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT ck_movimientos_puntos_tipo
        CHECK (
            tipo_movimiento IN (
                'CARGO',
                'DESCUENTO',
                'AJUSTE'
            )
        ),

    CONSTRAINT ck_movimientos_puntos_no_cero
        CHECK (
            puntos <> 0
        ),

    CONSTRAINT ck_movimientos_puntos_signo
        CHECK (
            (
                tipo_movimiento = 'CARGO'
                AND puntos > 0
            )
            OR
            (
                tipo_movimiento = 'DESCUENTO'
                AND puntos < 0
            )
            OR
            (
                tipo_movimiento = 'AJUSTE'
            )
        ),

    CONSTRAINT ck_movimientos_puntos_concepto_no_vacio
        CHECK (
            BTRIM(concepto) <> ''
        ),

    CONSTRAINT ck_movimientos_puntos_descripcion_no_vacia
        CHECK (
            descripcion IS NULL
            OR BTRIM(descripcion) <> ''
        ),

    CONSTRAINT ck_movimientos_puntos_origen
        CHECK (
            origen IN (
                'SISTEMA',
                'JUSTIFICANTE',
                'AJUSTE_MANUAL',
                'CIERRE_PERIODO'
            )
        )
);


CREATE INDEX IF NOT EXISTS
    ix_movimientos_puntos_empleado
ON asistencia.movimientos_puntos (
    empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_movimientos_puntos_periodo
ON asistencia.movimientos_puntos (
    periodo_evaluacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_movimientos_puntos_empleado_periodo
ON asistencia.movimientos_puntos (
    empleado_id,
    periodo_evaluacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_movimientos_puntos_incidencia
ON asistencia.movimientos_puntos (
    incidencia_id
);


CREATE INDEX IF NOT EXISTS
    ix_movimientos_puntos_justificante
ON asistencia.movimientos_puntos (
    justificante_id
);


CREATE INDEX IF NOT EXISTS
    ix_movimientos_puntos_aplicacion
ON asistencia.movimientos_puntos (
    aplicacion_justificante_id
);


CREATE INDEX IF NOT EXISTS
    ix_movimientos_puntos_fecha
ON asistencia.movimientos_puntos (
    fecha
);


CREATE INDEX IF NOT EXISTS
    ix_movimientos_puntos_tipo
ON asistencia.movimientos_puntos (
    tipo_movimiento
);


COMMIT;