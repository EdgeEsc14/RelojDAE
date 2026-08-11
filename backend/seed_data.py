"""
Script para generar e insertar datos ficticios de 3 meses de asistencia.

Genera:
- Empleados ficticios (si no hay suficientes)
- Asignaciones de horario
- Marcaciones crudas simuladas
- Asistencias diarias procesadas
- Incidencias derivadas
- Movimientos de puntos

Periodo: últimos 90 días (3 meses)
"""

import os
import sys
import random
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.security import hash_password

# Configuración
FECHA_FIN = date.today()
FECHA_INICIO = FECHA_FIN - timedelta(days=90)
DIAS_LABORALES = []  # Se calcula abajo (lunes a viernes)

# Calcular días laborales (lunes a viernes)
current = FECHA_INICIO
while current <= FECHA_FIN:
    if current.weekday() < 5:  # 0=Lunes, 4=Viernes
        DIAS_LABORALES.append(current)
    current += timedelta(days=1)

print(f"Periodo: {FECHA_INICIO} a {FECHA_FIN}")
print(f"Días laborales: {len(DIAS_LABORALES)}")

# Empleados ficticios
EMPLEADOS_FICTICIOS = [
    ("EMP-1001", "CARLOS", "MENDOZA", "REYES", "CAMC850312HDF"),
    ("EMP-1002", "MARÍA", "HERNÁNDEZ", "LÓPEZ", "MEHL900525MDF"),
    ("EMP-1003", "JORGE", "RAMÍREZ", "SOTO", "RAJE780815HDF"),
    ("EMP-1004", "ANA", "TORRES", "VEGA", "TOAV920110MDF"),
    ("EMP-1005", "PEDRO", "GARCÍA", "CRUZ", "GACP880420HDF"),
    ("EMP-1006", "LUCÍA", "MARTÍNEZ", "DÍAZ", "MADL950630MDF"),
    ("EMP-1007", "ROBERTO", "LÓPEZ", "HERNÁNDEZ", "LOHR810915HDF"),
    ("EMP-1008", "SOFÍA", "RUIZ", "MORENO", "RUMS930225MDF"),
    ("EMP-1009", "FERNANDO", "DÍAZ", "GARCÍA", "DIGF870710HDF"),
    ("EMP-1010", "PATRICIA", "SÁNCHEZ", "TORRES", "SATP900105MDF"),
    ("EMP-1011", "MIGUEL", "FLORES", "RAMÍREZ", "FLRM850620HDF"),
    ("EMP-1012", "ELENA", "MORALES", "CRUZ", "MOCE910815MDF"),
    ("EMP-1013", "DAVID", "JIMÉNEZ", "LÓPEZ", "JILD880320HDF"),
    ("EMP-1014", "LAURA", "CASTRO", "HERNÁNDEZ", "CAHL940510MDF"),
    ("EMP-1015", "ALEJANDRO", "VARGAS", "DÍAZ", "VADA860725HDF"),
]

# Perfiles de comportamiento (para hacer datos realistas)
PERFILES = {
    "puntual": {"prob_falta": 0.02, "prob_retardo_menor": 0.05, "prob_retardo_mayor": 0.02},
    "regular": {"prob_falta": 0.05, "prob_retardo_menor": 0.12, "prob_retardo_mayor": 0.05},
    "irregular": {"prob_falta": 0.10, "prob_retardo_menor": 0.20, "prob_retardo_mayor": 0.10},
    "problematico": {"prob_falta": 0.15, "prob_retardo_menor": 0.25, "prob_retardo_mayor": 0.15},
}


