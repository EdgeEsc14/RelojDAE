"""
CHARACTERIZATION TESTS — Comportamiento actual del motor.

Estos tests documentan qué hace el motor HOY.
Su propósito es detectar cambios accidentales durante el refactor.
Si un test aquí falla después de un cambio, significa que el refactor
alteró el comportamiento existente (intencionalmente o no).

NO representan el comportamiento correcto según el contrato.
"""

import pytest
from datetime import date, datetime, time, timedelta

from app.repositories.asistencia_procesamiento_repo import (
    _calcular_estatus_y_puntos,
    _calcular_minutos_retardo,
    _calcular_salida_programada,
    _combinar_fecha_hora,
)


FECHA = date(2026, 8, 18)
ENTRADA_08 = datetime(2026, 8, 18, 8, 0, 0)


# ============================================================
# Characterization: _calcular_minutos_retardo
# ============================================================


class TestCharRetardo:
    """Documenta cómo se calcula el retardo actualmente (truncado a minutos)."""

    @pytest.mark.unit
    def test_llegada_antes_retorno_cero(self):
        r = _calcular_minutos_retardo(ENTRADA_08, ENTRADA_08 - timedelta(minutes=5))
        assert r == 0

    @pytest.mark.unit
    def test_llegada_exacta_retorno_cero(self):
        r = _calcular_minutos_retardo(ENTRADA_08, ENTRADA_08)
        assert r == 0

    @pytest.mark.unit
    def test_llegada_5min_retorno_5(self):
        r = _calcular_minutos_retardo(ENTRADA_08, ENTRADA_08 + timedelta(minutes=5))
        assert r == 5

    @pytest.mark.unit
    def test_llegada_10min59seg_trunca_a_10(self):
        """Motor actual trunca segundos: 659 seg // 60 = 10."""
        r = _calcular_minutos_retardo(ENTRADA_08, ENTRADA_08 + timedelta(seconds=659))
        assert r == 10

    @pytest.mark.unit
    def test_llegada_11min00seg_es_11(self):
        r = _calcular_minutos_retardo(ENTRADA_08, ENTRADA_08 + timedelta(minutes=11))
        assert r == 11

    @pytest.mark.unit
    def test_llegada_sin_entrada_retorno_cero(self):
        r = _calcular_minutos_retardo(ENTRADA_08, None)
        assert r == 0


# ============================================================
# Characterization: _calcular_estatus_y_puntos (hardcoded 10/20/30)
# ============================================================


class TestCharEstatus:
    """
    Documenta la clasificación actual con límites hardcodeados.
    Motor actual: <=10 COMPLETO, <=20 RETARDO_MENOR, <=30 RETARDO_MAYOR, >30 FALTA.
    """

    @pytest.mark.unit
    def test_0min_completo(self):
        r = _calcular_estatus_y_puntos(0, True, True)
        assert r[0] == "COMPLETO"
        assert r[1] == 0

    @pytest.mark.unit
    def test_10min_completo(self):
        r = _calcular_estatus_y_puntos(10, True, True)
        assert r[0] == "COMPLETO"
        assert r[1] == 0

    @pytest.mark.unit
    def test_11min_retardo_menor(self):
        r = _calcular_estatus_y_puntos(11, True, True)
        assert r[0] == "RETARDO_MENOR"
        assert r[1] == 1

    @pytest.mark.unit
    def test_20min_retardo_menor(self):
        r = _calcular_estatus_y_puntos(20, True, True)
        assert r[0] == "RETARDO_MENOR"
        assert r[1] == 1

    @pytest.mark.unit
    def test_21min_retardo_mayor(self):
        r = _calcular_estatus_y_puntos(21, True, True)
        assert r[0] == "RETARDO_MAYOR"
        assert r[1] == 2

    @pytest.mark.unit
    def test_30min_retardo_mayor(self):
        r = _calcular_estatus_y_puntos(30, True, True)
        assert r[0] == "RETARDO_MAYOR"
        assert r[1] == 2

    @pytest.mark.unit
    def test_31min_falta(self):
        r = _calcular_estatus_y_puntos(31, True, True)
        assert r[0] == "FALTA"
        assert r[1] == 0

    @pytest.mark.unit
    def test_sin_entrada_dia_pasado_falta(self):
        fecha_pasada = date(2026, 8, 10)
        salida_prog = datetime(2026, 8, 10, 15, 0)
        r = _calcular_estatus_y_puntos(0, False, False, fecha=fecha_pasada, salida_programada=salida_prog)
        assert r is not None
        assert r[0] == "FALTA"
        assert r[2] is True  # requiere_revision

    @pytest.mark.unit
    def test_con_entrada_sin_salida_dia_pasado_omision(self):
        fecha_pasada = date(2026, 8, 10)
        salida_prog = datetime(2026, 8, 10, 15, 0)
        r = _calcular_estatus_y_puntos(5, True, False, fecha=fecha_pasada, salida_programada=salida_prog)
        assert r is not None
        assert r[0] == "OMISION_SALIDA"
        assert r[2] is True

    @pytest.mark.unit
    def test_determinista(self):
        """Mismos params → mismo resultado."""
        r1 = _calcular_estatus_y_puntos(15, True, True)
        r2 = _calcular_estatus_y_puntos(15, True, True)
        assert r1 == r2


# ============================================================
# Characterization: _calcular_salida_programada
# ============================================================


class TestCharSalidaProgramada:
    """Documenta el cálculo de salida para turnos normales y nocturnos."""

    @pytest.mark.unit
    def test_turno_normal(self):
        r = _calcular_salida_programada(FECHA, time(8, 0), time(15, 0))
        assert r == datetime(2026, 8, 18, 15, 0)

    @pytest.mark.unit
    def test_turno_nocturno_cruza_medianoche(self):
        r = _calcular_salida_programada(FECHA, time(22, 0), time(6, 0))
        assert r == datetime(2026, 8, 19, 6, 0)


# ============================================================
# Characterization: Jornada en curso
# ============================================================


class TestCharJornadaEnCurso:
    """Documenta el comportamiento actual para jornadas abiertas."""

    @pytest.mark.unit
    def test_sin_entrada_hoy_turno_abierto_retorna_none(self):
        """Hoy, sin entrada, turno no terminado → None (skip)."""
        hoy = date.today()
        salida_futura = datetime.combine(hoy, (datetime.now() + timedelta(hours=3)).time())
        r = _calcular_estatus_y_puntos(0, False, False, fecha=hoy, salida_programada=salida_futura)
        assert r is None

    @pytest.mark.unit
    def test_con_entrada_puntual_hoy_sin_salida_turno_abierto(self):
        """Hoy, entrada puntual, sin salida, turno abierto → COMPLETO."""
        hoy = date.today()
        salida_futura = datetime.combine(hoy, (datetime.now() + timedelta(hours=3)).time())
        r = _calcular_estatus_y_puntos(5, True, False, fecha=hoy, salida_programada=salida_futura)
        assert r is not None
        assert r[0] == "COMPLETO"

    @pytest.mark.unit
    def test_con_entrada_retardo_hoy_sin_salida_turno_abierto(self):
        """Hoy, entrada con 15 min retardo, sin salida, turno abierto → RETARDO_MENOR."""
        hoy = date.today()
        salida_futura = datetime.combine(hoy, (datetime.now() + timedelta(hours=3)).time())
        r = _calcular_estatus_y_puntos(15, True, False, fecha=hoy, salida_programada=salida_futura)
        assert r is not None
        assert r[0] == "RETARDO_MENOR"
