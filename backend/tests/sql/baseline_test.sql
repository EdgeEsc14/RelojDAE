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
DROP SCHEMA IF EXISTS auditoria CASCADE;
DROP SCHEMA IF EXISTS asistencia CASCADE;
DROP SCHEMA IF EXISTS seguridad CASCADE;
DROP SCHEMA IF EXISTS dispositivos CASCADE;
DROP SCHEMA IF EXISTS personal CASCADE;
DROP SCHEMA IF EXISTS organizacion CASCADE;

-- ============================================================
-- SCHEMAS
-- ============================================================

CREATE SCHEMA personal AUTHORIZATION reloj_app;
CREATE SCHEMA organizacion AUTHORIZATION reloj_app;
CREATE SCHEMA asistencia AUTHORIZATION reloj_app;
CREATE SCHEMA auditoria AUTHORIZATION reloj_app;
CREATE SCHEMA dispositivos AUTHORIZATION reloj_app;

-- ============================================================
-- organizacion.tipos_unidad (Dirección/División/Departamento/...)
-- Migración 010: distingue nivel jerárquico de cada unidad para que
-- el reporte departamental no mezcle Dirección/División con
-- Departamento.
-- ============================================================

CREATE TABLE organizacion.tipos_unidad (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(30) NOT NULL,
    nombre VARCHAR(80) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_tipos_unidad PRIMARY KEY (id),
    CONSTRAINT uq_tipos_unidad_codigo UNIQUE (codigo)
);

INSERT INTO organizacion.tipos_unidad (codigo, nombre) VALUES
    ('DIRECCION', 'Dirección'),
    ('DIVISION', 'División'),
    ('DEPARTAMENTO', 'Departamento'),
    ('COMITE', 'Comité'),
    ('ENCARGADURIA', 'Encargaduría');

-- ============================================================
-- organizacion.unidades_organizacionales (dependencia de empleados)
-- ============================================================

