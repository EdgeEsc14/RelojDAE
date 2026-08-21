"""Schemas para el módulo de Auditoría (solo lectura)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BitacoraEventoResumen(BaseModel):
    id: int
    fecha_evento: datetime
    esquema: str
    tabla: str
    objeto: str
    operacion: str
    registro_id: str | None = None
    usuario_app_id: int | None = None
    usuario_app_correo: str | None = None
    usuario_bd: str
    ip_origen: str | None = None
    modulo: str | None = None
    accion_app: str | None = None
    cambios: dict[str, Any] | None = None


class BitacoraListadoResponse(BaseModel):
    total: int
    items: list[BitacoraEventoResumen]


class BitacoraEventoDetalle(BaseModel):
    id: int
    fecha_evento: datetime
    esquema: str
    tabla: str
    operacion: str
    registro_id: str | None = None
    usuario_app_id: int | None = None
    usuario_app_correo: str | None = None
    usuario_bd: str
    ip_origen: str | None = None
    modulo: str | None = None
    accion_app: str | None = None
    datos_anteriores: dict[str, Any] | None = None
    datos_nuevos: dict[str, Any] | None = None
    cambios: dict[str, Any] | None = None


class BitacoraFiltrosResponse(BaseModel):
    esquemas: list[str]
    tablas: list[str]


class LoginEventoResumen(BaseModel):
    id: int
    fecha_evento: datetime
    usuario_id: int | None = None
    usuario_correo: str | None = None
    usuario_rol: str | None = None
    correo_intentado: str | None = None
    resultado: str
    motivo: str | None = None
    ip_origen_raw: str | None = None
    user_agent: str | None = None


class LoginListadoResponse(BaseModel):
    total: int
    items: list[LoginEventoResumen]


class AuditoriaResumenBitacora(BaseModel):
    total: int
    inserts: int
    updates: int
    deletes: int
    cambios_seguridad: int


class AuditoriaResumenLogin(BaseModel):
    total: int
    exitosos: int
    fallidos: int
    bloqueados: int


class AuditoriaResumenResponse(BaseModel):
    fecha_inicio: str
    fecha_fin: str
    bitacora: AuditoriaResumenBitacora
    login: AuditoriaResumenLogin
