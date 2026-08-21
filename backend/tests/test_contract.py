"""
CONTRACT TESTS — Comportamiento exigido por docs/CONTRATO_NUCLEO_ASISTENCIA.md.

Estos tests llaman al MOTOR REAL (_calcular_estatus_y_puntos, etc.)
y exigen el comportamiento del contrato.

Los que fallan porque el motor actual no cumple el contrato están
marcados con @pytest.mark.xfail(strict=True, reason="...").

Cuando el motor se corrija:
- Si el test pasa → pytest reporta XPASS(strict) → se debe retirar el xfail.
- Si sigue fallando → pytest reporta xfail (esperado).

NINGÚN incumplimiento del contrato puede aparecer como PASS.
"""

import pytest
from datetime import date, datetime, time, timedelta

from app.repositories.asistencia_procesamiento_repo import (
    _calcular_estatus_y_puntos,
    _calcular_minutos_retardo,
)

# Referencia: política DAE (migración 022)
# limite_tolerancia_segundos = 659 (~10:59)
# limite_retardo_menor_segundos = 1259 (~20:59)
# limite_retardo_mayor_segundos = 1859 (~30:59)

ENTRADA_PROGRAMADA = datetime(2026, 8, 18, 8, 0, 0)
FECHA = date(2026, 8, 18)
SALIDA_PROG = datetime(2026, 8, 18, 15, 0, 0)

POLITICA_DAE = {
    "id": 1,
    "limite_tolerancia_segundos": 659,
    "limite_retardo_menor_segundos": 1259,
    "limite_retardo_mayor_segundos": 1859,
    "puntos_retardo_menor": 1,
    "puntos_retardo_mayor": 2,
}


def _retardo_y_estatus(segundos_despues: int):
    """
    Helper: calcula el estatus llamando al motor REAL con precisión en
    segundos (Contrato §5) y la política DAE de referencia.
    """
    resultado = _calcular_estatus_y_puntos(
        segundos_retardo=segundos_despues,
        tiene_entrada=True,
        tiene_salida=True,
        politica=POLITICA_DAE,
        fecha=FECHA,
        salida_programada=SALIDA_PROG,
    )
    return resultado


# ============================================================
# §5 CONTRATO: TOLERANCIA debe existir como estatus
# ============================================================


class TestContratoTolerancia:
    """
    Contrato §5: llegada después de entrada y dentro de limite_tolerancia_segundos
    debe clasificarse como TOLERANCIA (0 puntos).
    """

    def test_300seg_tolerancia(self):
        """08:05:00 (300 seg) → debe ser TOLERANCIA."""
        r = _retardo_y_estatus(300)
        assert r[0] == "TOLERANCIA"
        assert r[1] == 0

    def test_659seg_frontera_tolerancia(self):
        """08:10:59 (659 seg) → debe ser TOLERANCIA (frontera exacta del límite)."""
        r = _retardo_y_estatus(659)
        assert r[0] == "TOLERANCIA"
        assert r[1] == 0


# ============================================================
# §5 CONTRATO: Fronteras en SEGUNDOS (no minutos)
# ============================================================


