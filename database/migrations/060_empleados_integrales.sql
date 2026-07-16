\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

-- ============================================================
-- 060_empleados_integrales.sql
--
-- Amplía el módulo de empleados con:
-- - Datos fiscales y de contacto.
-- - Catálogo de contratación.
-- - Códigos DAE-####.
-- - Estado detallado de sincronización con relojes.
-- - Soporte para varios dispositivos.
-- - Preparación para bloqueo sin eliminar al usuario físico.
-- ============================================================


-- ============================================================
-- 1. Catálogo de tipos de contratación
-- ============================================================

CREATE TABLE IF NOT EXISTS personal.tipos_contratacion (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion VARCHAR(500),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    orden SMALLINT NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_tipos_contratacion_codigo
        UNIQUE (codigo),

    CONSTRAINT ck_tipos_contratacion_codigo_no_vacio
        CHECK (BTRIM(codigo) <> ''),

    CONSTRAINT ck_tipos_contratacion_nombre_no_vacio
        CHECK (BTRIM(nombre) <> '')
);

INSERT INTO personal.tipos_contratacion (
    codigo,
    nombre,
    descripcion,
    orden,
    activo
)
VALUES
    (
        'BASE',
        'Base',
        'Personal con plaza o nombramiento de base.',
        10,
        TRUE
    ),
    (
        'CONFIANZA',
        'Confianza',
        'Personal con nombramiento de confianza.',
        20,
        TRUE
    ),
    (
        'HONORARIOS',
        'Honorarios',
        'Prestación de servicios profesionales por honorarios.',
        30,
        TRUE
    ),
    (
        'CARTA_COMPROMISO',
        'Carta compromiso',
        'Personal incorporado mediante carta compromiso.',
        40,
        TRUE
    ),
    (
        'EVENTUAL',
        'Eventual',
        'Personal contratado por un periodo determinado.',
        50,
        TRUE
    ),
    (
        'SERVICIO_SOCIAL',
        'Servicio social',
        'Prestador o prestadora de servicio social.',
        60,
        TRUE
    ),
    (
        'PRACTICAS_PROFESIONALES',
        'Prácticas profesionales',
        'Persona que realiza prácticas profesionales.',
        70,
        TRUE
    ),
    (
        'OTRO',
        'Otro',
        'Tipo de contratación no contemplado en el catálogo.',
        100,
        TRUE
    )
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    orden = EXCLUDED.orden,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;


-- ============================================================
-- 2. Nuevos datos del empleado
-- ============================================================

ALTER TABLE personal.empleados
ADD COLUMN IF NOT EXISTS rfc VARCHAR(13);

ALTER TABLE personal.empleados
ADD COLUMN IF NOT EXISTS curp VARCHAR(18);

ALTER TABLE personal.empleados
ADD COLUMN IF NOT EXISTS telefono VARCHAR(30);

ALTER TABLE personal.empleados
ADD COLUMN IF NOT EXISTS correo_personal VARCHAR(254);

ALTER TABLE personal.empleados
ADD COLUMN IF NOT EXISTS tipo_contratacion_id BIGINT;

ALTER TABLE personal.empleados
ADD COLUMN IF NOT EXISTS observaciones TEXT;

ALTER TABLE personal.empleados
ADD COLUMN IF NOT EXISTS motivo_baja VARCHAR(500);


-- Normalización preventiva.
UPDATE personal.empleados
SET rfc = NULLIF(
    UPPER(BTRIM(rfc)),
    ''
)
WHERE rfc IS NOT NULL;

UPDATE personal.empleados
SET curp = NULLIF(
    UPPER(BTRIM(curp)),
    ''
)
WHERE curp IS NOT NULL;

UPDATE personal.empleados
SET telefono = NULLIF(
    BTRIM(telefono),
    ''
)
WHERE telefono IS NOT NULL;

UPDATE personal.empleados
SET correo_personal = NULLIF(
    LOWER(BTRIM(correo_personal)),
    ''
)
WHERE correo_personal IS NOT NULL;


-- ============================================================
-- 3. Relaciones y validaciones de empleados
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_empleados_tipo_contratacion'
          AND conrelid = 'personal.empleados'::regclass
    ) THEN
        ALTER TABLE personal.empleados
        ADD CONSTRAINT fk_empleados_tipo_contratacion
        FOREIGN KEY (tipo_contratacion_id)
        REFERENCES personal.tipos_contratacion(id)
        ON DELETE RESTRICT;
    END IF;
END;
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_empleados_rfc_formato'
          AND conrelid = 'personal.empleados'::regclass
    ) THEN
        ALTER TABLE personal.empleados
        ADD CONSTRAINT ck_empleados_rfc_formato
        CHECK (
            rfc IS NULL
            OR (
                CHAR_LENGTH(rfc) IN (12, 13)
                AND rfc = UPPER(rfc)
                AND rfc !~ '[[:space:]]'
            )
        );
    END IF;
