\set ON_ERROR_STOP on
\encoding UTF8

\echo ''
\echo '============================================================'
\echo ' CHECK GENERAL BASE DE DATOS - RELOJ CHECADOR DAE'
\echo '============================================================'
\echo ''


\echo '1) Schemas esperados'
\echo '------------------------------------------------------------'

WITH schemas_esperados(nombre) AS (
    VALUES
        ('organizacion'),
        ('personal'),
        ('asistencia'),
        ('seguridad'),
        ('dispositivos'),
        ('auditoria')
)
SELECT
    s.nombre AS schema,
    CASE
        WHEN n.nspname IS NULL THEN 'FALTA'
        ELSE 'OK'
    END AS estatus
FROM schemas_esperados s
LEFT JOIN pg_namespace n
    ON n.nspname = s.nombre
ORDER BY
    s.nombre;


\echo ''
\echo '2) Tablas esperadas'
\echo '------------------------------------------------------------'

WITH tablas_esperadas(esquema, tabla) AS (
    VALUES
        ('organizacion', 'tipos_unidad'),
        ('organizacion', 'unidades_organizacionales'),
        ('organizacion', 'puestos'),

        ('personal', 'empleados'),

        ('seguridad', 'roles'),
        ('seguridad', 'modulos'),
        ('seguridad', 'permisos_rol'),
        ('seguridad', 'usuarios'),
        ('seguridad', 'usuarios_unidades'),

        ('dispositivos', 'dispositivos'),
        ('dispositivos', 'empleado_dispositivo'),
        ('dispositivos', 'sincronizaciones'),

        ('asistencia', 'tipos_turno'),
        ('asistencia', 'horarios'),
        ('asistencia', 'horario_dias'),
        ('asistencia', 'asignaciones_horario'),
        ('asistencia', 'politicas_asistencia'),
        ('asistencia', 'periodos_evaluacion'),
        ('asistencia', 'tipos_marcacion'),
        ('asistencia', 'marcaciones'),
        ('asistencia', 'asistencias_diarias'),
        ('asistencia', 'segmentos_trabajo'),
        ('asistencia', 'tipos_incidencia'),
        ('asistencia', 'incidencias'),
        ('asistencia', 'justificantes'),
        ('asistencia', 'aplicaciones_justificante'),
        ('asistencia', 'movimientos_puntos'),
        ('asistencia', 'resumen_periodo_empleado'),
        ('asistencia', 'descansos_obligatorios'),

        ('auditoria', 'bitacora')
)
SELECT
    t.esquema,
    t.tabla,
    CASE
        WHEN it.table_name IS NULL THEN 'FALTA'
        ELSE 'OK'
    END AS estatus
FROM tablas_esperadas t
LEFT JOIN information_schema.tables it
    ON it.table_schema = t.esquema
   AND it.table_name = t.tabla
   AND it.table_type = 'BASE TABLE'
ORDER BY
    t.esquema,
    t.tabla;


\echo ''
\echo '3) Conteo de tablas faltantes'
\echo '------------------------------------------------------------'

WITH tablas_esperadas(esquema, tabla) AS (
    VALUES
        ('organizacion', 'tipos_unidad'),
        ('organizacion', 'unidades_organizacionales'),
        ('organizacion', 'puestos'),
        ('personal', 'empleados'),
        ('seguridad', 'roles'),
        ('seguridad', 'modulos'),
        ('seguridad', 'permisos_rol'),
        ('seguridad', 'usuarios'),
        ('seguridad', 'usuarios_unidades'),
        ('dispositivos', 'dispositivos'),
        ('dispositivos', 'empleado_dispositivo'),
        ('dispositivos', 'sincronizaciones'),
        ('asistencia', 'tipos_turno'),
        ('asistencia', 'horarios'),
        ('asistencia', 'horario_dias'),
        ('asistencia', 'asignaciones_horario'),
        ('asistencia', 'politicas_asistencia'),
        ('asistencia', 'periodos_evaluacion'),
        ('asistencia', 'tipos_marcacion'),
        ('asistencia', 'marcaciones'),
        ('asistencia', 'asistencias_diarias'),
        ('asistencia', 'segmentos_trabajo'),
        ('asistencia', 'tipos_incidencia'),
        ('asistencia', 'incidencias'),
        ('asistencia', 'justificantes'),
        ('asistencia', 'aplicaciones_justificante'),
        ('asistencia', 'movimientos_puntos'),
        ('asistencia', 'resumen_periodo_empleado'),
        ('asistencia', 'descansos_obligatorios'),
        ('auditoria', 'bitacora')
),
revision AS (
    SELECT
        t.esquema,
        t.tabla,
        it.table_name
    FROM tablas_esperadas t
    LEFT JOIN information_schema.tables it
        ON it.table_schema = t.esquema
       AND it.table_name = t.tabla
       AND it.table_type = 'BASE TABLE'
)
SELECT
    COUNT(*) AS tablas_esperadas,
    COUNT(table_name) AS tablas_existentes,
    COUNT(*) - COUNT(table_name) AS tablas_faltantes
FROM revision;


\echo ''
\echo '4) Catálogos y datos base'
\echo '------------------------------------------------------------'