class TestContratoFronterasSegundos:
    """
    Contrato §5: Los límites se evalúan en segundos contra el motor real,
    usando la política DAE de referencia (659 / 1259 / 1859).

    Los 6 casos de frontera obligatorios:
    - 659 seg (08:10:59) → TOLERANCIA (frontera exacta de limite_tolerancia_segundos)
    - 660 seg (08:11:00) → RETARDO_MENOR
    - 1259 seg (08:20:59) → RETARDO_MENOR (frontera exacta de limite_retardo_menor_segundos)
    - 1260 seg (08:21:00) → RETARDO_MAYOR
    - 1859 seg (08:30:59) → RETARDO_MAYOR (frontera exacta de limite_retardo_mayor_segundos)
    - 1860 seg (08:31:00) → FALTA
    """

    def test_659seg_frontera_tolerancia(self):
        """08:10:59 (659 seg) → TOLERANCIA (frontera exacta del límite)."""
        r = _retardo_y_estatus(659)
        assert r[0] == "TOLERANCIA"
        assert r[1] == 0

    def test_660seg_retardo_menor(self):
        """08:11:00 (660 seg) → RETARDO_MENOR, puntos desde la política."""
        r = _retardo_y_estatus(660)
        assert r[0] == "RETARDO_MENOR"
        assert r[1] == 1

    def test_1259seg_retardo_menor(self):
        """08:20:59 (1259 seg) → RETARDO_MENOR (frontera exacta)."""
        r = _retardo_y_estatus(1259)
        assert r[0] == "RETARDO_MENOR"
        assert r[1] == 1

    def test_1260seg_retardo_mayor(self):
        """08:21:00 (1260 seg) → RETARDO_MAYOR, puntos desde la política."""
        r = _retardo_y_estatus(1260)
        assert r[0] == "RETARDO_MAYOR"
        assert r[1] == 2

    def test_1859seg_retardo_mayor(self):
        """08:30:59 (1859 seg) → RETARDO_MAYOR (frontera exacta)."""
        r = _retardo_y_estatus(1859)
        assert r[0] == "RETARDO_MAYOR"
        assert r[1] == 2

    def test_1860seg_falta(self):
        """08:31:00 (1860 seg) → FALTA, 0 puntos."""
        r = _retardo_y_estatus(1860)
        assert r[0] == "FALTA"
        assert r[1] == 0


# ============================================================
# §5 CONTRATO: Llegada puntual
# ============================================================


class TestContratoPuntual:
    """Contrato §5: llegada en hora o antes → COMPLETO."""

    def test_llegada_antes(self):
        """07:59:59 → COMPLETO."""
        r = _retardo_y_estatus(-1)
        assert r[0] == "COMPLETO"
        assert r[1] == 0

    def test_llegada_exacta(self):
        """08:00:00 → COMPLETO."""
        r = _retardo_y_estatus(0)
        assert r[0] == "COMPLETO"
        assert r[1] == 0


# ============================================================
# §7 CONTRATO: Omisiones
# ============================================================


class TestContratoOmisiones:
    """Contrato §7: omisiones deben marcar requiere_revision = TRUE."""

    def test_omision_salida(self):
        """Entrada sin salida, día pasado → OMISION_SALIDA, requiere_revision."""
        r = _calcular_estatus_y_puntos(
            segundos_retardo=5,
            tiene_entrada=True,
            tiene_salida=False,
            politica=POLITICA_DAE,
            fecha=FECHA,
            salida_programada=SALIDA_PROG,
        )
        assert r is not None
        assert r[0] == "OMISION_SALIDA"
        assert r[2] is True  # requiere_revision

    def test_omision_entrada(self):
        """
        Salida sin entrada → OMISION_ENTRADA.
        """
        r = _calcular_estatus_y_puntos(
            segundos_retardo=0,
            tiene_entrada=False,
            tiene_salida=True,
            politica=POLITICA_DAE,
            fecha=FECHA,
            salida_programada=SALIDA_PROG,
        )
        assert r is not None
        assert r[0] == "OMISION_ENTRADA"
        assert r[2] is True


# ============================================================
# §5 CONTRATO: Política NO hardcodeada
# ============================================================


class TestContratoNoHardcode:
    """
    Contrato §5: los límites deben provenir de politicas_asistencia.
    """

    def test_motor_acepta_politica_como_parametro(self):
        """
        La función _calcular_estatus_y_puntos debe recibir los límites
        de una política resuelta, no hardcodearlos.
        """
        import inspect
        sig = inspect.signature(_calcular_estatus_y_puntos)
        params = list(sig.parameters.keys())
        assert any(
            "politica" in p or "limite" in p or "segundos" in p
            for p in params
        ), f"Parámetros actuales: {params}"
        assert "politica" in params, f"Parámetros actuales: {params}"


# ============================================================
# §15 CONTRATO: Jornada en curso
# ============================================================