def main():
    db = SessionLocal()

    try:
        print("\n1. Verificando/creando unidades organizacionales...")
        unidades = asegurar_unidades(db)
        print(f"   Unidades disponibles: {len(unidades)}")

        print("\n2. Verificando/creando puestos...")
        puestos = asegurar_puestos(db)
        print(f"   Puestos disponibles: {len(puestos)}")

        print("\n3. Verificando/creando horarios...")
        horario_id = asegurar_horario(db)
        print(f"   Horario ID: {horario_id}")

        print("\n4. Creando empleados ficticios...")
        empleados = crear_empleados(db, unidades, puestos)
        print(f"   Empleados creados/verificados: {len(empleados)}")

        print("\n5. Asignando horarios...")
        asignar_horarios(db, empleados, horario_id)

        print("\n6. Generando asistencias diarias (3 meses)...")
        stats = generar_asistencias(db, empleados)
        print(f"   Registros generados: {stats['total']}")
        print(f"   Completos: {stats['completos']}, Retardos: {stats['retardos']}, Faltas: {stats['faltas']}")

        print("\n7. Generando incidencias...")
        inc_count = generar_incidencias(db, empleados)
        print(f"   Incidencias generadas: {inc_count}")

        print("\n8. Generando marcaciones crudas simuladas...")
        marc_count = generar_marcaciones_crudas(db, empleados)
        print(f"   Marcaciones generadas: {marc_count}")

        print("\n¡DATOS FICTICIOS INSERTADOS EXITOSAMENTE!")
        print(f"Periodo: {FECHA_INICIO} a {FECHA_FIN}")
        print(f"Empleados: {len(empleados)}")
        print(f"Días laborales: {len(DIAS_LABORALES)}")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def asegurar_unidades(db):
    """Verifica que existan unidades organizacionales o las crea."""
    rows = db.execute(text(
        "SELECT id, nombre FROM organizacion.unidades_organizacionales WHERE activo = TRUE LIMIT 10"
    )).mappings().all()

    if len(rows) >= 3:
        return [dict(r) for r in rows]

    # Crear unidades si no hay suficientes
    tipo_id = db.execute(text(
        "SELECT id FROM organizacion.tipos_unidad WHERE codigo = 'DEPARTAMENTO' LIMIT 1"
    )).scalar_one_or_none()

    if tipo_id is None:
        tipo_id = db.execute(text(
            "SELECT id FROM organizacion.tipos_unidad LIMIT 1"
        )).scalar_one()

    nuevas = [
        "Departamento de Sistemas",
        "Departamento de Recursos Humanos",
        "Departamento de Contabilidad",
        "Departamento de Servicios Generales",
        "Departamento de Vinculación",
    ]

    for nombre in nuevas:
        exists = db.execute(text(
            "SELECT id FROM organizacion.unidades_organizacionales WHERE LOWER(nombre) = LOWER(:nombre)"
        ), {"nombre": nombre}).scalar_one_or_none()

        if exists is None:
            db.execute(text("""
                INSERT INTO organizacion.unidades_organizacionales (codigo, nombre, tipo_unidad_id, activo)
                VALUES (:codigo, :nombre, :tipo_id, TRUE)
                ON CONFLICT (codigo) DO NOTHING
            """), {
                "codigo": nombre.upper().replace(" ", "_").replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")[:30],
                "nombre": nombre,
                "tipo_id": tipo_id,
            })

    db.commit()

    rows = db.execute(text(
        "SELECT id, nombre FROM organizacion.unidades_organizacionales WHERE activo = TRUE LIMIT 10"
    )).mappings().all()
    return [dict(r) for r in rows]


def asegurar_puestos(db):
    """Verifica que existan puestos o los crea."""
    rows = db.execute(text(
        "SELECT id, nombre FROM organizacion.puestos WHERE activo = TRUE LIMIT 10"
    )).mappings().all()

    if len(rows) >= 2:
        return [dict(r) for r in rows]

    nuevos = [
        ("ANALISTA", "Analista", 3),
        ("TECNICO", "Técnico", 4),
        ("AUXILIAR", "Auxiliar Administrativo", 5),
        ("COORDINADOR", "Coordinador", 2),
    ]

    for codigo, nombre, nivel in nuevos:
        db.execute(text("""
            INSERT INTO organizacion.puestos (codigo, nombre, nivel_jerarquico, activo)
            VALUES (:codigo, :nombre, :nivel, TRUE)
            ON CONFLICT (codigo) DO NOTHING
        """), {"codigo": codigo, "nombre": nombre, "nivel": nivel})

    db.commit()

    rows = db.execute(text(
        "SELECT id, nombre FROM organizacion.puestos WHERE activo = TRUE LIMIT 10"
    )).mappings().all()
    return [dict(r) for r in rows]


