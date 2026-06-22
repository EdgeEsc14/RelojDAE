\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE SCHEMA IF NOT EXISTS auditoria;


CREATE TABLE IF NOT EXISTS auditoria.bitacora (
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

    fecha_evento TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT clock_timestamp(),

    CONSTRAINT pk_bitacora
        PRIMARY KEY (id),

    CONSTRAINT ck_bitacora_operacion
        CHECK (
            operacion IN (
                'INSERT',
                'UPDATE',
                'DELETE'
            )
        ),

    CONSTRAINT ck_bitacora_esquema_no_vacio
        CHECK (
            BTRIM(esquema) <> ''
        ),

    CONSTRAINT ck_bitacora_tabla_no_vacia
        CHECK (
            BTRIM(tabla) <> ''
        ),

    CONSTRAINT ck_bitacora_datos_operacion
        CHECK (
            (
                operacion = 'INSERT'
                AND datos_nuevos IS NOT NULL
            )
            OR
            (
                operacion = 'UPDATE'
                AND datos_anteriores IS NOT NULL
                AND datos_nuevos IS NOT NULL
            )
            OR
            (
                operacion = 'DELETE'
                AND datos_anteriores IS NOT NULL
            )
        )
);


CREATE INDEX IF NOT EXISTS
    ix_bitacora_fecha_evento
ON auditoria.bitacora (
    fecha_evento
);


CREATE INDEX IF NOT EXISTS
    ix_bitacora_tabla
ON auditoria.bitacora (
    esquema,
    tabla
);


CREATE INDEX IF NOT EXISTS
    ix_bitacora_operacion
ON auditoria.bitacora (
    operacion
);


CREATE INDEX IF NOT EXISTS
    ix_bitacora_registro
ON auditoria.bitacora (
    esquema,
    tabla,
    registro_id
);


CREATE INDEX IF NOT EXISTS
    ix_bitacora_usuario_app
ON auditoria.bitacora (
    usuario_app_id
);


CREATE INDEX IF NOT EXISTS
    ix_bitacora_usuario_correo
ON auditoria.bitacora (
    usuario_app_correo
);


CREATE INDEX IF NOT EXISTS
    ix_bitacora_cambios_gin
ON auditoria.bitacora
USING GIN (
    cambios
);


CREATE OR REPLACE FUNCTION auditoria.fn_sanitizar_json(
    p_registro JSONB
)
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
                    jsonb_build_object(
                        'antes',
                        v_valor_anterior,
                        'despues',
                        v_valor_nuevo
                    )
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
        v_datos_nuevos :=
            auditoria.fn_sanitizar_json(
                to_jsonb(NEW)
            );

        v_datos_anteriores := NULL;
        v_cambios := NULL;
        v_registro_id := v_datos_nuevos ->> 'id';

    ELSIF TG_OP = 'UPDATE' THEN
        v_datos_anteriores :=
            auditoria.fn_sanitizar_json(
                to_jsonb(OLD)
            );

        v_datos_nuevos :=
            auditoria.fn_sanitizar_json(
                to_jsonb(NEW)
            );

        v_cambios :=
            auditoria.fn_jsonb_diff(
                v_datos_anteriores,
                v_datos_nuevos
            );

        IF v_cambios = '{}'::JSONB THEN
            RETURN NEW;
        END IF;

        v_registro_id :=
            COALESCE(
                v_datos_nuevos ->> 'id',
                v_datos_anteriores ->> 'id'
            );

    ELSIF TG_OP = 'DELETE' THEN
        v_datos_anteriores :=
            auditoria.fn_sanitizar_json(
                to_jsonb(OLD)
            );

        v_datos_nuevos := NULL;
        v_cambios := NULL;
        v_registro_id := v_datos_anteriores ->> 'id';
    END IF;


    v_usuario_app_id_text :=
        NULLIF(
            current_setting(
                'app.usuario_id',
                TRUE
            ),
            ''
        );

    BEGIN
        IF v_usuario_app_id_text IS NOT NULL THEN
            v_usuario_app_id := v_usuario_app_id_text::BIGINT;
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            v_usuario_app_id := NULL;
    END;


    v_usuario_app_correo :=
        NULLIF(
            current_setting(
                'app.usuario_correo',
                TRUE
            ),
            ''
        );

    v_ip_origen :=
        NULLIF(
            current_setting(
                'app.ip_origen',
                TRUE
            ),
            ''
        );

    v_modulo :=
        NULLIF(
            current_setting(
                'app.modulo',
                TRUE
            ),
            ''
        );

    v_accion_app :=
        NULLIF(
            current_setting(
                'app.accion',
                TRUE
            ),
            ''
        );


    INSERT INTO auditoria.bitacora (
        esquema,
        tabla,
        operacion,
        registro_id,
        usuario_bd,
        usuario_app_id,
        usuario_app_correo,
        ip_origen,
        modulo,
        accion_app,
        datos_anteriores,
        datos_nuevos,
        cambios,
        fecha_evento
    )
    VALUES (
        TG_TABLE_SCHEMA,
        TG_TABLE_NAME,
        TG_OP,
        v_registro_id,
        CURRENT_USER,
        v_usuario_app_id,
        v_usuario_app_correo,
        v_ip_origen,
        v_modulo,
        v_accion_app,
        v_datos_anteriores,
        v_datos_nuevos,
        v_cambios,
        clock_timestamp()
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
    v_trigger_name :=
        'trg_auditoria_' || p_esquema || '_' || p_tabla;

    EXECUTE format(
        'DROP TRIGGER IF EXISTS %I ON %I.%I',
        v_trigger_name,
        p_esquema,
        p_tabla
    );

    EXECUTE format(
        'CREATE TRIGGER %I
         AFTER INSERT OR UPDATE OR DELETE
         ON %I.%I
         FOR EACH ROW
         EXECUTE FUNCTION auditoria.fn_registrar_bitacora()',
        v_trigger_name,
        p_esquema,
        p_tabla
    );
END;
$$;


DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT
            table_schema,
            table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema IN (
              'organizacion',
              'personal',
              'asistencia',
              'seguridad',
              'dispositivos'
          )
        ORDER BY
            table_schema,
            table_name
    LOOP
        PERFORM auditoria.fn_crear_trigger_auditoria(
            r.table_schema,
            r.table_name
        );
    END LOOP;
END $$;


CREATE OR REPLACE VIEW auditoria.vw_bitacora_resumen AS
SELECT
    id,
    fecha_evento,
    usuario_app_correo,
    usuario_app_id,
    usuario_bd,
    esquema,
    tabla,
    esquema || '.' || tabla AS objeto,
    operacion,
    registro_id,
    modulo,
    accion_app,
    cambios
FROM auditoria.bitacora;


COMMIT;