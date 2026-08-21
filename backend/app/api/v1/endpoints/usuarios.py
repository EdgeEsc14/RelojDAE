"""
Endpoints para gestión de usuarios del sistema.

CRUD completo protegido por módulo SEGURIDAD.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.core.auth_dependencies import require_module_access
from app.core.database import get_db
from app.repositories.usuarios_repo import (
    actualizar_usuario,
    crear_usuario,
    desactivar_usuario,
    listar_roles,
    listar_usuarios,
    obtener_usuario_por_id,
)
from app.schemas.usuarios import (
    RolResponse,
    UsuarioCreadoResponse,
    UsuarioCreateRequest,
    UsuarioListResponse,
    UsuarioResponse,
    UsuarioUpdateRequest,
)


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios del Sistema"],
)


# ============================================================
# GET /usuarios — Listar usuarios
# ============================================================


@router.get(
    "",
    response_model=UsuarioListResponse,
)
def get_usuarios(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("SEGURIDAD", "consultar")
        ),
    ],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    rol_id: int | None = Query(default=None),
    estatus: str | None = Query(default=None),
    busqueda: str | None = Query(default=None, max_length=100),
) -> dict:
    """Lista todos los usuarios del sistema con filtros opcionales."""

    resultado = listar_usuarios(
        db,
        page=page,
        page_size=page_size,
        rol_id=rol_id,
        estatus=estatus,
        busqueda=busqueda,
    )

    return resultado


# ============================================================
# GET /usuarios/roles — Catálogo de roles
# ============================================================


@router.get(
    "/roles",
    response_model=list[RolResponse],
)
def get_roles(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("SEGURIDAD", "consultar")
        ),
    ],
) -> list[dict]:
    """Retorna los roles activos del sistema."""

    return listar_roles(db)


# ============================================================
# GET /usuarios/{usuario_id} — Detalle de usuario
# ============================================================


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
)
def get_usuario(
    usuario_id: int,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("SEGURIDAD", "consultar")
        ),
    ],
) -> dict:
    """Obtiene el detalle de un usuario específico."""

    usuario = obtener_usuario_por_id(db, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe usuario con id {usuario_id}.",
        )

    return usuario


# ============================================================
# POST /usuarios — Crear usuario
# ============================================================


@router.post(
    "",
    response_model=UsuarioCreadoResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_crear_usuario(
    payload: UsuarioCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("SEGURIDAD", "crear")
        ),
    ],
) -> dict:
    """
    Crea un nuevo usuario del sistema.

    La contraseña es siempre una temporal generada por el backend
    (nunca provista por quien llama). Se devuelve en texto plano
    únicamente en esta respuesta, una sola vez.

    Solo SUPER_ADMIN y RH_ADMIN pueden crear cuentas; RH_ADMIN no puede
    crear cuentas con rol SUPER_ADMIN.
    """

    try:
        usuario = crear_usuario(
            db,
            actor_role_codigo=access_scope.role_code,
            correo_electronico=payload.correo_electronico,
            rol_id=payload.rol_id,
            nombre_usuario=payload.nombre_usuario,
            empleado_id=payload.empleado_id,
            requiere_cambio_password=payload.requiere_cambio_password,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return usuario


# ============================================================
# PATCH /usuarios/{usuario_id} — Editar usuario
# ============================================================


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioResponse,
)
def patch_usuario(
    usuario_id: int,
    payload: UsuarioUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("SEGURIDAD", "editar")
        ),
    ],
) -> dict:
    """
    Actualiza campos de un usuario existente.

    Solo SUPER_ADMIN y RH_ADMIN pueden administrar usuarios; RH_ADMIN no
    puede modificar una cuenta SUPER_ADMIN ni promover a nadie a ese rol.
    """

    try:
        usuario = actualizar_usuario(
            db,
            usuario_id,
            actor_role_codigo=access_scope.role_code,
            correo_electronico=payload.correo_electronico,
            rol_id=payload.rol_id,
            nombre_usuario=payload.nombre_usuario,
            empleado_id=payload.empleado_id,
            estatus=payload.estatus,
            requiere_cambio_password=payload.requiere_cambio_password,
            nueva_password=payload.nueva_password,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe usuario con id {usuario_id}.",
        )

    return usuario


# ============================================================
# DELETE /usuarios/{usuario_id} — Desactivar usuario
# ============================================================


@router.delete(
    "/{usuario_id}",
    response_model=UsuarioResponse,
)
def delete_usuario(
    usuario_id: int,
    db: Annotated[Session, Depends(get_db)],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access("SEGURIDAD", "eliminar")
        ),
    ],
) -> dict:
    """
    Desactiva un usuario (no lo elimina de la base de datos).

    Solo SUPER_ADMIN y RH_ADMIN pueden desactivar cuentas; RH_ADMIN no
    puede desactivar una cuenta SUPER_ADMIN.
    """

    try:
        usuario = desactivar_usuario(
            db, usuario_id, actor_role_codigo=access_scope.role_code
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe usuario con id {usuario_id}.",
        )

    return usuario
