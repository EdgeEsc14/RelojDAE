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
        assert asistencia["requiere_revision"] is True
        assert resultado["errores"] == []

    def test_ausencia_total_dia_no_laboral_no_genera_falta(self, db_motor, seed_motor):
        """
        §3 + §6 Contrato: empleado activo + horario + DIA_NO_LABORAL + 0 marcaciones
        → DIA_NO_LABORAL, nunca FALTA. El motor debe resolver el calendario
        antes de generar la ausencia total.
        """
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
            VALUES (:cal_id, 'Festivo sin marcaciones', 'FESTIVO_OFICIAL',
                    'FECHA_ESPECIFICA', :fecha, TRUE, FALSE, 10)
            """
        ), {"cal_id": calendario_id, "fecha": FECHA_TEST})
        db_motor.commit()

        marc_count = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.marcaciones_crudas WHERE empleado_id = :eid AND fecha = :f"
        ), {"eid": empleado_id, "f": FECHA_TEST}).scalar_one()
        assert marc_count == 0, "No debería haber marcaciones"

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        assert asistencia is not None, (
            f"No se generó registro de asistencia. Resultado motor: {resultado}"
        )
        assert asistencia["estatus"] == "DIA_NO_LABORAL"
        assert asistencia["puntos_generados"] == 0
        assert asistencia["requiere_revision"] is False
        assert resultado["errores"] == []

    def test_idempotencia_ausencia_total_falta(self, db_motor, seed_motor):
        """§13: Reprocesar (empleado, fecha) con 0 marcaciones + día laboral produce el mismo resultado."""
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        asistencia_1 = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        asistencia_2 = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)

        assert asistencia_1 is not None
        assert asistencia_2 is not None
        assert asistencia_1["estatus"] == "FALTA"
        assert asistencia_2["estatus"] == "FALTA"
        assert asistencia_1["puntos_generados"] == asistencia_2["puntos_generados"]

        count = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.asistencias_diarias "
            "WHERE empleado_id = :eid AND fecha = :f"
        ), {"eid": empleado_id, "f": FECHA_TEST}).scalar_one()
        assert count == 1, f"Esperaba 1 registro, encontró {count}"

    def test_idempotencia_ausencia_total_dia_no_laboral(self, db_motor, seed_motor):
        """§13: Reprocesar (empleado, fecha) con 0 marcaciones + DIA_NO_LABORAL produce el mismo resultado."""
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
            VALUES (:cal_id, 'Festivo idempotencia', 'FESTIVO_OFICIAL',
                    'FECHA_ESPECIFICA', :fecha, TRUE, FALSE, 10)
            """
        ), {"cal_id": calendario_id, "fecha": FECHA_TEST})
        db_motor.commit()

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        asistencia_1 = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        asistencia_2 = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)

        assert asistencia_1 is not None
        assert asistencia_2 is not None
        assert asistencia_1["estatus"] == "DIA_NO_LABORAL"
        assert asistencia_2["estatus"] == "DIA_NO_LABORAL"

        count = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.asistencias_diarias "
            "WHERE empleado_id = :eid AND fecha = :f"
        ), {"eid": empleado_id, "f": FECHA_TEST}).scalar_one()
        assert count == 1, f"Esperaba 1 registro, encontró {count}"

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

    def test_omision_entrada_end_to_end(self, db_motor, seed_motor):
        """
        §7 Contrato: existe salida pero no entrada → OMISION_ENTRADA,
        requiere_revision = TRUE. Debe seguir siendo FALTA cuando no hay
        ninguna marcación (ver test_ausencia_total_genera_falta).
        """
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 15, 5, 0), punch=1)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        assert asistencia is not None, (
            f"No se generó registro de asistencia. Resultado motor: {resultado}"
        )
        assert asistencia["estatus"] == "OMISION_ENTRADA"
        assert asistencia["requiere_revision"] is True
        assert asistencia["puntos_generados"] == 0
        assert resultado["errores"] == []

    def test_idempotencia_omision_entrada(self, db_motor, seed_motor):
        """§13: Reprocesar (empleado, fecha) con salida sin entrada produce el mismo resultado."""
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 15, 5, 0), punch=1)
        db_motor.commit()

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        asistencia_1 = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)

        procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        asistencia_2 = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)

        assert asistencia_1["estatus"] == "OMISION_ENTRADA"
        assert asistencia_2["estatus"] == "OMISION_ENTRADA"

        count = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.asistencias_diarias "
            "WHERE empleado_id = :eid AND fecha = :f"
        ), {"eid": empleado_id, "f": FECHA_TEST}).scalar_one()
        assert count == 1, f"Esperaba 1 registro, encontró {count}"

    def test_ausencia_total_hoy_jornada_abierta_no_genera_falta(self, db_motor, seed_motor):
        """
        §15 Contrato: hoy, sin marcaciones, con la jornada todavía abierta
        (salida_programada aún no llega) → no se genera FALTA (ni ningún
        registro definitivo).
        """
        empleado_id = get_empleado_id(db_motor)
        hoy = date.today()

        db_motor.execute(text(
            "UPDATE asistencia.horarios SET hora_entrada = '00:00', hora_salida = '23:59' "
            "WHERE codigo = 'HORARIO_TEST'"
        ))
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, hoy, hoy)

        asistencia = obtener_asistencia(db_motor, empleado_id, hoy)
        assert asistencia is None, (
            f"No debería generarse registro con la jornada abierta. Encontrado: {asistencia}"
        )
        assert resultado["errores"] == []

    def test_ausencia_total_hoy_jornada_cerrada_genera_falta(self, db_motor, seed_motor):
        """
        §15 Contrato: hoy, sin marcaciones, con la jornada YA cerrada
        (salida_programada ya pasó) → sí se genera FALTA definitiva.
        """
        empleado_id = get_empleado_id(db_motor)
        hoy = date.today()

        db_motor.execute(text(
            "UPDATE asistencia.horarios SET hora_entrada = '00:00', hora_salida = '00:01' "
            "WHERE codigo = 'HORARIO_TEST'"
        ))
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, hoy, hoy)

        asistencia = obtener_asistencia(db_motor, empleado_id, hoy)
        assert asistencia is not None, (
            f"No se generó registro de asistencia. Resultado motor: {resultado}"
        )
        assert asistencia["estatus"] == "FALTA"
        assert asistencia["requiere_revision"] is True

    def test_entrada_sin_salida_hoy_jornada_abierta_no_genera_omision(self, db_motor, seed_motor):
        """
        §15 Contrato: hoy, con entrada marcada pero sin salida, jornada
        todavía abierta → no se genera OMISION_SALIDA (estatus provisional
        de entrada, requiere_revision = FALSE).
        """
        empleado_id = get_empleado_id(db_motor)
        hoy = date.today()

        db_motor.execute(text(
            "UPDATE asistencia.horarios SET hora_entrada = '00:00', hora_salida = '23:59' "
            "WHERE codigo = 'HORARIO_TEST'"
        ))
        db_motor.commit()

        insertar_marcacion(db_motor, empleado_id, datetime.combine(hoy, time(0, 0, 5)), punch=0)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, hoy, hoy)

        asistencia = obtener_asistencia(db_motor, empleado_id, hoy)
        assert asistencia is not None, (
            f"No se generó registro de asistencia. Resultado motor: {resultado}"
        )
        assert asistencia["estatus"] != "OMISION_SALIDA"
        assert asistencia["requiere_revision"] is False

    def test_entrada_sin_salida_hoy_jornada_cerrada_genera_omision_salida(self, db_motor, seed_motor):
        """
        §15 Contrato: hoy, con entrada marcada pero sin salida, jornada YA
        cerrada → sí se genera OMISION_SALIDA definitiva.
        """
        empleado_id = get_empleado_id(db_motor)
        hoy = date.today()

        db_motor.execute(text(
            "UPDATE asistencia.horarios SET hora_entrada = '00:00', hora_salida = '00:01' "
            "WHERE codigo = 'HORARIO_TEST'"
        ))
        db_motor.commit()

        insertar_marcacion(db_motor, empleado_id, datetime.combine(hoy, time(0, 0, 0)), punch=0)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, hoy, hoy)

        asistencia = obtener_asistencia(db_motor, empleado_id, hoy)
        assert asistencia is not None, (
            f"No se generó registro de asistencia. Resultado motor: {resultado}"
        )
        assert asistencia["estatus"] == "OMISION_SALIDA"
        assert asistencia["requiere_revision"] is True

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

    def test_empleado_sin_marcaciones_entra_al_universo(self, db_motor, seed_motor):
        """
        §2 Contrato: el universo de procesamiento parte de empleados activos +
        asignación de horario vigente + fecha, NO de marcaciones_crudas.
        Un empleado con cero marcaciones debe entrar al universo junto con
        uno que sí tiene marcaciones, en la misma corrida.
        """
        empleado_con_marcaciones = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()
        horario_id = db_motor.execute(text(
            "SELECT id FROM asistencia.horarios WHERE codigo = 'HORARIO_TEST'"
        )).scalar_one()

        # Segundo empleado, mismo horario, sin marcaciones
        db_motor.execute(text(
            "INSERT INTO personal.empleados "
            "(codigo_empleado, nombres, apellido_paterno, "
            "unidad_organizacional_id, puesto_id, estatus, zk_user_id) "
            "VALUES ('EMP-TEST-002', 'MARIA', 'LOPEZ', "
            "(SELECT id FROM organizacion.unidades_organizacionales WHERE codigo='TEST_UNIT'), "
            "(SELECT id FROM organizacion.puestos WHERE codigo='TEST_PUESTO'), "
            "'ACTIVO', '101')"
        ))
        db_motor.execute(text(
            "INSERT INTO asistencia.asignaciones_horario "
            "(empleado_id, horario_id, fecha_inicio, estatus) "
            "VALUES ("
            "(SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-002'), "
            ":horario_id, '2026-01-01', 'ACTIVA')"
        ), {"horario_id": horario_id})

        empleado_sin_marcaciones = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-002'"
        )).scalar_one()

        # Marcaciones solo para el primer empleado
        insertar_marcacion(db_motor, empleado_con_marcaciones, datetime(2026, 8, 18, 7, 55, 0), punch=0)
        insertar_marcacion(db_motor, empleado_con_marcaciones, datetime(2026, 8, 18, 15, 5, 0), punch=1)
        db_motor.commit()

        marc_count_sin = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.marcaciones_crudas WHERE empleado_id = :eid"
        ), {"eid": empleado_sin_marcaciones}).scalar_one()
        assert marc_count_sin == 0, "No debería haber marcaciones para EMP-TEST-002"

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        # Ambos empleados deben estar en el universo procesado en la misma corrida
        assert resultado["registros_encontrados"] >= 2, (
            f"El universo debe incluir empleados sin marcaciones. Resultado: {resultado}"
        )

        asistencia_con = obtener_asistencia(db_motor, empleado_con_marcaciones, FECHA_TEST)
        asistencia_sin = obtener_asistencia(db_motor, empleado_sin_marcaciones, FECHA_TEST)

        assert asistencia_con is not None
        assert asistencia_con["estatus"] == "COMPLETO"

        assert asistencia_sin is not None, (
            f"El empleado sin marcaciones debe generar registro de asistencia. Resultado: {resultado}"
        )
        assert asistencia_sin["primera_entrada"] is None
        assert asistencia_sin["ultima_salida"] is None
        assert asistencia_sin["estatus"] == "FALTA"

    def test_asignaciones_vigentes_duplicadas_reporta_error(self, db_motor, seed_motor):
        """
        Universo: como máximo una fila lógica por (empleado, fecha). Si existen
        dos asignaciones_horario ACTIVA vigentes simultáneamente para el mismo
        empleado y fecha, el motor NO debe elegir una automáticamente: debe
        reportar el conflicto en errores y no generar una asistencia_diaria
        ambigua para ese (empleado, fecha).
        """
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()
        horario_id = db_motor.execute(text(
            "SELECT id FROM asistencia.horarios WHERE codigo = 'HORARIO_TEST'"
        )).scalar_one()

        # seed_motor ya crea una asignación ACTIVA abierta (fecha_inicio='2026-01-01',
        # fecha_fin=NULL). Agregamos una segunda ACTIVA con rango cerrado que
        # también cubre FECHA_TEST — el índice único parcial solo prohíbe dos
        # filas con fecha_fin IS NULL, así que esta duplicidad SÍ es posible
        # a nivel de esquema.
        db_motor.execute(text(
            "INSERT INTO asistencia.asignaciones_horario "
            "(empleado_id, horario_id, fecha_inicio, fecha_fin, estatus) "
            "VALUES (:eid, :hid, '2026-08-01', '2026-08-31', 'ACTIVA')"
        ), {"eid": empleado_id, "hid": horario_id})
        db_motor.commit()

        vigentes = db_motor.execute(text(
            """
            SELECT COUNT(*) FROM asistencia.asignaciones_horario
            WHERE empleado_id = :eid
              AND estatus = 'ACTIVA'
              AND fecha_inicio <= :fecha
              AND (fecha_fin IS NULL OR fecha_fin >= :fecha)
            """
        ), {"eid": empleado_id, "fecha": FECHA_TEST}).scalar_one()
        assert vigentes == 2, (
            "Setup inválido: se esperaban 2 asignaciones ACTIVA vigentes solapadas"
        )

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        # No debe elegir una asignación silenciosamente: no debe existir
        # asistencia_diaria ambigua para ese empleado/fecha.
        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        assert asistencia is None, (
            f"El motor no debe generar una asistencia ambigua ante asignaciones "
            f"duplicadas. Resultado: {resultado}"
        )

        # Debe reportar el conflicto explícitamente en errores.
        assert len(resultado["errores"]) >= 1, (
            f"Debe reportar el conflicto de asignaciones duplicadas. Resultado: {resultado}"
        )
        error = resultado["errores"][0]
        assert error["empleado_id"] == empleado_id
        assert error["fecha"] == str(FECHA_TEST)
        error_msg = str(error["error"]).lower()
        assert "asignaci" in error_msg or "solapad" in error_msg, (
            f"El error debe indicar el conflicto de asignaciones: {error_msg}"
        )

    def test_politica_valida_puntos_desde_politica(self, db_motor, seed_motor):
        """
        §5/§6 Contrato: con una única política vigente, los puntos generados
        deben provenir de sus columnas (puntos_retardo_menor/mayor), NO de
        constantes hardcodeadas 1/2.
        """
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        # Política custom: puntos muy distintos de los hardcodes históricos (1/2).
        db_motor.execute(text(
            "UPDATE asistencia.politicas_asistencia "
            "SET puntos_retardo_menor = 7, puntos_retardo_mayor = 13 "
            "WHERE codigo = 'POLITICA_DAE_GENERAL'"
        ))
        db_motor.commit()

        # Entrada 08:15:00 → 900s de retardo: > tolerancia(659), <= retardo_menor(1259)
        # → RETARDO_MENOR con los puntos custom de la política (7, no 1).
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 8, 15, 0), punch=0)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 15, 0, 0), punch=1)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        assert asistencia is not None, f"Resultado: {resultado}"
        assert asistencia["estatus"] == "RETARDO_MENOR"
        assert asistencia["puntos_generados"] == 7, (
            "Los puntos deben salir de la política (7), no del hardcode histórico (1)."
        )

    def test_tolerancia_end_to_end(self, db_motor, seed_motor):
        """
        §5 Contrato: entrada dentro de limite_tolerancia_segundos debe
        clasificarse como TOLERANCIA (0 puntos), no COMPLETO ni RETARDO_MENOR.
        """
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        # Entrada 08:05:00 → 300s de retardo, dentro de limite_tolerancia_segundos (659).
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 8, 5, 0), punch=0)
        insertar_marcacion(db_motor, empleado_id, datetime(2026, 8, 18, 15, 0, 0), punch=1)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        assert asistencia is not None, f"Resultado: {resultado}"
        assert asistencia["estatus"] == "TOLERANCIA"
        assert asistencia["puntos_generados"] == 0
        assert asistencia["requiere_revision"] is False

    def test_multiples_politicas_vigentes_reporta_error(self, db_motor, seed_motor):
        """
        §5 Contrato: si hay más de una política ACTIVA vigente para la misma
        fecha (rangos de vigencia solapados), el motor NO debe elegir una
        automáticamente: debe reportar el conflicto en errores y no generar
        una asistencia_diaria ambigua para ese (empleado, fecha).
        """
        empleado_id = db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado='EMP-TEST-001'"
        )).scalar_one()

        # seed_motor ya crea POLITICA_DAE_GENERAL (activa, vigencia_desde=2026-01-01,
        # vigencia_hasta=NULL). Agregamos una segunda política ACTIVA cuya vigencia
        # también cubre FECHA_TEST.
        db_motor.execute(text(
            "INSERT INTO asistencia.politicas_asistencia "
            "(codigo, version, nombre, tipo_periodo, "
            "limite_tolerancia_segundos, limite_retardo_menor_segundos, limite_retardo_mayor_segundos, "
            "puntos_retardo_menor, puntos_retardo_mayor, puntos_para_descanso, "
            "max_dias_justificables_periodo, max_puntos_descontables_por_dia, "
            "descansos_para_revision_baja, faltas_consecutivas_revision_baja, "
            "vigencia_desde, vigencia_hasta, activo) "
            "VALUES ('POLITICA_DAE_ALTERNA', 1, 'Política alterna DAE', 'QUINCENAL', "
            "659, 1259, 1859, 1, 2, 10, 2, 2, 7, 3, '2026-08-01', '2026-08-31', TRUE)"
        ))
        db_motor.commit()

        vigentes = db_motor.execute(text(
            """
            SELECT COUNT(*) FROM asistencia.politicas_asistencia
            WHERE activo = TRUE
              AND vigencia_desde <= :fecha
              AND (vigencia_hasta IS NULL OR vigencia_hasta >= :fecha)
            """
        ), {"fecha": FECHA_TEST}).scalar_one()
        assert vigentes == 2, (
            "Setup inválido: se esperaban 2 políticas ACTIVA vigentes solapadas"
        )

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        # No debe elegir una política silenciosamente: no debe existir
        # asistencia_diaria ambigua para ese empleado/fecha.
        asistencia = obtener_asistencia(db_motor, empleado_id, FECHA_TEST)
        assert asistencia is None, (
            f"El motor no debe generar una asistencia ambigua ante políticas "
            f"duplicadas. Resultado: {resultado}"
        )

        assert len(resultado["errores"]) >= 1, (
            f"Debe reportar el conflicto de políticas duplicadas. Resultado: {resultado}"
        )
        error = resultado["errores"][0]
        assert error["empleado_id"] == empleado_id
        assert error["fecha"] == str(FECHA_TEST)
        error_msg = str(error["error"]).lower()
        assert "polít" in error_msg or "politic" in error_msg, (
            f"El error debe indicar el conflicto de políticas: {error_msg}"
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


# ============================================================
# ATOMICIDAD POR FECHA (Contrato §14)
# ============================================================


@pytest.mark.integration
class TestAtomicidadPorFecha:
    """
    La unidad transaccional de procesar_asistencia_diaria() es la FECHA
    completa: cada fecha se confirma o se revierte de forma independiente.

    Los fallos TÉCNICOS se simulan haciendo que resolver_fecha_laborable
    (importado dentro del módulo del motor) lance una excepción real para
    un empleado/fecha puntual, mediante monkeypatch. Es el equivalente
    controlado y determinista a un fallo de infraestructura (timeout,
    conexión perdida) sin depender de qué CHECK constraints existan en el
    esquema de la BD de test — y sin tocar el esquema real.
    """

    def _crear_empleado(self, db_motor, codigo, zk_user_id):
        db_motor.execute(text(
            "INSERT INTO personal.empleados "
            "(codigo_empleado, nombres, apellido_paterno, "
            "unidad_organizacional_id, puesto_id, estatus, zk_user_id) "
            "VALUES (:codigo, 'TEST', 'ATOMICIDAD', "
            "(SELECT id FROM organizacion.unidades_organizacionales WHERE codigo='TEST_UNIT'), "
            "(SELECT id FROM organizacion.puestos WHERE codigo='TEST_PUESTO'), "
            "'ACTIVO', :zk_user_id)"
        ), {"codigo": codigo, "zk_user_id": zk_user_id})
        return db_motor.execute(text(
            "SELECT id FROM personal.empleados WHERE codigo_empleado = :codigo"
        ), {"codigo": codigo}).scalar_one()

    def _asignar_horario_test(self, db_motor, empleado_id, fecha_inicio="2026-01-01"):
        horario_id = db_motor.execute(text(
            "SELECT id FROM asistencia.horarios WHERE codigo = 'HORARIO_TEST'"
        )).scalar_one()
        db_motor.execute(text(
            "INSERT INTO asistencia.asignaciones_horario "
            "(empleado_id, horario_id, fecha_inicio, estatus) "
            "VALUES (:eid, :hid, :finicio, 'ACTIVA')"
        ), {"eid": empleado_id, "hid": horario_id, "finicio": fecha_inicio})

    def _parchear_fallo_tecnico(self, monkeypatch, condicion):
        """
        Reemplaza resolver_fecha_laborable dentro del módulo del motor por
        una versión que lanza RuntimeError cuando `condicion(fecha,
        empleado_id)` es verdadera, y delega en la función real en caso
        contrario.
        """
        def resolver_con_fallo(db, fecha, empleado_id):
            if condicion(fecha, empleado_id):
                raise RuntimeError("Fallo técnico simulado (conexión perdida)")
            return resolver_fecha_laborable(db, fecha, empleado_id)

        monkeypatch.setattr(
            "app.repositories.asistencia_procesamiento_repo.resolver_fecha_laborable",
            resolver_con_fallo,
        )

    def test_fallo_tecnico_revierte_fecha_completa(self, db_motor, seed_motor, monkeypatch):
        """
        1. Un fallo técnico en un empleado a mitad de una fecha revierte
        TODA la fecha: incluye al empleado que ya se había procesado
        correctamente antes del fallo (EMP-TEST-001, vía seed_motor).
        """
        empleado_ok = get_empleado_id(db_motor)  # EMP-TEST-001, HORARIO_TEST normal
        insertar_marcacion(db_motor, empleado_ok, datetime(2026, 8, 18, 7, 55, 0), punch=0)
        insertar_marcacion(db_motor, empleado_ok, datetime(2026, 8, 18, 15, 5, 0), punch=1)

        empleado_roto = self._crear_empleado(db_motor, "EMP-TEST-ROTO", "201")
        self._asignar_horario_test(db_motor, empleado_roto)
        db_motor.commit()

        # empleado_ok tiene id menor (creado por seed_motor primero) y se
        # procesa antes que empleado_roto según ORDER BY u.fecha, u.empleado_id.
        assert empleado_ok < empleado_roto

        self._parchear_fallo_tecnico(
            monkeypatch,
            condicion=lambda fecha, empleado_id: empleado_id == empleado_roto,
        )

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        assert obtener_asistencia(db_motor, empleado_ok, FECHA_TEST) is None, (
            "El empleado sano no debe quedar persistido: la fecha completa "
            "debe revertirse por el fallo técnico del otro empleado."
        )
        assert obtener_asistencia(db_motor, empleado_roto, FECHA_TEST) is None

        count = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.asistencias_diarias WHERE fecha = :f"
        ), {"f": FECHA_TEST}).scalar_one()
        assert count == 0, "No debe quedar ningún registro parcial de la fecha fallida"

        assert resultado["procesadas"] == 0
        assert len(resultado["errores"]) == 1
        error = resultado["errores"][0]
        assert error["fecha"] == str(FECHA_TEST)
        assert "técnic" in error["error"].lower()

    def test_error_dominio_no_bloquea_otros_empleados_de_la_fecha(self, db_motor, seed_motor):
        """
        2. Un error de DOMINIO (asignaciones ACTIVA solapadas) en un
        empleado no debe impedir procesar a los demás empleados de la
        misma fecha.
        """
        empleado_dominio = get_empleado_id(db_motor)  # EMP-TEST-001
        horario_id = db_motor.execute(text(
            "SELECT id FROM asistencia.horarios WHERE codigo = 'HORARIO_TEST'"
        )).scalar_one()
        # Segunda asignación ACTIVA solapada para EMP-TEST-001 → dominio ambiguo
        db_motor.execute(text(
            "INSERT INTO asistencia.asignaciones_horario "
            "(empleado_id, horario_id, fecha_inicio, fecha_fin, estatus) "
            "VALUES (:eid, :hid, '2026-08-01', '2026-08-31', 'ACTIVA')"
        ), {"eid": empleado_dominio, "hid": horario_id})

        empleado_ok = self._crear_empleado(db_motor, "EMP-TEST-OK2", "202")
        self._asignar_horario_test(db_motor, empleado_ok)
        insertar_marcacion(db_motor, empleado_ok, datetime(2026, 8, 18, 7, 55, 0), punch=0)
        insertar_marcacion(db_motor, empleado_ok, datetime(2026, 8, 18, 15, 5, 0), punch=1)
        db_motor.commit()

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)

        errores_dominio = [
            e for e in resultado["errores"]
            if e["empleado_id"] == empleado_dominio
        ]
        assert len(errores_dominio) == 1
        assert "asignaciones_horario" in errores_dominio[0]["error"] or \
            "solapadas" in errores_dominio[0]["error"]
        assert obtener_asistencia(db_motor, empleado_dominio, FECHA_TEST) is None

        asistencia_ok = obtener_asistencia(db_motor, empleado_ok, FECHA_TEST)
        assert asistencia_ok is not None, (
            "El empleado sin conflicto debe procesarse aunque otro empleado "
            "de la misma fecha tenga un error de dominio."
        )
        assert asistencia_ok["estatus"] == "COMPLETO"

    def test_rango_dos_fechas_fallo_tecnico_una_no_afecta_la_otra(self, db_motor, seed_motor, monkeypatch):
        """
        3. En un rango de dos fechas, un fallo técnico en una fecha no
        debe impedir que la otra fecha quede correctamente procesada.
        """
        fecha_siguiente = FECHA_TEST + timedelta(days=1)

        empleado = self._crear_empleado(db_motor, "EMP-TEST-ROTO2", "203")
        self._asignar_horario_test(db_motor, empleado)
        db_motor.commit()

        self._parchear_fallo_tecnico(
            monkeypatch,
            condicion=lambda fecha, empleado_id: fecha == FECHA_TEST,
        )

        resultado = procesar_asistencia_diaria(db_motor, FECHA_TEST, fecha_siguiente)

        assert obtener_asistencia(db_motor, empleado, FECHA_TEST) is None
        errores_fecha_rota = [e for e in resultado["errores"] if e["fecha"] == str(FECHA_TEST)]
        assert len(errores_fecha_rota) == 1
        assert "técnic" in errores_fecha_rota[0]["error"].lower()

        asistencia_siguiente = obtener_asistencia(db_motor, empleado, fecha_siguiente)
        assert asistencia_siguiente is not None, (
            "La segunda fecha del rango debe procesarse aunque la primera "
            "haya fallado técnicamente."
        )
        assert asistencia_siguiente["estatus"] == "FALTA"
        assert asistencia_siguiente["requiere_revision"] is True

    def test_reintento_despues_de_rollback_es_idempotente(self, db_motor, seed_motor, monkeypatch):
        """
        4. Tras un fallo técnico (rollback de la fecha), corregir la causa
        (aquí: que ya no falle resolver_fecha_laborable) y reprocesar debe
        producir el resultado correcto, sin duplicar filas (idempotencia,
        Contrato §13).
        """
        empleado_ok = get_empleado_id(db_motor)
        insertar_marcacion(db_motor, empleado_ok, datetime(2026, 8, 18, 7, 55, 0), punch=0)
        insertar_marcacion(db_motor, empleado_ok, datetime(2026, 8, 18, 15, 5, 0), punch=1)

        empleado_roto = self._crear_empleado(db_motor, "EMP-TEST-ROTO3", "204")
        self._asignar_horario_test(db_motor, empleado_roto)
        db_motor.commit()

        self._parchear_fallo_tecnico(
            monkeypatch,
            condicion=lambda fecha, empleado_id: empleado_id == empleado_roto,
        )

        resultado_1 = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        assert len(resultado_1["errores"]) == 1
        assert obtener_asistencia(db_motor, empleado_ok, FECHA_TEST) is None
        assert obtener_asistencia(db_motor, empleado_roto, FECHA_TEST) is None

        # "Corregir" la causa del fallo técnico y reprocesar.
        monkeypatch.undo()

        resultado_2 = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        assert resultado_2["errores"] == []

        asistencia_ok = obtener_asistencia(db_motor, empleado_ok, FECHA_TEST)
        asistencia_roto = obtener_asistencia(db_motor, empleado_roto, FECHA_TEST)
        assert asistencia_ok is not None
        assert asistencia_ok["estatus"] == "COMPLETO"
        assert asistencia_roto is not None
        assert asistencia_roto["estatus"] == "FALTA"

        count_ok = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.asistencias_diarias "
            "WHERE empleado_id = :eid AND fecha = :f"
        ), {"eid": empleado_ok, "f": FECHA_TEST}).scalar_one()
        count_roto = db_motor.execute(text(
            "SELECT COUNT(*) FROM asistencia.asistencias_diarias "
            "WHERE empleado_id = :eid AND fecha = :f"
        ), {"eid": empleado_roto, "f": FECHA_TEST}).scalar_one()
        assert count_ok == 1
        assert count_roto == 1

        # Reprocesar de nuevo debe seguir siendo idempotente.
        resultado_3 = procesar_asistencia_diaria(db_motor, FECHA_TEST, FECHA_TEST)
        assert resultado_3["errores"] == []
        asistencia_ok_2 = obtener_asistencia(db_motor, empleado_ok, FECHA_TEST)
        asistencia_roto_2 = obtener_asistencia(db_motor, empleado_roto, FECHA_TEST)
        assert asistencia_ok_2["estatus"] == asistencia_ok["estatus"]
        assert asistencia_roto_2["estatus"] == asistencia_roto["estatus"]
