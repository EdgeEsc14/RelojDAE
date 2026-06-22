BEGIN;

CREATE SCHEMA IF NOT EXISTS personal
    AUTHORIZATION reloj_app;


CREATE TABLE IF NOT EXISTS personal.empleados (
    id BIGINT GENERATED ALWAYS AS IDENTITY,

    codigo_empleado VARCHAR(30) NOT NULL,

    nombres VARCHAR(120) NOT NULL,

    apellido_paterno VARCHAR(80) NOT NULL,

    apellido_materno VARCHAR(80),

    nombre_completo VARCHAR(300)
        GENERATED ALWAYS AS (
            BTRIM(
                nombres
                || ' '
                || apellido_paterno
                || ' '
                || COALESCE(apellido_materno, '')
            )
        ) STORED,

    rfc VARCHAR(13),

    correo_electronico VARCHAR(150),

    departamento_id BIGINT NOT NULL,

    puesto_id BIGINT NOT NULL,

    supervisor_id BIGINT,

    fecha_ingreso DATE,

    fecha_baja DATE,

    estatus VARCHAR(20)
        NOT NULL DEFAULT 'ACTIVO',

    activo BOOLEAN
        NOT NULL DEFAULT TRUE,

    fecha_creacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_modificacion TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_empleados
        PRIMARY KEY (id),

    CONSTRAINT uq_empleados_codigo
        UNIQUE (codigo_empleado),

    CONSTRAINT fk_empleados_departamento
        FOREIGN KEY (departamento_id)
        REFERENCES organizacion.departamentos (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_empleados_puesto
        FOREIGN KEY (puesto_id)
        REFERENCES organizacion.puestos (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_empleados_supervisor
        FOREIGN KEY (supervisor_id)
        REFERENCES personal.empleados (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT ck_empleados_codigo_no_vacio
        CHECK (
            BTRIM(codigo_empleado) <> ''
        ),

    CONSTRAINT ck_empleados_codigo_formato
        CHECK (
            codigo_empleado = UPPER(BTRIM(codigo_empleado))
            AND codigo_empleado ~ '^EMP-[0-9]{4,}$'
        ),

    CONSTRAINT ck_empleados_nombres_no_vacios
        CHECK (
            BTRIM(nombres) <> ''
        ),

    CONSTRAINT ck_empleados_apellido_paterno_no_vacio
        CHECK (
            BTRIM(apellido_paterno) <> ''
        ),

    CONSTRAINT ck_empleados_rfc_formato
        CHECK (
            rfc IS NULL
            OR rfc ~ '^[A-ZÑ&]{4}[0-9]{6}[A-Z0-9]{3}$'
        ),

    CONSTRAINT ck_empleados_correo_no_vacio
        CHECK (
            correo_electronico IS NULL
            OR BTRIM(correo_electronico) <> ''
        ),

    CONSTRAINT ck_empleados_estatus
        CHECK (
            estatus IN (
                'ACTIVO',
                'INACTIVO',
                'BAJA'
            )
        ),

    CONSTRAINT ck_empleados_no_autosupervision
        CHECK (
            supervisor_id IS NULL
            OR supervisor_id <> id
        ),

    CONSTRAINT ck_empleados_fechas
        CHECK (
            fecha_baja IS NULL
            OR fecha_ingreso IS NULL
            OR fecha_baja >= fecha_ingreso
        )
);


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_empleados_rfc
ON personal.empleados (
    UPPER(rfc)
)
WHERE rfc IS NOT NULL;


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_empleados_correo
ON personal.empleados (
    LOWER(BTRIM(correo_electronico))
)
WHERE correo_electronico IS NOT NULL;


CREATE INDEX IF NOT EXISTS
    ix_empleados_departamento
ON personal.empleados (
    departamento_id
);


CREATE INDEX IF NOT EXISTS
    ix_empleados_puesto
ON personal.empleados (
    puesto_id
);


CREATE INDEX IF NOT EXISTS
    ix_empleados_supervisor
ON personal.empleados (
    supervisor_id
);


CREATE INDEX IF NOT EXISTS
    ix_empleados_nombre_completo
ON personal.empleados (
    nombre_completo
);


COMMIT;