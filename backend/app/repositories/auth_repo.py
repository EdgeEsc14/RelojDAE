from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _normalize_role(value: Any) -> str:
    value_text = _clean_text(value).lower()

    if value_text == "super_admin":
        return "super_admin"

    if value_text == "rh_admin":
        return "rh_admin"

    if value_text == "supervisor":
        return "supervisor"

    if value_text == "empleado":
        return "empleado"

    if value_text == "auditor":
        return "auditor"

    value_text = value_text.replace("-", "_").replace(" ", "_")

    return value_text


def _user_from_row(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None

    rol = _normalize_role(
        row["rol_codigo"]
        or row["rol"]
    )

    return {
        "id": row["id"],
        "empleado_id": row["empleado_id"],
        "correo": row["correo"] or row["correo_electronico"],
        "correo_electronico": row["correo_electronico"],
        "nombre_usuario": row["nombre_usuario"],
        "password_hash": row["password_hash"],
        "rol_id": row["rol_id"],
        "rol": rol,
        "rol_codigo": row["rol_codigo"],
        "rol_nombre": row["rol_nombre"],
        "estatus": row["estatus"],
        "correo_verificado": bool(row["correo_verificado"]),
        "requiere_cambio_password": bool(row["requiere_cambio_password"]),
        "codigo_empleado": row["codigo_empleado"],
        "nombre_empleado": row["nombre_empleado"],
    }


def obtener_usuario_por_correo(
    *,
    db: Session,
    correo: str,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            u.id,
            u.empleado_id,
            u.correo,
            u.correo_electronico,
            u.nombre_usuario,
            u.password_hash,
            u.rol_id,
            u.rol,
            r.codigo AS rol_codigo,
            r.nombre AS rol_nombre,
            u.estatus,
            u.correo_verificado,
            u.requiere_cambio_password,
            e.codigo_empleado,
            e.nombre_completo AS nombre_empleado
        FROM seguridad.usuarios u
        LEFT JOIN seguridad.roles r
            ON r.id = u.rol_id
        LEFT JOIN personal.empleados e
            ON e.id = u.empleado_id
        WHERE LOWER(u.correo) = LOWER(:correo)
           OR LOWER(u.correo_electronico) = LOWER(:correo)
        LIMIT 1
        """
    )

    row = db.execute(query, {"correo": correo}).mappings().first()

    return _user_from_row(row)


def obtener_usuario_por_id(
    *,
    db: Session,
    usuario_id: int,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            u.id,
            u.empleado_id,
            u.correo,
            u.correo_electronico,
            u.nombre_usuario,
            u.password_hash,
            u.rol_id,
            u.rol,
            r.codigo AS rol_codigo,
            r.nombre AS rol_nombre,
            u.estatus,
            u.correo_verificado,
            u.requiere_cambio_password,
            e.codigo_empleado,
            e.nombre_completo AS nombre_empleado
        FROM seguridad.usuarios u
        LEFT JOIN seguridad.roles r
            ON r.id = u.rol_id
        LEFT JOIN personal.empleados e
            ON e.id = u.empleado_id
        WHERE u.id = :usuario_id
        LIMIT 1
        """
    )

    row = db.execute(query, {"usuario_id": usuario_id}).mappings().first()

    return _user_from_row(row)


def actualizar_ultimo_login(
    *,
    db: Session,
    usuario_id: int,
    ip_origen: str | None,
    ip_origen_raw: str | None,
    user_agent: str | None,
) -> None:
    query = text(
        """
        UPDATE seguridad.usuarios
        SET
            ultimo_login = NOW(),
            ultimo_login_ip = CAST(:ip_origen AS inet),
            ultimo_login_ip_raw = :ip_origen_raw,
            ultimo_login_user_agent = :user_agent,
            fecha_modificacion = NOW()
        WHERE id = :usuario_id
        """
    )

    db.execute(
        query,
        {
            "usuario_id": usuario_id,
            "ip_origen": ip_origen,
            "ip_origen_raw": ip_origen_raw,
            "user_agent": user_agent,
        },
    )


def registrar_login_auditoria(
    *,
    db: Session,
    usuario_id: int | None,
    correo_intentado: str,
    resultado: str,
    motivo: str | None,
    ip_origen: str | None,
    ip_origen_raw: str | None,
    forwarded_for: str | None,
    user_agent: str | None,
    metodo_http: str | None,
    ruta: str | None,
) -> None:
    query = text(
        """
        INSERT INTO seguridad.login_auditoria (
            usuario_id,
            correo_intentado,
            resultado,
            motivo,
            ip_origen,
            ip_origen_raw,
            forwarded_for,
            user_agent,
            metodo_http,
            ruta,
            fecha_evento
        )
        VALUES (
            :usuario_id,
            :correo_intentado,
            :resultado,
            :motivo,
            CAST(:ip_origen AS inet),
            :ip_origen_raw,
            :forwarded_for,
            :user_agent,
            :metodo_http,
            :ruta,
            NOW()
        )
        """
    )

    db.execute(
        query,
        {
            "usuario_id": usuario_id,
            "correo_intentado": correo_intentado,
            "resultado": resultado,
            "motivo": motivo,
            "ip_origen": ip_origen,
            "ip_origen_raw": ip_origen_raw,
            "forwarded_for": forwarded_for,
            "user_agent": user_agent,
            "metodo_http": metodo_http,
            "ruta": ruta,
        },
    )