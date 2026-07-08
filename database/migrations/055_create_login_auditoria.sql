BEGIN;

-- ============================================================
-- 055_create_login_auditoria.sql
-- Objetivo:
-- Registrar intentos de login del sistema web.
--
-- Sirve para:
-- - Auditar accesos.
-- - Detectar intentos fallidos.
-- - Revisar IP origen y navegador.
-- - Investigar accesos sospechosos.
--
-- Nota:
-- Esta tabla no es para usuarios ZKTeco.
-- Es auditoría del login web.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS seguridad;

CREATE TABLE IF NOT EXISTS seguridad.login_auditoria (
    id BIGSERIAL PRIMARY KEY,

    -- Usuario identificado, si existe
    usuario_id BIGINT,

    -- Correo o usuario escrito en el formulario de login
    correo_intentado VARCHAR(255),

    -- Resultado del intento
    resultado VARCHAR(50) NOT NULL,

    -- Motivo técnico o funcional
    motivo VARCHAR(100),

    -- Información de red
    ip_origen INET,
    ip_origen_raw VARCHAR(255),
    forwarded_for TEXT,

    -- Información del cliente
    user_agent TEXT,

    -- Información opcional de la petición
    metodo_http VARCHAR(20),
    ruta VARCHAR(255),

    -- Fecha del evento
    fecha_evento TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_login_auditoria_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES seguridad.usuarios(id)
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

CREATE INDEX IF NOT EXISTS ix_login_auditoria_usuario_id
ON seguridad.login_auditoria (usuario_id);

CREATE INDEX IF NOT EXISTS ix_login_auditoria_correo_intentado
ON seguridad.login_auditoria (LOWER(correo_intentado));

CREATE INDEX IF NOT EXISTS ix_login_auditoria_resultado
ON seguridad.login_auditoria (resultado);

CREATE INDEX IF NOT EXISTS ix_login_auditoria_ip_origen
ON seguridad.login_auditoria (ip_origen);

CREATE INDEX IF NOT EXISTS ix_login_auditoria_fecha_evento
ON seguridad.login_auditoria (fecha_evento DESC);

CREATE INDEX IF NOT EXISTS ix_login_auditoria_correo_fecha
ON seguridad.login_auditoria (LOWER(correo_intentado), fecha_evento DESC);

COMMENT ON TABLE seguridad.login_auditoria IS
'Histórico de intentos de login del sistema web Reloj DAE.';

COMMENT ON COLUMN seguridad.login_auditoria.usuario_id IS
'Usuario identificado en seguridad.usuarios, si el correo existe.';

COMMENT ON COLUMN seguridad.login_auditoria.correo_intentado IS
'Correo o usuario escrito en el formulario de login.';

COMMENT ON COLUMN seguridad.login_auditoria.resultado IS
'Resultado del intento de login.';

COMMENT ON COLUMN seguridad.login_auditoria.motivo IS
'Motivo del resultado: contraseña incorrecta, usuario inexistente, cuenta bloqueada, etc.';

COMMENT ON COLUMN seguridad.login_auditoria.ip_origen IS
'IP normalizada desde donde se realizó el intento.';

COMMENT ON COLUMN seguridad.login_auditoria.ip_origen_raw IS
'Valor crudo de IP recibido desde la petición.';

COMMENT ON COLUMN seguridad.login_auditoria.forwarded_for IS
'Header X-Forwarded-For si existe. Útil cuando la app está detrás de proxy.';

COMMENT ON COLUMN seguridad.login_auditoria.user_agent IS
'Navegador, dispositivo o cliente que hizo la petición.';

COMMENT ON COLUMN seguridad.login_auditoria.fecha_evento IS
'Fecha y hora del intento de login.';

COMMIT;