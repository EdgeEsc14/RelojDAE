from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.core.access_control import (
    AccessScope,
    PermissionAction,
)
from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.access_repo import build_access_scope
from app.repositories.auth_repo import obtener_usuario_por_id


bearer_scheme = HTTPBearer(auto_error=False)


def normalize_role(value) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado.",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        ) from exc

    user = obtener_usuario_por_id(
        db=db,
        usuario_id=user_id,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado.",
        )

    if user["estatus"] != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no activo.",
        )

    return user


def require_roles(*allowed_roles: str):
    """
    Dependencia conservada para endpoints administrativos
    todavía no migrados al sistema modular de permisos.
    """

    allowed = {
        normalize_role(role)
        for role in allowed_roles
    }

    def dependency(
        current_user: Annotated[
            dict,
            Depends(get_current_user),
        ],
    ) -> dict:
        user_role = normalize_role(
            current_user.get("rol")
        )

        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No tienes permisos para realizar "
                    "esta acción."
                ),
            )

        return current_user

    return dependency


def require_module_access(
    module_code: str,
    action: PermissionAction = "consultar",
):
    """
    Verifica una acción y devuelve el alcance efectivo.

    Ejemplo:

        Depends(
            require_module_access(
                "EMPLEADOS",
                "consultar",
            )
        )

    El endpoint recibe un AccessScope ya resuelto y puede
    enviarlo al repositorio para limitar las consultas SQL.
    """

    def dependency(
        db: Annotated[
            Session,
            Depends(get_db),
        ],
        current_user: Annotated[
            dict,
            Depends(get_current_user),
        ],
    ) -> AccessScope:
        access_scope = build_access_scope(
            db=db,
            current_user=current_user,
            module_code=module_code,
        )

        if not access_scope.has_data_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No tienes acceso al módulo solicitado."
                ),
            )

        if not access_scope.allows(action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No tienes permiso para realizar "
                    "esta acción."
                ),
            )

        if (
            access_scope.data_scope == "PROPIO"
            and access_scope.employee_id is None
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "El usuario no está vinculado "
                    "a un empleado."
                ),
            )

        if (
            access_scope.data_scope == "AREA"
            and not access_scope.allowed_unit_ids
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "El usuario no tiene unidades "
                    "organizacionales activas asignadas."
                ),
            )

        return access_scope

    return dependency