def asegurar_horario(db):
    """Verifica que exista un horario matutino o lo crea."""
    horario = db.execute(text(
        "SELECT id FROM asistencia.horarios WHERE activo = TRUE LIMIT 1"
    )).scalar_one_or_none()

    if horario:
        return horario

    # Necesitamos un tipo_turno
    tipo_turno_id = db.execute(text(
        "SELECT id FROM asistencia.tipos_turno WHERE activo = TRUE LIMIT 1"
    )).scalar_one_or_none()

    if tipo_turno_id is None:
        row = db.execute(text("""
            INSERT INTO asistencia.tipos_turno (
                codigo, nombre, duracion_jornada_minutos, activo
            ) VALUES ('MATUTINO', 'Matutino', 420, TRUE)
            ON CONFLICT (codigo) DO UPDATE SET activo = TRUE
            RETURNING id
        """)).mappings().one()
        tipo_turno_id = row["id"]
        db.commit()

    row = db.execute(text("""
        INSERT INTO asistencia.horarios (
            codigo, nombre, tipo_turno_id,
            hora_entrada, hora_salida,
            tolerancia_entrada_minutos, descanso_minutos,
            permite_tiempo_extra, activo,
            dias_aplicables
        ) VALUES (
            'MAT_08_15', 'Matutino 08:00 - 15:00', :tipo_turno_id,
            '08:00', '15:00',
            10, 0,
            TRUE, TRUE,
            '{1,2,3,4,5}'
        )
        ON CONFLICT (codigo) DO UPDATE SET activo = TRUE
        RETURNING id
    """), {"tipo_turno_id": tipo_turno_id}).mappings().one()

    db.commit()
    return row["id"]


def crear_empleados(db, unidades, puestos):
    """Crea empleados ficticios si no existen."""
    empleados = []

    for i, (codigo, nombres, ap, am, rfc) in enumerate(EMPLEADOS_FICTICIOS):
        existe = db.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado = :codigo"
        ), {"codigo": codigo}).scalar_one_or_none()

        if existe:
            empleados.append({"id": existe, "codigo": codigo, "perfil": _asignar_perfil(i)})
            continue

        unidad = random.choice(unidades)
        puesto = random.choice(puestos)

        row = db.execute(text("""
            INSERT INTO personal.empleados (
                codigo_empleado, nombres, apellido_paterno, apellido_materno,
                rfc, unidad_organizacional_id, puesto_id,
                estatus, zk_user_id
            ) VALUES (
                :codigo, :nombres, :ap, :am,
                :rfc, :unidad_id, :puesto_id,
                'ACTIVO', :zk_user_id
            )
            RETURNING id
        """), {
            "codigo": codigo,
            "nombres": nombres,
            "ap": ap,
            "am": am,
            "rfc": rfc,
            "unidad_id": unidad["id"],
            "puesto_id": puesto["id"],
            "zk_user_id": str(1000 + i),
        }).mappings().one()

        empleados.append({"id": row["id"], "codigo": codigo, "perfil": _asignar_perfil(i)})

    db.commit()
    return empleados


def _asignar_perfil(index):
    """Asigna un perfil de comportamiento según el índice."""
    if index < 5:
        return "puntual"
    elif index < 9:
        return "regular"
    elif index < 12:
        return "irregular"
    else:
        return "problematico"


def asignar_horarios(db, empleados, horario_id):
    """Asigna horario a empleados que no lo tengan."""
    for emp in empleados:
        existe = db.execute(text("""
            SELECT id FROM asistencia.asignaciones_horario
            WHERE empleado_id = :emp_id AND estatus = 'ACTIVA'
            LIMIT 1
        """), {"emp_id": emp["id"]}).scalar_one_or_none()

        if existe:
            continue

        db.execute(text("""
            INSERT INTO asistencia.asignaciones_horario (
                empleado_id, horario_id, fecha_inicio, estatus
            ) VALUES (:emp_id, :horario_id, :fecha_inicio, 'ACTIVA')
        """), {
            "emp_id": emp["id"],
            "horario_id": horario_id,
            "fecha_inicio": FECHA_INICIO - timedelta(days=30),
        })

    db.commit()


