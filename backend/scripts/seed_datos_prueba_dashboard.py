"""
Genera empleados ficticios de prueba (prefijo DAE-, nombres aleatorios) para
poblar el Dashboard: puntualidad, retardos menores/mayores, faltas e
inasistencias, incluyendo un caso real de Dia de Omision (descanso
obligatorio) y un caso real de alerta de revision de baja por faltas
consecutivas.

A diferencia de seed_data.py (que escribe asistencias_diarias directamente),
este script solo inserta marcaciones_crudas y ejecuta el motor real:

    procesar_asistencia_diaria()  -> calcula estatus por dia
    acumular_puntos_periodo()     -> calcula puntos, DOs y alertas de baja

para que el resultado (incluyendo el Dia de Omision) sea producto del mismo
calculo que usa el sistema en produccion, no un valor inventado.

Tambien registra a cada empleado ficticio en el reloj ZKTeco fisico
(dispositivo activo), usando IDs de usuario ZK verificados de antemano
contra el dispositivo real (9950-9957) para no colisionar con usuarios ya
existentes ahi.

Uso:
    .v_relojdae\\Scripts\\python.exe scripts\\seed_datos_prueba_dashboard.py
"""

import os
import random
import string
import sys
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

from app.core.access_control import AccessScope
from app.core.database import SessionLocal
from app.repositories.asistencia_procesamiento_repo import procesar_asistencia_diaria
from app.repositories.empleados_integral_repo import crear_alta_integral_empleado
from app.schemas.empleados_integral import AltaIntegralEmpleadoRequest
from app.services.empleados_sincronizacion_service import sincronizar_empleado_relojes
from app.services.puntos_acumulacion_service import acumular_puntos_periodo


FECHA_INICIO = date(2026, 7, 21)
FECHA_FIN = date(2026, 8, 23)

PERIODO_JULIO = (date(2026, 7, 21), date(2026, 7, 31))
PERIODO_AGOSTO = (date(2026, 8, 1), date(2026, 8, 15))
PERIODO_GAP = (date(2026, 8, 16), FECHA_FIN)

HORARIO_ID = 1  # ADMINISTRATIVO 08:00-15:00, tolerancia real via politica
DISPOSITIVO_IP_SIMULADA = "SEED-DAE"

EMPLEADOS_PRUEBA = [
    {"perfil": "puntual", "zk": "9950", "unidad": 8, "puesto": 9,
     "obs": "Empleado ficticio de prueba (dashboard demo) - perfil puntual."},
    {"perfil": "puntual", "zk": "9951", "unidad": 10, "puesto": 2,
     "obs": "Empleado ficticio de prueba (dashboard demo) - perfil puntual."},
    {"perfil": "retardo_menor", "zk": "9952", "unidad": 7, "puesto": 8,
     "obs": "Empleado ficticio de prueba (dashboard demo) - retardos menores frecuentes."},
    {"perfil": "retardo_menor", "zk": "9953", "unidad": 9, "puesto": 9,
     "obs": "Empleado ficticio de prueba (dashboard demo) - retardos menores frecuentes."},
    {"perfil": "retardo_mayor_do", "zk": "9954", "unidad": 6, "puesto": 8,
     "obs": ("Empleado ficticio de prueba (dashboard demo) - retardos mayores "
             "concentrados en la quincena 01-15/ago/2026 para disparar un "
             "Dia de Omision (descanso obligatorio) real via "
             "acumular_puntos_periodo, no insertado a mano.")},
    {"perfil": "retardo_mayor_leve", "zk": "9955", "unidad": 11, "puesto": 2,
     "obs": "Empleado ficticio de prueba (dashboard demo) - retardos mayores ocasionales."},
    {"perfil": "faltas_consecutivas", "zk": "9956", "unidad": 12, "puesto": 9,
     "obs": ("Empleado ficticio de prueba (dashboard demo) - racha de 3 "
             "faltas consecutivas en agosto para disparar la alerta real de "
             "revision de baja (3+ faltas consecutivas).")},
    {"perfil": "inasistencias_esporadicas", "zk": "9957", "unidad": 13, "puesto": 8,
     "obs": "Empleado ficticio de prueba (dashboard demo) - inasistencias esporadicas no consecutivas."},
]


def random_word(n):
    return "".join(random.choices(string.ascii_uppercase, k=n))


def fake_rfc(i):
    letras = "".join(random.choices(string.ascii_uppercase, k=2))
    return f"XAXX{900000 + i:06d}{letras}{i % 10}"


def weekdays(inicio, fin):
    dias = []
    actual = inicio
    while actual <= fin:
        if actual.weekday() < 5:
            dias.append(actual)
        actual += timedelta(days=1)
    return dias


