"""
Continuacion puntual de seed_datos_prueba_dashboard.py:

1. Corrige la racha de faltas de DAE-0017: el primer intento (03-05 ago)
   choco con un evento de calendario activo (id=1, "DIaaa de prueba",
   recurrente cada 4 de agosto, es_laborable=false) que ya existia en la
   BD como dato de prueba de otra sesion, partiendo la racha en 2+1 en
   vez de 3 consecutivos. Se reubica a 12-14 ago (verificado limpio
   contra asistencia.calendario_eventos).

2. Re-ejecuta el motor real (procesar_asistencia_diaria) para reflejar
   el cambio.

3. Ejecuta acumular_puntos_periodo (ya con el fix de
   asistencia.descansos_obligatorios) para julio, agosto 1-15 y el
   hueco 16-23, y reporta los DOs y alertas de faltas consecutivas
   generados de verdad.
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

from app.core.database import SessionLocal
from app.repositories.asistencia_procesamiento_repo import procesar_asistencia_diaria
from app.services.puntos_acumulacion_service import acumular_puntos_periodo

FECHA_INICIO = date(2026, 7, 21)
FECHA_FIN = date(2026, 8, 23)

PERIODO_JULIO = (date(2026, 7, 21), date(2026, 7, 31))
PERIODO_AGOSTO = (date(2026, 8, 1), date(2026, 8, 15))
PERIODO_GAP = (date(2026, 8, 16), FECHA_FIN)


def main():
    db = SessionLocal()

    try:
        print("1. Eliminando marcaciones de DAE-0017 en 12-14 ago (para forzar FALTA limpia)...")
        result = db.execute(
            text(
                """
                DELETE FROM asistencia.marcaciones_crudas mc
                USING personal.empleados e
                WHERE mc.empleado_id = e.id
                  AND e.codigo_empleado = 'DAE-0017'
                  AND mc.fecha_hora::date BETWEEN '2026-08-12' AND '2026-08-14'
                """
            )
        )
        db.commit()
        print(f"   Marcaciones eliminadas: {result.rowcount}")

        print(f"\n2. Reprocesando asistencia real ({FECHA_INICIO} a {FECHA_FIN})...")
        resultado_proc = procesar_asistencia_diaria(db, FECHA_INICIO, FECHA_FIN)
        db.commit()
        print(f"   OK, claves de resultado: {list(resultado_proc.keys())}")

        verificacion = db.execute(
            text(
                """
                SELECT ad.fecha, ad.estatus
                FROM asistencia.asistencias_diarias ad
                JOIN personal.empleados e ON e.id = ad.empleado_id
                WHERE e.codigo_empleado = 'DAE-0017'
                  AND ad.fecha BETWEEN '2026-08-11' AND '2026-08-15'
                ORDER BY ad.fecha
                """
            )
        ).mappings().all()
        print("   DAE-0017 11-15 ago:", [(r["fecha"].isoformat(), r["estatus"]) for r in verificacion])

        print("\n3. Ejecutando motor real de puntos/DO (ya corregido)...")
        for nombre, (fi, ff) in (
            ("Quincena jul 21-31", PERIODO_JULIO),
            ("Quincena ago 01-15", PERIODO_AGOSTO),
            ("Hueco ago 16-23", PERIODO_GAP),
        ):
            resultado = acumular_puntos_periodo(db, fi, ff)
            print(f"   {nombre}: movimientos={resultado['movimientos_puntos_insertados']} "
                  f"DOs={len(resultado['dos_generados'])} "
                  f"alertas_faltas={len(resultado['alertas_faltas_consecutivas'])} "
                  f"periodos_no_resueltos={len(resultado['periodos_no_resueltos'])}")
            for do in resultado["dos_generados"]:
                print(f"      -> DO real: {do}")
            for al in resultado["alertas_faltas_consecutivas"]:
                print(f"      -> Alerta faltas consecutivas real: {al}")

        print("\n4. Verificando asistencia.descansos_obligatorios...")
        dos_reales = db.execute(
            text(
                """
                SELECT e.codigo_empleado, do_.numero_descanso_periodo, do_.puntos_efectivos_periodo, do_.estatus
                FROM asistencia.descansos_obligatorios do_
                JOIN personal.empleados e ON e.id = do_.empleado_id
                ORDER BY e.codigo_empleado, do_.numero_descanso_periodo
                """
            )
        ).mappings().all()
        for row in dos_reales:
            print(f"   {row['codigo_empleado']}: DO #{row['numero_descanso_periodo']} "
                  f"({row['puntos_efectivos_periodo']} pts) estatus={row['estatus']}")

        print("\n5. Verificando resumen_periodo_empleado.requiere_revision_baja...")
        revisiones = db.execute(
            text(
                """
                SELECT e.codigo_empleado, rpe.requiere_revision_baja, rpe.motivo_revision_baja
                FROM asistencia.resumen_periodo_empleado rpe
                JOIN personal.empleados e ON e.id = rpe.empleado_id
                WHERE rpe.requiere_revision_baja = true
                  AND e.codigo_empleado LIKE 'DAE-00%'
                """
            )
        ).mappings().all()
        for row in revisiones:
            print(f"   {row['codigo_empleado']}: {row['motivo_revision_baja']}")

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
