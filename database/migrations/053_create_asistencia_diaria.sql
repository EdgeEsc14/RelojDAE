BEGIN;

-- ============================================================
-- 053_create_asistencia_diaria.sql
-- Objetivo:
-- Guardar el resultado procesado de las marcaciones crudas.
--
-- Fuente:
-- asistencia.marcaciones_crudas
--
-- Esta tabla NO reemplaza las marcaciones crudas.
-- Es una tabla derivada para consulta operativa de asistencia.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS asistencia;

CREATE TABLE IF NOT EXISTS asistencia.asistencia_diaria (
    id BIGSERIAL PRIMARY KEY,

    -- Relación con empleado
    empleado_id INTEGER,
    codigo_empleado VARCHAR(50) NOT NULL,
    nombre_empleado VARCHAR(255),

    -- Día procesado
    fecha DATE NOT NULL,

    -- Entrada y salida detectadas
    entrada_fecha_hora TIMESTAMP WITHOUT TIME ZONE,
    salida_fecha_hora TIMESTAMP WITHOUT TIME ZONE,
    entrada_hora TIME WITHOUT TIME ZONE,
    salida_hora TIME WITHOUT TIME ZONE,

    -- Referencia a marcaciones crudas usadas
    entrada_marcacion_cruda_id BIGINT,
    salida_marcacion_cruda_id BIGINT,
    primera_marcacion_cruda_id BIGINT,
    ultima_marcacion_cruda_id BIGINT,

    -- Resumen de marcaciones
    primera_marcacion_fecha_hora TIMESTAMP WITHOUT TIME ZONE,
    ultima_marcacion_fecha_hora TIMESTAMP WITHOUT TIME ZONE,
    total_marcaciones INTEGER NOT NULL DEFAULT 0,
    total_entradas INTEGER NOT NULL DEFAULT 0,
    total_salidas INTEGER NOT NULL DEFAULT 0,

    -- Cálculos iniciales
    tiempo_trabajado_minutos INTEGER,
    minutos_retardo INTEGER,
    minutos_extra INTEGER,

    -- Estatus del día
    estatus_dia VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',

    -- Observaciones del procesamiento
    observaciones TEXT,

    -- Control de origen/procesamiento
    origen VARCHAR(50) NOT NULL DEFAULT 'MARCACIONES_CRUDAS',
    sync_run_id VARCHAR(100),
    procesado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_asistencia_diaria_empleado_fecha UNIQUE (
        codigo_empleado,
        fecha
    ),

    CONSTRAINT ck_asistencia_diaria_estatus CHECK (
        estatus_dia IN (
            'COMPLETA',
            'OMISION_ENTRADA',
            'OMISION_SALIDA',
            'INCOMPLETA',
            'SIN_MARCACIONES',
            'PENDIENTE'
        )
    ),

    CONSTRAINT ck_asistencia_diaria_totales CHECK (
        total_marcaciones >= 0
        AND total_entradas >= 0
        AND total_salidas >= 0
    ),

    CONSTRAINT ck_asistencia_diaria_tiempo CHECK (
        tiempo_trabajado_minutos IS NULL
        OR tiempo_trabajado_minutos >= 0
    )
);

COMMENT ON TABLE asistencia.asistencia_diaria IS
'Resultado procesado diario de asistencia a partir de marcaciones crudas.';

COMMENT ON COLUMN asistencia.asistencia_diaria.codigo_empleado IS
'Código del empleado procesado. Se obtiene desde personal.empleados cuando la marcación cruda tiene vínculo ZKTeco.';

COMMENT ON COLUMN asistencia.asistencia_diaria.fecha IS
'Día de asistencia procesado.';

COMMENT ON COLUMN asistencia.asistencia_diaria.entrada_fecha_hora IS
'Primera marcación tipo entrada detectada para el empleado en el día.';

COMMENT ON COLUMN asistencia.asistencia_diaria.salida_fecha_hora IS
'Última marcación tipo salida detectada para el empleado en el día.';

COMMENT ON COLUMN asistencia.asistencia_diaria.estatus_dia IS
'Estatus calculado del día: COMPLETA, OMISION_ENTRADA, OMISION_SALIDA, INCOMPLETA, SIN_MARCACIONES o PENDIENTE.';

COMMENT ON COLUMN asistencia.asistencia_diaria.origen IS
'Fuente de procesamiento. Inicialmente MARCACIONES_CRUDAS.';

CREATE INDEX IF NOT EXISTS ix_asistencia_diaria_fecha
ON asistencia.asistencia_diaria (fecha DESC);

CREATE INDEX IF NOT EXISTS ix_asistencia_diaria_codigo_empleado
ON asistencia.asistencia_diaria (codigo_empleado);

CREATE INDEX IF NOT EXISTS ix_asistencia_diaria_empleado_fecha
ON asistencia.asistencia_diaria (codigo_empleado, fecha DESC);

CREATE INDEX IF NOT EXISTS ix_asistencia_diaria_estatus
ON asistencia.asistencia_diaria (estatus_dia);

CREATE INDEX IF NOT EXISTS ix_asistencia_diaria_procesado_en
ON asistencia.asistencia_diaria (procesado_en DESC);

COMMIT;