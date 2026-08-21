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

# Política de referencia (misma que la política DAE sembrada en BD de test:
# limite_tolerancia_segundos=659, limite_retardo_menor_segundos=1259,
# limite_retardo_mayor_segundos=1859, puntos_retardo_menor=1, puntos_retardo_mayor=2).
POLITICA_DAE = {
    "id": 1,
    "limite_tolerancia_segundos": 659,
    "limite_retardo_menor_segundos": 1259,
    "limite_retardo_mayor_segundos": 1859,
    "puntos_retardo_menor": 1,
    "puntos_retardo_mayor": 2,
}


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
# Characterization: _calcular_estatus_y_puntos (segundos + política)
# ============================================================


class TestCharEstatus:
    """
    Documenta la clasificación de _calcular_estatus_y_puntos: límites en
    segundos y puntos, ambos leídos de la política resuelta (Contrato §5).
    Sin hardcodes de minutos ni de puntos.
    """

    @pytest.mark.unit
    def test_0seg_completo(self):
        r = _calcular_estatus_y_puntos(0, True, True, POLITICA_DAE)
        assert r[0] == "COMPLETO"
        assert r[1] == 0

    @pytest.mark.unit
    def test_negativo_completo(self):
        """Llegada antes de la hora programada → COMPLETO."""
        r = _calcular_estatus_y_puntos(-30, True, True, POLITICA_DAE)
        assert r[0] == "COMPLETO"
        assert r[1] == 0

    @pytest.mark.unit
    def test_300seg_tolerancia(self):
        r = _calcular_estatus_y_puntos(300, True, True, POLITICA_DAE)
        assert r[0] == "TOLERANCIA"
        assert r[1] == 0

    @pytest.mark.unit
    def test_659seg_frontera_tolerancia(self):
        r = _calcular_estatus_y_puntos(659, True, True, POLITICA_DAE)
        assert r[0] == "TOLERANCIA"
        assert r[1] == 0

    @pytest.mark.unit
    def test_660seg_retardo_menor(self):
        r = _calcular_estatus_y_puntos(660, True, True, POLITICA_DAE)
        assert r[0] == "RETARDO_MENOR"
        assert r[1] == POLITICA_DAE["puntos_retardo_menor"]

    @pytest.mark.unit
    def test_1259seg_retardo_menor(self):
        r = _calcular_estatus_y_puntos(1259, True, True, POLITICA_DAE)
        assert r[0] == "RETARDO_MENOR"
        assert r[1] == POLITICA_DAE["puntos_retardo_menor"]

    @pytest.mark.unit
    def test_1260seg_retardo_mayor(self):
        r = _calcular_estatus_y_puntos(1260, True, True, POLITICA_DAE)
        assert r[0] == "RETARDO_MAYOR"
        assert r[1] == POLITICA_DAE["puntos_retardo_mayor"]

    @pytest.mark.unit
    def test_1859seg_retardo_mayor(self):
        r = _calcular_estatus_y_puntos(1859, True, True, POLITICA_DAE)
        assert r[0] == "RETARDO_MAYOR"
        assert r[1] == POLITICA_DAE["puntos_retardo_mayor"]

    @pytest.mark.unit
    def test_1860seg_falta(self):
        r = _calcular_estatus_y_puntos(1860, True, True, POLITICA_DAE)
        assert r[0] == "FALTA"
        assert r[1] == 0

    @pytest.mark.unit
    def test_puntos_provienen_de_la_politica_no_hardcodeados(self):
        """Los puntos deben leerse de la política, no ser 1/2 fijos."""
        politica_custom = dict(POLITICA_DAE, puntos_retardo_menor=5, puntos_retardo_mayor=9)
        r_menor = _calcular_estatus_y_puntos(700, True, True, politica_custom)
        r_mayor = _calcular_estatus_y_puntos(1300, True, True, politica_custom)
        assert r_menor[0] == "RETARDO_MENOR"
        assert r_menor[1] == 5
        assert r_mayor[0] == "RETARDO_MAYOR"
        assert r_mayor[1] == 9

    @pytest.mark.unit
    def test_sin_entrada_dia_pasado_falta(self):
        fecha_pasada = date(2026, 8, 10)
        salida_prog = datetime(2026, 8, 10, 15, 0)
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE, fecha=fecha_pasada, salida_programada=salida_prog
        )
        assert r is not None
        assert r[0] == "FALTA"
        assert r[2] is True  # requiere_revision

    @pytest.mark.unit
    def test_con_entrada_sin_salida_dia_pasado_omision(self):
        fecha_pasada = date(2026, 8, 10)
        salida_prog = datetime(2026, 8, 10, 15, 0)
        r = _calcular_estatus_y_puntos(
            300, True, False, POLITICA_DAE, fecha=fecha_pasada, salida_programada=salida_prog
        )
        assert r is not None
        assert r[0] == "OMISION_SALIDA"
        assert r[2] is True

    @pytest.mark.unit
    def test_determinista(self):
        """Mismos params → mismo resultado."""
        r1 = _calcular_estatus_y_puntos(900, True, True, POLITICA_DAE)
        r2 = _calcular_estatus_y_puntos(900, True, True, POLITICA_DAE)
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
        r = _calcular_estatus_y_puntos(0, False, False, POLITICA_DAE, fecha=hoy, salida_programada=salida_futura)
        assert r is None

    @pytest.mark.unit
    def test_con_entrada_puntual_hoy_sin_salida_turno_abierto(self):
        """Hoy, entrada puntual (0 seg), sin salida, turno abierto → COMPLETO."""
        hoy = date.today()
        salida_futura = datetime.combine(hoy, (datetime.now() + timedelta(hours=3)).time())
        r = _calcular_estatus_y_puntos(0, True, False, POLITICA_DAE, fecha=hoy, salida_programada=salida_futura)
        assert r is not None
        assert r[0] == "COMPLETO"

    @pytest.mark.unit
    def test_con_entrada_retardo_hoy_sin_salida_turno_abierto(self):
        """Hoy, entrada con 900 seg (15 min) de retardo, sin salida, turno abierto → RETARDO_MENOR."""
        hoy = date.today()
        salida_futura = datetime.combine(hoy, (datetime.now() + timedelta(hours=3)).time())
        r = _calcular_estatus_y_puntos(900, True, False, POLITICA_DAE, fecha=hoy, salida_programada=salida_futura)
        assert r is not None
        assert r[0] == "RETARDO_MENOR"

    @pytest.mark.unit
    def test_sin_entrada_hoy_turno_cerrado_genera_falta(self):
        """Hoy, sin entrada, turno ya cerrado (salida_programada pasada) → FALTA."""
        hoy = date.today()
        salida_pasada = datetime.now() - timedelta(minutes=1)
        r = _calcular_estatus_y_puntos(0, False, False, POLITICA_DAE, fecha=hoy, salida_programada=salida_pasada)
        assert r is not None
        assert r[0] == "FALTA"

    @pytest.mark.unit
    def test_con_entrada_hoy_turno_cerrado_sin_salida_genera_omision(self):
        """Hoy, con entrada sin salida, turno ya cerrado → OMISION_SALIDA."""
        hoy = date.today()
        salida_pasada = datetime.now() - timedelta(minutes=1)
        r = _calcular_estatus_y_puntos(5, True, False, POLITICA_DAE, fecha=hoy, salida_programada=salida_pasada)
        assert r is not None
        assert r[0] == "OMISION_SALIDA"

    @pytest.mark.unit
    def test_turno_nocturno_fila_de_ayer_abierto_hoy_no_cierra(self):
        """
        Turno nocturno: la fila pertenece a "ayer" (día de entrada) pero la
        salida programada cae hoy y aún no llega → no debe cerrarse como
        FALTA. Antes del fix, el gate comparaba fecha (de la fila) == hoy y
        fallaba para este caso.
        """
        fecha_fila = date.today() - timedelta(days=1)
        salida_futura = datetime.now() + timedelta(hours=2)
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE, fecha=fecha_fila, salida_programada=salida_futura
        )
        assert r is None

    @pytest.mark.unit
    def test_turno_nocturno_fila_de_ayer_cerrado_genera_falta(self):
        """Turno nocturno con salida programada (hoy) ya pasada → FALTA definitiva."""
        fecha_fila = date.today() - timedelta(days=1)
        salida_pasada = datetime.now() - timedelta(minutes=1)
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE, fecha=fecha_fila, salida_programada=salida_pasada
        )
        assert r is not None
        assert r[0] == "FALTA"
