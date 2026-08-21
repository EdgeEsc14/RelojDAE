"""
Servicio de generación de reporte PDF individual por empleado.

Usa reportlab para generar un documento tamaño carta con:
- Encabezado institucional con logo
- Datos del empleado
- Tabla diaria de asistencia
- Resumen estadístico
- Pie de página con número de página y fecha de generación

Diseño: institucional, profesional, colores discretos.
"""

from __future__ import annotations

import io
from datetime import date, datetime, time
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.services.institucion_config import (
    obtener_configuracion_institucional,
    obtener_logo_path,
)


# ============================================================
# Colores institucionales
# ============================================================

COLOR_PRIMARY = colors.HexColor("#6f1d46")  # Guinda IPN
COLOR_PRIMARY_LIGHT = colors.HexColor("#8c2f5d")
COLOR_ACCENT = colors.HexColor("#c9a227")  # Dorado
COLOR_HEADER_BG = colors.HexColor("#f6eaf0")
COLOR_TABLE_HEADER = colors.HexColor("#6f1d46")
COLOR_TABLE_HEADER_TEXT = colors.white
COLOR_ROW_ALT = colors.HexColor("#faf7f4")
COLOR_BORDER = colors.HexColor("#d6d3d1")
COLOR_TEXT = colors.HexColor("#1f2937")
COLOR_TEXT_MUTED = colors.HexColor("#6b7280")

# Estatus colors
STATUS_COLORS = {
    "COMPLETO": colors.HexColor("#10b981"),
    "TOLERANCIA": colors.HexColor("#0ea5e9"),
    "RETARDO_MENOR": colors.HexColor("#f59e0b"),
    "RETARDO_MAYOR": colors.HexColor("#ea580c"),
    "FALTA": colors.HexColor("#ef4444"),
    "OMISION_ENTRADA": colors.HexColor("#8b5cf6"),
    "OMISION_SALIDA": colors.HexColor("#8b5cf6"),
    "DIA_NO_LABORAL": colors.HexColor("#9ca3af"),
}


# ============================================================
# Utilidades
# ============================================================

def _format_time(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    text = str(value)
    if "T" in text:
        return text.split("T")[1][:5]
    if len(text) >= 5:
        return text[:5]
    return text or "—"


def _format_date(value) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value)


def _format_day_name(value) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        return days[value.weekday()]
    return ""


def _format_minutes_as_hours(minutes: int) -> str:
    if minutes <= 0:
        return "—"
    h = minutes // 60
    m = minutes % 60
    if h == 0:
        return f"{m}m"
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"


def _format_status(status: str) -> str:
    mapping = {
        "COMPLETO": "Completo",
        "TOLERANCIA": "Tolerancia",
        "RETARDO_MENOR": "Ret. menor",
        "RETARDO_MAYOR": "Ret. mayor",
        "FALTA": "Falta",
        "OMISION_ENTRADA": "Om. entrada",
        "OMISION_SALIDA": "Om. salida",
        "DIA_NO_LABORAL": "No laboral",
    }
    return mapping.get((status or "").upper(), status or "—")


# ============================================================
# Generador principal
# ============================================================

