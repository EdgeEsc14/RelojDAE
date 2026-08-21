"""
Configuración institucional real (nombre, nombre corto, pie de página)
y resolución del logo configurado.

Fuente única de verdad para todo generador de reportes (PDF/CSV) y
para el endpoint de branding. Se guarda como archivo JSON junto al
logo (mismo directorio que ya usa /branding/logo), sin introducir una
tabla nueva: es la misma estrategia de almacenamiento por archivo que
ya existía para el logo, extendida a los campos de texto.

No hardcodear aquí ningún nombre de institución real: los valores por
defecto son neutros y solo se usan mientras nadie haya configurado
Datos institucionales en Configuración.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# app/services/institucion_config.py -> parents[1] = app
BRANDING_DIR = Path(__file__).resolve().parents[1] / "static" / "branding"
CONFIG_PATH = BRANDING_DIR / "config.json"

DEFAULTS: dict[str, str] = {
    "nombre_institucion": "Institución",
    "nombre_corto": "",
    "pie_pagina": "",
}


def obtener_configuracion_institucional() -> dict[str, str]:
    """
    Retorna la configuración institucional vigente.

    Si no se ha configurado nada todavía, retorna valores neutros
    (nunca el nombre de una institución real hardcodeado).
    """
    if not CONFIG_PATH.exists():
        return dict(DEFAULTS)

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULTS)

    return {
        "nombre_institucion": str(
            data.get("nombre_institucion") or DEFAULTS["nombre_institucion"]
        ),
        "nombre_corto": str(
            data.get("nombre_corto") or DEFAULTS["nombre_corto"]
        ),
        "pie_pagina": str(data.get("pie_pagina") or ""),
    }


def guardar_configuracion_institucional(
    *,
    nombre_institucion: str,
    nombre_corto: str,
    pie_pagina: str | None,
) -> dict[str, str]:
    """Persiste la configuración institucional en config.json."""

    nombre_institucion = nombre_institucion.strip()
    nombre_corto = nombre_corto.strip()
    pie_pagina_limpio = (pie_pagina or "").strip()

    if not nombre_institucion:
        raise ValueError("El nombre de la institución no puede estar vacío.")

    config: dict[str, str] = {
        "nombre_institucion": nombre_institucion,
        "nombre_corto": nombre_corto,
        "pie_pagina": pie_pagina_limpio,
    }

    BRANDING_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return config


def obtener_logo_path() -> Path | None:
    """
    Ruta del logo institucional configurado, o None si no existe.

    Único punto de resolución del logo: cualquier generador de
    reportes debe usar esta función en vez de recalcular la ruta,
    para no repetir (y potencialmente desalinear) BRANDING_DIR.
    """
    for ext in (".png", ".jpg", ".jpeg"):
        path = BRANDING_DIR / f"logo{ext}"
        if path.exists():
            return path
    return None
