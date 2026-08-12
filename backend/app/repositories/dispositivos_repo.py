"""
Repositorio para gestión de dispositivos ZKTeco.

CRUD completo sobre dispositivos.dispositivos.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


# ============================================================
# Listar dispositivos
# ============================================================


def listar_dispositivos(
    db: Session,
    *,
    activo: bool | None = None,
    busqueda: str | None = None,
) -> list[dict[str, Any]]:
    """Lista todos los dispositivos con filtros opcionales."""

    conditions: list[str] = []
    params: dict[str, Any] = {}

    if activo is not None:
        conditions.append("d.activo = :activo")
        params["activo"] = activo

    if busqueda:
        conditions.append(
            """
            (
                LOWER(d.nombre) LIKE :busqueda
                OR LOWER(d.codigo) LIKE :busqueda
                OR d.ip::text LIKE :busqueda
                OR LOWER(COALESCE(d.ubicacion, '')) LIKE :busqueda
                OR LOWER(COALESCE(d.modelo, '')) LIKE :busqueda
            )
            """
        )
        params["busqueda"] = f"%{busqueda.strip().lower()}%"

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(
        text(
            f"""
            SELECT
                d.id,
                d.codigo,
                d.nombre,
                HOST(d.ip) AS ip,
                d.puerto,
                d.password_comunicacion,
                d.numero_serie,
                d.modelo,
                d.firmware,
                d.ubicacion,
                d.descripcion,
                d.activo,
                d.estado_conexion,
                d.ultima_conexion,
                d.ultima_comprobacion,
                d.ultima_sincronizacion_marcaciones,
                d.ultima_sincronizacion_hora,
                d.ultimo_desfase_segundos,
                d.ultimo_resultado_hora,
                d.ultimo_error,
                d.ultimo_error_hora,
                d.fecha_creacion,
                d.fecha_modificacion
            FROM dispositivos.dispositivos d
            {where_clause}
            ORDER BY d.activo DESC, d.nombre ASC
            """
        ),
        params,
    ).mappings().all()

    return [dict(row) for row in rows]


# ============================================================
# Obtener por ID
# ============================================================


def obtener_dispositivo_por_id(
    db: Session,
    dispositivo_id: int,
) -> dict[str, Any] | None:
    """Obtiene un dispositivo por ID."""

    row = db.execute(
        text(
            """
            SELECT
                d.id,
                d.codigo,
                d.nombre,
                HOST(d.ip) AS ip,
                d.puerto,
                d.password_comunicacion,
                d.numero_serie,
                d.modelo,
                d.firmware,
                d.ubicacion,
                d.descripcion,
                d.activo,
                d.estado_conexion,
                d.ultima_conexion,
                d.ultima_comprobacion,
                d.ultima_sincronizacion_marcaciones,
                d.ultima_sincronizacion_hora,
                d.ultimo_desfase_segundos,
                d.ultimo_resultado_hora,
                d.ultimo_error,
                d.ultimo_error_hora,
                d.fecha_creacion,
                d.fecha_modificacion
            FROM dispositivos.dispositivos d
            WHERE d.id = :id
            """
        ),
        {"id": dispositivo_id},
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


# ============================================================
# Crear dispositivo
# ============================================================


def crear_dispositivo(
    db: Session,
    *,
    codigo: str,
    nombre: str,
    ip: str,
    puerto: int = 4370,
    password_comunicacion: int = 0,
    ubicacion: str | None = None,
    descripcion: str | None = None,
    modelo: str | None = None,
    numero_serie: str | None = None,
    firmware: str | None = None,
) -> dict[str, Any]:
    """Crea un nuevo dispositivo."""

    try:
        row = db.execute(
            text(
                """
                INSERT INTO dispositivos.dispositivos (
                    codigo, nombre, ip, puerto, password_comunicacion,
                    ubicacion, descripcion, modelo, numero_serie, firmware,
                    activo, estado_conexion
                )
                VALUES (
                    :codigo, :nombre, :ip::inet, :puerto, :password_comunicacion,
                    :ubicacion, :descripcion, :modelo, :numero_serie, :firmware,
                    TRUE, 'DESCONECTADO'
                )
                RETURNING id
                """
            ),
            {
                "codigo": codigo.strip().upper(),
                "nombre": nombre.strip(),
                "ip": ip.strip(),
                "puerto": puerto,
                "password_comunicacion": password_comunicacion,
                "ubicacion": ubicacion,
                "descripcion": descripcion,
                "modelo": modelo,
                "numero_serie": numero_serie,
                "firmware": firmware,
            },
        ).mappings().one()

        db.commit()
        return obtener_dispositivo_por_id(db, row["id"])

    except SQLAlchemyError:
        db.rollback()
        raise


# ============================================================
# Actualizar dispositivo
# ============================================================


def actualizar_dispositivo(
    db: Session,
    dispositivo_id: int,
    *,
    nombre: str | None = None,
    ip: str | None = None,
    puerto: int | None = None,
    password_comunicacion: int | None = None,
    ubicacion: str | None = None,
    descripcion: str | None = None,
    modelo: str | None = None,
    numero_serie: str | None = None,
    firmware: str | None = None,
    activo: bool | None = None,
) -> dict[str, Any] | None:
    """Actualiza un dispositivo existente."""

    current = obtener_dispositivo_por_id(db, dispositivo_id)
    if current is None:
        return None

    sets: list[str] = []
    params: dict[str, Any] = {"id": dispositivo_id}

    if nombre is not None:
        sets.append("nombre = :nombre")
        params["nombre"] = nombre.strip()

    if ip is not None:
        sets.append("ip = :ip::inet")
        params["ip"] = ip.strip()

    if puerto is not None:
        sets.append("puerto = :puerto")
        params["puerto"] = puerto

    if password_comunicacion is not None:
        sets.append("password_comunicacion = :password_comunicacion")
        params["password_comunicacion"] = password_comunicacion

    if ubicacion is not None:
        sets.append("ubicacion = :ubicacion")
        params["ubicacion"] = ubicacion if ubicacion else None

    if descripcion is not None:
        sets.append("descripcion = :descripcion")
        params["descripcion"] = descripcion if descripcion else None

    if modelo is not None:
        sets.append("modelo = :modelo")
        params["modelo"] = modelo if modelo else None

    if numero_serie is not None:
        sets.append("numero_serie = :numero_serie")
        params["numero_serie"] = numero_serie if numero_serie else None

    if firmware is not None:
        sets.append("firmware = :firmware")
        params["firmware"] = firmware if firmware else None

    if activo is not None:
        sets.append("activo = :activo")
        params["activo"] = activo
        if not activo:
            sets.append("estado_conexion = 'DESHABILITADO'")

    if not sets:
        return current

    sets.append("fecha_modificacion = CURRENT_TIMESTAMP")

    try:
        db.execute(
            text(f"UPDATE dispositivos.dispositivos SET {', '.join(sets)} WHERE id = :id"),
            params,
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_dispositivo_por_id(db, dispositivo_id)


# ============================================================
# Actualizar estado de conexión
# ============================================================


def actualizar_estado_conexion(
    db: Session,
    dispositivo_id: int,
    *,
    estado_conexion: str,
    ultimo_error: str | None = None,
    modelo: str | None = None,
    firmware: str | None = None,
    numero_serie: str | None = None,
) -> None:
    """Actualiza estado de conexión después de una comprobación."""

    sets = [
        "estado_conexion = :estado_conexion",
        "ultima_comprobacion = CURRENT_TIMESTAMP",
        "fecha_modificacion = CURRENT_TIMESTAMP",
    ]
    params: dict[str, Any] = {
        "id": dispositivo_id,
        "estado_conexion": estado_conexion,
    }

    if estado_conexion == "CONECTADO":
        sets.append("ultima_conexion = CURRENT_TIMESTAMP")
        sets.append("ultimo_error = NULL")
    else:
        sets.append("ultimo_error = :ultimo_error")
        params["ultimo_error"] = ultimo_error

    if modelo:
        sets.append("modelo = :modelo")
        params["modelo"] = modelo

    if firmware:
        sets.append("firmware = :firmware")
        params["firmware"] = firmware

    if numero_serie:
        sets.append("numero_serie = :numero_serie")
        params["numero_serie"] = numero_serie

    try:
        db.execute(
            text(f"UPDATE dispositivos.dispositivos SET {', '.join(sets)} WHERE id = :id"),
            params,
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise


# ============================================================
# Actualizar última sincronización
# ============================================================


def actualizar_ultima_sincronizacion(
    db: Session,
    dispositivo_id: int,
) -> None:
    """Registra que se realizó una sincronización exitosa."""

    try:
        db.execute(
            text(
                """
                UPDATE dispositivos.dispositivos
                SET ultima_sincronizacion_marcaciones = CURRENT_TIMESTAMP,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {"id": dispositivo_id},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
