"""
Schemas Pydantic para el módulo de incidencias.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class IncidenciaListItem(BaseModel):
    """Elemento de la lista de incidencias."""

    id: int
    empleado_id: int
    codigo_empleado: str
    nombre_empleado: str
    departamento: str | None = None
    tipo_incidencia_id: int
    tipo_codigo: str
    tipo_nombre: str
    tipo_categoria: str
    fecha: date
    descripcion: str | None = None
    puntos_originales: int
    puntos_justificados: int
    puntos_efectivos: int
    estatus: str
    origen: str
    requiere_revision: bool
    fecha_creacion: datetime | None = None
    fecha_revision: datetime | None = None


class IncidenciaListResponse(BaseModel):
    """Respuesta paginada de incidencias."""

    items: list[IncidenciaListItem]
    total: int
    page: int
    page_size: int


class IncidenciaDetailResponse(BaseModel):
    """Detalle completo de una incidencia."""

    id: int
    empleado_id: int
    codigo_empleado: str
    nombre_empleado: str
    departamento: str | None = None
    tipo_incidencia_id: int
    tipo_codigo: str
    tipo_nombre: str
    tipo_categoria: str
    genera_puntos: bool
    requiere_justificacion: bool
    requiere_aprobacion: bool
    asistencia_diaria_id: int | None = None
    periodo_evaluacion_id: int | None = None
    fecha: date
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    descripcion: str | None = None
    puntos_originales: int
    puntos_justificados: int
    puntos_efectivos: int
    estatus: str
    origen: str
    requiere_revision: bool
    creada_por_usuario_id: int | None = None
    revisada_por_usuario_id: int | None = None
    fecha_revision: datetime | None = None
    comentario_revision: str | None = None
    fecha_creacion: datetime | None = None
    fecha_modificacion: datetime | None = None


class IncidenciaCreateRequest(BaseModel):
    """Payload para crear una incidencia manual."""

    empleado_id: int
    tipo_incidencia_id: int
    fecha: date
    descripcion: str | None = Field(default=None, max_length=700)
    puntos_originales: int = Field(default=0, ge=0)


class IncidenciaReviewRequest(BaseModel):
    """Payload para aprobar/rechazar una incidencia."""

    estatus: str = Field(
        description="Nuevo estatus: APROBADA, RECHAZADA, JUSTIFICADA o CANCELADA."
    )
    comentario_revision: str | None = Field(
        default=None,
        max_length=700,
        description="Comentario de la revisión.",
    )


class IncidenciasContadoresResponse(BaseModel):
    """Contadores de incidencias por estatus."""

    total: int = 0
    PENDIENTE: int = 0
    SIN_JUSTIFICAR: int = 0
    JUSTIFICADA: int = 0
    APROBADA: int = 0
    RECHAZADA: int = 0
    CANCELADA: int = 0