def pick_racha_consecutiva(dias, ventana_inicio, ventana_fin, largo=3):
    candidatos = sorted(d for d in dias if ventana_inicio <= d <= ventana_fin)
    for idx in range(len(candidatos) - largo + 1):
        tramo = candidatos[idx: idx + largo]
        if all((tramo[j + 1] - tramo[j]).days == 1 for j in range(largo - 1)):
            return tramo
    raise RuntimeError("No se encontro una racha de dias consecutivos en la ventana dada.")


def entrada_dt(dia, tipo):
    if tipo == "COMPLETO":
        return datetime.combine(dia, time(7, 58, 0))
    if tipo == "TOLERANCIA":
        return datetime.combine(dia, time(8, 5, 0))
    if tipo == "RETARDO_MENOR":
        return datetime.combine(dia, time(8, 15, 0))
    if tipo == "RETARDO_MAYOR":
        return datetime.combine(dia, time(8, 26, 0))
    return None


def salida_dt(dia):
    return datetime.combine(dia, time(15, random.randint(0, 10), random.randint(0, 59)))


def plan_dias(perfil, dias, racha_faltas):
    plan = {}
    for d in dias:
        en_agosto = PERIODO_AGOSTO[0] <= d <= PERIODO_AGOSTO[1]
        r = random.random()

        if perfil == "puntual":
            tipo = "COMPLETO" if r < 0.75 else ("TOLERANCIA" if r < 0.93 else "RETARDO_MENOR")

        elif perfil == "retardo_menor":
            tipo = "RETARDO_MENOR" if r < 0.55 else ("COMPLETO" if r < 0.8 else "TOLERANCIA")

        elif perfil == "retardo_mayor_do":
            if en_agosto:
                tipo = "RETARDO_MAYOR"
            else:
                tipo = "RETARDO_MAYOR" if r < 0.3 else ("COMPLETO" if r < 0.7 else "RETARDO_MENOR")

        elif perfil == "retardo_mayor_leve":
            tipo = "RETARDO_MAYOR" if r < 0.25 else ("RETARDO_MENOR" if r < 0.5 else "COMPLETO")

        elif perfil == "faltas_consecutivas":
            if d in racha_faltas:
                tipo = "FALTA"
            else:
                tipo = "COMPLETO" if r < 0.7 else ("TOLERANCIA" if r < 0.85 else "RETARDO_MENOR")

        elif perfil == "inasistencias_esporadicas":
            tipo = "FALTA" if r < 0.18 else ("COMPLETO" if r < 0.7 else "TOLERANCIA")

        else:
            raise ValueError(f"Perfil desconocido: {perfil}")

        plan[d] = tipo
    return plan


def insertar_marcacion(db, empleado_id, codigo_empleado, zk_user_id, fecha_hora, punch, punch_label, sync_run_id):
    db.execute(
        text(
            """
            INSERT INTO asistencia.marcaciones_crudas (
                dispositivo_origen, dispositivo_ip,
                zk_uid_registro, zk_user_id,
                fecha_hora, punch, punch_label, status, status_label,
                empleado_id, codigo_empleado,
                raw_payload, sync_run_id
            ) VALUES (
                :origen, NULL,
                :uid, :zk_user_id,
                :fecha_hora, :punch, :punch_label, 1, 'Huella',
                :empleado_id, :codigo,
                '{}'::jsonb, :sync_id
            )
            ON CONFLICT DO NOTHING
            """
        ),
        {
            "origen": DISPOSITIVO_IP_SIMULADA,
            "uid": int(zk_user_id),
            "zk_user_id": zk_user_id,
            "fecha_hora": fecha_hora,
            "punch": punch,
            "punch_label": punch_label,
            "empleado_id": empleado_id,
            "codigo": codigo_empleado,
            "sync_id": sync_run_id,
        },
    )


def obtener_admin_user_id(db):
    row = db.execute(
        text(
            """
            SELECT u.id
            FROM seguridad.usuarios u
            JOIN seguridad.roles r ON r.id = u.rol_id
            WHERE r.codigo = 'SUPER_ADMIN' AND u.activo = true
            ORDER BY u.id DESC
            LIMIT 1
            """
        )
    ).scalar_one()
    return int(row)