CREATE TABLE organizacion.unidades_organizacionales (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(60) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    unidad_padre_id BIGINT,
    tipo_unidad_id BIGINT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_unidades_organizacionales PRIMARY KEY (id),
    CONSTRAINT uq_unidades_organizacionales_codigo UNIQUE (codigo),
    CONSTRAINT fk_unidades_organizacionales_padre
        FOREIGN KEY (unidad_padre_id)
        REFERENCES organizacion.unidades_organizacionales (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_unidades_organizacionales_tipo
        FOREIGN KEY (tipo_unidad_id)
        REFERENCES organizacion.tipos_unidad (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
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
-- dispositivos.dispositivos / dispositivos.empleado_dispositivo
--
-- Subconjunto fiel de la migración 024_create_dispositivos.sql,
-- indispensable para probar la resolución canónica de identidad ZK
-- (dispositivo_origen + zk_user_id) frente al fallback legacy
-- personal.empleados.zk_user_id (Contrato §10).
-- ============================================================

CREATE TABLE dispositivos.dispositivos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(40) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    ip INET NOT NULL,
    puerto INTEGER NOT NULL DEFAULT 4370,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_dispositivos PRIMARY KEY (id),
    CONSTRAINT uq_dispositivos_codigo UNIQUE (codigo)
);

CREATE TABLE dispositivos.empleado_dispositivo (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    empleado_id BIGINT NOT NULL,
    dispositivo_id BIGINT NOT NULL,
    zk_uid INTEGER,
    zk_user_id VARCHAR(50) NOT NULL,
    nombre_en_dispositivo VARCHAR(150),
    sincronizado BOOLEAN NOT NULL DEFAULT FALSE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_empleado_dispositivo PRIMARY KEY (id),
    CONSTRAINT fk_empleado_dispositivo_empleado
        FOREIGN KEY (empleado_id) REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_empleado_dispositivo_dispositivo
        FOREIGN KEY (dispositivo_id) REFERENCES dispositivos.dispositivos (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ck_empleado_dispositivo_zk_user_id_no_vacio
        CHECK (BTRIM(zk_user_id) <> '')
);

CREATE UNIQUE INDEX uq_empleado_dispositivo_zk_user_id_activo
ON dispositivos.empleado_dispositivo (dispositivo_id, zk_user_id)
WHERE activo = TRUE;

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

-- ============================================================
-- asistencia.tipos_incidencia / asistencia.incidencias /
-- asistencia.movimientos_puntos
--
-- Subconjunto reducido: listar_asistencia_diaria() y
-- obtener_resumen_asistencia_empleado() las consultan siempre (LEFT
-- JOIN / conteo), aunque estén vacías, así que deben existir para las
-- pruebas HTTP de autorización. Sin datos semilla — solo estructura.
-- ============================================================

CREATE TABLE asistencia.tipos_incidencia (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    categoria VARCHAR(30) NOT NULL,

    CONSTRAINT pk_tipos_incidencia PRIMARY KEY (id),
    CONSTRAINT uq_tipos_incidencia_codigo UNIQUE (codigo)
);

CREATE TABLE asistencia.incidencias (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    empleado_id BIGINT NOT NULL,
    asistencia_diaria_id BIGINT,
    periodo_evaluacion_id BIGINT,
    tipo_incidencia_id BIGINT NOT NULL,
    fecha DATE NOT NULL,
    descripcion VARCHAR(700),
    puntos_originales SMALLINT NOT NULL DEFAULT 0,
    puntos_justificados SMALLINT NOT NULL DEFAULT 0,
    puntos_efectivos SMALLINT
        GENERATED ALWAYS AS (
            GREATEST(puntos_originales - puntos_justificados, 0)
        ) STORED,
    estatus VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
    origen VARCHAR(30) NOT NULL DEFAULT 'PROCESAMIENTO',
    requiere_revision BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT pk_incidencias PRIMARY KEY (id),
    CONSTRAINT fk_incidencias_empleado
        FOREIGN KEY (empleado_id) REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_incidencias_asistencia
        FOREIGN KEY (asistencia_diaria_id)
        REFERENCES asistencia.asistencias_diarias (id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_incidencias_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_incidencias_tipo
        FOREIGN KEY (tipo_incidencia_id)
        REFERENCES asistencia.tipos_incidencia (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX ix_incidencias_asistencia ON asistencia.incidencias (asistencia_diaria_id);

CREATE TABLE asistencia.movimientos_puntos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    empleado_id BIGINT NOT NULL,
    periodo_evaluacion_id BIGINT,
    fecha DATE NOT NULL,
    tipo_movimiento VARCHAR(30) NOT NULL,
    concepto VARCHAR(150) NOT NULL,
    puntos SMALLINT NOT NULL,
    descripcion VARCHAR(700),
    origen VARCHAR(30) NOT NULL DEFAULT 'SISTEMA',
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_movimientos_puntos PRIMARY KEY (id),
    CONSTRAINT fk_movimientos_puntos_empleado
        FOREIGN KEY (empleado_id) REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_movimientos_puntos_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- ============================================================
-- asistencia.resumen_periodo_empleado
--
-- Subconjunto reducido: acumular_puntos_periodo() la actualiza siempre
-- tras procesar_asistencia_diaria() (POST /asistencia/procesar), aunque
-- no exista ningún periodo abierto que empate (UPDATE sin filas
-- afectadas es válido). Solo estructura, sin datos semilla.
-- ============================================================

CREATE TABLE asistencia.resumen_periodo_empleado (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    empleado_id BIGINT NOT NULL,
    periodo_evaluacion_id BIGINT NOT NULL,
    politica_asistencia_id BIGINT,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    dias_completos SMALLINT NOT NULL DEFAULT 0,
    retardos_menores SMALLINT NOT NULL DEFAULT 0,
    retardos_mayores SMALLINT NOT NULL DEFAULT 0,
    faltas SMALLINT NOT NULL DEFAULT 0,
    minutos_ordinarios INTEGER NOT NULL DEFAULT 0,
    minutos_extra INTEGER NOT NULL DEFAULT 0,
    minutos_retardo INTEGER NOT NULL DEFAULT 0,
    puntos_brutos SMALLINT NOT NULL DEFAULT 0,
    descansos_obligatorios_generados SMALLINT NOT NULL DEFAULT 0,
    faltas_consecutivas_max SMALLINT NOT NULL DEFAULT 0,
    estatus VARCHAR(30) NOT NULL DEFAULT 'ABIERTO',
    fecha_calculo TIMESTAMP WITH TIME ZONE,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_resumen_periodo_empleado PRIMARY KEY (id),
    CONSTRAINT fk_resumen_periodo_empleado_empleado
        FOREIGN KEY (empleado_id) REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_resumen_periodo_empleado_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- ============================================================
-- SCHEMA: seguridad
-- Subconjunto fiel del esquema real (migraciones 012, 013, 015, 017,
-- 018, 054), reducido a las columnas que usa build_access_scope /
-- get_current_user / get_allowed_employee_ids para las pruebas HTTP de
-- autorización (Contrato §16). Tipos, nombres y CHECK de alcance/acciones
-- reales preservados.
-- ============================================================

CREATE SCHEMA seguridad AUTHORIZATION reloj_app;

CREATE TABLE seguridad.roles (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(40) NOT NULL,
    nombre VARCHAR(80) NOT NULL,
    descripcion VARCHAR(300),
    es_sistema BOOLEAN NOT NULL DEFAULT FALSE,
    orden_visual SMALLINT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_roles PRIMARY KEY (id),
    CONSTRAINT uq_roles_codigo UNIQUE (codigo)
);

CREATE TABLE seguridad.modulos (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_modulos PRIMARY KEY (id),
    CONSTRAINT uq_modulos_codigo UNIQUE (codigo)
);

CREATE TABLE seguridad.permisos_rol (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    rol_id BIGINT NOT NULL,
    modulo_id BIGINT NOT NULL,

    alcance_datos VARCHAR(20) NOT NULL DEFAULT 'NINGUNO',

    puede_consultar BOOLEAN NOT NULL DEFAULT FALSE,
    puede_crear BOOLEAN NOT NULL DEFAULT FALSE,
    puede_editar BOOLEAN NOT NULL DEFAULT FALSE,
    puede_eliminar BOOLEAN NOT NULL DEFAULT FALSE,
    puede_aprobar BOOLEAN NOT NULL DEFAULT FALSE,
    puede_exportar BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT pk_permisos_rol PRIMARY KEY (id),
    CONSTRAINT fk_permisos_rol_rol
        FOREIGN KEY (rol_id) REFERENCES seguridad.roles (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_permisos_rol_modulo
        FOREIGN KEY (modulo_id) REFERENCES seguridad.modulos (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT uq_permisos_rol_rol_modulo UNIQUE (rol_id, modulo_id),

    CONSTRAINT ck_permisos_rol_alcance CHECK (
        alcance_datos IN ('TOTAL', 'AREA', 'PROPIO', 'NINGUNO')
    ),
    CONSTRAINT ck_permisos_rol_acciones_requieren_consulta CHECK (
        puede_consultar = TRUE
        OR (
            puede_crear = FALSE
            AND puede_editar = FALSE
            AND puede_eliminar = FALSE
            AND puede_aprobar = FALSE
            AND puede_exportar = FALSE
        )
    )
);

CREATE TABLE seguridad.usuarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    empleado_id BIGINT,
    rol_id BIGINT NOT NULL,
    rol VARCHAR(50),

    correo VARCHAR(255),
    correo_electronico VARCHAR(150) NOT NULL,
    nombre_usuario VARCHAR(100),
    password_hash TEXT,

    estatus VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    correo_verificado BOOLEAN NOT NULL DEFAULT TRUE,
    requiere_cambio_password BOOLEAN NOT NULL DEFAULT FALSE,

    ultimo_login TIMESTAMP WITHOUT TIME ZONE,
    ultimo_login_ip INET,
    ultimo_login_ip_raw VARCHAR(255),
    ultimo_login_user_agent TEXT,

    fecha_creacion TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    fecha_modificacion TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_usuarios PRIMARY KEY (id),
    CONSTRAINT fk_usuarios_empleado
        FOREIGN KEY (empleado_id) REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_usuarios_rol
        FOREIGN KEY (rol_id) REFERENCES seguridad.roles (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ck_usuarios_estatus CHECK (
        estatus IN (
            'ACTIVO',
            'INACTIVO',
            'PENDIENTE_VERIFICACION',
            'PENDIENTE_APROBACION',
            'RECHAZADO',
            'BLOQUEADO'
        )
    )
);

-- Un empleado no puede tener dos cuentas VIGENTES simultáneas (fiel a
-- ux_usuarios_empleado_activo, migración 054): cuentas inactivas
-- históricas no bloquean crear una nueva.
CREATE UNIQUE INDEX ux_usuarios_empleado_activo
ON seguridad.usuarios (empleado_id)
WHERE empleado_id IS NOT NULL
  AND estatus IN ('ACTIVO', 'PENDIENTE_APROBACION', 'PENDIENTE_VERIFICACION');

CREATE TABLE seguridad.usuarios_unidades (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    usuario_id BIGINT NOT NULL,
    unidad_organizacional_id BIGINT NOT NULL,

    incluye_descendientes BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_fin DATE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_usuarios_unidades PRIMARY KEY (id),
    CONSTRAINT fk_usuarios_unidades_usuario
        FOREIGN KEY (usuario_id) REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT fk_usuarios_unidades_unidad
        FOREIGN KEY (unidad_organizacional_id)
        REFERENCES organizacion.unidades_organizacionales (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ck_usuarios_unidades_fechas CHECK (
        fecha_fin IS NULL OR fecha_fin >= fecha_inicio
    )
);

CREATE INDEX ix_usuarios_unidades_usuario ON seguridad.usuarios_unidades (usuario_id);

-- ============================================================
-- seguridad.login_auditoria
--
-- Subconjunto fiel de la migración 055: POST /auth/login la escribe en
-- cada intento (éxito o fallo), así que debe existir para probar login
-- end-to-end.
-- ============================================================

CREATE TABLE seguridad.login_auditoria (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT,
    correo_intentado VARCHAR(255),
    resultado VARCHAR(50) NOT NULL,
    motivo VARCHAR(100),
    ip_origen INET,
    ip_origen_raw VARCHAR(255),
    forwarded_for TEXT,
    user_agent TEXT,
    metodo_http VARCHAR(20),
    ruta VARCHAR(255),
    fecha_evento TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_login_auditoria_usuario
        FOREIGN KEY (usuario_id) REFERENCES seguridad.usuarios (id)
        ON DELETE SET NULL,
    CONSTRAINT ck_login_auditoria_resultado CHECK (
        resultado IN (
            'EXITOSO',
            'FALLIDO',
            'BLOQUEADO',
            'PENDIENTE_VERIFICACION',
            'PENDIENTE_APROBACION',
            'USUARIO_INACTIVO',
            'ERROR'
        )
    )
);

-- ============================================================
-- auditoria.bitacora
--
-- Subconjunto fiel de la migración 035: trigger genérico de
-- INSERT/UPDATE/DELETE aplicado a todas las tablas base de
-- organizacion/personal/asistencia/seguridad/dispositivos, igual que
-- en producción. Necesario para probar /auditoria end-to-end contra
-- cambios reales, no simulados.
-- ============================================================

CREATE TABLE auditoria.bitacora (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    esquema VARCHAR(80) NOT NULL,
    tabla VARCHAR(120) NOT NULL,
    operacion VARCHAR(20) NOT NULL,
    registro_id TEXT,
    usuario_bd TEXT NOT NULL DEFAULT CURRENT_USER,
    usuario_app_id BIGINT,
    usuario_app_correo VARCHAR(320),
    ip_origen VARCHAR(80),
    modulo VARCHAR(80),
    accion_app VARCHAR(150),
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    cambios JSONB,
    fecha_evento TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),

    CONSTRAINT pk_bitacora PRIMARY KEY (id),
    CONSTRAINT ck_bitacora_operacion CHECK (operacion IN ('INSERT', 'UPDATE', 'DELETE'))
);

CREATE INDEX ix_bitacora_fecha_evento ON auditoria.bitacora (fecha_evento);
CREATE INDEX ix_bitacora_tabla ON auditoria.bitacora (esquema, tabla);

CREATE OR REPLACE FUNCTION auditoria.fn_sanitizar_json(p_registro JSONB)
RETURNS JSONB
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT
        p_registro
        - 'password_hash'
        - 'password_reloj'
        - 'password_comunicacion'
        - 'token'
        - 'access_token'
        - 'refresh_token';
$$;

CREATE OR REPLACE FUNCTION auditoria.fn_jsonb_diff(
    p_anterior JSONB,
    p_nuevo JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_resultado JSONB := '{}'::JSONB;
    v_campo TEXT;
    v_valor_anterior JSONB;
    v_valor_nuevo JSONB;
BEGIN
    FOR v_campo IN
        SELECT jsonb_object_keys(p_anterior || p_nuevo)
    LOOP
        v_valor_anterior := p_anterior -> v_campo;
        v_valor_nuevo := p_nuevo -> v_campo;

        IF v_valor_anterior IS DISTINCT FROM v_valor_nuevo THEN
            v_resultado :=
                v_resultado ||
                jsonb_build_object(
                    v_campo,
                    jsonb_build_object('antes', v_valor_anterior, 'despues', v_valor_nuevo)
                );
        END IF;
    END LOOP;

    RETURN v_resultado;
END;
$$;

CREATE OR REPLACE FUNCTION auditoria.fn_registrar_bitacora()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_datos_anteriores JSONB;
    v_datos_nuevos JSONB;
    v_cambios JSONB;
    v_registro_id TEXT;
    v_usuario_app_id_text TEXT;
    v_usuario_app_id BIGINT;
    v_usuario_app_correo TEXT;
    v_ip_origen TEXT;
    v_modulo TEXT;
    v_accion_app TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_datos_nuevos := auditoria.fn_sanitizar_json(to_jsonb(NEW));
        v_datos_anteriores := NULL;
        v_cambios := NULL;
        v_registro_id := v_datos_nuevos ->> 'id';
    ELSIF TG_OP = 'UPDATE' THEN
        v_datos_anteriores := auditoria.fn_sanitizar_json(to_jsonb(OLD));
        v_datos_nuevos := auditoria.fn_sanitizar_json(to_jsonb(NEW));
        v_cambios := auditoria.fn_jsonb_diff(v_datos_anteriores, v_datos_nuevos);

        IF v_cambios = '{}'::JSONB THEN
            RETURN NEW;
        END IF;

        v_registro_id := COALESCE(v_datos_nuevos ->> 'id', v_datos_anteriores ->> 'id');
    ELSIF TG_OP = 'DELETE' THEN
        v_datos_anteriores := auditoria.fn_sanitizar_json(to_jsonb(OLD));
        v_datos_nuevos := NULL;
        v_cambios := NULL;
        v_registro_id := v_datos_anteriores ->> 'id';
    END IF;

    v_usuario_app_id_text := NULLIF(current_setting('app.usuario_id', TRUE), '');

    BEGIN
        IF v_usuario_app_id_text IS NOT NULL THEN
            v_usuario_app_id := v_usuario_app_id_text::BIGINT;
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            v_usuario_app_id := NULL;
    END;

    v_usuario_app_correo := NULLIF(current_setting('app.usuario_correo', TRUE), '');
    v_ip_origen := NULLIF(current_setting('app.ip_origen', TRUE), '');
    v_modulo := NULLIF(current_setting('app.modulo', TRUE), '');
    v_accion_app := NULLIF(current_setting('app.accion', TRUE), '');

    INSERT INTO auditoria.bitacora (
        esquema, tabla, operacion, registro_id, usuario_bd,
        usuario_app_id, usuario_app_correo, ip_origen, modulo, accion_app,
        datos_anteriores, datos_nuevos, cambios, fecha_evento
    )
    VALUES (
        TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP, v_registro_id, CURRENT_USER,
        v_usuario_app_id, v_usuario_app_correo, v_ip_origen, v_modulo, v_accion_app,
        v_datos_anteriores, v_datos_nuevos, v_cambios, clock_timestamp()
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION auditoria.fn_crear_trigger_auditoria(
    p_esquema TEXT,
    p_tabla TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_trigger_name TEXT;
BEGIN
    v_trigger_name := 'trg_auditoria_' || p_esquema || '_' || p_tabla;

    EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I.%I', v_trigger_name, p_esquema, p_tabla);
    EXECUTE format(
        'CREATE TRIGGER %I AFTER INSERT OR UPDATE OR DELETE ON %I.%I
         FOR EACH ROW EXECUTE FUNCTION auditoria.fn_registrar_bitacora()',
        v_trigger_name, p_esquema, p_tabla
    );
END;
$$;

-- ============================================================
-- asistencia.descansos_obligatorios
--
-- Fiel a migraciones/034_create_descansos_y_sincronizaciones.sql.
-- acumular_puntos_periodo() escribe aquí los DO reales (Contrato: 10
-- puntos acumulados en el periodo -> 1 DO). No usar
-- asistencia.movimientos_puntos para esto: esa tabla exige puntos != 0
-- (y puntos > 0 para tipo_movimiento='CARGO'), y un DO no es un cargo
-- de puntos. Se define aquí (tras seguridad.usuarios) porque tiene FKs
-- hacia ese esquema.
-- ============================================================

CREATE TABLE asistencia.descansos_obligatorios (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    empleado_id BIGINT NOT NULL,
    periodo_evaluacion_id BIGINT NOT NULL,
    resumen_periodo_empleado_id BIGINT,
    incidencia_id BIGINT,
    numero_descanso_periodo SMALLINT NOT NULL DEFAULT 1,
    numero_descanso_historico INTEGER,
    puntos_efectivos_periodo SMALLINT NOT NULL,
    fecha_generacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_programada DATE,
    fecha_aplicacion DATE,
    estatus VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
    requiere_revision_baja BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_revision_baja VARCHAR(700),
    generado_por_usuario_id BIGINT,
    programado_por_usuario_id BIGINT,
    aplicado_por_usuario_id BIGINT,
    cancelado_por_usuario_id BIGINT,
    fecha_cancelacion TIMESTAMP WITH TIME ZONE,
    motivo_cancelacion VARCHAR(700),
    observaciones VARCHAR(1000),
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_descansos_obligatorios PRIMARY KEY (id),
    CONSTRAINT fk_descansos_empleado
        FOREIGN KEY (empleado_id) REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_descansos_periodo
        FOREIGN KEY (periodo_evaluacion_id)
        REFERENCES asistencia.periodos_evaluacion (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_descansos_resumen
        FOREIGN KEY (resumen_periodo_empleado_id)
        REFERENCES asistencia.resumen_periodo_empleado (id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_descansos_incidencia
        FOREIGN KEY (incidencia_id) REFERENCES asistencia.incidencias (id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_descansos_generado_por
        FOREIGN KEY (generado_por_usuario_id) REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_descansos_programado_por
        FOREIGN KEY (programado_por_usuario_id) REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_descansos_aplicado_por
        FOREIGN KEY (aplicado_por_usuario_id) REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT fk_descansos_cancelado_por
        FOREIGN KEY (cancelado_por_usuario_id) REFERENCES seguridad.usuarios (id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    CONSTRAINT uq_descansos_empleado_periodo_numero
        UNIQUE (empleado_id, periodo_evaluacion_id, numero_descanso_periodo),
    CONSTRAINT ck_descansos_numero_periodo CHECK (numero_descanso_periodo > 0),
    CONSTRAINT ck_descansos_numero_historico
        CHECK (numero_descanso_historico IS NULL OR numero_descanso_historico > 0),
    CONSTRAINT ck_descansos_puntos CHECK (puntos_efectivos_periodo >= 0),
    CONSTRAINT ck_descansos_estatus
        CHECK (estatus IN ('PENDIENTE', 'PROGRAMADO', 'APLICADO', 'CANCELADO')),
    CONSTRAINT ck_descansos_programado
        CHECK ((estatus = 'PROGRAMADO' AND fecha_programada IS NOT NULL) OR (estatus <> 'PROGRAMADO')),
    CONSTRAINT ck_descansos_aplicado
        CHECK ((estatus = 'APLICADO' AND fecha_aplicacion IS NOT NULL) OR (estatus <> 'APLICADO')),
    CONSTRAINT ck_descansos_cancelado
        CHECK (
            (estatus = 'CANCELADO' AND fecha_cancelacion IS NOT NULL
                AND motivo_cancelacion IS NOT NULL AND BTRIM(motivo_cancelacion) <> '')
            OR (estatus <> 'CANCELADO')
        ),
    CONSTRAINT ck_descansos_fecha_aplicacion
        CHECK (fecha_aplicacion IS NULL OR fecha_programada IS NULL OR fecha_aplicacion >= fecha_programada),
    CONSTRAINT ck_descansos_motivo_revision_no_vacio
        CHECK (motivo_revision_baja IS NULL OR BTRIM(motivo_revision_baja) <> ''),
    CONSTRAINT ck_descansos_motivo_cancelacion_no_vacio
        CHECK (motivo_cancelacion IS NULL OR BTRIM(motivo_cancelacion) <> ''),
    CONSTRAINT ck_descansos_observaciones_no_vacias
        CHECK (observaciones IS NULL OR BTRIM(observaciones) <> '')
);

DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema IN ('organizacion', 'personal', 'asistencia', 'seguridad', 'dispositivos')
        ORDER BY table_schema, table_name
    LOOP
        PERFORM auditoria.fn_crear_trigger_auditoria(r.table_schema, r.table_name);
    END LOOP;
END $$;

CREATE OR REPLACE VIEW auditoria.vw_bitacora_resumen AS
SELECT
    id, fecha_evento, usuario_app_correo, usuario_app_id, usuario_bd,
    esquema, tabla, esquema || '.' || tabla AS objeto, operacion,
    registro_id, modulo, accion_app, cambios
FROM auditoria.bitacora;
