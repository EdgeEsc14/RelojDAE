"""
Schemas Pydantic para el módulo de Calendario Laboral.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


TIPOS_EVENTO_VALIDOS = {
    "FESTIVO_OFICIAL",
    "DESCANSO_INSTITUCIONAL",
    "DESCANSO_SINDICAL",
    "VACACIONES",
    "INHABIL_ADMINISTRATIVO",
    "SUSPENSION_LABORES",
    "LABORABLE_EXTRAORDINARIO",
    "OTRO",
}

TIPOS_RECURRENCIA_VALIDOS = {
    "FECHA_ESPECIFICA",
    "ANUAL_FIJA",
    "PERIODO",
}


class CalendarioEventoCreateRequest(BaseModel):
    """Payload para crear un evento de calendario."""

    calendario_id: int | None = Field(
        default=None,
        description="ID del calendario. Si no se envía, se usa el activo.",
    )
    nombre: str = Field(min_length=1, max_length=200)
    descripcion: str | None = Field(default=None, max_length=700)
    tipo_evento: str = Field(description="Tipo de evento.")
    tipo_recurrencia: str = Field(description="Tipo de recurrencia.")
    fecha_inicio: date | None = Field(default=None)
    fecha_fin: date | None = Field(default=None)
    mes: int | None = Field(default=None, ge=1, le=12)
    dia: int | None = Field(default=None, ge=1, le=31)
    afecta_asistencia: bool = Field(default=True)
    es_laborable: bool = Field(default=False)
    prioridad: int = Field(default=50, ge=1, le=100)

    @field_validator("tipo_evento")
    @classmethod
    def validar_tipo_evento(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in TIPOS_EVENTO_VALIDOS:
            raise ValueError(f"tipo_evento debe ser uno de: {', '.join(sorted(TIPOS_EVENTO_VALIDOS))}")
        return v

    @field_validator("tipo_recurrencia")
    @classmethod
    def validar_tipo_recurrencia(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in TIPOS_RECURRENCIA_VALIDOS:
            raise ValueError(
                f"tipo_recurrencia debe ser uno de: {', '.join(sorted(TIPOS_RECURRENCIA_VALIDOS))}"
            )
        return v


class CalendarioEventoUpdateRequest(BaseModel):
    """Payload para actualizar un evento de calendario."""

    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    descripcion: str | None = Field(default=None, max_length=700)
    tipo_evento: str | None = Field(default=None)
    tipo_recurrencia: str | None = Field(default=None)
    fecha_inicio: date | None = Field(default=None)
    fecha_fin: date | None = Field(default=None)
    mes: int | None = Field(default=None, ge=1, le=12)
    dia: int | None = Field(default=None, ge=1, le=31)
    afecta_asistencia: bool | None = Field(default=None)
    es_laborable: bool | None = Field(default=None)
    prioridad: int | None = Field(default=None, ge=1, le=100)
    activo: bool | None = Field(default=None)

    @field_validator("tipo_evento")
    @classmethod
    def validar_tipo_evento(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if v not in TIPOS_EVENTO_VALIDOS:
            raise ValueError(f"tipo_evento debe ser uno de: {', '.join(sorted(TIPOS_EVENTO_VALIDOS))}")
        return v

    @field_validator("tipo_recurrencia")
    @classmethod
    def validar_tipo_recurrencia(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if v not in TIPOS_RECURRENCIA_VALIDOS:
            raise ValueError(
                f"tipo_recurrencia debe ser uno de: {', '.join(sorted(TIPOS_RECURRENCIA_VALIDOS))}"
            )
        return v


class CalendarioEventoResponse(BaseModel):
    """Respuesta de un evento de calendario."""

    id: int
    calendario_id: int
    nombre: str
    descripcion: str | None = None
    tipo_evento: str
    tipo_recurrencia: str
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    mes: int | None = None
    dia: int | None = None
    afecta_asistencia: bool
    es_laborable: bool
    prioridad: int
    activo: bool
    fecha_creacion: datetime | None = None
    fecha_modificacion: datetime | None = None


class CalendarioEventoListResponse(BaseModel):
    """Respuesta paginada de eventos."""

    items: list[CalendarioEventoResponse]
    total: int
    page: int
    page_size: int


class ConsultaDiaResponse(BaseModel):
    """Respuesta de la consulta de un día específico."""

    fecha: str
    es_laborable: bool
    fuente: str
    eventos: list[dict]