def generar_asistencias(db, empleados):
    """Genera registros de asistencia diaria para 3 meses."""
    stats = {"total": 0, "completos": 0, "retardos": 0, "faltas": 0}

    # Obtener horario_id para referencia
    horario_id = db.execute(text(
        "SELECT id FROM asistencia.horarios WHERE activo = TRUE LIMIT 1"
    )).scalar_one()

    for emp in empleados:
        perfil = PERFILES[emp["perfil"]]

        for dia in DIAS_LABORALES:
            # Determinar estatus del día
            rand = random.random()

            if rand < perfil["prob_falta"]:
                estatus = "FALTA"
                minutos_retardo = 0
                puntos = 0
                primera_entrada = None
                ultima_salida = None
                stats["faltas"] += 1
            elif rand < perfil["prob_falta"] + perfil["prob_retardo_mayor"]:
                estatus = "RETARDO_MAYOR"
                minutos_retardo = random.randint(21, 30)
                puntos = 2
                primera_entrada = _generar_entrada(dia, minutos_retardo)
                ultima_salida = _generar_salida(dia)
                stats["retardos"] += 1
            elif rand < perfil["prob_falta"] + perfil["prob_retardo_mayor"] + perfil["prob_retardo_menor"]:
                estatus = "RETARDO_MENOR"
                minutos_retardo = random.randint(11, 20)
                puntos = 1
                primera_entrada = _generar_entrada(dia, minutos_retardo)
                ultima_salida = _generar_salida(dia)
                stats["retardos"] += 1
            else:
                estatus = "COMPLETO"
                minutos_retardo = random.randint(0, 10)
                puntos = 0
                primera_entrada = _generar_entrada(dia, minutos_retardo)
                ultima_salida = _generar_salida(dia)
                stats["completos"] += 1

            entrada_programada = datetime.combine(dia, time(8, 0))
            salida_programada = datetime.combine(dia, time(15, 0))

            minutos_ordinarios = 420 if primera_entrada and ultima_salida else 0
            minutos_extra = random.randint(0, 60) if estatus == "COMPLETO" and random.random() < 0.15 else 0

            db.execute(text("""
                INSERT INTO asistencia.asistencias_diarias (
                    empleado_id, politica_asistencia_id, horario_id, fecha,
                    entrada_programada, salida_programada,
                    primera_entrada, ultima_salida,
                    minutos_retardo, minutos_ordinarios, minutos_extra,
                    estatus, puntos_generados,
                    procesada, requiere_revision, observaciones,
                    fecha_procesamiento
                ) VALUES (
                    :emp_id, 1, :horario_id, :fecha,
                    :entrada_programada, :salida_programada,
                    :primera_entrada, :ultima_salida,
                    :minutos_retardo, :minutos_ordinarios, :minutos_extra,
                    :estatus, :puntos,
                    TRUE, :requiere_revision, :observaciones,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT (empleado_id, fecha) DO UPDATE SET
                    estatus = EXCLUDED.estatus,
                    puntos_generados = EXCLUDED.puntos_generados,
                    minutos_retardo = EXCLUDED.minutos_retardo,
                    primera_entrada = EXCLUDED.primera_entrada,
                    ultima_salida = EXCLUDED.ultima_salida,
                    procesada = TRUE,
                    fecha_procesamiento = CURRENT_TIMESTAMP,
                    fecha_modificacion = CURRENT_TIMESTAMP
            """), {
                "emp_id": emp["id"],
                "horario_id": horario_id,
                "fecha": dia,
                "entrada_programada": entrada_programada,
                "salida_programada": salida_programada,
                "primera_entrada": primera_entrada,
                "ultima_salida": ultima_salida,
                "minutos_retardo": minutos_retardo,
                "minutos_ordinarios": minutos_ordinarios,
                "minutos_extra": minutos_extra,
                "estatus": estatus,
                "puntos": puntos,
                "requiere_revision": estatus == "FALTA",
                "observaciones": _generar_observacion(estatus, minutos_retardo),
            })

            stats["total"] += 1

    db.commit()
    return stats


