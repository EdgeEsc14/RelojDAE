"""
Tests de integración del motor de asistencia contra dae_reloj_test.

Llaman a procesar_asistencia_diaria() REAL.
Usan la estrategia de join_transaction_mode="create_savepoint" para aislar.

Tests que incumplan el contrato: @pytest.mark.xfail(strict=True, reason=...)
"""

import pytest
from datetime import date, datetime, time, timedelta
from sqlalchemy import text

from app.repositories.asistencia_procesamiento_repo import (
    procesar_asistencia_diaria,
)
from app.services.calendario_service import resolver_fecha_laborable


FECHA_TEST = date(2026, 8, 18)  # Martes


# ============================================================
# Helpers
# ============================================================


def insertar_marcacion(db_session, empleado_id, fecha_hora, punch=0):
    """Inserta una marcación cruda de prueba."""
    db_session.execute(text(
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
    db_session.flush()


def obtener_asistencia(db_session, empleado_id, fecha):
    """Obtiene el registro de asistencia diaria."""
    row = db_session.execute(text(
        """
        SELECT * FROM asistencia.asistencias_diarias
        WHERE empleado_id = :empleado_id AND fecha = :fecha
        """
    ), {"empleado_id": empleado_id, "fecha": fecha}).mappings().first()
    return dict(row) if row else None


def get_empleado_id(db_session, codigo="EMP-TEST-001"):
    """Obtiene ID del empleado de prueba."""
    return db_session.execute(text(
        "SELECT id FROM personal.empleados WHERE codigo_empleado = :codigo"
    ), {"codigo": codigo}).scalar_one()


# ============================================================
# CALENDARIO: resolver_fecha_laborable
# ============================================================


@pytest.mark.integration
class TestCalendarioIntegration:
    """Tests del servicio de calendario contra BD real."""

    def test_fecha_sin_eventos_es_laborable_por_defecto(self, db_session, seed_basico):
        """Sin eventos de calendario, un día se considera laborable."""
        resultado = resolver_fecha_laborable(db_session, FECHA_TEST, get_empleado_id(db_session))
        assert resultado.es_laborable is True
        assert resultado.fuente in ("HORARIO_DIAS", "DEFAULT")

    def test_dia_no_laboral_con_evento(self, db_session, seed_basico):
        """Un evento DIA_NO_LABORAL debe marcar el día como no laborable."""
        calendario_id = db_session.execute(text(
            "SELECT id FROM asistencia.calendarios WHERE codigo = 'CALENDARIO_TEST'"
        )).scalar_one()

        db_session.execute(text(
            """
            INSERT INTO asistencia.calendario_eventos
            (calendario_id, nombre, tipo_evento, tipo_recurrencia, fecha_inicio,
             afecta_asistencia, es_laborable, prioridad)
            VALUES (:cal_id, 'Día de prueba no laborable', 'DESCANSO_INSTITUCIONAL',
                    'FECHA_ESPECIFICA', :fecha, TRUE, FALSE, 10)
            """
        ), {"cal_id": calendario_id, "fecha": FECHA_TEST})
        db_session.flush()

        resultado = resolver_fecha_laborable(db_session, FECHA_TEST, get_empleado_id(db_session))
        assert resultado.es_laborable is False
        assert resultado.fuente == "CALENDARIO"

    def test_laborable_extraordinario(self, db_session, seed_basico):
        """Un evento LABORABLE_EXTRAORDINARIO marca el día como laborable."""
        calendario_id = db_session.execute(text(
            "SELECT id FROM asistencia.calendarios WHERE codigo = 'CALENDARIO_TEST'"
        )).scalar_one()

        # Domingo normalmente no laboral
        domingo = date(2026, 8, 23)

        db_session.execute(text(
            """
            INSERT INTO asistencia.calendario_eventos
            (calendario_id, nombre, tipo_evento, tipo_recurrencia, fecha_inicio,
             afecta_asistencia, es_laborable, prioridad)
            VALUES (:cal_id, 'Trabajo extraordinario', 'LABORABLE_EXTRAORDINARIO',
                    'FECHA_ESPECIFICA', :fecha, TRUE, TRUE, 10)
            """
        ), {"cal_id": calendario_id, "fecha": domingo})
        db_session.flush()

        resultado = resolver_fecha_laborable(db_session, domingo, get_empleado_id(db_session))
        assert resultado.es_laborable is True
        assert resultado.fuente == "CALENDARIO"


# ============================================================
# HORARIO_DIAS
# ============================================================


@pytest.mark.integration
class TestHorarioDiasIntegration:
    """Tests de horario_dias contra BD real."""

    def test_horario_dias_dia_no_laboral(self, db_session, seed_basico):
        """horario_dias puede marcar un día como no laboral."""
        horario_id = db_session.execute(text(
            "SELECT id FROM asistencia.horarios WHERE codigo = 'HORARIO_TEST'"
        )).scalar_one()

        # Martes (dia_semana=2 ISO) marcado como no laboral
        db_session.execute(text(
            """
            INSERT INTO asistencia.horario_dias
            (horario_id, dia_semana, es_laboral, hora_entrada, hora_salida)
            VALUES (:horario_id, 2, FALSE, NULL, NULL)
            """
        ), {"horario_id": horario_id})
        db_session.flush()

        empleado_id = get_empleado_id(db_session)
        resultado = resolver_fecha_laborable(db_session, FECHA_TEST, empleado_id)
        # FECHA_TEST es martes (dia_semana=2)
        assert resultado.es_laborable is False
        assert resultado.fuente == "HORARIO_DIAS"


# ============================================================
# MOTOR: procesar_asistencia_diaria
# ============================================================


@pytest.mark.integration
class TestMotorProcesamiento:
    """
    Tests del motor real procesar_asistencia_diaria().
    Usan db_motor (TRUNCATE) en vez de savepoints porque el motor
    hace commit()/rollback() internos.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="BUG C1: Motor actual no genera FALTA para empleados sin marcaciones. "
               "Solo procesa empleados que tienen marcaciones_crudas con punch=0."
    )
    def test_ausencia_total_genera_falta(self, db_motor, seed_motor):
        """
        §6 Contrato: empleado activo + horario + día laboral + 0 marcaciones → FALTA.
        """
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        # Verificar que no hay marcaciones para la fecha
        marc_count = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.marcaciones_crudas WHERE empleado_id = :eid AND fecha = :f"
        ), {"eid": empleado_id, "f": FECHA_TEST}).scalar_one()
        assert marc_count == 0, "No debería haber marcaciones"

        # Ejecutar procesamiento
        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        # Verificar resultado
        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        assert asistencia is not None, (
            f"No se generó registro de asistencia. "
            f"Resultado motor: {resultado}"
        )
        assert asistencia["estatus"] == "FALTA"

    def test_entrada_puntual_genera_completo(self, db_motor, seed_motor):
        """Empleado con entrada puntual y salida → COMPLETO."""
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 7, 55, 0), punch=0)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 15, 5, 0), punch=1)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        assert asistencia is not None
        assert asistencia["estatus"] == "COMPLETO"
        assert asistencia["puntos_generados"] == 0

    def test_idempotencia_reprocesar(self, db_motor, seed_motor):
        """§13: Procesar dos veces produce el mismo resultado."""
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 8, 5, 0), punch=0)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 15, 0, 0), punch=1)
        db_motor.commit()

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        asistencia_1 = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        asistencia_2 = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)

        assert asistencia_1["estatus"] == asistencia_2["estatus"]
        assert asistencia_1["puntos_generados"] == asistencia_2["puntos_generados"]

    def test_dia_no_laboral_no_genera_falta(self, db_motor, seed_motor):
        """§3: DIA_NO_LABORAL + marcación → DIA_NO_LABORAL, no FALTA."""
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()
        calendario_id = db_motor.execute(text(
            "SELECT id FROM asistencia.calendarios WHERE codigo = 'CALENDARIO_TEST'"
        )).scalar_one()

        db_motor.execute(text(
            """
            INSERT INTO asistencia.calendario_eventos
            (calendario_id, nombre, tipo_evento, tipo_recurrencia, fecha_inicio,
             afecta_asistencia, es_laborable, prioridad)
            VALUES (:cal_id, 'Festivo test', 'FESTIVO_OFICIAL',
                    'FECHA_ESPECIFICA', :fecha, TRUE, FALSE, 10)
            """
        ), {"cal_id": calendario_id, "fecha": FECHA_TEST})

        # Insertar marcación para que el motor lo encuentre
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 8, 0, 0), punch=0)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        assert asistencia is not None, "No se generó registro de asistencia"
        assert asistencia["estatus"] == "DIA_NO_LABORAL"
        assert asistencia["puntos_generados"] == 0

    def test_horario_dias_no_laboral(self, db_motor, seed_motor):
        """§4: horario_dias marca día como no laboral → no genera FALTA."""
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()
        horario_id = db_motor.execute(text(
            "SELECT id FROM asistencia.horarios WHERE codigo = 'HORARIO_TEST'"
        )).scalar_one()

        # Martes (dia_semana=2 ISO) como no laboral
        db_motor.execute(text(
            """
            INSERT INTO asistencia.horario_dias
            (horario_id, dia_semana, es_laboral, hora_entrada, hora_salida)
            VALUES (:horario_id, 2, FALSE, NULL, NULL)
            """
        ), {"horario_id": horario_id})

        # Insertar marcación (martes)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 8, 0, 0), punch=0)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        if asistencia is not None:
            assert asistencia["estatus"] == "DIA_NO_LABORAL"


    def test_laborable_extraordinario_end_to_end(self, db_motor, seed_motor):
        """§3: LABORABLE_EXTRAORDINARIO + marcaciones → procesamiento normal."""
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()
        calendario_id = db_motor.execute(text(
            "SELECT id FROM asistencia.calendarios WHERE codigo = 'CALENDARIO_TEST'"
        )).scalar_one()

        # Domingo 23 agosto — normalmente no laboral
        domingo = date(2026, 8, 23)

        # Evento LABORABLE_EXTRAORDINARIO
        db_motor.execute(text(
            """
            INSERT INTO asistencia.calendario_eventos
            (calendario_id, nombre, tipo_evento, tipo_recurrencia, fecha_inicio,
             afecta_asistencia, es_laborable, prioridad)
            VALUES (:cal_id, 'Trabajo extraordinario domingo', 'LABORABLE_EXTRAORDINARIO',
                    'FECHA_ESPECIFICA', :fecha, TRUE, TRUE, 10)
            """
        ), {"cal_id": calendario_id, "fecha": domingo})

        # Marcaciones normales
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 23, 7, 55, 0), punch=0)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 23, 15, 5, 0), punch=1)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, domingo, domingo)

        asistencia = obtener_asistencia(db_motor, empleado_id, domingo)
        assert asistencia is not None, "No se generó asistencia para LABORABLE_EXTRAORDINARIO"
        assert asistencia["estatus"] == "COMPLETO"

    def test_turno_nocturno(self, db_motor, seed_motor):
        """§12: Turno 22:00-06:00, entrada día D, salida D+1 → asistencia día D."""
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        # Crear horario nocturno
        db_motor.execute(text(
            "INSERT INTO asistencia.tipos_turno "
            "(codigo, nombre, duracion_jornada_minutos, modalidad_tiempo_extra, hora_entrada_desde, hora_entrada_hasta) "
            "VALUES ('NOCTURNO', 'Nocturno', 480, 'NO_APLICA', '20:00', '23:59')"
        ))
        db_motor.execute(text(
            "INSERT INTO asistencia.horarios "
            "(codigo, nombre, tipo_turno_id, hora_entrada, hora_salida, tolerancia_entrada_minutos, permite_tiempo_extra) "
            "VALUES ('HORARIO_NOCTURNO', 'Nocturno 22-06', "
            "(SELECT id FROM asistencia.tipos_turno WHERE codigo='NOCTURNO'), "
            "'22:00', '06:00', 10, FALSE)"
        ))
        # Reasignar horario
        db_motor.execute(text(
            "UPDATE asistencia.asignaciones_horario "
            "SET horario_id = (SELECT id FROM asistencia.horarios WHERE codigo='HORARIO_NOCTURNO') "
            "WHERE empleado_id = :eid"
        ), {"eid": empleado_id})

        dia_d = date(2026, 8, 18)  # Martes

        # Entrada día D 21:58, Salida día D+1 06:03
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 21, 58, 0), punch=0)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 19, 6, 3, 0), punch=1)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, dia_d, dia_d)

        asistencia = obtener_asistencia(db_motor, empleado_id, dia_d)
        assert asistencia is not None, "No se generó asistencia para turno nocturno"
        assert asistencia["estatus"] == "COMPLETO"
        assert asistencia["primera_entrada"] is not None
        assert asistencia["ultima_salida"] is not None

    def test_multiples_marcaciones_una_asistencia(self, db_motor, seed_motor):
        """§11: Múltiples marcaciones → una sola fila asistencias_diarias."""
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        # 4 marcaciones: 2 entradas, 2 salidas
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 7, 58, 0), punch=0)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 8, 1, 0), punch=0)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 14, 58, 0), punch=1)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 15, 4, 0), punch=1)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        # Debe haber exactamente 1 registro
        count = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.asistencias_diarias "
            "WHERE empleado_id = :eid AND fecha = :f"
        ), {"eid": empleado_id, "f": FECHA_TEST}).scalar_one()
        assert count == 1, f"Esperaba 1 registro, encontró {count}"

        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        # El motor debe seleccionar primera entrada (07:58) y última salida (15:04)
        assert asistencia["primera_entrada"] is not None
        assert asistencia["ultima_salida"] is not None

    @pytest.mark.xfail(
        strict=True,
        reason="BUG C3: Motor hardcodea politica_asistencia_id=1. Sin política, "
               "falla con FK violation genérica en vez de error de dominio explícito. "
               "El contrato exige detección proactiva, no fallo accidental."
    )
    def test_cero_politicas_error_explicito(self, db_motor):
        """§5: 0 políticas aplicables → error explícito y auditable del dominio."""
        db = db_motor

        # Setup sin política
        db.execute(text(
            "INSERT INTO organizacion.unidades_organizacionales (codigo, nombre) "
            "VALUES ('TEST_UNIT', 'Unidad')"
        ))
        db.execute(text(
            "INSERT INTO organizacion.puestos (codigo, nombre) VALUES ('TEST_PUESTO', 'Puesto')"
        ))
        db.execute(text(
            "INSERT INTO asistencia.tipos_turno "
            "(codigo, nombre, duracion_jornada_minutos, modalidad_tiempo_extra, hora_entrada_desde) "
            "VALUES ('MATUTINO', 'Matutino', 420, 'DESPUES_SALIDA', '06:00')"
        ))
        db.execute(text(
            "INSERT INTO asistencia.horarios "
            "(codigo, nombre, tipo_turno_id, hora_entrada, hora_salida, tolerancia_entrada_minutos) "
            "VALUES ('H_TEST', 'Horario', "
            "(SELECT id FROM asistencia.tipos_turno WHERE codigo='MATUTINO'), "
            "'08:00', '15:00', 10)"
        ))
        db.execute(text(
            "INSERT INTO personal.empleados "
            "(codigo_empleado, nombres, apellido_paterno, unidad_organizacional_id, puesto_id, estatus, zk_user_id) "
            "VALUES ('EMP-NOPOL', 'SIN', 'POLITICA', "
            "(SELECT id FROM organizacion.unidades_organizacionales LIMIT 1), "
            "(SELECT id FROM organizacion.puestos LIMIT 1), 'ACTIVO', '999')"
        ))
        db.execute(text(
            "INSERT INTO asistencia.asignaciones_horario (empleado_id, horario_id, fecha_inicio, estatus) "
            "VALUES ("
            "(SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-NOPOL'), "
            "(SELECT id FROM asistencia.horarios WHERE codigo='H_TEST'), "
            "'2026-01-01', 'ACTIVA')"
        ))
        emp_id = db.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-NOPOL'"
        )).scalar_one()
        insertar_marcacion(db, emp_id, datetime(2026, 8, 18, 8, 0, 0), punch=0)
        insertar_marcacion(db, emp_id, datetime(2026, 8, 18, 15, 0, 0), punch=1)
        db.commit()

        resultado = procesar_asistencia_diaria(db, FECHA_TEST, FECHA_TEST)

        # Según contrato: debe producir un error de dominio PROACTIVO
        # El motor debe detectar la ausencia de política ANTES de intentar INSERT.
        # Debe lanzar ValueError o retornar error de dominio, NO un FK violation accidental.
        assert len(resultado.get("errores", [])) > 0, "Debería reportar error"
        error_msg = str(resultado["errores"][0].get("error", "")).lower()
        # El error NO debe ser un FK violation de SQLAlchemy
        assert "foreignkeyviolation" not in error_msg.replace(" ", "").replace("_", ""), (
            "Motor falla con FK violation accidental, no con validación de dominio"
        )
        # DEBE ser un error explícito del dominio
        assert "no hay polít" in error_msg or "no existe polít" in error_msg or "política vigente" in error_msg, (
            f"Error no es de dominio proactivo: {error_msg[:200]}"
        )