def generar_reporte_pdf_empleado(
    datos: dict[str, Any],
) -> bytes:
    """
    Genera el PDF completo del reporte de asistencia/incidencias
    de un empleado y retorna los bytes del archivo.
    """

    buffer = io.BytesIO()

    # Configuración del documento
    page_width, page_height = letter
    margin_left = 1.5 * cm
    margin_right = 1.5 * cm
    margin_top = 2.0 * cm
    margin_bottom = 2.5 * cm

    doc = BaseDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=margin_left,
        rightMargin=margin_right,
        topMargin=margin_top,
        bottomMargin=margin_bottom,
        title="Reporte de Asistencia por Empleado",
        author="RelojDAE - Sistema de Control de Asistencia",
    )

    # Frame principal
    frame = Frame(
        margin_left,
        margin_bottom,
        page_width - margin_left - margin_right,
        page_height - margin_top - margin_bottom,
        id="main",
    )

    # Datos para header/footer
    empleado = datos["empleado"]
    fecha_inicio = datos["fecha_inicio"]
    fecha_fin = datos["fecha_fin"]
    config_institucional = obtener_configuracion_institucional()
    pie_pagina = config_institucional["pie_pagina"]

    def _header_footer(canvas, doc_instance):
        """Dibuja header y footer en cada página."""
        canvas.saveState()

        # --- Footer ---
        footer_y = 1.2 * cm if not pie_pagina else 1.6 * cm
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(COLOR_TEXT_MUTED)

        # Izquierda: fecha de generación
        now_text = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        canvas.drawString(margin_left, footer_y, f"Generado: {now_text}")

        # Centro: sistema
        canvas.drawCentredString(
            page_width / 2, footer_y, "RelojDAE — Sistema de Control de Asistencia"
        )

        # Derecha: página
        canvas.drawRightString(
            page_width - margin_right,
            footer_y,
            f"Página {doc_instance.page}",
        )

        # Pie de página institucional configurado (Configuración >
        # Datos institucionales), si existe.
        if pie_pagina:
            canvas.drawCentredString(
                page_width / 2, footer_y - 10, pie_pagina
            )

        # Línea separadora footer
        canvas.setStrokeColor(COLOR_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(
            margin_left, footer_y + 10,
            page_width - margin_right, footer_y + 10,
        )

        canvas.restoreState()

    template = PageTemplate(
        id="main",
        frames=[frame],
        onPage=_header_footer,
    )
    doc.addPageTemplates([template])

    # Estilos
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=COLOR_PRIMARY,
        spaceAfter=2 * mm,
        alignment=TA_CENTER,
    )

    style_subtitle = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=COLOR_TEXT_MUTED,
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    )

    style_section = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=COLOR_PRIMARY,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
    )

    style_normal = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=COLOR_TEXT,
        leading=11,
    )

    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=COLOR_TEXT_MUTED,
    )

    style_value = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=COLOR_TEXT,
    )

    # ============================================================
    # Construir contenido
    # ============================================================

    elements = []

    # --- ENCABEZADO INSTITUCIONAL ---
    header_data = _build_header(datos, style_title, style_subtitle)
    elements.extend(header_data)

    # --- DATOS DEL EMPLEADO ---
    elements.append(Paragraph("Datos del empleado", style_section))
    employee_table = _build_employee_info_table(datos, style_label, style_value)
    elements.append(employee_table)
    elements.append(Spacer(1, 4 * mm))

    # --- TABLA DIARIA ---
    elements.append(Paragraph("Detalle diario de asistencia", style_section))
    daily_table = _build_daily_table(datos)
    elements.append(daily_table)
    elements.append(Spacer(1, 4 * mm))

    # --- RESUMEN ---
    elements.append(Paragraph("Resumen del periodo", style_section))
    summary_table = _build_summary_table(datos)
    elements.append(summary_table)

    # Construir PDF
    doc.build(elements)

    buffer.seek(0)
    return buffer.read()


# ============================================================
# Secciones del reporte
# ============================================================

def _build_header(
    datos: dict[str, Any],
    style_title: ParagraphStyle,
    style_subtitle: ParagraphStyle,
) -> list:
    """Construye el encabezado institucional con logo."""

    elements = []
    empleado = datos["empleado"]
    fecha_inicio = datos["fecha_inicio"]
    fecha_fin = datos["fecha_fin"]

    logo_path = obtener_logo_path()

    # Configuración institucional real (Configuración > Datos
    # institucionales). Nunca hardcodear aquí un nombre de institución
    # real: si no se ha configurado nada, se usan valores neutros.
    config_institucional = obtener_configuracion_institucional()
    institution_name = config_institucional["nombre_institucion"]
    unit_name = config_institucional["nombre_corto"]

    title_content = []
    title_content.append(Paragraph(institution_name, ParagraphStyle(
        "InstName", fontName="Helvetica-Bold", fontSize=10,
        textColor=COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=1 * mm,
    )))
    if unit_name:
        title_content.append(Paragraph(unit_name, ParagraphStyle(
            "UnitName", fontName="Helvetica", fontSize=9,
            textColor=COLOR_TEXT, alignment=TA_CENTER, spaceAfter=2 * mm,
        )))
    title_content.append(Paragraph(
        "Reporte de Incidencias por Empleado",
        style_title,
    ))
    title_content.append(Paragraph(
        f"Periodo: {_format_date(fecha_inicio)} al {_format_date(fecha_fin)}",
        style_subtitle,
    ))

    if logo_path:
        try:
            logo_img = Image(str(logo_path), width=2.2 * cm, height=2.2 * cm)
            logo_img.hAlign = "CENTER"

            header_table_data = [[logo_img, title_content]]
            header_table = Table(
                header_table_data,
                colWidths=[3 * cm, 15.5 * cm],
            )
            header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(header_table)
        except Exception:
            # Si falla el logo, solo poner texto
            elements.extend(title_content)
    else:
        elements.extend(title_content)

    # Línea separadora
    elements.append(Spacer(1, 2 * mm))
    separator = Table(
        [[""]],
        colWidths=[18.5 * cm],
        rowHeights=[0.5 * mm],
    )
    separator.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_PRIMARY),
        ("LINEBELOW", (0, 0), (-1, -1), 0, COLOR_PRIMARY),
    ]))
    elements.append(separator)
    elements.append(Spacer(1, 3 * mm))

    return elements


