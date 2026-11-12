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
    _calcular_minutos_extra,
    _calcular_minutos_ordinarios,
    _calcular_minutos_retardo,
    _construir_sesiones,
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
# §15 CONTRATO (enmendado): ventana de entrada cerrada → FALTA anticipada
# ============================================================


class TestContratoVentanaEntrada:
    """
    Contrato §15 enmendado: una vez que entrada_programada +
    limite_retardo_mayor_segundos ha pasado, la ausencia total es
    definitiva aunque el turno siga abierto (salida_programada futura).

    No se debe esperar el fin del turno para reconocer una falta
    cuando ya es imposible llegar dentro del tiempo permitido.
    """

    def test_ventana_entrada_cerrada_shift_abierto_genera_falta(self):
        """
        Entrada hace 2h, límite retardo_mayor ~31 min → ventana cerrada.
        Turno aún no termina. Debe generarse FALTA sin esperar salida.
        """
        hoy = date.today()
        entrada_pasada = datetime.now() - timedelta(hours=2)
        salida_futura = datetime.now() + timedelta(hours=5)
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE,
            fecha=hoy,
            salida_programada=salida_futura,
            entrada_programada=entrada_pasada,
        )
        assert r is not None
        assert r[0] == "FALTA"
        assert r[2] is True

    def test_ventana_entrada_aun_abierta_no_genera_falta(self):
        """
        Entrada en 5 min → ventana de entrada todavía abierta.
        No debe generarse FALTA aunque ya sea hora de entrada.
        """
        hoy = date.today()
        entrada_futura = datetime.now() + timedelta(minutes=5)
        salida_futura = datetime.now() + timedelta(hours=8)
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE,
            fecha=hoy,
            salida_programada=salida_futura,
            entrada_programada=entrada_futura,
        )
        assert r is None or r[0] != "FALTA"

    def test_sin_entrada_programada_usa_salida_como_antes(self):
        """
        Sin entrada_programada → comportamiento previo: esperar salida_programada.
        Shift abierto → no genera resultado.
        """
        hoy = date.today()
        salida_futura = datetime.now() + timedelta(hours=3)
        r = _calcular_estatus_y_puntos(
            0, False, False, POLITICA_DAE,
            fecha=hoy,
            salida_programada=salida_futura,
        )
        assert r is None or r[0] != "FALTA"

    def test_omision_salida_sigue_usando_salida_programada(self):
        """
        OMISION_SALIDA no se adelanta: aunque la ventana de entrada ya cerró,
        si hay entrada y falta salida, se espera salida_programada.
        """
        hoy = date.today()
        entrada_pasada = datetime.now() - timedelta(hours=4)
        salida_futura = datetime.now() + timedelta(hours=1)
        r = _calcular_estatus_y_puntos(
            300, True, False, POLITICA_DAE,
            fecha=hoy,
            salida_programada=salida_futura,
            entrada_programada=entrada_pasada,
        )
        assert r is not None
        assert r[0] != "OMISION_SALIDA"


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


# ============================================================
# §11 CONTRATO (enmendado): modelo de sesiones posicionales
# ============================================================

T = datetime  # alias para brevedad en los tests de sesiones

E8 = T(2026, 8, 18, 8, 0, 0)    # entrada regular
S14 = T(2026, 8, 18, 14, 0, 0)  # salida regular
E1435 = T(2026, 8, 18, 14, 35, 0)  # entrada OT (tras bloqueo 30 min)
S17 = T(2026, 8, 18, 17, 0, 0)  # salida OT


