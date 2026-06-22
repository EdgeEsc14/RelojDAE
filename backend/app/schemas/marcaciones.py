from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class MarcacionListadoItem(BaseModel):
    id: int

    fecha: date
    fecha_hora: datetime

    empleado_id: int | None = None
    codigo_empleado: str | None = None
    nombre_completo: str | None = None
    empleado_estatus: str | None = None

    empleado_dispositivo_id: int | None = None
    zk_user_id: str
    zk_uid: int | None = None
    nombre_en_dispositivo: str | None = None

    dispositivo_id: int
    dispositivo_codigo: str | None = None
    dispositivo_nombre: str | None = None
    dispositivo_ip: str | None = None
    dispositivo_puerto: int | None = None

    tipo_marcacion_id: int
    tipo_marcacion_codigo: str | None = None
    tipo_marcacion_nombre: str | None = None
    tipo_marcacion_categoria: str | None = None
    es_entrada: bool | None = None
    es_salida: bool | None = None
    es_tiempo_extra: bool | None = None

    punch_original: int | None = None
    estado_verificacion: int | None = None
    codigo_trabajo: str | None = None
    origen: str

    raw_data: Any | None = None

    procesada: bool
    fecha_procesamiento: datetime | None = None
    observaciones: str | None = None

    sincronizacion_id: int | None = None
    sincronizacion_estatus: str | None = None
    sincronizacion_tipo: str | None = None

    fecha_sincronizacion: datetime
    fecha_creacion: datetime


class MarcacionesListadoResponse(BaseModel):
    total: int
    fecha: date | None = None
    limit: int
    offset: int
    items: list[MarcacionListadoItem]