def _build_employee_info_table(
    datos: dict[str, Any],
    style_label: ParagraphStyle,
    style_value: ParagraphStyle,
) -> Table:
    """Construye tabla con datos del empleado."""

    empleado = datos["empleado"]
    horario = datos.get("horario")

    info_pairs = [
        ("Clave:", empleado.get("codigo_empleado") or "—"),
        ("Nombre:", empleado.get("nombre_completo") or "—"),
        ("RFC:", empleado.get("rfc") or "No registrado"),
        ("Área:", empleado.get("unidad_organizacional") or "—"),
        ("Puesto:", empleado.get("puesto") or "No asignado"),
        ("Horario:", horario.get("horario_nombre") if horario else "Sin horario"),
        ("Turno:", horario.get("tipo_turno_nombre") if horario else "—"),
        (
            "Horario detalle:",
            f"{_format_time(horario.get('hora_entrada'))} - {_format_time(horario.get('hora_salida'))}"
            if horario else "—"
        ),
    ]

    # 2 columnas de pares label-value
    table_data = []
    for i in range(0, len(info_pairs), 2):
        row = []
        pair1 = info_pairs[i]
        row.append(Paragraph(pair1[0], style_label))
        row.append(Paragraph(str(pair1[1]), style_value))

        if i + 1 < len(info_pairs):
            pair2 = info_pairs[i + 1]
            row.append(Paragraph(pair2[0], style_label))
            row.append(Paragraph(str(pair2[1]), style_value))
        else:
            row.extend(["", ""])

        table_data.append(row)

    table = Table(
        table_data,
        colWidths=[2.5 * cm, 6.5 * cm, 2.5 * cm, 6.5 * cm],
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_HEADER_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    return table


def _build_daily_table(datos: dict[str, Any]) -> Table:
    """Construye la tabla diaria de asistencia."""

    asistencias = datos.get("asistencias", [])
    incidencias = datos.get("incidencias", [])

    # Indexar incidencias por fecha
    incidencias_por_fecha: dict[str, list] = {}
    for inc in incidencias:
        fecha_key = str(inc.get("fecha", ""))
        incidencias_por_fecha.setdefault(fecha_key, []).append(inc)

    # Header
    header = [
        "Fecha", "Día", "Entrada", "Salida",
        "T. Ordinario", "T. Extra", "Retardo",
        "Estado", "Incidencia", "Puntos", "Revisión",
    ]

    cell_style = ParagraphStyle(
        "Cell", fontName="Helvetica", fontSize=7,
        textColor=COLOR_TEXT, leading=9,
    )

    header_style = ParagraphStyle(
        "HeaderCell", fontName="Helvetica-Bold", fontSize=7,
        textColor=COLOR_TABLE_HEADER_TEXT, leading=9,
    )

    table_data = [[Paragraph(h, header_style) for h in header]]

    for a in asistencias:
        fecha = a.get("fecha")
        estatus = (a.get("estatus") or "").upper()
        fecha_str = str(fecha) if fecha else ""

        # Buscar incidencia del día
        incs_dia = incidencias_por_fecha.get(fecha_str, [])
        inc_text = ""
        if incs_dia:
            inc_text = incs_dia[0].get("tipo_nombre") or incs_dia[0].get("tipo_codigo") or ""

        row = [
            Paragraph(_format_date(fecha), cell_style),
            Paragraph(_format_day_name(fecha), cell_style),
            Paragraph(_format_time(a.get("primera_entrada")), cell_style),
            Paragraph(_format_time(a.get("ultima_salida")), cell_style),
            Paragraph(_format_minutes_as_hours(int(a.get("minutos_ordinarios") or 0)), cell_style),
            Paragraph(_format_minutes_as_hours(int(a.get("minutos_extra") or 0)), cell_style),
            Paragraph(f"{int(a.get('minutos_retardo') or 0)}m" if int(a.get("minutos_retardo") or 0) > 0 else "—", cell_style),
            Paragraph(_format_status(estatus), cell_style),
            Paragraph(inc_text or "—", cell_style),
            Paragraph(str(int(a.get("puntos_generados") or 0)), cell_style),
            Paragraph("Sí" if a.get("requiere_revision") else "—", cell_style),
        ]
        table_data.append(row)

    if not asistencias:
        table_data.append([Paragraph("Sin registros de asistencia en este periodo.", cell_style)] + [""] * 10)

    col_widths = [
        2.0 * cm,   # Fecha
        1.2 * cm,   # Día
        1.5 * cm,   # Entrada
        1.5 * cm,   # Salida
        1.7 * cm,   # T. Ordinario
        1.4 * cm,   # T. Extra
        1.3 * cm,   # Retardo
        1.8 * cm,   # Estado
        2.6 * cm,   # Incidencia
        1.1 * cm,   # Puntos
        1.4 * cm,   # Revisión
    ]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Estilo de tabla
    style_commands = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_TABLE_HEADER_TEXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # Body
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),

        # Borders
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_PRIMARY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
    ]

    # Alternate row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_commands.append(
                ("BACKGROUND", (0, i), (-1, i), COLOR_ROW_ALT)
            )

    table.setStyle(TableStyle(style_commands))

    return table


