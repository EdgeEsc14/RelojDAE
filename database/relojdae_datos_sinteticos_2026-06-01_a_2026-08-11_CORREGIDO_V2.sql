
-- ============================================================
-- RelojDAE - Datos sinteticos de marcaciones
-- Periodo: 2026-06-01 al 2026-08-11
-- Etiqueta: TEST-SYNTH-20260601-20260811-V1
--
-- OBJETIVO:
-- 1) Crear 8 empleados ficticios claramente identificables.
-- 2) Generar entradas/salidas de lunes a viernes.
-- 3) Incluir puntualidad, tolerancia, retardos, ausencias,
--    salidas faltantes y algunos duplicados.
-- 4) Poder borrar TODO el lote sin tocar datos reales.
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 0. LIMPIEZA PREVIA DEL MISMO LOTE
--    Hace que el script sea re-ejecutable.
-- ------------------------------------------------------------
DELETE FROM asistencia.marcaciones_crudas
WHERE sync_run_id = 'TEST-SYNTH-20260601-20260811-V1';

-- ------------------------------------------------------------
-- 1. EMPLEADOS FICTICIOS
--    Se usa unidad_organizacional_id=1 y puesto_id=2 porque
--    existen actualmente en tu base.
-- ------------------------------------------------------------
WITH personas(codigo_empleado, nombres, apellido_paterno, apellido_materno, correo, zk_user_id) AS (
    VALUES
        ('TEST-1001','Ana','Torres','Molina','ana.torres.test@dae.local','9101'),
        ('TEST-1002','Carlos','Mendoza','Ruiz','carlos.mendoza.test@dae.local','9102'),
        ('TEST-1003','Daniela','Ruiz','Vargas','daniela.ruiz.test@dae.local','9103'),
        ('TEST-1004','Eduardo','Salas','Ortega','eduardo.salas.test@dae.local','9104'),
        ('TEST-1005','Fernanda','Lopez','Castro','fernanda.lopez.test@dae.local','9105'),
        ('TEST-1006','Gabriel','Ortega','Navarro','gabriel.ortega.test@dae.local','9106'),
        ('TEST-1007','Isabel','Castro','Mendez','isabel.castro.test@dae.local','9107'),
        ('TEST-1008','Jorge','Navarro','Luna','jorge.navarro.test@dae.local','9108')
)
INSERT INTO personal.empleados (
    codigo_empleado,
    nombres,
    apellido_paterno,
    apellido_materno,
    unidad_organizacional_id,
    puesto_id,
    supervisor_id,
    fecha_ingreso,
    estatus,
    correo,
    zk_user_id,
    observaciones
)
SELECT
    p.codigo_empleado,
    p.nombres,
    p.apellido_paterno,
    p.apellido_materno,
    1,
    2,
    NULL,
    DATE '2026-01-01',
    'ACTIVO',
    p.correo,
    p.zk_user_id,
    'DATOS_SINTETICOS_RELOJ_2026'
FROM personas p
WHERE NOT EXISTS (
    SELECT 1
    FROM personal.empleados e
    WHERE e.codigo_empleado = p.codigo_empleado
);

