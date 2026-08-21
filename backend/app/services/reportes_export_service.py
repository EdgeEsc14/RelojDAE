"""
Servicio de exportación de reportes en CSV y PDF.

Genera archivos descargables a partir de datos de reportes.
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime
from typing import Any

from app.services.institucion_config import obtener_configuracion_institucional, obtener_logo_path


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
    writer.writerow(["Tolerancia", resumen.get("tolerancias", 0)])
    writer.writerow(["Retardos menores", resumen["retardos_menores"]])
    writer.writerow(["Retardos mayores", resumen["retardos_mayores"]])
    writer.writerow(["Faltas", resumen["faltas"]])
    writer.writerow(["Omisiones de entrada", resumen.get("omisiones_entrada", 0)])
    writer.writerow(["Omisiones de salida", resumen["omisiones_salida"]])
    writer.writerow(["Días no laborales", resumen.get("dias_no_laborales", 0)])
    writer.writerow(["Días que requieren revisión", resumen.get("dias_requieren_revision", 0)])
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
        "Requiere revisión",
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
            "Sí" if dia.get("requiere_revision") else "No",
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
        "Tolerancia",
        "Ret. menores",
        "Ret. mayores",
        "Faltas",
        "Om. entrada",
        "Om. salida",
        "No laborales",
        "Requieren revisión",
        "Puntos",
        "Horas ordinarias",
        "Horas extra",
    ])

    for dept in data["departamentos"]:
        writer.writerow([
            dept["unidad_nombre"] or "Sin departamento (unidad de nivel superior)",
            dept["total_empleados"],
            dept["total_registros"],
            dept["dias_completos"],
            dept.get("tolerancias", 0),
            dept["retardos_menores"],
            dept["retardos_mayores"],
            dept["faltas"],
            dept.get("omisiones_entrada", 0),
            dept["omisiones_salida"],
            dept.get("dias_no_laborales", 0),
            dept.get("dias_requieren_revision", 0),
            dept["total_puntos"],
            _minutos_a_horas(dept["total_minutos_ordinarios"]),
            _minutos_a_horas(dept["total_minutos_extra"]),
        ])

    # Detalle por empleado
    detalle_empleados = data.get("detalle_empleados") or []

    if detalle_empleados:
        writer.writerow([])
        writer.writerow(["DETALLE POR EMPLEADO"])
        writer.writerow([
            "Código",
            "Nombre",
            "Departamento",
            "Registros",
            "Completos",
            "Tolerancia",
            "Ret. menores",
            "Ret. mayores",
            "Faltas",
            "Om. entrada",
            "Om. salida",
            "No laborales",
            "Requieren revisión",
            "Puntos",
            "Horas ordinarias",
            "Horas extra",
        ])

        for emp in detalle_empleados:
            writer.writerow([
                emp["codigo_empleado"],
                emp["nombre_completo"],
                emp["unidad_nombre"] or "Sin departamento (unidad de nivel superior)",
                emp["total_registros"],
                emp["dias_completos"],
                emp.get("tolerancias", 0),
                emp["retardos_menores"],
                emp["retardos_mayores"],
                emp["faltas"],
                emp.get("omisiones_entrada", 0),
                emp["omisiones_salida"],
                emp.get("dias_no_laborales", 0),
                emp.get("dias_requieren_revision", 0),
                emp["total_puntos"],
                _minutos_a_horas(emp["total_minutos_ordinarios"]),
                _minutos_a_horas(emp["total_minutos_extra"]),
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


def _draw_encabezado_institucional(pdf, titulo: str) -> None:
    """
    Encabezado institucional compartido por los PDF generados con fpdf.

    Usa la configuración real (Configuración > Datos institucionales)
    y el logo configurado; nunca un nombre de institución hardcodeado.
    Si no hay logo configurado, no se dibuja imagen (fallback neutro).
    """
    config = obtener_configuracion_institucional()
    logo_path = obtener_logo_path()

    if logo_path is not None:
        try:
            pdf.image(str(logo_path), x=10, y=8, h=14)
        except Exception:
            pass

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, _safe_text(titulo), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, _safe_text(config["nombre_institucion"]), align="C", new_x="LMARGIN", new_y="NEXT")
    if config["nombre_corto"]:
        pdf.cell(0, 5, _safe_text(config["nombre_corto"]), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)


def _draw_pie_pagina(pdf) -> None:
    """Pie de página institucional compartido (Configuración > pie de página)."""
    config = obtener_configuracion_institucional()
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    if config["pie_pagina"]:
        pdf.cell(0, 5, _safe_text(config["pie_pagina"]), new_x="LMARGIN", new_y="NEXT")


def generar_pdf_reporte_departamental(data: dict[str, Any]) -> bytes:
    """Genera PDF del reporte departamental."""

    from fpdf import FPDF

    pdf = FPDF(orientation="L", unit="mm", format="letter")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    totales = data["totales"]

    _draw_encabezado_institucional(pdf, "Reporte Departamental de Asistencia")

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

    # Tabla por departamento
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "DETALLE POR DEPARTAMENTO", new_x="LMARGIN", new_y="NEXT")

    headers = [
        "Departamento", "Emp.", "Completos", "Toler.", "Ret.Men", "Ret.May",
        "Faltas", "Om.Ent", "Om.Sal", "No lab.", "Revisar", "Puntos",
        "Hrs Ord.", "Hrs Extra",
    ]
    col_widths = [38, 12, 18, 15, 15, 15, 15, 15, 15, 15, 15, 15, 18, 18]

    pdf.set_font("Helvetica", "B", 7)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 5, header, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    for dept in data["departamentos"]:
        nombre = _safe_text(
            (dept["unidad_nombre"] or "Sin departamento (nivel superior)")
        )[:26]
        pdf.cell(col_widths[0], 5, nombre, border=1)
        pdf.cell(col_widths[1], 5, str(dept["total_empleados"]), border=1, align="C")
        pdf.cell(col_widths[2], 5, str(dept["dias_completos"]), border=1, align="C")
        pdf.cell(col_widths[3], 5, str(dept.get("tolerancias", 0)), border=1, align="C")
        pdf.cell(col_widths[4], 5, str(dept["retardos_menores"]), border=1, align="C")
        pdf.cell(col_widths[5], 5, str(dept["retardos_mayores"]), border=1, align="C")
        pdf.cell(col_widths[6], 5, str(dept["faltas"]), border=1, align="C")
        pdf.cell(col_widths[7], 5, str(dept.get("omisiones_entrada", 0)), border=1, align="C")
        pdf.cell(col_widths[8], 5, str(dept["omisiones_salida"]), border=1, align="C")
        pdf.cell(col_widths[9], 5, str(dept.get("dias_no_laborales", 0)), border=1, align="C")
        pdf.cell(col_widths[10], 5, str(dept.get("dias_requieren_revision", 0)), border=1, align="C")
        pdf.cell(col_widths[11], 5, str(dept["total_puntos"]), border=1, align="C")
        pdf.cell(col_widths[12], 5, _minutos_a_horas(dept["total_minutos_ordinarios"]), border=1, align="C")
        pdf.cell(col_widths[13], 5, _minutos_a_horas(dept["total_minutos_extra"]), border=1, align="C")
        pdf.ln()

    # Tabla por empleado
    detalle_empleados = data.get("detalle_empleados") or []

    if detalle_empleados:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "DETALLE POR EMPLEADO", new_x="LMARGIN", new_y="NEXT")

        emp_headers = [
            "Codigo", "Nombre", "Departamento", "Completos",
            "Ret.Men", "Ret.May", "Faltas", "Revisar", "Puntos",
        ]
        emp_col_widths = [20, 45, 38, 20, 18, 18, 15, 15, 15]

        pdf.set_font("Helvetica", "B", 7)
        for i, header in enumerate(emp_headers):
            pdf.cell(emp_col_widths[i], 5, header, border=1, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 7)
        for emp in detalle_empleados:
            pdf.cell(emp_col_widths[0], 5, _safe_text(emp["codigo_empleado"]), border=1)
            pdf.cell(emp_col_widths[1], 5, _safe_text(emp["nombre_completo"])[:26], border=1)
            pdf.cell(
                emp_col_widths[2], 5,
                _safe_text(emp["unidad_nombre"] or "Sin departamento")[:22],
                border=1,
            )
            pdf.cell(emp_col_widths[3], 5, str(emp["dias_completos"]), border=1, align="C")
            pdf.cell(emp_col_widths[4], 5, str(emp["retardos_menores"]), border=1, align="C")
            pdf.cell(emp_col_widths[5], 5, str(emp["retardos_mayores"]), border=1, align="C")
            pdf.cell(emp_col_widths[6], 5, str(emp["faltas"]), border=1, align="C")
            pdf.cell(emp_col_widths[7], 5, str(emp.get("dias_requieren_revision", 0)), border=1, align="C")
            pdf.cell(emp_col_widths[8], 5, str(emp["total_puntos"]), border=1, align="C")
            pdf.ln()

    _draw_pie_pagina(pdf)

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


