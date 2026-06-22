\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS asistencia.resumen_periodo_empleado (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    empleado_id BIGINT NOT NULL,

    periodo_evaluacion_id BIGINT NOT NULL,

    politica_asistencia_id BIGINT NOT NULL,

    fecha_inicio DATE NOT NULL,

    fecha_fin DATE NOT NULL,

    dias_laborales SMALLINT
        NOT NULL DEFAULT 0,

    dias_completos SMALLINT
        NOT NULL DEFAULT 0,

    dias_tolerancia SMALLINT
        NOT NULL DEFAULT 0,

    retardos_menores SMALLINT
        NOT NULL DEFAULT 0,

    retardos_mayores SMALLINT
        NOT NULL DEFAULT 0,

    faltas SMALLINT
        NOT NULL DEFAULT 0,

    faltas_justificadas SMALLINT
        NOT NULL DEFAULT 0,

    omisiones_entrada SMALLINT
        NOT NULL DEFAULT 0,

    omisiones_salida SMALLINT
        NOT NULL DEFAULT 0,

    dias_con_tiempo_extra SMALLINT
        NOT NULL DEFAULT 0,

    minutos_ordinarios INTEGER
        NOT NULL DEFAULT 0,

    minutos_extra INTEGER
        NOT NULL DEFAULT 0,

    minutos_retardo INTEGER
        NOT NULL DEFAULT 0,

    puntos_brutos SMALLINT
        NOT NULL DEFAULT 0,

    puntos_justificados SMALLINT
        NOT NULL DEFAULT 0,

    puntos_ajuste SMALLINT
        NOT NULL DEFAULT 0,

    puntos_efectivos SMALLINT
        GENERATED ALWAYS AS (
            CAST(
                GREATEST(
                    puntos_brutos::INTEGER
                    - puntos_justificados::INTEGER
                    + puntos_ajuste::INTEGER,
                    0
                )
                AS SMALLINT
            )
        ) STORED,

    justificantes_solicitados SMALLINT
        NOT NULL DEFAULT 0,

    justificantes_aprobados SMALLINT
        NOT NULL DEFAULT 0,

    dias_justificados SMALLINT
        NOT NULL DEFAULT 0,

    descansos_obligatorios_generados SMALLINT
        NOT NULL DEFAULT 0,

    faltas_consecutivas_max SMALLINT
        NOT NULL DEFAULT 0,

    requiere_revision_baja BOOLEAN
        NOT NULL DEFAULT FALSE,

    motivo_revision_baja VARCHAR(700),

    estatus VARCHAR(30)
        NOT NULL DEFAULT 'ABIERTO',

    fecha_calculo TIMESTAMP WITH TIME ZONE,

    fecha_cierre TIMESTAMP WITH TIME ZONE,

    cerrado_por_usuario_id BIGINT,

    observaciones VARCHAR(1000),

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_resumen_periodo_empleado
        PRIMARY KEY (id),

    CONSTRAINT fk_resumen_periodo_empleado
        FOREIGN KEY (empleado_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_resumen_periodo_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_resumen_periodo_politica
        FOREIGN KEY (politica_asistencia_id)
        REFERENCES asistencia.politicas_asistencia (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_resumen_periodo_cerrado_por
        FOREIGN KEY (cerrado_por_usuario_id)
        REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT uq_resumen_periodo_empleado
        UNIQUE (
            empleado_id,
            periodo_evaluacion_id
        ),

    CONSTRAINT ck_resumen_periodo_fechas
        CHECK (
            fecha_fin >= fecha_inicio
        ),

    CONSTRAINT ck_resumen_periodo_dias_no_negativos
        CHECK (
            dias_laborales >= 0
            AND dias_completos >= 0
            AND dias_tolerancia >= 0
            AND retardos_menores >= 0
            AND retardos_mayores >= 0
            AND faltas >= 0
            AND faltas_justificadas >= 0
            AND omisiones_entrada >= 0
            AND omisiones_salida >= 0
            AND dias_con_tiempo_extra >= 0
        ),

    CONSTRAINT ck_resumen_periodo_minutos_no_negativos
        CHECK (
            minutos_ordinarios >= 0
            AND minutos_extra >= 0
            AND minutos_retardo >= 0
        ),

    CONSTRAINT ck_resumen_periodo_puntos
        CHECK (
            puntos_brutos >= 0
            AND puntos_justificados >= 0
            AND puntos_justificados <= puntos_brutos
        ),

    CONSTRAINT ck_resumen_periodo_justificantes
        CHECK (
            justificantes_solicitados >= 0
            AND justificantes_aprobados >= 0
            AND justificantes_aprobados <= justificantes_solicitados
            AND dias_justificados >= 0
        ),

    CONSTRAINT ck_resumen_periodo_descansos
        CHECK (
            descansos_obligatorios_generados >= 0
            AND faltas_consecutivas_max >= 0
        ),

    CONSTRAINT ck_resumen_periodo_estatus
        CHECK (
            estatus IN (
                'ABIERTO',
                'CALCULADO',
                'CERRADO',
                'RECALCULAR',
                'CANCELADO'
            )
        ),

    CONSTRAINT ck_resumen_periodo_cierre
        CHECK (
            (
                estatus = 'CERRADO'
                AND fecha_cierre IS NOT NULL
            )
            OR
            (
                estatus <> 'CERRADO'
            )
        ),

    CONSTRAINT ck_resumen_periodo_motivo_revision_no_vacio
        CHECK (
            motivo_revision_baja IS NULL
            OR BTRIM(motivo_revision_baja) <> ''
        ),

    CONSTRAINT ck_resumen_periodo_observaciones_no_vacias
        CHECK (
            observaciones IS NULL
            OR BTRIM(observaciones) <> ''
        )
);


CREATE INDEX IF NOT EXISTS
    ix_resumen_periodo_empleado
ON asistencia.resumen_periodo_empleado (
    empleado_id
);


CREATE INDEX IF NOT EXISTS
    ix_resumen_periodo_periodo
ON asistencia.resumen_periodo_empleado (
    periodo_evaluacion_id
);


CREATE INDEX IF NOT EXISTS
    ix_resumen_periodo_politica
ON asistencia.resumen_periodo_empleado (
    politica_asistencia_id
);


CREATE INDEX IF NOT EXISTS
    ix_resumen_periodo_fechas
ON asistencia.resumen_periodo_empleado (
    fecha_inicio,
    fecha_fin
);


CREATE INDEX IF NOT EXISTS
    ix_resumen_periodo_estatus
ON asistencia.resumen_periodo_empleado (
    estatus
);


CREATE INDEX IF NOT EXISTS
    ix_resumen_periodo_revision_baja
ON asistencia.resumen_periodo_empleado (
    requiere_revision_baja
);


COMMIT;