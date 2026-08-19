-- ============================================================
-- baseline_test.sql
-- Esquema mínimo para tests de integración del núcleo de asistencia.
--
-- ESTE ARCHIVO SOLO SE APLICA A: dae_reloj_test
-- NUNCA ejecutar contra dae_reloj.
--
-- Subconjunto fiel del esquema real. Tablas reducidas a las
-- columnas necesarias para el motor de asistencia.
-- Tipos, constraints y nombres REALES preservados.
-- ============================================================

-- Verificación de seguridad
DO $$
BEGIN
    IF current_database() <> 'dae_reloj_test' THEN
        RAISE EXCEPTION 'ABORTAR: Este script solo puede ejecutarse en dae_reloj_test. BD actual: %', current_database();
    END IF;
END $$;

-- Limpiar schemas si existen (para re-aplicar)
DROP SCHEMA IF EXISTS asistencia CASCADE;
DROP SCHEMA IF EXISTS personal CASCADE;
DROP SCHEMA IF EXISTS organizacion CASCADE;

-- ============================================================
-- SCHEMAS
-- ============================================================

CREATE SCHEMA personal AUTHORIZATION reloj_app;
CREATE SCHEMA organizacion AUTHORIZATION reloj_app;
CREATE SCHEMA asistencia AUTHORIZATION reloj_app;

-- ============================================================
-- organizacion.unidades_organizacionales (dependencia de empleados)
-- ============================================================

CREATE TABLE organizacion.unidades_organizacionales (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(60) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_unidades_organizacionales PRIMARY KEY (id),
    CONSTRAINT uq_unidades_organizacionales_codigo UNIQUE (codigo)
);

-- ============================================================
-- organizacion.puestos (dependencia de empleados)
-- ============================================================

CREATE TABLE organizacion.puestos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(60) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    nivel_jerarquico SMALLINT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_puestos PRIMARY KEY (id),
    CONSTRAINT uq_puestos_codigo UNIQUE (codigo)
);

-- ============================================================
-- personal.empleados
-- ============================================================