def _build_summary_table(datos: dict[str, Any]) -> Table:
    """Construye la tabla de resumen estadístico."""

    resumen = datos.get("resumen", {})

    summary_pairs = [
        ("Total días procesados:", str(resumen.get("total_dias", 0))),
        ("Días completos:", str(resumen.get("dias_completos", 0))),
        ("Tolerancia:", str(resumen.get("tolerancias", 0))),
        ("Retardos menores:", str(resumen.get("retardos_menores", 0))),
        ("Retardos mayores:", str(resumen.get("retardos_mayores", 0))),
        ("Faltas:", str(resumen.get("faltas", 0))),
        ("Omisiones de entrada:", str(resumen.get("omisiones_entrada", 0))),
        ("Omisiones de salida:", str(resumen.get("omisiones_salida", 0))),
        ("Días no laborales:", str(resumen.get("dias_no_laborales", 0))),
        ("Días que requieren revisión:", str(resumen.get("dias_requieren_revision", 0))),
        ("Total horas ordinarias:", f"{resumen.get('total_horas_ordinarias', 0)} hrs"),
        ("Total horas extra:", f"{resumen.get('total_horas_extra', 0)} hrs"),
        ("Total minutos retardo:", f"{resumen.get('total_minutos_retardo', 0)} min"),
        ("Puntos acumulados:", str(resumen.get("puntos_totales", 0))),
        ("Total incidencias:", str(resumen.get("total_incidencias", 0))),
        ("Incidencias justificadas:", str(resumen.get("incidencias_justificadas", 0))),
        ("Incidencias pendientes:", str(resumen.get("incidencias_pendientes", 0))),
    ]

    label_style = ParagraphStyle(
        "SummaryLabel", fontName="Helvetica-Bold", fontSize=8,
        textColor=COLOR_TEXT_MUTED, leading=11,
    )
    value_style = ParagraphStyle(
        "SummaryValue", fontName="Helvetica-Bold", fontSize=8,
        textColor=COLOR_TEXT, leading=11,
    )

    # 2 columnas de resumen
    table_data = []
    for i in range(0, len(summary_pairs), 2):
        row = []
        p1 = summary_pairs[i]
        row.append(Paragraph(p1[0], label_style))
        row.append(Paragraph(p1[1], value_style))

        if i + 1 < len(summary_pairs):
            p2 = summary_pairs[i + 1]
            row.append(Paragraph(p2[0], label_style))
            row.append(Paragraph(p2[1], value_style))
        else:
            row.extend(["", ""])

        table_data.append(row)

    table = Table(
        table_data,
        colWidths=[4 * cm, 3 * cm, 4 * cm, 3 * cm],
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_HEADER_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, COLOR_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    return table
