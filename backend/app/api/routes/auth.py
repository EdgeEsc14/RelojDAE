from __future__ import annotations

import ipaddress
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, verify_password
from app.repositories.auth_repo import (
    actualizar_ultimo_login,
    obtener_usuario_por_correo,
    obtener_usuario_por_id,
    registrar_login_auditoria,
)
from app.schemas.auth import AuthLoginRequest, AuthTokenResponse, AuthUserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


def _clean_text(value) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _normalize_ip(value: str | None) -> str | None:
    value_text = _clean_text(value)

    if not value_text:
        return None

    try:
        return str(ipaddress.ip_address(value_text))
    except ValueError:
        return None


def _get_request_context(request: Request) -> dict:
    forwarded_for = request.headers.get("x-forwarded-for")
    user_agent = request.headers.get("user-agent")
    client_host = request.client.host if request.client else None

    ip_raw = None

    if forwarded_for:
        ip_raw = forwarded_for.split(",")[0].strip()
    else:
        ip_raw = client_host

    return {
        "ip_origen": _normalize_ip(ip_raw),
        "ip_origen_raw": ip_raw,
        "forwarded_for": forwarded_for,
        "user_agent": user_agent,
        "metodo_http": request.method,
        "ruta": str(request.url.path),
    }


def _public_user(user: dict) -> AuthUserResponse:
    return AuthUserResponse(
        id=user["id"],
        correo=user["correo"],
        nombre_usuario=user["nombre_usuario"],
        rol_id=user["rol_id"],
        rol=user["rol"],
        rol_codigo=user["rol_codigo"],
        rol_nombre=user["rol_nombre"],
        estatus=user["estatus"],
        correo_verificado=user["correo_verificado"],
        empleado_id=user["empleado_id"],
        codigo_empleado=user["codigo_empleado"],
        nombre_empleado=user["nombre_empleado"],
    )


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado.",
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )

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


@router.post("/login", response_model=AuthTokenResponse)
def login(
    payload: AuthLoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    correo = _clean_text(payload.correo).lower()
    context = _get_request_context(request)

    user = obtener_usuario_por_correo(
        db=db,
        correo=correo,
    )

    try:
        if not user:
            registrar_login_auditoria(
                db=db,
                usuario_id=None,
                correo_intentado=correo,
                resultado="FALLIDO",
                motivo="USUARIO_NO_EXISTE",
                **context,
            )
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas.",
            )

        if user["estatus"] != "ACTIVO":
            resultado = user["estatus"]

            if resultado not in {
                "PENDIENTE_VERIFICACION",
                "PENDIENTE_APROBACION",
                "USUARIO_INACTIVO",
                "BLOQUEADO",
            }:
                resultado = "USUARIO_INACTIVO"

            registrar_login_auditoria(
                db=db,
                usuario_id=user["id"],
                correo_intentado=correo,
                resultado=resultado,
                motivo=f"USUARIO_{user['estatus']}",
                **context,
            )
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Usuario no activo. Estatus: {user['estatus']}.",
            )

        if not verify_password(payload.password, user["password_hash"]):
            registrar_login_auditoria(
                db=db,
                usuario_id=user["id"],
                correo_intentado=correo,
                resultado="FALLIDO",
                motivo="PASSWORD_INCORRECTO",
                **context,
            )
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas.",
            )

        actualizar_ultimo_login(
            db=db,
            usuario_id=user["id"],
            ip_origen=context["ip_origen"],
            ip_origen_raw=context["ip_origen_raw"],
            user_agent=context["user_agent"],
        )

        registrar_login_auditoria(
            db=db,
            usuario_id=user["id"],
            correo_intentado=correo,
            resultado="EXITOSO",
            motivo="LOGIN_OK",
            **context,
        )

        db.commit()

        token = create_access_token(
            {
                "sub": str(user["id"]),
                "correo": user["correo"],
                "rol": user["rol"],
            }
        )

        fresh_user = obtener_usuario_por_id(
            db=db,
            usuario_id=user["id"],
        )

        return AuthTokenResponse(
            access_token=token,
            token_type="bearer",
            user=_public_user(fresh_user),
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        print("\nERROR REAL EN LOGIN:")
        print(type(exc))
        print(str(exc))
        print("\n")

        try:
            registrar_login_auditoria(
                db=db,
                usuario_id=user["id"] if user else None,
                correo_intentado=correo,
                resultado="ERROR",
                motivo=str(exc)[:100],
                **context,
            )
            db.commit()
        except Exception as audit_exc:
            db.rollback()
            print("\nERROR GUARDANDO AUDITORIA:")
            print(type(audit_exc))
            print(str(audit_exc))
            print("\n")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al iniciar sesión.",
        ) from exc

@router.get("/me", response_model=AuthUserResponse)
def me(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return _public_user(current_user)