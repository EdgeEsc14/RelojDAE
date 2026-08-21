"""
Tests de acumulación de puntos y resolución del Periodo de Evaluación.

Causa raíz corregida: puntos_acumulacion_service.py usaba
COALESCE(..., 1) como periodo_evaluacion_id al insertar en
asistencia.movimientos_puntos. En la BD real no existe
asistencia.periodos_evaluacion.id = 1, así que cualquier
POST /asistencia/procesar que generara puntos (RETARDO_MENOR/MAYOR)
violaba fk_movimientos_puntos_periodo y devolvía 500 — incluso cuando
el procesamiento de asistencia en sí era correcto.

Cubre:
1. periodo válido -> movimientos_puntos se insertan con ese periodo;
2. cero periodos -> no FK violation ni periodo_id inventado, se reporta;
3. múltiples periodos -> no se elige uno arbitrario, se reporta;
4. reprocesar sigue siendo idempotente (asistencia y movimientos_puntos);
5. POST /asistencia/procesar nunca responde 500 por periodo sin resolver.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import text

from app.core.security import create_access_token
from app.repositories.asistencia_procesamiento_repo import (
    procesar_asistencia_diaria,
)
from app.services.puntos_acumulacion_service import acumular_puntos_periodo


FECHA_TEST = date(2026, 8, 18)  # Martes


# ============================================================
# Helpers
# ============================================================


def insertar_marcacion(db, empleado_id, fecha_hora, punch=0):
    db.execute(text(
        """
        INSERT INTO asistencia.marcaciones_crudas
        (dispositivo_origen, zk_user_id, fecha_hora, punch, punch_label, empleado_id, raw_payload)
        VALUES ('TEST', '100', :fecha_hora, :punch, :punch_label, :empleado_id, '{}'::jsonb)
        """
    ), {
        "fecha_hora": fecha_hora,
        "punch": punch,
        "punch_label": "Entrada" if punch == 0 else "Salida",
        "empleado_id": empleado_id,
    })
    db.flush()


def get_empleado_id(db, codigo="EMP-TEST-001"):
    return db.execute(text(
        "SELECT id FROM personal.empleados WHERE codigo_empleado = :codigo"
    ), {"codigo": codigo}).scalar_one()


def get_politica_id(db, codigo="POLITICA_DAE_GENERAL"):
    return db.execute(text(
        "SELECT id FROM asistencia.politicas_asistencia WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def crear_periodo(
    db, *, politica_id, codigo, fecha_inicio, fecha_fin,
    numero_periodo=1, estatus="ABIERTO",
):
    db.execute(text(
        "INSERT INTO asistencia.periodos_evaluacion "
        "(politica_asistencia_id, codigo, nombre, tipo_periodo, anio, "
        "numero_periodo, fecha_inicio, fecha_fin, estatus) "
        "VALUES (:politica_id, :codigo, :codigo, 'QUINCENAL', 2026, "
        ":numero_periodo, :fecha_inicio, :fecha_fin, :estatus)"
    ), {
        "politica_id": politica_id,
        "codigo": codigo,
        "numero_periodo": numero_periodo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "estatus": estatus,
    })
    return db.execute(text(
        "SELECT id FROM asistencia.periodos_evaluacion WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def generar_retardo_menor(db, empleado_id, fecha=FECHA_TEST):
    """Entrada 08:15 -> 900s de retardo: RETARDO_MENOR (1 punto, seed_motor)."""
    insertar_marcacion(db, empleado_id, datetime.combine(fecha, datetime.min.time()).replace(hour=8, minute=15))
    insertar_marcacion(db, empleado_id, datetime.combine(fecha, datetime.min.time()).replace(hour=15, minute=0), punch=1)
    db.commit()


def contar_movimientos_puntos(db, empleado_id, fecha=FECHA_TEST):
    return db.execute(text(
        "SELECT COUNT(*) FROM asistencia.movimientos_puntos "
        "WHERE empleado_id = :empleado_id AND fecha = :fecha AND tipo_movimiento = 'CARGO'"
    ), {"empleado_id": empleado_id, "fecha": fecha}).scalar_one()


# ============================================================
# 1-4: nivel servicio, contra dae_reloj_test
# ============================================================


@pytest.mark.integration
class TestAcumulacionPuntosPeriodo:
    def test_periodo_valido_inserta_movimientos_puntos(self, db_motor, seed_motor):
        empleado_id = get_empleado_id(db_motor)
        politica_id = get_politica_id(db_motor)
        periodo_id = crear_periodo(
            db_motor, politica_id=politica_id, codigo="PERIODO_VALIDO",
            fecha_inicio=date(2026, 8, 1), fecha_fin=date(2026, 8, 31),
        )
        db_motor.commit()

        generar_retardo_menor(db_motor, empleado_id)
        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        resultado = acumular_puntos_periodo(db_motor, FECHA_TEST, FECHA_TEST)

        assert resultado["periodos_no_resueltos"] == []
        assert resultado["movimientos_puntos_insertados"] == 1

        movimiento = db_motor.execute(text(
            "SELECT periodo_evaluacion_id, puntos FROM asistencia.movimientos_puntos "
            "WHERE empleado_id = :empleado_id AND fecha = :fecha AND tipo_movimiento = 'CARGO'"
        ), {"empleado_id": empleado_id, "fecha": FECHA_TEST}).mappings().one()

        assert movimiento["periodo_evaluacion_id"] == periodo_id
        assert movimiento["puntos"] == 1

    def test_cero_periodos_no_viola_fk_ni_inventa_id(self, db_motor, seed_motor):
        """Sin ningún periodo_evaluacion sembrado (el escenario real que
        causaba el 500): no debe lanzar excepción ni insertar con un id
        inventado (p. ej. 1)."""
        empleado_id = get_empleado_id(db_motor)

        generar_retardo_menor(db_motor, empleado_id)
        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        # No debe lanzar IntegrityError por FK.
        resultado = acumular_puntos_periodo(db_motor, FECHA_TEST, FECHA_TEST)

        assert resultado["movimientos_puntos_insertados"] == 0
        assert contar_movimientos_puntos(db_motor, empleado_id) == 0

        problemas = resultado["periodos_no_resueltos"]
        assert len(problemas) >= 1
        problema = next(p for p in problemas if p["contexto"] == "insercion_movimientos")
        assert problema["estado"] == "SIN_PERIODO"
        assert problema["fecha"] == str(FECHA_TEST)
        assert problema["candidatos"] == []

    def test_multiples_periodos_no_elige_arbitrariamente(self, db_motor, seed_motor):
        empleado_id = get_empleado_id(db_motor)
        politica_id = get_politica_id(db_motor)

        periodo_a = crear_periodo(
            db_motor, politica_id=politica_id, codigo="PERIODO_A",
            fecha_inicio=date(2026, 8, 1), fecha_fin=date(2026, 8, 31),
            numero_periodo=1,
        )
        periodo_b = crear_periodo(
            db_motor, politica_id=politica_id, codigo="PERIODO_B",
            fecha_inicio=date(2026, 8, 15), fecha_fin=date(2026, 9, 15),
            numero_periodo=2,
        )
        db_motor.commit()

        generar_retardo_menor(db_motor, empleado_id)
        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        resultado = acumular_puntos_periodo(db_motor, FECHA_TEST, FECHA_TEST)

        assert resultado["movimientos_puntos_insertados"] == 0
        assert contar_movimientos_puntos(db_motor, empleado_id) == 0

        problema = next(
            p for p in resultado["periodos_no_resueltos"]
            if p["contexto"] == "insercion_movimientos"
        )
        assert problema["estado"] == "MULTIPLES_PERIODOS"
        assert sorted(problema["candidatos"]) == sorted([periodo_a, periodo_b])

    def test_reprocesar_es_idempotente(self, db_motor, seed_motor):
        empleado_id = get_empleado_id(db_motor)
        politica_id = get_politica_id(db_motor)
        crear_periodo(
            db_motor, politica_id=politica_id, codigo="PERIODO_IDEMPOTENTE",
            fecha_inicio=date(2026, 8, 1), fecha_fin=date(2026, 8, 31),
        )
        db_motor.commit()

        generar_retardo_menor(db_motor, empleado_id)

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        acumular_puntos_periodo(db_motor, FECHA_TEST, FECHA_TEST)

        # Reprocesar el mismo rango una segunda vez.
        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        resultado_2 = acumular_puntos_periodo(db_motor, FECHA_TEST, FECHA_TEST)

        total_asistencias = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.asistencias_diarias "
            "WHERE empleado_id = :empleado_id AND fecha = :fecha"
        ), {"empleado_id": empleado_id, "fecha": FECHA_TEST}).scalar_one()

        assert total_asistencias == 1, "No debe duplicar la fila de asistencia diaria."
        assert resultado_2["movimientos_puntos_insertados"] == 0, (
            "La segunda pasada no debe volver a insertar el mismo movimiento."
        )
        assert contar_movimientos_puntos(db_motor, empleado_id) == 1, (
            "No debe duplicar el movimiento de puntos ya registrado."
        )


# ============================================================
# 5: nivel HTTP, POST /asistencia/procesar nunca 500 por periodo
# ============================================================


def _crear_modulo(db, codigo="ASISTENCIA"):
    db.execute(text(
        "INSERT INTO seguridad.modulos (codigo, nombre, activo) "
        "VALUES (:codigo, :codigo, TRUE) ON CONFLICT (codigo) DO NOTHING"
    ), {"codigo": codigo})
    return db.execute(text(
        "SELECT id FROM seguridad.modulos WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()


def _crear_rol_asistencia_total(db, codigo="ROL_PROCESAR_PUNTOS"):
    db.execute(text(
        "INSERT INTO seguridad.roles (codigo, nombre, activo) VALUES (:codigo, :codigo, TRUE)"
    ), {"codigo": codigo})
    rol_id = db.execute(text(
        "SELECT id FROM seguridad.roles WHERE codigo = :codigo"
    ), {"codigo": codigo}).scalar_one()
    modulo_id = _crear_modulo(db)
    db.execute(text(
        "INSERT INTO seguridad.permisos_rol "
        "(rol_id, modulo_id, alcance_datos, puede_consultar, puede_crear, "
        "puede_editar, puede_eliminar, puede_aprobar, puede_exportar) "
        "VALUES (:rol_id, :modulo_id, 'TOTAL', TRUE, FALSE, TRUE, FALSE, FALSE, FALSE)"
    ), {"rol_id": rol_id, "modulo_id": modulo_id})
    return rol_id


def _crear_usuario(db, *, rol_id, correo):
    db.execute(text(
        "INSERT INTO seguridad.usuarios (rol_id, correo, correo_electronico, estatus) "
        "VALUES (:rol_id, :correo, :correo, 'ACTIVO')"
    ), {"rol_id": rol_id, "correo": correo})
    return db.execute(text(
        "SELECT id FROM seguridad.usuarios WHERE correo_electronico = :correo"
    ), {"correo": correo}).scalar_one()


@pytest.mark.integration
class TestProcesarAsistenciaHTTPNoFalla500:
    def test_sin_periodo_configurado_no_devuelve_500(self, db_motor, seed_motor, api_client):
        empleado_id = get_empleado_id(db_motor)
        generar_retardo_menor(db_motor, empleado_id)

        rol_id = _crear_rol_asistencia_total(db_motor)
        usuario_id = _crear_usuario(db_motor, rol_id=rol_id, correo="procesa_puntos@dae.test")
        db_motor.commit()

        token = create_access_token({"sub": str(usuario_id)})

        resp = api_client.post(
            "/api/v1/asistencia/procesar",
            json={"fecha_inicio": str(FECHA_TEST), "fecha_fin": str(FECHA_TEST)},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()

        # El procesamiento de asistencia en sí debe seguir siendo correcto.
        assert body["procesadas"] >= 1
        assert body["errores"] == []

        # La acumulación de puntos reporta el problema de forma
        # explícita, sin haber lanzado un 500.
        acumulacion = body["acumulacion_puntos"]
        assert acumulacion is not None
        assert acumulacion.get("error") is None, (
            "No debería caer en el fallback genérico: el problema de "
            "periodo debe resolverse dentro de acumular_puntos_periodo."
        )
        problema = next(
            p for p in acumulacion["periodos_no_resueltos"]
            if p["contexto"] == "insercion_movimientos"
        )
        assert problema["estado"] == "SIN_PERIODO"

        # La asistencia procesada debe existir pese a que no hubo periodo.
        asistencia = db_motor.execute(text(
            "SELECT estatus FROM asistencia.asistencias_diarias "
            "WHERE empleado_id = :empleado_id AND fecha = :fecha"
        ), {"empleado_id": empleado_id, "fecha": FECHA_TEST}).mappings().one()
        assert asistencia["estatus"] == "RETARDO_MENOR"
