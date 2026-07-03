from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def obtener_empleado_por_codigo_para_zk(
    *,
    db: Session,
    codigo_empleado: str,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            id,
            codigo_empleado,
            nombres,
            apellido_paterno,
            apellido_materno,
            nombre_completo,
            correo,
            estatus,
            zk_user_id
        FROM personal.empleados
        WHERE codigo_empleado = :codigo_empleado
        LIMIT 1
        """
    )

    row = db.execute(
        query,
        {"codigo_empleado": codigo_empleado},
    ).mappings().first()

    if row is None:
        return None

    return {
        "id": row["id"],
        "codigo_empleado": row["codigo_empleado"],
        "nombres": row["nombres"],
        "apellido_paterno": row["apellido_paterno"],
        "apellido_materno": row["apellido_materno"],
        "nombre_completo": row["nombre_completo"],
        "correo": row["correo"],
        "estatus": row["estatus"],
        "zk_user_id": _clean_text(row["zk_user_id"]),
    }


def obtener_empleado_por_zk_user_id(
    *,
    db: Session,
    zk_user_id: str,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            id,
            codigo_empleado,
            nombre_completo,
            correo,
            estatus,
            zk_user_id
        FROM personal.empleados
        WHERE zk_user_id = :zk_user_id
        LIMIT 1
        """
    )

    row = db.execute(
        query,
        {"zk_user_id": zk_user_id},
    ).mappings().first()

    if row is None:
        return None

    return {
        "id": row["id"],
        "codigo_empleado": row["codigo_empleado"],
        "nombre_completo": row["nombre_completo"],
        "correo": row["correo"],
        "estatus": row["estatus"],
        "zk_user_id": _clean_text(row["zk_user_id"]),
    }


def vincular_empleado_con_zk_user_id(
    *,
    db: Session,
    codigo_empleado: str,
    zk_user_id: str,
) -> dict[str, Any]:
    codigo_empleado = _clean_text(codigo_empleado)
    zk_user_id = _clean_text(zk_user_id)

    if not codigo_empleado:
        raise ValueError("El código de empleado es obligatorio.")

    if not zk_user_id:
        raise ValueError("El zk_user_id es obligatorio.")

    empleado = obtener_empleado_por_codigo_para_zk(
        db=db,
        codigo_empleado=codigo_empleado,
    )

    if empleado is None:
        raise ValueError(f"No existe empleado con código {codigo_empleado}.")

    empleado_ocupando_zk_id = obtener_empleado_por_zk_user_id(
        db=db,
        zk_user_id=zk_user_id,
    )

    if (
        empleado_ocupando_zk_id is not None
        and empleado_ocupando_zk_id["codigo_empleado"] != codigo_empleado
    ):
        raise ValueError(
            f"El zk_user_id {zk_user_id} ya está asignado al empleado "
            f"{empleado_ocupando_zk_id['codigo_empleado']} - "
            f"{empleado_ocupando_zk_id['nombre_completo']}."
        )

    update_query = text(
        """
        UPDATE personal.empleados
        SET
            zk_user_id = :zk_user_id,
            fecha_modificacion = NOW()
        WHERE codigo_empleado = :codigo_empleado
        RETURNING
            id,
            codigo_empleado,
            nombres,
            apellido_paterno,
            apellido_materno,
            nombre_completo,
            correo,
            estatus,
            zk_user_id
        """
    )

    row = db.execute(
        update_query,
        {
            "codigo_empleado": codigo_empleado,
            "zk_user_id": zk_user_id,
        },
    ).mappings().first()

    db.commit()

    if row is None:
        raise ValueError(f"No se pudo actualizar el empleado {codigo_empleado}.")

    return {
        "id": row["id"],
        "codigo_empleado": row["codigo_empleado"],
        "nombres": row["nombres"],
        "apellido_paterno": row["apellido_paterno"],
        "apellido_materno": row["apellido_materno"],
        "nombre_completo": row["nombre_completo"],
        "correo": row["correo"],
        "estatus": row["estatus"],
        "zk_user_id": _clean_text(row["zk_user_id"]),
    }


def desvincular_empleado_de_zk(
    *,
    db: Session,
    codigo_empleado: str,
) -> dict[str, Any]:
    codigo_empleado = _clean_text(codigo_empleado)

    if not codigo_empleado:
        raise ValueError("El código de empleado es obligatorio.")

    empleado = obtener_empleado_por_codigo_para_zk(
        db=db,
        codigo_empleado=codigo_empleado,
    )

    if empleado is None:
        raise ValueError(f"No existe empleado con código {codigo_empleado}.")

    update_query = text(
        """
        UPDATE personal.empleados
        SET
            zk_user_id = NULL,
            fecha_modificacion = NOW()
        WHERE codigo_empleado = :codigo_empleado
        RETURNING
            id,
            codigo_empleado,
            nombres,
            apellido_paterno,
            apellido_materno,
            nombre_completo,
            correo,
            estatus,
            zk_user_id
        """
    )

    row = db.execute(
        update_query,
        {"codigo_empleado": codigo_empleado},
    ).mappings().first()

    db.commit()

    if row is None:
        raise ValueError(f"No se pudo desvincular el empleado {codigo_empleado}.")

    return {
        "id": row["id"],
        "codigo_empleado": row["codigo_empleado"],
        "nombres": row["nombres"],
        "apellido_paterno": row["apellido_paterno"],
        "apellido_materno": row["apellido_materno"],
        "nombre_completo": row["nombre_completo"],
        "correo": row["correo"],
        "estatus": row["estatus"],
        "zk_user_id": _clean_text(row["zk_user_id"]),
    }