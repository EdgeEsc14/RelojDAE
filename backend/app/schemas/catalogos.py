from datetime import datetime, time

from pydantic import BaseModel


class UnidadOrganizacionalCatalogoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    unidad_padre_id: int | None = None
    activo: bool
    tipo_unidad_id: int
    tipo_unidad_codigo: str | None = None
    tipo_unidad_nombre: str | None = None
    clave_organica: str | None = None
    orden_visual: int = 0


class PuestoCatalogoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    nivel_jerarquico: int
    activo: bool

class TipoContratacionCatalogoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    activo: bool

class TipoTurnoCatalogoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    hora_entrada_desde: time | None = None
    hora_entrada_hasta: time | None = None
    duracion_jornada_minutos: int
    modalidad_tiempo_extra: str
    activo: bool


class HorarioCatalogoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    tolerancia_entrada_minutos: int
    descanso_minutos: int
    permite_tiempo_extra: bool
    activo: bool
    tipo_turno_id: int
    tipo_turno_codigo: str | None = None
    tipo_turno_nombre: str | None = None


class DispositivoCatalogoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    ip: str
    puerto: int
    numero_serie: str | None = None
    modelo: str | None = None
    firmware: str | None = None
    ubicacion: str | None = None
    activo: bool
    ultima_conexion: datetime | None = None
    ultima_sincronizacion: datetime | None = None


class RolCatalogoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    es_sistema: bool
    orden_visual: int
    activo: bool


class TipoMarcacionCatalogoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    categoria: str
    es_entrada: bool
    es_salida: bool
    es_tiempo_extra: bool
    requiere_pareja: bool
    activo: bool


class TipoIncidenciaCatalogoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    categoria: str
    genera_puntos: bool
    puntos_default: int
    requiere_justificacion: bool
    requiere_aprobacion: bool
    afecta_asistencia: bool
    activo: bool
    orden_visual: int


class CatalogosTodosResponse(BaseModel):
    unidades_organizacionales: list[UnidadOrganizacionalCatalogoItem]
    puestos: list[PuestoCatalogoItem]
    tipos_turno: list[TipoTurnoCatalogoItem]
    horarios: list[HorarioCatalogoItem]
    dispositivos: list[DispositivoCatalogoItem]
    roles: list[RolCatalogoItem]
    tipos_marcacion: list[TipoMarcacionCatalogoItem]
    tipos_incidencia: list[TipoIncidenciaCatalogoItem]
    tipos_contratacion: list[TipoContratacionCatalogoItem]    