def main():
    db = SessionLocal()

    try:
        admin_user_id = obtener_admin_user_id(db)
        print(f"Usando usuario administrador id={admin_user_id} para auditoria/scope.")

        access_scope = AccessScope(
            user_id=admin_user_id,
            employee_id=None,
            role_id=None,
            role_code="SUPER_ADMIN",
            module_code="EMPLEADOS",
            data_scope="TOTAL",
            can_read=True,
            can_create=True,
            can_edit=True,
            can_delete=True,
            can_approve=True,
            can_export=True,
            allowed_unit_ids=(),
        )

        print("\n1. Creando empleados ficticios via alta integral real...")
        creados = []
        for i, spec in enumerate(EMPLEADOS_PRUEBA, start=1):
            payload = AltaIntegralEmpleadoRequest(
                nombres=random_word(6),
                apellido_paterno=random_word(7),
                apellido_materno=random_word(5),
                rfc=fake_rfc(i),
                correo_personal=f"prueba.dae{i}@ejemplo.invalid",
                tipo_contratacion_id=5,
                fecha_ingreso=date(2026, 6, 1),
                puesto_id=spec["puesto"],
                unidad_organizacional_id=spec["unidad"],
                horario_id=HORARIO_ID,
                observaciones=spec["obs"],
                registrar_en_reloj=True,
                todos_dispositivos_activos=True,
                zk_user_id=spec["zk"],
            )

            resultado = crear_alta_integral_empleado(
                db=db,
                payload=payload,
                solicitado_por_usuario_id=admin_user_id,
            )

            creados.append({**resultado, "perfil": spec["perfil"], "zk": spec["zk"]})
            print(f"   {resultado['codigo_empleado']}  perfil={spec['perfil']:<28} zk_user_id={spec['zk']}")

        print("\n2. Sincronizando empleados ficticios al reloj ZKTeco fisico...")
        for c in creados:
            try:
                sync = sincronizar_empleado_relojes(
                    db=db,
                    codigo_empleado=c["codigo_empleado"],
                    access_scope=access_scope,
                )
                print(f"   {c['codigo_empleado']}: {sync['exitosos']}/{sync['total_dispositivos']} dispositivo(s) OK")
                for r in sync["resultados"]:
                    if not r["exitoso"]:
                        print(f"      ERROR: {r['mensaje']}")
            except Exception as exc:
                print(f"   ERROR sincronizando {c['codigo_empleado']}: {exc}")

        print("\n3. Generando marcaciones_crudas realistas (sin tocar asistencias_diarias)...")
        dias = weekdays(FECHA_INICIO, FECHA_FIN)
        racha_faltas = pick_racha_consecutiva(dias, *PERIODO_AGOSTO, largo=3)
        print(f"   Racha de faltas consecutivas elegida: {[d.isoformat() for d in racha_faltas]}")

        total_marcaciones = 0
        for c in creados:
            plan = plan_dias(c["perfil"], dias, racha_faltas)
            for dia, tipo in plan.items():
                if tipo == "FALTA":
                    continue

                entrada = entrada_dt(dia, tipo)
                salida = salida_dt(dia)
                sync_id = f"SEED-DAE-{dia.isoformat()}"

                insertar_marcacion(
                    db, c["empleado_id"], c["codigo_empleado"], c["zk"],
                    entrada, 0, "Entrada", sync_id,
                )
                insertar_marcacion(
                    db, c["empleado_id"], c["codigo_empleado"], c["zk"],
                    salida, 1, "Salida", sync_id,
                )
                total_marcaciones += 2

        db.commit()
        print(f"   Marcaciones insertadas: {total_marcaciones}")

        print(f"\n4. Ejecutando motor real de asistencia ({FECHA_INICIO} a {FECHA_FIN})...")
        resultado_proc = procesar_asistencia_diaria(db, FECHA_INICIO, FECHA_FIN)
        db.commit()
        print(f"   procesar_asistencia_diaria -> claves: {list(resultado_proc.keys())}")

        print("\n5. Ejecutando motor real de puntos/DO por quincena resoluble...")
        resultado_julio = acumular_puntos_periodo(db, *PERIODO_JULIO)
        print(f"   Quincena jul: movimientos={resultado_julio['movimientos_puntos_insertados']} "
              f"DOs={len(resultado_julio['dos_generados'])} "
              f"alertas_faltas={len(resultado_julio['alertas_faltas_consecutivas'])}")

        resultado_agosto = acumular_puntos_periodo(db, *PERIODO_AGOSTO)
        print(f"   Quincena ago 1-15: movimientos={resultado_agosto['movimientos_puntos_insertados']} "
              f"DOs={len(resultado_agosto['dos_generados'])} "
              f"alertas_faltas={len(resultado_agosto['alertas_faltas_consecutivas'])}")
        for do in resultado_agosto["dos_generados"]:
            print(f"      -> DO real generado: {do}")
        for al in resultado_agosto["alertas_faltas_consecutivas"]:
            print(f"      -> Alerta faltas consecutivas real: {al}")

        resultado_gap = acumular_puntos_periodo(db, *PERIODO_GAP)
        print(f"   Ventana 16-23 ago (sin periodo de evaluacion abierto): "
              f"periodos_no_resueltos={len(resultado_gap['periodos_no_resueltos'])}")

        print("\nLISTO.")

    except Exception as exc:
        db.rollback()
        print(f"\nERROR: {exc}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
