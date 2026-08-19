"""
Servicio de exportación de reportes en CSV y PDF.

Genera archivos descargables a partir de datos de reportes.
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime
from typing import Any


# ============================================================
# CSV Export
# ============================================================


def generar_csv_reporte_empleado(data: dict[str, Any]) -> str:
    """Genera CSV del reporte individual de un empleado."""

    output = io.StringIO()
    writer = csv.writer(output)

    empleado = data["empleado"]
    resumen = data["resumen"]

    # Header
    writer.writerow(["REPORTE DE ASISTENCIA - EMPLEADO"])
    writer.writerow([])
    writer.writerow(["Código", empleado["codigo_empleado"]])
    writer.writerow(["Nombre", empleado["nombre_completo"]])
    writer.writerow(["Puesto", empleado.get("puesto") or ""])
    writer.writerow(["Área", empleado.get("unidad_organizacional") or ""])
    writer.writerow(["Periodo", f"{data['fecha_inicio']} a {data['fecha_fin']}"])
    writer.writerow([])

    # Resumen
    writer.writerow(["RESUMEN"])
    writer.writerow(["Días en periodo", resumen["dias_periodo"]])
    writer.writerow(["Días completos", resumen["dias_completos"]])
    writer.writerow(["Retardos menores", resumen["retardos_menores"]])
    writer.writerow(["Retardos mayores", resumen["retardos_mayores"]])
    writer.writerow(["Faltas", resumen["faltas"]])
    writer.writerow(["Omisiones de salida", resumen["omisiones_salida"]])
    writer.writerow(["Total puntos", resumen["total_puntos"]])
    writer.writerow(["Minutos retardo", resumen["total_minutos_retardo"]])
    writer.writerow(["Horas ordinarias", _minutos_a_horas(resumen["total_minutos_ordinarios"])])
    writer.writerow(["Horas extra", _minutos_a_horas(resumen["total_minutos_extra"])])
    writer.writerow(["% Asistencia", f"{resumen['porcentaje_asistencia']}%"])
    writer.writerow([])

    # Detalle diario
    writer.writerow(["DETALLE DIARIO"])
    writer.writerow([
        "Fecha",
        "Entrada programada",
        "Salida programada",
        "Primera entrada",
        "Última salida",
        "Min. retardo",
        "Min. ordinarios",
        "Min. extra",
        "Estatus",
        "Puntos",
        "Observaciones",
    ])

    for dia in data["dias"]:
        writer.writerow([
            _format_date(dia["fecha"]),
            _format_datetime(dia["entrada_programada"]),
            _format_datetime(dia["salida_programada"]),
            _format_datetime(dia["primera_entrada"]),
            _format_datetime(dia["ultima_salida"]),
            dia["minutos_retardo"] or 0,
            dia["minutos_ordinarios"] or 0,
            dia["minutos_extra"] or 0,
            dia["estatus"],
            dia["puntos_generados"] or 0,
            dia["observaciones"] or "",
        ])

    return output.getvalue()


def generar_csv_reporte_departamental(data: dict[str, Any]) -> str:
    """Genera CSV del reporte departamental."""

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["REPORTE DEPARTAMENTAL DE ASISTENCIA"])
    writer.writerow([])
    writer.writerow(["Periodo", f"{data['fecha_inicio']} a {data['fecha_fin']}"])
    writer.writerow([])

    # Totales
    totales = data["totales"]
    writer.writerow(["RESUMEN GENERAL"])
    writer.writerow(["Departamentos", totales["departamentos"]])
    writer.writerow(["Empleados", totales["empleados"]])
    writer.writerow(["Días completos", totales["dias_completos"]])
    writer.writerow(["Faltas", totales["faltas"]])
    writer.writerow(["Retardos", totales["retardos"]])
    writer.writerow([])

    # Detalle por departamento
    writer.writerow(["DETALLE POR DEPARTAMENTO"])
    writer.writerow([
        "Departamento",
        "Empleados",
        "Registros",
        "Completos",
        "Ret. menores",
        "Ret. mayores",
        "Faltas",
        "Omisiones",
        "Puntos",
        "Horas ordinarias",
        "Horas extra",
    ])

    for dept in data["departamentos"]:
        writer.writerow([
            dept["unidad_nombre"] or "Sin departamento",
            dept["total_empleados"],
            dept["total_registros"],
            dept["dias_completos"],
            dept["retardos_menores"],
            dept["retardos_mayores"],
            dept["faltas"],
            dept["omisiones_salida"],
            dept["total_puntos"],
            _minutos_a_horas(dept["total_minutos_ordinarios"]),
            _minutos_a_horas(dept["total_minutos_extra"]),
        ])

    return output.getvalue()


# ============================================================
# PDF Export
# ============================================================


def _safe_text(value) -> str:
    """
    Convierte texto a formato seguro para PDF con fuentes estándar.
    Reemplaza caracteres no-latin1 con equivalentes ASCII.
    """
    if value is None:
        return ""
    text = str(value)
    # Reemplazos comunes de acentos/caracteres especiales
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N", "ü": "u", "Ü": "U",
        "¿": "?", "¡": "!", "°": "o",
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    # Eliminar cualquier otro caracter que no sea latin-1
    try:
        text.encode("latin-1")
    except UnicodeEncodeError:
        text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


def generar_pdf_reporte_empleado(data: dict[str, Any]) -> bytes:
    """Genera PDF del reporte individual de un empleado."""

    from fpdf import FPDF

    pdf = FPDF(orientation="L", unit="mm", format="letter")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    empleado = data["empleado"]
    resumen = data["resumen"]

    # Título
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Reporte de Asistencia - Empleado", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Direccion de Administracion Escolar", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Datos del empleado
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "DATOS DEL EMPLEADO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 5, "Codigo:")
    pdf.cell(60, 5, _safe_text(empleado["codigo_empleado"]))
    pdf.cell(40, 5, "Puesto:")
    pdf.cell(0, 5, _safe_text(empleado.get("puesto") or "N/A"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(40, 5, "Nombre:")
    pdf.cell(60, 5, _safe_text(empleado["nombre_completo"]))
    pdf.cell(40, 5, "Area:")
    pdf.cell(0, 5, _safe_text(empleado.get("unidad_organizacional") or "N/A"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(40, 5, "Periodo:")
    pdf.cell(0, 5, f"{data['fecha_inicio']} a {data['fecha_fin']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Resumen
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "RESUMEN DEL PERIODO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)

    col_w = 45
    pdf.cell(col_w, 5, f"Dias completos: {resumen['dias_completos']}")
    pdf.cell(col_w, 5, f"Retardos menores: {resumen['retardos_menores']}")
    pdf.cell(col_w, 5, f"Retardos mayores: {resumen['retardos_mayores']}")
    pdf.cell(col_w, 5, f"Faltas: {resumen['faltas']}")
    pdf.cell(0, 5, f"Puntos: {resumen['total_puntos']}", new_x="LMARGIN", new_y="NEXT")

    pdf.cell(col_w, 5, f"Horas ordinarias: {_minutos_a_horas(resumen['total_minutos_ordinarios'])}")
    pdf.cell(col_w, 5, f"Horas extra: {_minutos_a_horas(resumen['total_minutos_extra'])}")
    pdf.cell(col_w, 5, f"Asistencia: {resumen['porcentaje_asistencia']}%")
    pdf.cell(0, 5, "", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Tabla detalle
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "DETALLE DIARIO", new_x="LMARGIN", new_y="NEXT")

    headers = ["Fecha", "Ent. Prog.", "Sal. Prog.", "Entrada", "Salida", "Ret.", "Ord.", "Extra", "Estatus", "Pts"]
    col_widths = [22, 28, 28, 28, 28, 14, 14, 14, 32, 12]

    pdf.set_font("Helvetica", "B", 7)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 5, header, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    for dia in data["dias"]:
        pdf.cell(col_widths[0], 5, _format_date(dia["fecha"]), border=1, align="C")
        pdf.cell(col_widths[1], 5, _format_time_only(dia["entrada_programada"]), border=1, align="C")
        pdf.cell(col_widths[2], 5, _format_time_only(dia["salida_programada"]), border=1, align="C")
        pdf.cell(col_widths[3], 5, _format_time_only(dia["primera_entrada"]), border=1, align="C")
        pdf.cell(col_widths[4], 5, _format_time_only(dia["ultima_salida"]), border=1, align="C")
        pdf.cell(col_widths[5], 5, str(dia["minutos_retardo"] or 0), border=1, align="C")
        pdf.cell(col_widths[6], 5, str(dia["minutos_ordinarios"] or 0), border=1, align="C")
        pdf.cell(col_widths[7], 5, str(dia["minutos_extra"] or 0), border=1, align="C")
        pdf.cell(col_widths[8], 5, _safe_text(_format_estatus(dia["estatus"])), border=1, align="C")
        pdf.cell(col_widths[9], 5, str(dia["puntos_generados"] or 0), border=1, align="C")
        pdf.ln()

    # Footer
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()


def generar_pdf_reporte_departamental(data: dict[str, Any]) -> bytes:
    """Genera PDF del reporte departamental."""

    from fpdf import FPDF

    pdf = FPDF(orientation="L", unit="mm", format="letter")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    totales = data["totales"]

    # Título
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Reporte Departamental de Asistencia", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Direccion de Administracion Escolar", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Periodo
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 5, "Periodo:")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"{data['fecha_inicio']} a {data['fecha_fin']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Resumen general
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "RESUMEN GENERAL", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    col_w = 50
    pdf.cell(col_w, 5, f"Departamentos: {totales['departamentos']}")
    pdf.cell(col_w, 5, f"Empleados: {totales['empleados']}")
    pdf.cell(col_w, 5, f"Dias completos: {totales['dias_completos']}")
    pdf.cell(col_w, 5, f"Faltas: {totales['faltas']}")
    pdf.cell(0, 5, f"Retardos: {totales['retardos']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Tabla
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "DETALLE POR DEPARTAMENTO", new_x="LMARGIN", new_y="NEXT")

    headers = ["Departamento", "Emp.", "Completos", "Ret.Men", "Ret.May", "Faltas", "Omis.", "Puntos", "Hrs Ord.", "Hrs Extra"]
    col_widths = [55, 15, 22, 20, 20, 18, 18, 18, 25, 25]

    pdf.set_font("Helvetica", "B", 7)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 5, header, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    for dept in data["departamentos"]:
        nombre = _safe_text((dept["unidad_nombre"] or "Sin departamento"))[:30]
        pdf.cell(col_widths[0], 5, nombre, border=1)
        pdf.cell(col_widths[1], 5, str(dept["total_empleados"]), border=1, align="C")
        pdf.cell(col_widths[2], 5, str(dept["dias_completos"]), border=1, align="C")
        pdf.cell(col_widths[3], 5, str(dept["retardos_menores"]), border=1, align="C")
        pdf.cell(col_widths[4], 5, str(dept["retardos_mayores"]), border=1, align="C")
        pdf.cell(col_widths[5], 5, str(dept["faltas"]), border=1, align="C")
        pdf.cell(col_widths[6], 5, str(dept["omisiones_salida"]), border=1, align="C")
        pdf.cell(col_widths[7], 5, str(dept["total_puntos"]), border=1, align="C")
        pdf.cell(col_widths[8], 5, _minutos_a_horas(dept["total_minutos_ordinarios"]), border=1, align="C")
        pdf.cell(col_widths[9], 5, _minutos_a_horas(dept["total_minutos_extra"]), border=1, align="C")
        pdf.ln()

    # Footer
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()


# ============================================================
# Helpers
# ============================================================


def _minutos_a_horas(minutos: int) -> str:
    """Convierte minutos a formato HH:MM."""
    if not minutos:
        return "00:00"
    h = int(minutos) // 60
    m = int(minutos) % 60
    return f"{h:02d}:{m:02d}"


def _format_date(value) -> str:
    """Formatea fecha a DD/MM/YYYY."""
    if value is None:
        return ""
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    try:
        return datetime.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(value)


def _format_datetime(value) -> str:
    """Formatea datetime a DD/MM/YYYY HH:MM."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    try:
        return datetime.fromisoformat(str(value)).strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return str(value)


def _format_time_only(value) -> str:
    """Formatea datetime a solo HH:MM."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    try:
        return datetime.fromisoformat(str(value)).strftime("%H:%M")
    except (ValueError, TypeError):
        return str(value)


def _format_estatus(estatus: str | None) -> str:
    """Formatea estatus legible."""
    labels = {
        "COMPLETO": "Completo",
        "RETARDO_MENOR": "Ret. menor",
        "RETARDO_MAYOR": "Ret. mayor",
        "FALTA": "Falta",
        "OMISION_SALIDA": "Om. salida",
    }
    return labels.get(estatus or "", estatus or "")
