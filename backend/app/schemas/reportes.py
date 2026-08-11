"""
Schemas Pydantic para el módulo de reportes.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ReporteEmpleadoRequest(BaseModel):
    """Parámetros para generar reporte individual de empleado."""

    fecha_inicio: date
    fecha_fin: date

    def model_post_init(self, __context) -> None:
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin no puede ser anterior a fecha_inicio.")


class ReporteDepartamentalRequest(BaseModel):
    """Parámetros para generar reporte departamental."""

    fecha_inicio: date
    fecha_fin: date
    unidad_organizacional_id: int | None = Field(
        default=None,
        description="Filtrar por departamento específico.",
    )

    def model_post_init(self, __context) -> None:
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin no puede ser anterior a fecha_inicio.")