END;
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_empleados_curp_formato'
          AND conrelid = 'personal.empleados'::regclass
    ) THEN
        ALTER TABLE personal.empleados
        ADD CONSTRAINT ck_empleados_curp_formato
        CHECK (
            curp IS NULL
            OR (
                CHAR_LENGTH(curp) = 18
                AND curp = UPPER(curp)
                AND curp !~ '[[:space:]]'
            )
        );
    END IF;
END;
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_empleados_correo_personal'
          AND conrelid = 'personal.empleados'::regclass
    ) THEN
        ALTER TABLE personal.empleados
        ADD CONSTRAINT ck_empleados_correo_personal
        CHECK (
            correo_personal IS NULL
            OR (
                BTRIM(correo_personal) <> ''
                AND POSITION('@' IN correo_personal) > 1
            )
        );
    END IF;
END;
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_empleados_baja_consistente'
          AND conrelid = 'personal.empleados'::regclass
    ) THEN
        ALTER TABLE personal.empleados
        ADD CONSTRAINT ck_empleados_baja_consistente
        CHECK (
            fecha_baja IS NULL
            OR fecha_ingreso IS NULL
            OR fecha_baja >= fecha_ingreso
        );
    END IF;
END;
$$;


CREATE UNIQUE INDEX IF NOT EXISTS ux_empleados_rfc
ON personal.empleados (
    UPPER(BTRIM(rfc))
)
WHERE rfc IS NOT NULL
  AND BTRIM(rfc) <> '';


CREATE UNIQUE INDEX IF NOT EXISTS ux_empleados_curp
ON personal.empleados (
    UPPER(BTRIM(curp))
)
WHERE curp IS NOT NULL
  AND BTRIM(curp) <> '';


CREATE INDEX IF NOT EXISTS ix_empleados_tipo_contratacion
ON personal.empleados (tipo_contratacion_id);


CREATE INDEX IF NOT EXISTS ix_empleados_supervisor
ON personal.empleados (supervisor_id);


-- ============================================================
-- 4. Secuencia para códigos DAE-####
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS personal.codigo_empleado_dae_seq
AS BIGINT
MINVALUE 1
START WITH 1
INCREMENT BY 1
CACHE 1;


DO $$
DECLARE
    v_maximo BIGINT;
BEGIN
    SELECT MAX(
        (
            SUBSTRING(
                codigo_empleado
                FROM '^DAE-([0-9]+)$'
            )
        )::BIGINT
    )
    INTO v_maximo
    FROM personal.empleados
    WHERE codigo_empleado ~ '^DAE-[0-9]+$';

    IF v_maximo IS NULL THEN
        PERFORM setval(
            'personal.codigo_empleado_dae_seq',
            1,
            FALSE
        );
    ELSE
        PERFORM setval(
            'personal.codigo_empleado_dae_seq',
            v_maximo,
            TRUE
        );
    END IF;
END;
$$;


CREATE OR REPLACE FUNCTION personal.generar_codigo_empleado_dae()
RETURNS VARCHAR
LANGUAGE plpgsql
VOLATILE
AS $$
DECLARE
    v_numero BIGINT;
BEGIN
    v_numero := nextval(
        'personal.codigo_empleado_dae_seq'
    );

    RETURN
        'DAE-' ||
        CASE
            WHEN v_numero < 10000
                THEN LPAD(v_numero::TEXT, 4, '0')
            ELSE v_numero::TEXT
        END;
END;
$$;


COMMENT ON FUNCTION personal.generar_codigo_empleado_dae() IS
'Genera el siguiente código laboral con formato DAE-####.';


-- ============================================================
-- 5. Dispositivo predeterminado
-- ============================================================

ALTER TABLE dispositivos.dispositivos
ADD COLUMN IF NOT EXISTS es_predeterminado BOOLEAN
NOT NULL DEFAULT FALSE;


UPDATE dispositivos.dispositivos
SET es_predeterminado = TRUE
WHERE id = (
    SELECT d.id
    FROM dispositivos.dispositivos d
    WHERE d.activo = TRUE
    ORDER BY d.id
    LIMIT 1
)
AND NOT EXISTS (
    SELECT 1
    FROM dispositivos.dispositivos d2
    WHERE d2.es_predeterminado = TRUE
);


CREATE UNIQUE INDEX IF NOT EXISTS ux_dispositivos_un_predeterminado
ON dispositivos.dispositivos ((1))
WHERE es_predeterminado = TRUE;


-- ============================================================
-- 6. Estado detallado de sincronización por reloj
-- ============================================================

ALTER TABLE dispositivos.empleado_dispositivo
ADD COLUMN IF NOT EXISTS estado_sincronizacion VARCHAR(30)
NOT NULL DEFAULT 'PENDIENTE';