class TestContratoSesiones:
    """
    Contrato §11: _construir_sesiones debe emparejar marcaciones
    cronológicamente en sesiones posicionales.
    """

    def test_cero_marcaciones(self):
        s = _construir_sesiones([], 0)
        assert s["sesion_regular"] == (None, None)
        assert s["sesion_ot"] is None
        assert s["exceso_marcaciones"] is False

    def test_una_marcacion(self):
        s = _construir_sesiones([E8.isoformat()], 1)
        entrada, salida = s["sesion_regular"]
        assert entrada == E8
        assert salida is None
        assert s["sesion_ot"] is None

    def test_dos_marcaciones_sesion_regular_completa(self):
        """Par normal: entrada + salida = sesión regular sin OT."""
        s = _construir_sesiones([E8.isoformat(), S14.isoformat()], 2)
        assert s["sesion_regular"] == (E8, S14)
        assert s["sesion_ot"] is None
        assert s["exceso_marcaciones"] is False

    def test_tres_marcaciones_ot_sin_salida(self):
        """Tercera marca abre sesión OT sin cierre → omisión de salida en OT."""
        s = _construir_sesiones(
            [E8.isoformat(), S14.isoformat(), E1435.isoformat()], 3
        )
        assert s["sesion_regular"] == (E8, S14)
        ot_e, ot_s = s["sesion_ot"]
        assert ot_e == E1435
        assert ot_s is None

    def test_cuatro_marcaciones_ambas_sesiones_completas(self):
        """Día con jornada regular y tiempo extra, ambas completas."""
        s = _construir_sesiones(
            [E8.isoformat(), S14.isoformat(), E1435.isoformat(), S17.isoformat()], 4
        )
        assert s["sesion_regular"] == (E8, S14)
        assert s["sesion_ot"] == (E1435, S17)
        assert s["exceso_marcaciones"] is False

    def test_cinco_marcaciones_exceso_usa_primeras_cuatro(self):
        """Más de 4 marcas: procesa solo las primeras 4 y activa exceso."""
        extra = T(2026, 8, 18, 17, 30, 0)
        marcas = [
            E8.isoformat(), S14.isoformat(),
            E1435.isoformat(), S17.isoformat(),
            extra.isoformat(),
        ]
        s = _construir_sesiones(marcas, 5)
        assert s["sesion_regular"] == (E8, S14)
        assert s["sesion_ot"] == (E1435, S17)
        assert s["exceso_marcaciones"] is True
        assert s["total_marcaciones"] == 5

    def test_orden_cronologico_garantizado(self):
        """Aunque el input llegue desordenado, el emparejamiento es por tiempo."""
        s = _construir_sesiones(
            [S14.isoformat(), E1435.isoformat(), E8.isoformat(), S17.isoformat()], 4
        )
        assert s["sesion_regular"] == (E8, S14)
        assert s["sesion_ot"] == (E1435, S17)

    def test_acepta_lista_vacia_json(self):
        s = _construir_sesiones("[]", 0)
        assert s["sesion_regular"] == (None, None)
        assert s["sesion_ot"] is None

    def test_acepta_json_string(self):
        """Acepta JSON serializado como string (formato de retorno de PostgreSQL)."""
        import json
        raw = json.dumps([E8.isoformat(), S14.isoformat()])
        s = _construir_sesiones(raw, 2)
        assert s["sesion_regular"] == (E8, S14)


# ============================================================
# §19 CONTRATO (enmendado): minutos extra con modelo de sesiones
# ============================================================

POLITICA_MARGEN = {
    **{k: v for k, v in {
        "id": 1,
        "limite_tolerancia_segundos": 659,
        "limite_retardo_menor_segundos": 1259,
        "limite_retardo_mayor_segundos": 1859,
        "puntos_retardo_menor": 1,
        "puntos_retardo_mayor": 2,
        "margen_tiempo_extra_segundos": 1800,  # 30 min
    }.items()}
}

EP = T(2026, 8, 18, 8, 0, 0)    # entrada programada
SP = T(2026, 8, 18, 14, 0, 0)   # salida programada (turno 8–14)
MARGEN = 1800                     # 30 min en segundos


