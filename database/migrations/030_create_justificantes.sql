\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.justificantes (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    empleado_id BIGINT NOT NULL,

    periodo_evaluacion_id BIGINT NOT NULL,

    folio VARCHAR(60),

    motivo VARCHAR(700) NOT NULL,

    descripcion VARCHAR(1000),

    dias_solicitados SMALLINT
        NOT NULL DEFAULT 1,

    dias_aprobados SMALLINT
        NOT NULL DEFAULT 0,

    puntos_solicitados SMALLINT
        NOT NULL DEFAULT 0,

    puntos_aprobados SMALLINT
        NOT NULL DEFAULT 0,

    documento_url VARCHAR(500),

    estatus VARCHAR(30)
        NOT NULL DEFAULT 'PENDIENTE',

    solicitado_por_usuario_id BIGINT,

    revisado_por_usuario_id BIGINT,

    fecha_solicitud TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_revision TIMESTAMP WITH TIME ZONE,

    comentario_revision VARCHAR(1000),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_justificantes
        PRIMARY KEY (id),

    CONSTRAINT fk_justificantes_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_justificantes_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_justificantes_solicitado_por
        FOREIGN KEY (solicitado_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT fk_justificantes_revisado_por
        FOREIGN KEY (revisado_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT ck_justificantes_folio_no_vacio
        CHECK (
            folio IS NULL
            OR BTRIM(folio) <> ''
        ),

    CONSTRAINT ck_justificantes_motivo_no_vacio
        CHECK (
            BTRIM(motivo) <> ''
        ),

    CONSTRAINT ck_justificantes_descripcion_no_vacia
        CHECK (
            descripcion IS NULL
            OR BTRIM(descripcion) <> ''
        ),

    CONSTRAINT ck_justificantes_dias
        CHECK (
            dias_solicitados > 0
            AND dias_aprobados >= 0
            AND dias_aprobados <= dias_solicitados
        ),

    CONSTRAINT ck_justificantes_puntos
        CHECK (
            puntos_solicitados >= 0
            AND puntos_aprobados >= 0
            AND puntos_aprobados <= puntos_solicitados
        ),

    CONSTRAINT ck_justificantes_documento_url_no_vacio
        CHECK (
            documento_url IS NULL
            OR BTRIM(documento_url) <> ''
        ),

    CONSTRAINT ck_justificantes_estatus
        CHECK (
            estatus IN (
                'PENDIENTE',
                'APROBADO',
                'RECHAZADO',
                'CANCELADO'
            )
        ),

    CONSTRAINT ck_justificantes_revision
        CHECK (
            (
                estatus IN (
                    'APROBADO',
                    'RECHAZADO',
                    'CANCELADO'
                )
                AND fecha_revision IS NOT NULL
            )
            OR
            (
                estatus = 'PENDIENTE'
            )
        ),

    CONSTRAINT ck_justificantes_aprobacion
        CHECK (
            (
                estatus = 'APROBADO'
                AND dias_aprobados > 0
            )
            OR
            (
                estatus <> 'APROBADO'
            )
        ),

    CONSTRAINT ck_justificantes_comentario_revision_no_vacio
        CHECK (
            comentario_revision IS NULL
            OR BTRIM(comentario_revision) <> ''
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_justificantes_folio
ON asistencia.justificantes (
    folio
)
WHERE folio IS NOT NULL;


CREATE INDEX IF NOT EXISTS
    ix_justificantes_empleado
ON asistencia.justificantes (
    empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_justificantes_periodo
ON asistencia.justificantes (
    periodo_evaluacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_justificantes_empleado_periodo
ON asistencia.justificantes (
    empleado_id,
    periodo_evaluacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_justificantes_estatus
ON asistencia.justificantes (
    estatus
);


CREATE INDEX IF NOT EXISTS
    ix_justificantes_fecha_solicitud
ON asistencia.justificantes (
    fecha_solicitud
);


COMMIT;