class TestContratoJornadaEnCurso:
    """
    Contrato §15: No generar resultados definitivos para jornadas abiertas.
    """

    def test_sin_entrada_hoy_turno_abierto_no_genera_falta(self):
        """Hoy, sin entrada, turno abierto → no debe generar FALTA."""
        hoy = date.today()
        salida_futura = datetime.combine(hoy, (datetime.now() + timedelta(hours=3)).time())
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE, fecha=hoy, salida_programada=salida_futura
        )
        # Debe ser None (no procesar) — NO debe ser FALTA
        assert r is None or r[0] != "FALTA"

    def test_con_entrada_hoy_turno_abierto_no_genera_omision(self):
        """Hoy, con entrada, turno abierto → no debe generar OMISION_SALIDA."""
        hoy = date.today()
        salida_futura = datetime.combine(hoy, (datetime.now() + timedelta(hours=3)).time())
        r = _calcular_estatus_y_puntos(
            5, True, False, POLITICA_DAE, fecha=hoy, salida_programada=salida_futura
        )
        if r is not None:
            assert r[0] != "OMISION_SALIDA"

    def test_sin_entrada_hoy_turno_ya_cerrado_genera_falta(self):
        """Hoy, sin entrada, turno YA cerrado (salida_programada pasada) → FALTA definitiva."""
        hoy = date.today()
        salida_pasada = datetime.now() - timedelta(minutes=1)
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE, fecha=hoy, salida_programada=salida_pasada
        )
        assert r is not None
        assert r[0] == "FALTA"
        assert r[2] is True

    def test_con_entrada_hoy_turno_ya_cerrado_genera_omision_salida(self):
        """Hoy, con entrada sin salida, turno YA cerrado → OMISION_SALIDA definitiva."""
        hoy = date.today()
        salida_pasada = datetime.now() - timedelta(minutes=1)
        r = _calcular_estatus_y_puntos(
            5, True, False, POLITICA_DAE, fecha=hoy, salida_programada=salida_pasada
        )
        assert r is not None
        assert r[0] == "OMISION_SALIDA"
        assert r[2] is True

    def test_turno_nocturno_antes_del_cierre_no_genera_resultado_definitivo(self):
        """
        Turno nocturno en curso: entrada fue "ayer" (fecha de la fila), la salida
        programada cae "hoy" y todavía no llega. No debe cerrarse como FALTA
        aunque la fecha de la fila ya no sea la fecha de "hoy" (regresión del
        bug de comparar solo fecha_date == hoy).
        """
        fecha_fila = date.today() - timedelta(days=1)
        salida_futura = datetime.now() + timedelta(hours=2)
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE, fecha=fecha_fila, salida_programada=salida_futura
        )
        assert r is None or r[0] != "FALTA"

    def test_turno_nocturno_despues_del_cierre_genera_resultado_definitivo(self):
        """
        Turno nocturno ya cerrado: entrada fue "ayer" (fecha de la fila), la
        salida programada ya pasó → debe generar resultado definitivo (FALTA
        por ausencia total).
        """
        fecha_fila = date.today() - timedelta(days=1)
        salida_pasada = datetime.now() - timedelta(minutes=1)
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE, fecha=fecha_fila, salida_programada=salida_pasada
        )
        assert r is not None
        assert r[0] == "FALTA"
        assert r[2] is True


# ============================================================
# Tests que REQUIEREN integración PostgreSQL (documentados, no implementados)
# ============================================================


class TestRequierenIntegracion:
    """
    Tests que requerían infraestructura HTTP (TestClient + JWT) que no
    existía en el repo. Esa infraestructura (fixture `api_client` en
    conftest.py + esquema `seguridad` en tests/sql/baseline_test.sql) ya
    existe y la cobertura real de §16 vive en:

        tests/test_authorization_http.py::TestAutorizacionAsistenciaHTTP

    - test_autorizacion_total_accede      -> test_total_mantiene_acceso_correcto
    - test_autorizacion_area_no_ve_otras  -> test_area_no_puede_salir_de_su_alcance
    - test_autorizacion_propio_no_ve_otros -> test_propio_no_puede_consultar_otro_empleado
    - test_autorizacion_lectura_no_procesa -> test_lectura_puede_consultar_pero_no_modificar

    Se retiran los `skip` de aquí porque el comportamiento ya queda
    demostrado en ese archivo (no se dejan placeholders duplicados).
    """
