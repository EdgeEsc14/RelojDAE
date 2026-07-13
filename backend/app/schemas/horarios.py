from datetime import datetime, time

from pydantic import BaseModel, Field


class HorarioCreate(BaseModel):
    codigo: str = Field(min_length=2, max_length=30)
    nombre: str = Field(min_length=2, max_length=120)
    descripcion: str | None = Field(default=None, max_length=300)

    tipo_turno_id: int

    hora_entrada: time
    hora_salida: time

    tolerancia_entrada_minutos: int = Field(default=10, ge=0, le=240)
    descanso_minutos: int = Field(default=0, ge=0, le=240)
    permite_tiempo_extra: bool = True
    activo: bool = True


class HorarioEstatusUpdate(BaseModel):
    activo: bool


class HorarioResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None

    tolerancia_entrada_minutos: int
    descanso_minutos: int
    permite_tiempo_extra: bool
    activo: bool

    tipo_turno_id: int
    hora_entrada: time
    hora_salida: time

    tipo_turno_codigo: str
    tipo_turno_nombre: str
    hora_entrada_desde: time | None = None
    hora_entrada_hasta: time | None = None
    duracion_jornada_minutos: int
    modalidad_tiempo_extra: str

    empleados_asignados: int = 0

    fecha_creacion: datetime | None = None
    fecha_modificacion: datetime | None = None

class HorariosListadoResponse(BaseModel):
    total: int
    items: list[HorarioResponse]