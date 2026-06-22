BEGIN;

INSERT INTO asistencia.horarios (
    codigo,
    nombre,
    descripcion,
    tolerancia_entrada_minutos,
    descanso_minutos,
    permite_tiempo_extra,
    activo
)
VALUES (
    'ADMINISTRATIVO',
    'Horario administrativo',
    'Jornada administrativa de lunes a viernes.',
    10,
    60,
    TRUE,
    TRUE
)
ON CONFLICT (codigo)
DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    tolerancia_entrada_minutos =
        EXCLUDED.tolerancia_entrada_minutos,
    descanso_minutos =
        EXCLUDED.descanso_minutos,
    permite_tiempo_extra =
        EXCLUDED.permite_tiempo_extra,
    activo = EXCLUDED.activo,
    fecha_modificacion = CURRENT_TIMESTAMP;


INSERT INTO asistencia.horario_dias (
    horario_id,
    dia_semana,
    es_laboral,
    hora_entrada,
    hora_salida
)
SELECT
    horario.id,
    dias.dia_semana,
    dias.es_laboral,
    dias.hora_entrada,
    dias.hora_salida
FROM asistencia.horarios AS horario
CROSS JOIN (
    VALUES
        (
            1,
            TRUE,
            TIME '08:00',
            TIME '17:00'
        ),
        (
            2,
            TRUE,
            TIME '08:00',
            TIME '17:00'
        ),
        (
            3,
            TRUE,
            TIME '08:00',
            TIME '17:00'
        ),
        (
            4,
            TRUE,
            TIME '08:00',
            TIME '17:00'
        ),
        (
            5,
            TRUE,
            TIME '08:00',
            TIME '17:00'
        ),
        (
            6,
            FALSE,
            NULL::TIME,
            NULL::TIME
        ),
        (
            7,
            FALSE,
            NULL::TIME,
            NULL::TIME
        )
) AS dias (
    dia_semana,
    es_laboral,
    hora_entrada,
    hora_salida
)
WHERE horario.codigo = 'ADMINISTRATIVO'
ON CONFLICT (
    horario_id,
    dia_semana
)
DO UPDATE SET
    es_laboral = EXCLUDED.es_laboral,
    hora_entrada = EXCLUDED.hora_entrada,
    hora_salida = EXCLUDED.hora_salida,
    fecha_modificacion = CURRENT_TIMESTAMP;

COMMIT;