"""
Configuración central de pytest para RelojDAE.

AISLAMIENTO:
- Los tests NUNCA se conectan a la BD productiva (dae_reloj).
- Los tests unitarios (marker @pytest.mark.unit) no requieren BD.
- Los tests de integración requieren una BD separada (fase posterior).

ESTRATEGIA:
- Characterization tests: documentan el comportamiento actual del motor.
- Contract tests: exigen el comportamiento del contrato contra el motor real.
  Usan xfail(strict=True) cuando el motor actual no cumple.
"""

import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

# Asegurar que el directorio backend esté en sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# Valores de la política DAE General (migración 022)
# Usados como referencia para generar valores esperados.
# ============================================================

POLITICA_DAE = {
    "limite_tolerancia_segundos": 659,
    "limite_retardo_menor_segundos": 1259,
    "limite_retardo_mayor_segundos": 1859,
    "puntos_retardo_menor": 1,
    "puntos_retardo_mayor": 2,
    "puntos_para_descanso": 10,
    "descansos_para_revision_baja": 7,
    "faltas_consecutivas_revision_baja": 3,
}


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def politica_dae():
    """Política DAE General según migración 022."""
    return POLITICA_DAE.copy()
