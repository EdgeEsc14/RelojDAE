\set ON_ERROR_STOP on

BEGIN;

SELECT set_config('app.usuario_correo', 'admin.sistema@dae.local', TRUE);
SELECT set_config('app.modulo', 'CORRECCION_BD', TRUE);
SELECT set_config('app.accion', 'FIX_INTEGRIDAD_BASE', TRUE);


-- ============================================================
-- 1) Consolidar correo en personal.empleados
--    Mantener: correo VARCHAR(320)
--    Eliminar: correo_electronico si existe
-- ============================================================

ALTER TABLE personal.empleados
    ADD COLUMN IF NOT EXISTS correo VARCHAR(320);

ALTER TABLE personal.empleados
    ALTER COLUMN correo TYPE VARCHAR(320);


DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'personal'
          AND table_name = 'empleados'
          AND column_name = 'correo_electronico'
    ) THEN

        IF EXISTS (
            SELECT 1
            FROM personal.empleados
            WHERE correo IS NOT NULL
              AND correo_electronico IS NOT NULL
              AND LOWER(BTRIM(correo)) <> LOWER(BTRIM(correo_electronico))
        ) THEN
            RAISE EXCEPTION
                'Hay empleados con correo y correo_electronico diferentes. Revisa antes de eliminar columna.';
        END IF;

        UPDATE personal.empleados
        SET correo = correo_electronico
        WHERE correo IS NULL
          AND correo_electronico IS NOT NULL;

        ALTER TABLE personal.empleados
            DROP COLUMN correo_electronico;
    END IF;
END $$;


DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM (
            SELECT
                LOWER(BTRIM(correo)) AS correo_normalizado
            FROM personal.empleados
            WHERE correo IS NOT NULL
            GROUP BY LOWER(BTRIM(correo))
            HAVING COUNT(*) > 1
        ) duplicados
    ) THEN
        RAISE EXCEPTION
            'Existen correos duplicados en personal.empleados. Corrige antes de crear índice único.';
    END IF;
END $$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_empleados_correo_no_vacio'
          AND conrelid = 'personal.empleados'::regclass
    ) THEN
        ALTER TABLE personal.empleados
            ADD CONSTRAINT ck_empleados_correo_no_vacio
            CHECK (
                correo IS NULL
                OR BTRIM(correo) <> ''
            );
    END IF;
END $$;


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_empleados_correo_normalizado
ON personal.empleados (
    LOWER(BTRIM(correo))
)
WHERE correo IS NOT NULL;


-- ============================================================
-- 2) Asegurar UNIQUE real para usuario por empleado
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM (
            SELECT
                empleado_id
            FROM seguridad.usuarios
            WHERE empleado_id IS NOT NULL
            GROUP BY empleado_id
            HAVING COUNT(*) > 1
        ) duplicados
    ) THEN
        RAISE EXCEPTION
            'Existen empleados con más de un usuario en seguridad.usuarios. Corrige antes de crear UNIQUE.';
    END IF;
END $$;


DO $$
DECLARE
    v_es_unico BOOLEAN;
BEGIN
    SELECT i.indisunique
    INTO v_es_unico
    FROM pg_class c
    JOIN pg_namespace n
        ON n.oid = c.relnamespace
    JOIN pg_index i
        ON i.indexrelid = c.oid
    WHERE n.nspname = 'seguridad'
      AND c.relname = 'uq_usuarios_empleado';

    IF v_es_unico = FALSE THEN
        DROP INDEX seguridad.uq_usuarios_empleado;
    END IF;
END $$;


CREATE UNIQUE INDEX IF NOT EXISTS
    uq_usuarios_empleado
ON seguridad.usuarios (
    empleado_id
)
WHERE empleado_id IS NOT NULL;


-- ============================================================
-- 3) Proteger historial de marcaciones
--    Cambiar empleado_id de ON DELETE SET NULL a ON DELETE RESTRICT
-- ============================================================

ALTER TABLE asistencia.marcaciones
    DROP CONSTRAINT IF EXISTS fk_marcaciones_empleado;

ALTER TABLE asistencia.marcaciones
    ADD CONSTRAINT fk_marcaciones_empleado
    FOREIGN KEY (empleado_id)
    REFERENCES personal.empleados (id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT;


-- ============================================================
-- 4) Blindar horario_dias
--    Si es laboral, debe tener entrada y salida.
--    Si no es laboral, no debe tener horas.
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_horario_dias_horas_laborales'
          AND conrelid = 'asistencia.horario_dias'::regclass
    ) THEN
        ALTER TABLE asistencia.horario_dias
            ADD CONSTRAINT ck_horario_dias_horas_laborales
            CHECK (
                (
                    es_laboral = TRUE
                    AND hora_entrada IS NOT NULL
                    AND hora_salida IS NOT NULL
                    AND hora_entrada <> hora_salida
                )
                OR
                (
                    es_laboral = FALSE
                    AND hora_entrada IS NULL
                    AND hora_salida IS NULL
                )
            );
    END IF;
END $$;


-- ============================================================
-- 5) Documentar password_reloj
--    No se elimina porque algunos relojes pueden requerirlo
--    para sincronización, pero queda advertencia formal.
-- ============================================================

COMMENT ON COLUMN dispositivos.empleado_dispositivo.password_reloj IS
'Campo sensible. No guardar contraseña en texto plano salvo que el hardware lo requiera. Preferir NULL, hash o cifrado desde backend. Este campo está excluido de auditoría JSON.';


COMMIT;