CREATE TABLE personal.empleados (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo_empleado VARCHAR(30) NOT NULL,
    nombres VARCHAR(120) NOT NULL,
    apellido_paterno VARCHAR(80) NOT NULL,
    apellido_materno VARCHAR(80),

    nombre_completo VARCHAR(300)
        GENERATED ALWAYS AS (
            BTRIM(
                nombres || ' ' || apellido_paterno || ' ' || COALESCE(apellido_materno, '')
            )
        ) STORED,

    rfc VARCHAR(13),
    correo VARCHAR(320),
    correo_personal VARCHAR(254),

    unidad_organizacional_id BIGINT NOT NULL,
    puesto_id BIGINT NOT NULL,
    supervisor_id BIGINT,

    fecha_ingreso DATE,
    fecha_baja DATE,

    estatus VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',

    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    zk_user_id VARCHAR(50),

    CONSTRAINT pk_empleados PRIMARY KEY (id),
    CONSTRAINT uq_empleados_codigo UNIQUE (codigo_empleado),

    CONSTRAINT fk_empleados_unidad_organizacional
        FOREIGN KEY (unidad_organizacional_id)
        REFERENCES organizacion.unidades_organizacionales (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,

    CONSTRAINT fk_empleados_puesto
        FOREIGN KEY (puesto_id)
        REFERENCES organizacion.puestos (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,

    CONSTRAINT fk_empleados_supervisor
        FOREIGN KEY (supervisor_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT ON DELETE SET NULL,

    CONSTRAINT ck_empleados_estatus CHECK (
        estatus IN ('ACTIVO', 'INACTIVO', 'BAJA')
    )
);

CREATE UNIQUE INDEX ux_empleados_zk_user_id
ON personal.empleados (zk_user_id)
WHERE zk_user_id IS NOT NULL AND btrim(zk_user_id) <> '';

-- ============================================================
-- asistencia.tipos_turno
-- ============================================================

CREATE TABLE asistencia.tipos_turno (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(30) NOT NULL,
    nombre VARCHAR(80) NOT NULL,
    descripcion VARCHAR(300),
    hora_entrada_desde TIME WITHOUT TIME ZONE,
    hora_entrada_hasta TIME WITHOUT TIME ZONE,
    duracion_jornada_minutos SMALLINT NOT NULL,
    modalidad_tiempo_extra VARCHAR(30) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_tipos_turno PRIMARY KEY (id),
    CONSTRAINT uq_tipos_turno_codigo UNIQUE (codigo),
    CONSTRAINT ck_tipos_turno_modalidad CHECK (
        modalidad_tiempo_extra IN ('ANTES_ENTRADA', 'DESPUES_SALIDA', 'NO_APLICA')
    )
);

-- ============================================================
-- asistencia.horarios
-- ============================================================

CREATE TABLE asistencia.horarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(40) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion VARCHAR(500),
    tipo_turno_id BIGINT NOT NULL,
    hora_entrada TIME NOT NULL,
    hora_salida TIME NOT NULL,
    tolerancia_entrada_minutos SMALLINT NOT NULL DEFAULT 0,
    descanso_minutos SMALLINT NOT NULL DEFAULT 0,
    permite_tiempo_extra BOOLEAN NOT NULL DEFAULT FALSE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_horarios PRIMARY KEY (id),
    CONSTRAINT uq_horarios_codigo UNIQUE (codigo),
    CONSTRAINT fk_horarios_tipo_turno
        FOREIGN KEY (tipo_turno_id)
        REFERENCES asistencia.tipos_turno (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ck_horarios_tolerancia_no_negativa CHECK (tolerancia_entrada_minutos >= 0),
    CONSTRAINT ck_horarios_descanso_no_negativo CHECK (descanso_minutos >= 0)
);

-- ============================================================
-- asistencia.horario_dias
-- ============================================================

CREATE TABLE asistencia.horario_dias (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    horario_id BIGINT NOT NULL,
    dia_semana SMALLINT NOT NULL,
    es_laboral BOOLEAN NOT NULL DEFAULT TRUE,
    hora_entrada TIME WITHOUT TIME ZONE,
    hora_salida TIME WITHOUT TIME ZONE,
    cruza_medianoche BOOLEAN
        GENERATED ALWAYS AS (
            es_laboral AND hora_salida < hora_entrada
        ) STORED,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_horario_dias PRIMARY KEY (id),
    CONSTRAINT fk_horario_dias_horario
        FOREIGN KEY (horario_id) REFERENCES asistencia.horarios (id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT uq_horario_dias_horario_dia UNIQUE (horario_id, dia_semana),
    CONSTRAINT ck_horario_dias_dia_semana CHECK (dia_semana BETWEEN 1 AND 7),
    CONSTRAINT ck_horario_dias_horas CHECK (
        (es_laboral = TRUE AND hora_entrada IS NOT NULL AND hora_salida IS NOT NULL AND hora_entrada <> hora_salida)
        OR (es_laboral = FALSE AND hora_entrada IS NULL AND hora_salida IS NULL)
    )
);

-- ============================================================
-- asistencia.asignaciones_horario
-- ============================================================

CREATE TABLE asistencia.asignaciones_horario (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    empleado_id BIGINT NOT NULL,
    horario_id BIGINT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    estatus VARCHAR(20) NOT NULL DEFAULT 'ACTIVA',
    motivo VARCHAR(300),
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_asignaciones_horario PRIMARY KEY (id),
    CONSTRAINT fk_asignaciones_horario_empleado
        FOREIGN KEY (empleado_id) REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_asignaciones_horario_horario
        FOREIGN KEY (horario_id) REFERENCES asistencia.horarios (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ck_asignaciones_horario_estatus CHECK (estatus IN ('ACTIVA', 'CERRADA', 'CANCELADA')),
    CONSTRAINT ck_asignaciones_horario_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

-- ============================================================
-- asistencia.politicas_asistencia
-- ============================================================

CREATE TABLE asistencia.politicas_asistencia (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(40) NOT NULL,
    version SMALLINT NOT NULL DEFAULT 1,
    nombre VARCHAR(120) NOT NULL,
    descripcion VARCHAR(500),
    tipo_periodo VARCHAR(20) NOT NULL,
    limite_tolerancia_segundos INTEGER NOT NULL,
    limite_retardo_menor_segundos INTEGER NOT NULL,
    limite_retardo_mayor_segundos INTEGER NOT NULL,
    puntos_retardo_menor SMALLINT NOT NULL DEFAULT 1,
    puntos_retardo_mayor SMALLINT NOT NULL DEFAULT 2,
    puntos_para_descanso SMALLINT NOT NULL DEFAULT 10,
    max_dias_justificables_periodo SMALLINT NOT NULL DEFAULT 2,
    max_puntos_descontables_por_dia SMALLINT NOT NULL DEFAULT 2,
    descansos_para_revision_baja SMALLINT NOT NULL DEFAULT 7,
    faltas_consecutivas_revision_baja SMALLINT NOT NULL DEFAULT 3,
    vigencia_desde DATE NOT NULL,
    vigencia_hasta DATE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_politicas_asistencia PRIMARY KEY (id),
    CONSTRAINT uq_politicas_asistencia_codigo_version UNIQUE (codigo, version)
);

-- ============================================================
-- asistencia.periodos_evaluacion (FK requerida por asistencias_diarias)
-- ============================================================

CREATE TABLE asistencia.periodos_evaluacion (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    politica_asistencia_id BIGINT NOT NULL,
    codigo VARCHAR(60) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    tipo_periodo VARCHAR(20) NOT NULL,
    anio SMALLINT NOT NULL,
    numero_periodo SMALLINT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estatus VARCHAR(20) NOT NULL DEFAULT 'ABIERTO',
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_periodos_evaluacion PRIMARY KEY (id),
    CONSTRAINT fk_periodos_politica
        FOREIGN KEY (politica_asistencia_id)
        REFERENCES asistencia.politicas_asistencia (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT uq_periodos_codigo UNIQUE (codigo)
);

-- ============================================================
-- asistencia.calendarios
-- ============================================================

CREATE TABLE asistencia.calendarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(40) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion VARCHAR(500),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_calendarios PRIMARY KEY (id),
    CONSTRAINT uq_calendarios_codigo UNIQUE (codigo)
);

-- ============================================================
-- asistencia.calendario_eventos
-- ============================================================

CREATE TABLE asistencia.calendario_eventos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    calendario_id BIGINT NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion VARCHAR(700),
    tipo_evento VARCHAR(40) NOT NULL,
    tipo_recurrencia VARCHAR(30) NOT NULL,
    fecha_inicio DATE,
    fecha_fin DATE,
    mes SMALLINT,
    dia SMALLINT,
    afecta_asistencia BOOLEAN NOT NULL DEFAULT TRUE,
    es_laborable BOOLEAN NOT NULL DEFAULT FALSE,
    prioridad SMALLINT NOT NULL DEFAULT 50,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_calendario_eventos PRIMARY KEY (id),
    CONSTRAINT fk_calendario_eventos_calendario
        FOREIGN KEY (calendario_id) REFERENCES asistencia.calendarios (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ck_calendario_eventos_tipo_evento CHECK (
        tipo_evento IN (
            'FESTIVO_OFICIAL', 'DESCANSO_INSTITUCIONAL', 'DESCANSO_SINDICAL',
            'VACACIONES', 'INHABIL_ADMINISTRATIVO', 'SUSPENSION_LABORES',
            'LABORABLE_EXTRAORDINARIO', 'OTRO'
        )
    ),
    CONSTRAINT ck_calendario_eventos_tipo_recurrencia CHECK (
        tipo_recurrencia IN ('FECHA_ESPECIFICA', 'ANUAL_FIJA', 'PERIODO')
    ),
    CONSTRAINT ck_calendario_eventos_prioridad CHECK (prioridad BETWEEN 1 AND 100)
);

-- ============================================================
-- asistencia.marcaciones_crudas
-- ============================================================

CREATE TABLE asistencia.marcaciones_crudas (
    id BIGSERIAL PRIMARY KEY,
    dispositivo_origen VARCHAR(100) NOT NULL DEFAULT 'ZKTeco',
    dispositivo_ip VARCHAR(50),
    zk_uid_registro INTEGER,
    zk_user_id VARCHAR(50) NOT NULL,
    fecha_hora TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    fecha DATE GENERATED ALWAYS AS (fecha_hora::date) STORED,
    hora TIME WITHOUT TIME ZONE GENERATED ALWAYS AS (fecha_hora::time) STORED,
    punch INTEGER,
    punch_label VARCHAR(100),
    status INTEGER,
    status_label VARCHAR(150),
    empleado_id INTEGER,
    codigo_empleado VARCHAR(50),
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    sync_run_id VARCHAR(100),
    sincronizado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX ux_marcaciones_crudas_zk_evento
ON asistencia.marcaciones_crudas (
    dispositivo_origen,
    (COALESCE(dispositivo_ip, '')),
    (COALESCE(zk_uid_registro, -1)),
    zk_user_id,
    fecha_hora,
    (COALESCE(punch, -1)),
    (COALESCE(status, -1))
);

-- ============================================================
-- asistencia.asistencias_diarias
-- ============================================================

CREATE TABLE asistencia.asistencias_diarias (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    empleado_id BIGINT NOT NULL,
    periodo_evaluacion_id BIGINT,
    politica_asistencia_id BIGINT NOT NULL,
    horario_id BIGINT NOT NULL,
    fecha DATE NOT NULL,
    entrada_programada TIMESTAMP WITH TIME ZONE,
    salida_programada TIMESTAMP WITH TIME ZONE,
    primera_entrada TIMESTAMP WITH TIME ZONE,
    ultima_salida TIMESTAMP WITH TIME ZONE,
    minutos_retardo INTEGER NOT NULL DEFAULT 0,
    minutos_ordinarios INTEGER NOT NULL DEFAULT 0,
    minutos_extra INTEGER NOT NULL DEFAULT 0,
    estatus VARCHAR(40) NOT NULL DEFAULT 'SIN_PROCESAR',
    puntos_generados SMALLINT NOT NULL DEFAULT 0,
    procesada BOOLEAN NOT NULL DEFAULT FALSE,
    requiere_revision BOOLEAN NOT NULL DEFAULT FALSE,
    observaciones VARCHAR(500),
    fecha_procesamiento TIMESTAMP WITH TIME ZONE,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_asistencias_diarias PRIMARY KEY (id),
    CONSTRAINT fk_asistencias_empleado
        FOREIGN KEY (empleado_id) REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_asistencias_periodo
        FOREIGN KEY (periodo_evaluacion_id) REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_asistencias_politica
        FOREIGN KEY (politica_asistencia_id) REFERENCES asistencia.politicas_asistencia (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_asistencias_horario
        FOREIGN KEY (horario_id) REFERENCES asistencia.horarios (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT uq_asistencias_empleado_fecha UNIQUE (empleado_id, fecha),
    CONSTRAINT ck_asistencias_minutos_no_negativos CHECK (
        minutos_retardo >= 0 AND minutos_ordinarios >= 0 AND minutos_extra >= 0
    ),
    CONSTRAINT ck_asistencias_puntos_no_negativos CHECK (puntos_generados >= 0),
    CONSTRAINT ck_asistencias_estatus CHECK (
        estatus IN (
            'SIN_PROCESAR', 'COMPLETO', 'COMPLETO_CON_TIEMPO_EXTRA',
            'TOLERANCIA', 'RETARDO_MENOR', 'RETARDO_MAYOR',
            'FALTA', 'OMISION_ENTRADA', 'OMISION_SALIDA',
            'DIA_NO_LABORAL', 'JUSTIFICADA', 'CANCELADA'
        )
    ),
    CONSTRAINT ck_asistencias_procesamiento CHECK (
        (procesada = TRUE AND fecha_procesamiento IS NOT NULL)
        OR (procesada = FALSE)
    )
);

CREATE INDEX ix_asistencias_empleado ON asistencia.asistencias_diarias (empleado_id);
CREATE INDEX ix_asistencias_fecha ON asistencia.asistencias_diarias (fecha);
CREATE INDEX ix_asistencias_estatus ON asistencia.asistencias_diarias (estatus);