def generar_incidencias(db, empleados):
    """Genera incidencias basadas en las asistencias procesadas."""
    # Obtener tipos de incidencia
    tipos = db.execute(text(
        "SELECT id, codigo FROM asistencia.tipos_incidencia WHERE activo = TRUE"
    )).mappings().all()

    tipo_map = {r["codigo"]: r["id"] for r in tipos}
    count = 0

    for emp in empleados:
        # Buscar asistencias con problemas
        asistencias = db.execute(text("""
            SELECT id, fecha, estatus, puntos_generados
            FROM asistencia.asistencias_diarias
            WHERE empleado_id = :emp_id
              AND estatus IN ('RETARDO_MENOR', 'RETARDO_MAYOR', 'FALTA', 'OMISION_SALIDA')
              AND fecha BETWEEN :inicio AND :fin
            ORDER BY fecha
        """), {
            "emp_id": emp["id"],
            "inicio": FECHA_INICIO,
            "fin": FECHA_FIN,
        }).mappings().all()

        for asist in asistencias:
            tipo_codigo = asist["estatus"]
            tipo_id = tipo_map.get(tipo_codigo)

            if tipo_id is None:
                continue

            # Verificar que no exista ya
            existe = db.execute(text("""
                SELECT id FROM asistencia.incidencias
                WHERE asistencia_diaria_id = :asist_id
                  AND tipo_incidencia_id = :tipo_id
                  AND estatus != 'CANCELADA'
                LIMIT 1
            """), {"asist_id": asist["id"], "tipo_id": tipo_id}).scalar_one_or_none()

            if existe:
                continue

            # Determinar estatus de la incidencia (algunas ya revisadas)
            rand = random.random()
            if rand < 0.3:
                inc_estatus = "APROBADA"
            elif rand < 0.5:
                inc_estatus = "RECHAZADA"
            elif rand < 0.7:
                inc_estatus = "SIN_JUSTIFICAR"
            else:
                inc_estatus = "PENDIENTE"

            fecha_revision = None
            if inc_estatus in ("APROBADA", "RECHAZADA"):
                fecha_revision = datetime.combine(
                    asist["fecha"] + timedelta(days=random.randint(1, 5)),
                    time(random.randint(9, 14), random.randint(0, 59))
                )

            db.execute(text("""
                INSERT INTO asistencia.incidencias (
                    empleado_id, asistencia_diaria_id, tipo_incidencia_id,
                    fecha, puntos_originales, estatus, origen,
                    requiere_revision, fecha_revision
                ) VALUES (
                    :emp_id, :asist_id, :tipo_id,
                    :fecha, :puntos, :estatus, 'PROCESAMIENTO',
                    :requiere_revision, :fecha_revision
                )
                ON CONFLICT (asistencia_diaria_id, tipo_incidencia_id)
                    WHERE asistencia_diaria_id IS NOT NULL AND estatus != 'CANCELADA'
                DO NOTHING
            """), {
                "emp_id": emp["id"],
                "asist_id": asist["id"],
                "tipo_id": tipo_id,
                "fecha": asist["fecha"],
                "puntos": asist["puntos_generados"],
                "estatus": inc_estatus,
                "requiere_revision": inc_estatus == "PENDIENTE",
                "fecha_revision": fecha_revision,
            })

            count += 1

    db.commit()
    return count