ALTER TABLE dispositivos.empleado_dispositivo
ADD COLUMN IF NOT EXISTS intentos_sincronizacion INTEGER
NOT NULL DEFAULT 0;

ALTER TABLE dispositivos.empleado_dispositivo
ADD COLUMN IF NOT EXISTS fecha_ultimo_intento TIMESTAMPTZ;

ALTER TABLE dispositivos.empleado_dispositivo
ADD COLUMN IF NOT EXISTS ultimo_error TEXT;

ALTER TABLE dispositivos.empleado_dispositivo
ADD COLUMN IF NOT EXISTS solicitado_por_usuario_id BIGINT;

ALTER TABLE dispositivos.empleado_dispositivo
ADD COLUMN IF NOT EXISTS fecha_bloqueo TIMESTAMPTZ;

ALTER TABLE dispositivos.empleado_dispositivo
ADD COLUMN IF NOT EXISTS motivo_bloqueo VARCHAR(500);


-- Adaptar relaciones existentes.
UPDATE dispositivos.empleado_dispositivo
SET estado_sincronizacion = 'SINCRONIZADO'
WHERE sincronizado = TRUE;

UPDATE dispositivos.empleado_dispositivo
SET estado_sincronizacion = 'PENDIENTE'
WHERE sincronizado = FALSE
  AND estado_sincronizacion NOT IN (
      'ERROR',
      'BLOQUEO_PENDIENTE',
      'BLOQUEADO',
      'ERROR_BLOQUEO'
  );


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname =
            'ck_empleado_dispositivo_estado_sincronizacion'
          AND conrelid =
            'dispositivos.empleado_dispositivo'::regclass
    ) THEN
        ALTER TABLE dispositivos.empleado_dispositivo
        ADD CONSTRAINT
            ck_empleado_dispositivo_estado_sincronizacion
        CHECK (
            estado_sincronizacion IN (
                'PENDIENTE',
                'SINCRONIZANDO',
                'SINCRONIZADO',
                'ERROR',
                'BLOQUEO_PENDIENTE',
                'BLOQUEADO',
                'ERROR_BLOQUEO'
            )
        );
    END IF;
END;
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname =
            'ck_empleado_dispositivo_intentos_no_negativos'
          AND conrelid =
            'dispositivos.empleado_dispositivo'::regclass
    ) THEN
        ALTER TABLE dispositivos.empleado_dispositivo
        ADD CONSTRAINT
            ck_empleado_dispositivo_intentos_no_negativos
        CHECK (intentos_sincronizacion >= 0);
    END IF;
END;
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname =
            'fk_empleado_dispositivo_solicitado_por'
          AND conrelid =
            'dispositivos.empleado_dispositivo'::regclass
    ) THEN
        ALTER TABLE dispositivos.empleado_dispositivo
        ADD CONSTRAINT
            fk_empleado_dispositivo_solicitado_por
        FOREIGN KEY (solicitado_por_usuario_id)
        REFERENCES seguridad.usuarios(id)
        ON DELETE SET NULL;
    END IF;
END;
$$;


CREATE INDEX IF NOT EXISTS
    ix_empleado_dispositivo_estado_sincronizacion
ON dispositivos.empleado_dispositivo (
    estado_sincronizacion
);


CREATE INDEX IF NOT EXISTS
    ix_empleado_dispositivo_pendientes
ON dispositivos.empleado_dispositivo (
    dispositivo_id,
    estado_sincronizacion
)
WHERE activo = TRUE
  AND estado_sincronizacion IN (
      'PENDIENTE',
      'ERROR',
      'BLOQUEO_PENDIENTE',
      'ERROR_BLOQUEO'
  );


-- ============================================================
-- 7. Comentarios
-- ============================================================

COMMENT ON COLUMN personal.empleados.rfc IS
'RFC del empleado. Obligatorio para nuevas altas desde la aplicación.';

COMMENT ON COLUMN personal.empleados.curp IS
'CURP opcional. Debe ser única cuando se capture.';

COMMENT ON COLUMN personal.empleados.correo_personal IS
'Correo personal utilizado para contacto y cuenta inicial.';

COMMENT ON COLUMN personal.empleados.tipo_contratacion_id IS
'Tipo de contratación vigente del empleado.';

COMMENT ON COLUMN dispositivos.dispositivos.es_predeterminado IS
'Indica el reloj seleccionado inicialmente durante el alta.';

COMMENT ON COLUMN
    dispositivos.empleado_dispositivo.estado_sincronizacion IS
'Estado de la operación entre el empleado y el reloj físico.';

COMMENT ON COLUMN
    dispositivos.empleado_dispositivo.ultimo_error IS
'Último error obtenido al crear, actualizar o bloquear al usuario en el reloj.';


COMMIT;