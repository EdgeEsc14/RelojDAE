"""Schemas para configuración institucional (branding)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConfiguracionInstitucionalResponse(BaseModel):
    nombre_institucion: str
    nombre_corto: str
    pie_pagina: str


class ConfiguracionInstitucionalUpdate(BaseModel):
    nombre_institucion: str = Field(..., min_length=1, max_length=200)
    nombre_corto: str = Field(default="", max_length=200)
    pie_pagina: str = Field(default="", max_length=500)