def generar_marcaciones_crudas(db, empleados):
    """Genera marcaciones crudas simuladas para los últimos 30 días."""
    count = 0
    # Solo últimos 30 días para no sobrecargar
    dias_recientes = [d for d in DIAS_LABORALES if d >= FECHA_FIN - timedelta(days=30)]

    for emp in empleados:
        zk_user_id = str(1000 + EMPLEADOS_FICTICIOS.index(
            next((e for e in EMPLEADOS_FICTICIOS if e[0] == emp["codigo"]), EMPLEADOS_FICTICIOS[0])
        ))

        for dia in dias_recientes:
            # Verificar si hay asistencia para este día
            asist = db.execute(text("""
                SELECT primera_entrada, ultima_salida, estatus
                FROM asistencia.asistencias_diarias
                WHERE empleado_id = :emp_id AND fecha = :fecha
                LIMIT 1
            """), {"emp_id": emp["id"], "fecha": dia}).mappings().first()

            if asist is None or asist["estatus"] == "FALTA":
                continue

            # Generar marcación de entrada
            if asist["primera_entrada"]:
                entrada_dt = asist["primera_entrada"]
                if hasattr(entrada_dt, 'replace'):
                    db.execute(text("""
                        INSERT INTO asistencia.marcaciones_crudas (
                            dispositivo_origen, dispositivo_ip,
                            zk_uid_registro, zk_user_id,
                            fecha_hora, punch, punch_label, status, status_label,
                            empleado_id, codigo_empleado,
                            raw_payload, sync_run_id
                        ) VALUES (
                            'ZKTeco', '192.168.1.201',
                            :uid, :zk_user_id,
                            :fecha_hora, 0, 'Entrada', 1, 'Huella',
                            :emp_id, :codigo,
                            '{}'::jsonb, :sync_id
                        )
                        ON CONFLICT DO NOTHING
                    """), {
                        "uid": random.randint(1, 99999),
                        "zk_user_id": zk_user_id,
                        "fecha_hora": entrada_dt,
                        "emp_id": emp["id"],
                        "codigo": emp["codigo"],
                        "sync_id": f"SEED-{dia.isoformat()}",
                    })
                    count += 1

            # Generar marcación de salida
            if asist["ultima_salida"]:
                salida_dt = asist["ultima_salida"]
                if hasattr(salida_dt, 'replace'):
                    db.execute(text("""
                        INSERT INTO asistencia.marcaciones_crudas (
                            dispositivo_origen, dispositivo_ip,
                            zk_uid_registro, zk_user_id,
                            fecha_hora, punch, punch_label, status, status_label,
                            empleado_id, codigo_empleado,
                            raw_payload, sync_run_id
                        ) VALUES (
                            'ZKTeco', '192.168.1.201',
                            :uid, :zk_user_id,
                            :fecha_hora, 1, 'Salida', 1, 'Huella',
                            :emp_id, :codigo,
                            '{}'::jsonb, :sync_id
                        )
                        ON CONFLICT DO NOTHING
                    """), {
                        "uid": random.randint(1, 99999),
                        "zk_user_id": zk_user_id,
                        "fecha_hora": salida_dt,
                        "emp_id": emp["id"],
                        "codigo": emp["codigo"],
                        "sync_id": f"SEED-{dia.isoformat()}",
                    })
                    count += 1

    db.commit()
    return count


def _generar_entrada(dia, minutos_retardo):
    """Genera un datetime de entrada con el retardo indicado."""
    hora = 8
    minuto = minutos_retardo + random.randint(-2, 2)
    if minuto < 0:
        minuto = 0
    segundo = random.randint(0, 59)
    return datetime.combine(dia, time(hora, min(minuto, 59), segundo))


def _generar_salida(dia):
    """Genera un datetime de salida normal."""
    hora = 15
    minuto = random.randint(0, 10)
    segundo = random.randint(0, 59)
    return datetime.combine(dia, time(hora, minuto, segundo))


def _generar_observacion(estatus, minutos_retardo):
    """Genera observación según estatus."""
    if estatus == "COMPLETO":
        return "Asistencia dentro de tolerancia."
    elif estatus == "RETARDO_MENOR":
        return f"Entrada con {minutos_retardo} minutos de retardo."
    elif estatus == "RETARDO_MAYOR":
        return f"Entrada con {minutos_retardo} minutos de retardo."
    elif estatus == "FALTA":
        return "No se encontró checada de entrada para el día."
    return None


if __name__ == "__main__":
    main()
