from __future__ import annotations

import ipaddress
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.repositories.auth_repo import (
    actualizar_password_propio,
    actualizar_ultimo_login,
    obtener_usuario_por_correo,
    obtener_usuario_por_id,
    registrar_login_auditoria,
)
from app.schemas.auth import (
    AuthChangePasswordRequest,
    AuthLoginRequest,
    AuthTokenResponse,
    AuthUserResponse,
)


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
        requiere_cambio_password=bool(user.get("requiere_cambio_password")),
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
            estatus_usuario = str(
                user.get("estatus") or ""
            ).strip().upper()

            # Debe coincidir con ck_login_auditoria_resultado (migración
            # 055): solo BLOQUEADO y PENDIENTE_* son valores válidos
            # idénticos al estatus; cualquier otro (INACTIVO, RECHAZADO,
            # etc.) debe mapearse a USUARIO_INACTIVO para no violar el
            # CHECK constraint al registrar la auditoría.
            resultados_identicos_a_estatus = {
                "PENDIENTE_VERIFICACION",
                "PENDIENTE_APROBACION",
                "BLOQUEADO",
            }

            resultado = (
                estatus_usuario
                if estatus_usuario in resultados_identicos_a_estatus
                else "USUARIO_INACTIVO"
            )

            registrar_login_auditoria(
                db=db,
                usuario_id=user["id"],
                correo_intentado=correo,
                resultado=resultado,
                motivo=f"USUARIO_{estatus_usuario or 'SIN_ESTATUS'}",
                **context,
            )

            db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario no se encuentra activo.",
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


@router.post("/change-password", response_model=AuthUserResponse)
def change_password(
    payload: AuthChangePasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Cambio de contraseña autoservicio (requiere la contraseña actual).

    No pasa por require_module_access: debe seguir siendo alcanzable
    aunque requiere_cambio_password esté en TRUE, para que el primer
    login pueda completarse. Tras el cambio, requiere_cambio_password
    queda en FALSE y la contraseña temporal anterior deja de servir
    (su hash se sobrescribe).
    """
    if not verify_password(payload.password_actual, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La contraseña actual no es correcta.",
        )

    if payload.password_nueva == payload.password_actual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente de la actual.",
        )

    actualizar_password_propio(
        db=db,
        usuario_id=current_user["id"],
        password_hash=hash_password(payload.password_nueva),
    )

    fresh_user = obtener_usuario_por_id(db=db, usuario_id=current_user["id"])

    return _public_user(fresh_user)