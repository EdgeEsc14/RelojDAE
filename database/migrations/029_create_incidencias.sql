\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.incidencias (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    empleado_id BIGINT NOT NULL,

    asistencia_diaria_id BIGINT,

    periodo_evaluacion_id BIGINT,

    tipo_incidencia_id BIGINT NOT NULL,

    fecha DATE NOT NULL,

    fecha_inicio TIMESTAMP WITH TIME ZONE,

    fecha_fin TIMESTAMP WITH TIME ZONE,

    descripcion VARCHAR(700),

    puntos_originales SMALLINT
        NOT NULL DEFAULT 0,

    puntos_justificados SMALLINT
        NOT NULL DEFAULT 0,

    puntos_efectivos SMALLINT
        GENERATED ALWAYS AS (
            GREATEST(
                puntos_originales - puntos_justificados,
                0
            )
        ) STORED,

    estatus VARCHAR(30)
        NOT NULL DEFAULT 'PENDIENTE',

    origen VARCHAR(30)
        NOT NULL DEFAULT 'PROCESAMIENTO',

    requiere_revision BOOLEAN
        NOT NULL DEFAULT FALSE,

    creada_por_usuario_id BIGINT,

    revisada_por_usuario_id BIGINT,

    fecha_revision TIMESTAMP WITH TIME ZONE,

    comentario_revision VARCHAR(700),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_incidencias
        PRIMARY KEY (id),

    CONSTRAINT fk_incidencias_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_incidencias_asistencia
        FOREIGN KEY (asistencia_diaria_id)
        REFERENCES asistencia.asistencias_diarias (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_incidencias_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_incidencias_tipo
        FOREIGN KEY (tipo_incidencia_id)
        REFERENCES asistencia.tipos_incidencia (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_incidencias_creada_por_usuario
        FOREIGN KEY (creada_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_incidencias_revisada_por_usuario
        FOREIGN KEY (revisada_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT ck_incidencias_fechas
        CHECK (
            fecha_fin IS NULL
            OR fecha_inicio IS NULL
            OR fecha_fin >= fecha_inicio
        ),

    CONSTRAINT ck_incidencias_puntos
        CHECK (
            puntos_originales >= 0
            AND puntos_justificados >= 0
            AND puntos_justificados <= puntos_originales
        ),

    CONSTRAINT ck_incidencias_estatus
        CHECK (
            estatus IN (
                'PENDIENTE',
                'SIN_JUSTIFICAR',
                'JUSTIFICADA',
                'APROBADA',
                'RECHAZADA',
                'CANCELADA'
            )
        ),

    CONSTRAINT ck_incidencias_origen
        CHECK (
            origen IN (
                'PROCESAMIENTO',
                'MANUAL',
                'IMPORTACION',
                'AJUSTE'
            )
        ),

    CONSTRAINT ck_incidencias_revision
        CHECK (
            (
                estatus IN (
                    'APROBADA',
                    'RECHAZADA',
                    'JUSTIFICADA',
                    'CANCELADA'
                )
                AND fecha_revision IS NOT NULL
            )
            OR
            (
                estatus IN (
                    'PENDIENTE',
                    'SIN_JUSTIFICAR'
                )
            )
        ),

    CONSTRAINT ck_incidencias_descripcion_no_vacia
        CHECK (
            descripcion IS NULL
            OR BTRIM(descripcion) <> ''
        ),

    CONSTRAINT ck_incidencias_comentario_revision_no_vacio
        CHECK (
            comentario_revision IS NULL
            OR BTRIM(comentario_revision) <> ''
        )
);


CREATE INDEX IF NOT EXISTS
    ix_incidencias_empleado
ON asistencia.incidencias (
    empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_incidencias_asistencia
ON asistencia.incidencias (
    asistencia_diaria_id
);


CREATE INDEX IF NOT EXISTS
    ix_incidencias_periodo
ON asistencia.incidencias (
    periodo_evaluacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_incidencias_tipo
ON asistencia.incidencias (
    tipo_incidencia_id
);


CREATE INDEX IF NOT EXISTS
    ix_incidencias_fecha
ON asistencia.incidencias (
    fecha
);


CREATE INDEX IF NOT EXISTS
    ix_incidencias_estatus
ON asistencia.incidencias (
    estatus
);


CREATE INDEX IF NOT EXISTS
    ix_incidencias_origen
ON asistencia.incidencias (
    origen
);


CREATE INDEX IF NOT EXISTS
    ix_incidencias_empleado_periodo
ON asistencia.incidencias (
    empleado_id,
    periodo_evaluacion_id
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_incidencias_asistencia_tipo
ON asistencia.incidencias (
    asistencia_diaria_id,
    tipo_incidencia_id
)
WHERE asistencia_diaria_id IS NOT NULL
  AND estatus <> 'CANCELADA';


COMMIT;