-- ------------------------------------------------------------
-- 2. GENERACION DETERMINISTA DE JORNADAS
--
-- Casos incluidos:
--  - entradas antes de las 08:00
--  - 08:00 a 08:10 (tolerancia)
--  - 08:11 a 08:20 (retardo menor)
--  - 08:21 a 08:30 (retardo mayor)
--  - despues de 08:31
--  - ausencias completas
--  - algunas salidas faltantes
--
-- No genera sabados ni domingos.
-- ------------------------------------------------------------
WITH empleados_test AS (
    SELECT
        id AS empleado_id,
        codigo_empleado,
        zk_user_id,
        row_number() OVER (ORDER BY codigo_empleado)::int AS emp_n
    FROM personal.empleados
    WHERE codigo_empleado LIKE 'TEST-10%'
),
dias AS (
    SELECT d::date AS fecha
    FROM generate_series(
        DATE '2026-06-01',
        DATE '2026-08-11',
        INTERVAL '1 day'
    ) AS g(d)
    WHERE EXTRACT(ISODOW FROM d) BETWEEN 1 AND 5
),
base AS (
    SELECT
        e.*,
        d.fecha,
        (
            abs(
                ('x' || substr(md5(e.codigo_empleado || d.fecha::text),1,8))::bit(32)::int
            ) % 100
        ) AS patron
    FROM empleados_test e
    CROSS JOIN dias d
),
jornadas AS (
    SELECT
        *,
        CASE
            -- ~4% ausencias
            WHEN patron < 4 THEN NULL

            -- puntual temprano: 07:48-07:59
            WHEN patron < 35 THEN
                timestamp '2026-01-01 07:48:00'
                + ((patron + emp_n) % 12) * interval '1 minute'

            -- tolerancia: 08:00-08:10
            WHEN patron < 70 THEN
                timestamp '2026-01-01 08:00:00'
                + ((patron + emp_n) % 11) * interval '1 minute'

            -- retardo menor: 08:11-08:20
            WHEN patron < 84 THEN
                timestamp '2026-01-01 08:11:00'
                + ((patron + emp_n) % 10) * interval '1 minute'

            -- retardo mayor: 08:21-08:30
            WHEN patron < 94 THEN
                timestamp '2026-01-01 08:21:00'
                + ((patron + emp_n) % 10) * interval '1 minute'

            -- llegada despues de 08:31
            ELSE
                timestamp '2026-01-01 08:31:00'
                + ((patron + emp_n) % 20) * interval '1 minute'
        END AS entrada_base
    FROM base
),
horarios AS (
    SELECT
        *,
        CASE
            WHEN entrada_base IS NULL THEN NULL
            ELSE fecha::timestamp + entrada_base::time
                 + ((patron * 17 + emp_n * 13) % 60) * interval '1 second'
        END AS entrada,
        CASE
            WHEN entrada_base IS NULL THEN NULL
            ELSE fecha::timestamp + entrada_base::time
                 + interval '7 hours'
                 + (5 + ((patron + emp_n) % 26)) * interval '1 minute'
                 + ((patron * 11 + emp_n * 7) % 60) * interval '1 second'
        END AS salida
    FROM jornadas
),
marcas AS (
    -- ENTRADAS
    SELECT
        empleado_id,
        codigo_empleado,
        zk_user_id,
        fecha,
        entrada AS fecha_hora,
        0 AS punch,
        'Entrada'::varchar AS punch_label,
        emp_n,
        patron,
        1 AS orden
    FROM horarios
    WHERE entrada IS NOT NULL

    UNION ALL

    -- SALIDAS
    SELECT
        empleado_id,
        codigo_empleado,
        zk_user_id,
        fecha,
        salida AS fecha_hora,
        1 AS punch,
        'Salida'::varchar AS punch_label,
        emp_n,
        patron,
        2 AS orden
    FROM horarios
    WHERE salida IS NOT NULL
      -- ~3% de jornadas sin salida para probar incidencias
      AND patron NOT IN (17, 43, 79)

    UNION ALL

    -- DUPLICADO ocasional de entrada (+1 minuto)
    SELECT
        empleado_id,
        codigo_empleado,
        zk_user_id,
        fecha,
        entrada + interval '1 minute' AS fecha_hora,
        0 AS punch,
        'Entrada'::varchar AS punch_label,
        emp_n,
        patron,
        3 AS orden
    FROM horarios
    WHERE entrada IS NOT NULL
      AND patron IN (26, 62)
),
enumeradas AS (
    SELECT
        *,
        row_number() OVER (
            ORDER BY fecha_hora, empleado_id, orden
        ) AS n
    FROM marcas
)
INSERT INTO asistencia.marcaciones_crudas (
    dispositivo_origen,
    dispositivo_ip,
    zk_uid_registro,
    zk_user_id,
    fecha_hora,
    fecha,
    hora,
    punch,
    punch_label,
    status,
    status_label,
    empleado_id,
    codigo_empleado,
    raw_payload,
    sync_run_id
)
SELECT
    'ZKTeco',
    '192.168.137.2',
    500000 + n::int,
    zk_user_id,
    fecha_hora,
    fecha_hora::date,
    fecha_hora::time,
    punch,
    punch_label,
    1,
    'Huella / verificacion biometrica',
    empleado_id,
    codigo_empleado,
    jsonb_build_object(
        'uid', 500000 + n::int,
        'hora', to_char(fecha_hora,'HH24:MI:SS'),
        'fecha', to_char(fecha_hora,'YYYY-MM-DD'),
        'punch', punch,
        'status', 1,
        'user_id', zk_user_id,
        'timestamp', to_char(fecha_hora,'YYYY-MM-DD"T"HH24:MI:SS'),
        'punch_label', punch_label,
        'status_label', 'Huella / verificacion biometrica',
        'synthetic', true,
        'dataset', 'TEST-SYNTH-20260601-20260811-V1'
    ),
    'TEST-SYNTH-20260601-20260811-V1'
FROM enumeradas;

-- ------------------------------------------------------------
-- 3. RESUMEN DEL LOTE INSERTADO
-- ------------------------------------------------------------
SELECT
    COUNT(*) AS marcaciones_insertadas,
    COUNT(DISTINCT empleado_id) AS empleados,
    MIN(fecha_hora) AS primera_marcacion,
    MAX(fecha_hora) AS ultima_marcacion,
    COUNT(*) FILTER (WHERE punch = 0) AS entradas,
    COUNT(*) FILTER (WHERE punch = 1) AS salidas
FROM asistencia.marcaciones_crudas
WHERE sync_run_id = 'TEST-SYNTH-20260601-20260811-V1';

COMMIT;

-- ============================================================
-- CONSULTAS DE VALIDACION
-- ============================================================

-- Ver las primeras 50 checadas:
SELECT
    id,
    codigo_empleado,
    zk_user_id,
    fecha_hora,
    punch,
    punch_label,
    sync_run_id
FROM asistencia.marcaciones_crudas
WHERE sync_run_id = 'TEST-SYNTH-20260601-20260811-V1'
ORDER BY fecha_hora, codigo_empleado
LIMIT 50;

-- Resumen por empleado:
SELECT
    codigo_empleado,
    COUNT(*) FILTER (WHERE punch=0) AS entradas,
    COUNT(*) FILTER (WHERE punch=1) AS salidas,
    MIN(fecha) AS desde,
    MAX(fecha) AS hasta
FROM asistencia.marcaciones_crudas
WHERE sync_run_id = 'TEST-SYNTH-20260601-20260811-V1'
GROUP BY codigo_empleado
ORDER BY codigo_empleado;

-- ============================================================
-- ROLLBACK / BORRADO DEL DATASET DE PRUEBA
-- Ejecutar SOLO cuando quieras borrar el lote.
-- Primero borra marcaciones y despues empleados ficticios.
-- ============================================================
-- BEGIN;
-- DELETE FROM asistencia.marcaciones_crudas
-- WHERE sync_run_id = 'TEST-SYNTH-20260601-20260811-V1';
--
-- DELETE FROM personal.empleados
-- WHERE observaciones = 'DATOS_SINTETICOS_RELOJ_2026'
--   AND codigo_empleado LIKE 'TEST-10%';
-- COMMIT;
