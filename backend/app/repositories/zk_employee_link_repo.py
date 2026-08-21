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


def resolver_empleado_id_para_marcacion(
    *,
    db: Session,
    dispositivo_origen: str | None,
    zk_user_id: str | None,
) -> dict[str, Any]:
    """
    Resuelve el empleado_id para una marcación cruda (dispositivo_origen +
    zk_user_id), priorizando dispositivos.empleado_dispositivo como fuente
    canónica sobre personal.empleados.zk_user_id (fallback legacy
    temporal de compatibilidad — Contrato §10).

    Reglas de resolución:

    1. Si dispositivo_origen identifica un dispositivo conocido
       (dispositivos.dispositivos.codigo, comparado sin distinguir
       mayúsculas/espacios) y existe una relación ACTIVA para
       (dispositivo_id, zk_user_id) en empleado_dispositivo, se usa esa
       fuente canónica. El índice único parcial
       uq_empleado_dispositivo_zk_user_id_activo garantiza que esta
       combinación resuelve, como máximo, a un único empleado.

    2. Si el dispositivo NO se identifica (dispositivo_origen vacío o sin
       coincidencia en dispositivos.dispositivos), se busca el
       zk_user_id en empleado_dispositivo entre TODOS los dispositivos
       activos:
       - Si resuelve a un único empleado, se usa como canónico.
       - Si resuelve a más de un empleado distinto (mismo zk_user_id
         reutilizado en dispositivos diferentes para empleados
         diferentes — el riesgo central de tener un solo campo escalar
         en personal.empleados), NO se elige ninguno: se reporta como
         conflicto explícito (conflicto=True, empleado_id=None).

    3. Si no hay ninguna relación resoluble en empleado_dispositivo (ni
       por dispositivo específico ni a través de todos), se cae al
       campo legacy personal.empleados.zk_user_id (también único).

    4. Si tampoco resuelve ahí, la marcación queda sin resolver
       (huérfana), igual que el comportamiento previo a este cambio.

    Retorna:
        {
            "empleado_id": int | None,
            "codigo_empleado": str | None,
            "fuente": "CANONICA" | "LEGACY" | "NINGUNA",
            "conflicto": bool,
            "detalle": str | None,
        }
    """
    zk_user_id = _clean_text(zk_user_id)
    dispositivo_origen = _clean_text(dispositivo_origen)

    sin_resolver = {
        "empleado_id": None,
        "codigo_empleado": None,
        "fuente": "NINGUNA",
        "conflicto": False,
        "detalle": None,
    }

    if not zk_user_id:
        return sin_resolver

    dispositivo_id = None

    if dispositivo_origen:
        dispositivo_id = db.execute(
            text(
                """
                SELECT id
                FROM dispositivos.dispositivos
                WHERE UPPER(BTRIM(codigo)) = UPPER(BTRIM(:codigo))
                LIMIT 1
                """
            ),
            {"codigo": dispositivo_origen},
        ).scalar()

    if dispositivo_id is not None:
        row = db.execute(
            text(
                """
                SELECT e.id, e.codigo_empleado
                FROM dispositivos.empleado_dispositivo ed
                INNER JOIN personal.empleados e
                    ON e.id = ed.empleado_id
                WHERE ed.dispositivo_id = :dispositivo_id
                  AND ed.zk_user_id = :zk_user_id
                  AND ed.activo = TRUE
                LIMIT 1
                """
            ),
            {"dispositivo_id": dispositivo_id, "zk_user_id": zk_user_id},
        ).mappings().first()

        if row is not None:
            return {
                "empleado_id": int(row["id"]),
                "codigo_empleado": row["codigo_empleado"],
                "fuente": "CANONICA",
                "conflicto": False,
                "detalle": None,
            }

    else:
        candidatos = db.execute(
            text(
                """
                SELECT DISTINCT ed.empleado_id
                FROM dispositivos.empleado_dispositivo ed
                WHERE ed.zk_user_id = :zk_user_id
                  AND ed.activo = TRUE
                ORDER BY ed.empleado_id
                """
            ),
            {"zk_user_id": zk_user_id},
        ).scalars().all()

        if len(candidatos) == 1:
            row = db.execute(
                text(
                    "SELECT id, codigo_empleado FROM personal.empleados WHERE id = :id"
                ),
                {"id": candidatos[0]},
            ).mappings().first()

            return {
                "empleado_id": int(candidatos[0]),
                "codigo_empleado": row["codigo_empleado"] if row else None,
                "fuente": "CANONICA",
                "conflicto": False,
                "detalle": None,
            }

        if len(candidatos) > 1:
            return {
                "empleado_id": None,
                "codigo_empleado": None,
                "fuente": "NINGUNA",
                "conflicto": True,
                "detalle": (
                    f"zk_user_id '{zk_user_id}' sin dispositivo identificado "
                    f"('{dispositivo_origen or '(vacío)'}') y asignado a "
                    f"{len(candidatos)} empleados distintos en "
                    "dispositivos.empleado_dispositivo "
                    f"(empleado_id: {list(candidatos)}). No se elige "
                    "automáticamente."
                ),
            }

    # Sin relación resoluble en empleado_dispositivo: fallback legacy.
    row = db.execute(
        text(
            """
            SELECT id, codigo_empleado
            FROM personal.empleados
            WHERE zk_user_id = :zk_user_id
            LIMIT 1
            """
        ),
        {"zk_user_id": zk_user_id},
    ).mappings().first()

    if row is not None:
        return {
            "empleado_id": int(row["id"]),
            "codigo_empleado": row["codigo_empleado"],
            "fuente": "LEGACY",
            "conflicto": False,
            "detalle": None,
        }

    return sin_resolver


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