SELECT
    'roles' AS elemento,
    COUNT(*) AS registros,
    CASE WHEN COUNT(*) >= 5 THEN 'OK' ELSE 'REVISAR' END AS estatus
FROM seguridad.roles

UNION ALL

SELECT
    'modulos',
    COUNT(*),
    CASE WHEN COUNT(*) >= 11 THEN 'OK' ELSE 'REVISAR' END
FROM seguridad.modulos

UNION ALL

SELECT
    'permisos_rol',
    COUNT(*),
    CASE WHEN COUNT(*) >= 55 THEN 'OK' ELSE 'REVISAR' END
FROM seguridad.permisos_rol

UNION ALL

SELECT
    'tipos_unidad',
    COUNT(*),
    CASE WHEN COUNT(*) >= 5 THEN 'OK' ELSE 'REVISAR' END
FROM organizacion.tipos_unidad

UNION ALL

SELECT
    'organigrama_dae',
    COUNT(*),
    CASE WHEN COUNT(*) >= 13 THEN 'OK' ELSE 'REVISAR' END
FROM organizacion.unidades_organizacionales

UNION ALL

SELECT
    'tipos_turno',
    COUNT(*),
    CASE WHEN COUNT(*) >= 2 THEN 'OK' ELSE 'REVISAR' END
FROM asistencia.tipos_turno

UNION ALL

SELECT
    'horarios',
    COUNT(*),
    CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'REVISAR' END
FROM asistencia.horarios

UNION ALL

SELECT
    'horario_dias',
    COUNT(*),
    CASE WHEN COUNT(*) >= 7 THEN 'OK' ELSE 'REVISAR' END
FROM asistencia.horario_dias

UNION ALL

SELECT
    'politicas_asistencia',
    COUNT(*),
    CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'REVISAR' END
FROM asistencia.politicas_asistencia

UNION ALL

SELECT
    'tipos_marcacion',
    COUNT(*),
    CASE WHEN COUNT(*) >= 5 THEN 'OK' ELSE 'REVISAR' END
FROM asistencia.tipos_marcacion

UNION ALL

SELECT
    'tipos_incidencia',
    COUNT(*),
    CASE WHEN COUNT(*) >= 9 THEN 'OK' ELSE 'REVISAR' END
FROM asistencia.tipos_incidencia

UNION ALL

SELECT
    'dispositivos',
    COUNT(*),
    CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'REVISAR' END
FROM dispositivos.dispositivos

ORDER BY
    elemento;


\echo ''
\echo '5) Roles cargados'
\echo '------------------------------------------------------------'

SELECT
    codigo,
    nombre,
    activo
FROM seguridad.roles
ORDER BY
    orden_visual;


\echo ''
\echo '6) Organigrama DAE'
\echo '------------------------------------------------------------'

WITH RECURSIVE arbol AS (
    SELECT
        u.id,
        u.unidad_padre_id,
        u.codigo,
        u.nombre,
        u.clave_organica,
        0 AS nivel,
        u.nombre::TEXT AS ruta
    FROM organizacion.unidades_organizacionales u
    WHERE u.unidad_padre_id IS NULL

    UNION ALL

    SELECT
        h.id,
        h.unidad_padre_id,
        h.codigo,
        h.nombre,
        h.clave_organica,
        a.nivel + 1,
        a.ruta || ' > ' || h.nombre
    FROM organizacion.unidades_organizacionales h
    JOIN arbol a
        ON a.id = h.unidad_padre_id
)
SELECT
    nivel,
    codigo,
    nombre,
    clave_organica,
    ruta
FROM arbol
ORDER BY
    ruta;


\echo ''
\echo '7) Dispositivo ZKTeco registrado'
\echo '------------------------------------------------------------'

SELECT
    codigo,
    nombre,
    ip,
    puerto,
    modelo,
    firmware,
    ubicacion,
    activo
FROM dispositivos.dispositivos
ORDER BY
    id;


\echo ''
\echo '8) Auditoría - triggers activos'
\echo '------------------------------------------------------------'

SELECT
    n.nspname AS esquema,
    c.relname AS tabla,
    t.tgname AS trigger
FROM pg_trigger t
JOIN pg_class c
    ON c.oid = t.tgrelid
JOIN pg_namespace n
    ON n.oid = c.relnamespace
WHERE t.tgisinternal = FALSE
  AND t.tgname LIKE 'trg_auditoria_%'
ORDER BY
    n.nspname,
    c.relname;


\echo ''
\echo '9) Conteo de triggers de auditoría'
\echo '------------------------------------------------------------'

SELECT
    COUNT(*) AS total_triggers_auditoria,
    CASE
        WHEN COUNT(*) >= 29 THEN 'OK'
        ELSE 'REVISAR'
    END AS estatus
FROM pg_trigger t
WHERE t.tgisinternal = FALSE
  AND t.tgname LIKE 'trg_auditoria_%';


\echo ''
\echo '10) Vista de auditoría'
\echo '------------------------------------------------------------'

SELECT
    table_schema,
    table_name,
    CASE
        WHEN table_name IS NOT NULL THEN 'OK'
        ELSE 'FALTA'
    END AS estatus
FROM information_schema.views
WHERE table_schema = 'auditoria'
  AND table_name = 'vw_bitacora_resumen';


\echo ''
\echo 'TOdo salio re bien hermano'
\echo ''