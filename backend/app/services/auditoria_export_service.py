"""Exportación CSV de la Auditoría (bitácora de cambios y accesos)."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any


def generar_csv_bitacora(items: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Fecha/hora", "Esquema", "Tabla", "Operación",
        "Registro ID", "Usuario", "IP", "Módulo", "Acción", "Cambios",
    ])

    for item in items:
        fecha = item.get("fecha_evento")
        writer.writerow([
            item.get("id"),
            fecha.strftime("%d/%m/%Y %H:%M:%S") if isinstance(fecha, datetime) else fecha,
            item.get("esquema"),
            item.get("tabla"),
            item.get("operacion"),
            item.get("registro_id") or "",
            item.get("usuario_app_correo") or "Sistema",
            item.get("ip_origen") or "",
            item.get("modulo") or "",
            item.get("accion_app") or "",
            item.get("cambios") or "",
        ])

    return output.getvalue()


def generar_csv_login(items: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Fecha/hora", "Correo intentado", "Usuario vinculado",
        "Rol", "Resultado", "Motivo", "IP", "User agent",
    ])

    for item in items:
        fecha = item.get("fecha_evento")
        writer.writerow([
            item.get("id"),
            fecha.strftime("%d/%m/%Y %H:%M:%S") if isinstance(fecha, datetime) else fecha,
            item.get("correo_intentado") or "",
            item.get("usuario_correo") or "",
            item.get("usuario_rol") or "",
            item.get("resultado"),
            item.get("motivo") or "",
            item.get("ip_origen_raw") or "",
            item.get("user_agent") or "",
        ])

    return output.getvalue()
