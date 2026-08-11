"""
Schemas Pydantic para el módulo de gestión de usuarios del sistema.

Maneja la creación, edición, listado y respuesta de usuarios.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UsuarioCreateRequest(BaseModel):
    """Payload para crear un usuario del sistema."""

    correo_electronico: str = Field(
        min_length=5,
        max_length=150,
        description="Correo electrónico del usuario (se usa para login).",
    )
    password: str = Field(
        min_length=8,
        max_length=200,
        description="Contraseña inicial del usuario.",
    )
    rol_id: int = Field(
        description="ID del rol a asignar (de seguridad.roles).",
    )
    nombre_usuario: str | None = Field(
        default=None,
        max_length=80,
        description="Nombre de usuario opcional. Si no se envía se genera del correo.",
    )
    empleado_id: int | None = Field(
        default=None,
        description="ID del empleado a vincular. Opcional para cuentas técnicas.",
    )
    requiere_cambio_password: bool = Field(
        default=True,
        description="Si el usuario debe cambiar contraseña al primer login.",
    )

    @field_validator("correo_electronico")
    @classmethod
    def validar_correo(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Formato de correo electrónico inválido.")
        return v

    @field_validator("nombre_usuario")
    @classmethod
    def validar_nombre_usuario(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if not v:
            return None
        return v


class UsuarioUpdateRequest(BaseModel):
    """Payload para actualizar un usuario existente."""

    correo_electronico: str | None = Field(
        default=None,
        min_length=5,
        max_length=150,
    )
    rol_id: int | None = Field(default=None)
    nombre_usuario: str | None = Field(
        default=None,
        max_length=80,
    )
    empleado_id: int | None = Field(default=None)
    estatus: str | None = Field(
        default=None,
        description="Nuevo estatus: ACTIVO, INACTIVO, BLOQUEADO.",
    )
    requiere_cambio_password: bool | None = Field(default=None)
    nueva_password: str | None = Field(
        default=None,
        min_length=8,
        max_length=200,
        description="Nueva contraseña. Se hashea antes de guardar.",
    )

    @field_validator("correo_electronico")
    @classmethod
    def validar_correo(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Formato de correo electrónico inválido.")
        return v

    @field_validator("estatus")
    @classmethod
    def validar_estatus(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        validos = {"ACTIVO", "INACTIVO", "BLOQUEADO"}
        if v not in validos:
            raise ValueError(f"Estatus debe ser uno de: {', '.join(sorted(validos))}")
        return v


class UsuarioResponse(BaseModel):
    """Respuesta completa de un usuario del sistema."""

    id: int
    correo_electronico: str
    nombre_usuario: str | None = None
    rol_id: int
    rol_codigo: str
    rol_nombre: str
    empleado_id: int | None = None
    codigo_empleado: str | None = None
    nombre_empleado: str | None = None
    estatus: str
    activo: bool
    requiere_cambio_password: bool
    ultimo_login: datetime | None = None
    fecha_creacion: datetime | None = None
    fecha_modificacion: datetime | None = None


class UsuarioListResponse(BaseModel):
    """Respuesta paginada para listado de usuarios."""

    items: list[UsuarioResponse]
    total: int
    page: int
    page_size: int


class RolResponse(BaseModel):
    """Respuesta para catálogo de roles."""

    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    es_sistema: bool
    activo: bool