class TestContratoMinutosExtraConSesiones:
    """
    Contrato §19 (enmendado): _calcular_minutos_extra usa duración
    real de la sesión OT, no la diferencia MAX(salida) − salida_programada.
    """

    def _extra(self, sesion_regular, sesion_ot, modalidad="DESPUES_SALIDA",
               permite=True):
        return _calcular_minutos_extra(
            modalidad_tiempo_extra=modalidad,
            entrada_programada=EP,
            salida_programada=SP,
            sesion_regular=sesion_regular,
            sesion_ot=sesion_ot,
            permite_tiempo_extra=permite,
            margen_tiempo_extra_segundos=MARGEN,
        )

    def test_sin_sesion_ot_cero_extra(self):
        """Solo jornada regular → 0 minutos extra."""
        assert self._extra((E8, S14), None) == 0

    def test_sesion_ot_completa_usa_duracion_real(self):
        """
        OT 14:35–17:00 = 145 min.
        Con MIN/MAX sería 17:00–14:00=180 min (incorrecto).
        El nuevo motor devuelve 145 (duración real de la sesión).
        """
        assert self._extra((E8, S14), (E1435, S17)) == 145

    def test_sesion_ot_sin_salida_cero_extra(self):
        """OT sin checada de salida → no se puede calcular → 0."""
        assert self._extra((E8, S14), (E1435, None)) == 0

    def test_sesion_ot_demasiado_temprana_es_invalida(self):
        """
        Si el OT inicia antes de salida_programada + margen, no es válido.
        14:10 < 14:00 + 30 min → 0.
        """
        ot_temprana = T(2026, 8, 18, 14, 10, 0)
        assert self._extra((E8, S14), (ot_temprana, S17)) == 0

    def test_no_permite_tiempo_extra_siempre_cero(self):
        assert self._extra((E8, S14), (E1435, S17), permite=False) == 0

    def test_antes_entrada_mantiene_logica_excedente_menos_margen(self):
        """
        ANTES_ENTRADA: llegó 90 min antes, margen 30 min → 60 min extra.
        La lógica es entrada_programada − primera_entrada − margen.
        """
        llegada_temprana = T(2026, 8, 18, 6, 30, 0)
        minutos = _calcular_minutos_extra(
            modalidad_tiempo_extra="ANTES_ENTRADA",
            entrada_programada=EP,
            salida_programada=SP,
            sesion_regular=(llegada_temprana, S14),
            sesion_ot=None,
            permite_tiempo_extra=True,
            margen_tiempo_extra_segundos=MARGEN,
        )
        assert minutos == 60

    def test_antes_entrada_dentro_del_margen_cero(self):
        """Llegó 20 min antes, margen 30 min → 0 (no supera el margen)."""
        llegada = T(2026, 8, 18, 7, 40, 0)
        minutos = _calcular_minutos_extra(
            modalidad_tiempo_extra="ANTES_ENTRADA",
            entrada_programada=EP,
            salida_programada=SP,
            sesion_regular=(llegada, S14),
            sesion_ot=None,
            permite_tiempo_extra=True,
            margen_tiempo_extra_segundos=MARGEN,
        )
        assert minutos == 0


# ============================================================
# §11 CONTRATO: minutos ordinarios usa duración real de sesión 1
# ============================================================


class TestContratoMinutosOrdinarios:
    """
    _calcular_minutos_ordinarios debe usar la duración real de la
    sesión regular (no el span completo del día).
    """

    def test_sesion_completa_sin_descanso(self):
        """8:00–14:00 sin descanso = 360 min ordinarios."""
        assert _calcular_minutos_ordinarios(
            sesion_regular=(E8, S14),
            duracion_jornada_minutos=360,
            descanso_minutos=0,
        ) == 360

    def test_sesion_con_descanso_fijo(self):
        """8:00–14:00 con 30 min descanso fijo del horario = 330 min."""
        assert _calcular_minutos_ordinarios(
            sesion_regular=(E8, S14),
            duracion_jornada_minutos=360,
            descanso_minutos=30,
        ) == 330

    def test_sesion_sin_salida_es_cero(self):
        assert _calcular_minutos_ordinarios(
            sesion_regular=(E8, None),
            duracion_jornada_minutos=360,
            descanso_minutos=0,
        ) == 0

    def test_sesion_sin_entrada_es_cero(self):
        assert _calcular_minutos_ordinarios(
            sesion_regular=(None, None),
            duracion_jornada_minutos=360,
            descanso_minutos=0,
        ) == 0

    def test_capped_a_duracion_jornada(self):
        """Si la sesión excede la jornada programada, se trunca."""
        s_tardio = T(2026, 8, 18, 15, 0, 0)  # 7 horas trabajadas
        assert _calcular_minutos_ordinarios(
            sesion_regular=(E8, s_tardio),
            duracion_jornada_minutos=360,  # jornada = 6 h
            descanso_minutos=0,
        ) == 360

    def test_sesion_ot_no_afecta_ordinarios(self):
        """
        Con sesión OT completa, los minutos ordinarios siguen siendo
        solo la duración de la sesión regular (8:00–14:00 = 360 min).
        El motor ya no resta minutos_extra de los ordinarios.
        """
        assert _calcular_minutos_ordinarios(
            sesion_regular=(E8, S14),
            duracion_jornada_minutos=360,
            descanso_minutos=0,
        ) == 360
