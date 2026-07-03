from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _normalize_zk_user_id(value: Any) -> str:
    """
    Normaliza el identificador ZKTeco para comparar:
    personal.empleados.zk_user_id
    contra
    ZKTeco user.user_id
    """
    return _clean_text(value)


def listar_empleados_para_conciliacion(db: Session) -> list[dict[str, Any]]:
    """
    Obtiene empleados desde personal.empleados para compararlos contra usuarios ZKTeco.

    Campo clave:
    personal.empleados.zk_user_id = ZKTeco user_id
    """

    query = text(
        """
        SELECT
            id,
            codigo_empleado,
            nombres,
            apellido_paterno,
            apellido_materno,
            nombre_completo,
            rfc,
            correo,
            estatus,
            zk_user_id
        FROM personal.empleados
        ORDER BY codigo_empleado ASC
        """
    )

    rows = db.execute(query).mappings().all()

    empleados: list[dict[str, Any]] = []

    for row in rows:
        empleados.append(
            {
                "id": row["id"],
                "codigo_empleado": row["codigo_empleado"],
                "nombres": row["nombres"],
                "apellido_paterno": row["apellido_paterno"],
                "apellido_materno": row["apellido_materno"],
                "nombre_completo": row["nombre_completo"],
                "rfc": row["rfc"],
                "correo": row["correo"],
                "estatus": row["estatus"],
                "zk_user_id": _normalize_zk_user_id(row["zk_user_id"]),
            }
        )

    return empleados


def conciliar_empleados_con_usuarios_zk(
    *,
    db: Session,
    zk_users: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compara empleados de BD contra usuarios reales del reloj.

    Criterio principal:
    personal.empleados.zk_user_id == zk_user.user_id

    Solo lectura:
    - No modifica BD.
    - No modifica reloj.
    """

    empleados = listar_empleados_para_conciliacion(db)

    zk_operativos = [
        user
        for user in zk_users
        if not user.get("is_admin") and not user.get("is_protected")
    ]

    empleados_por_zk_user_id: dict[str, list[dict[str, Any]]] = {}

    for empleado in empleados:
        zk_user_id = _normalize_zk_user_id(empleado.get("zk_user_id"))

        if not zk_user_id:
            continue

        empleados_por_zk_user_id.setdefault(zk_user_id, []).append(empleado)

    zk_por_user_id: dict[str, dict[str, Any]] = {
        _normalize_zk_user_id(user.get("user_id")): user
        for user in zk_operativos
        if _normalize_zk_user_id(user.get("user_id"))
    }

    matched: list[dict[str, Any]] = []
    employees_without_zk_user: list[dict[str, Any]] = []
    zk_users_without_employee: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for empleado in empleados:
        empleado_zk_user_id = _normalize_zk_user_id(empleado.get("zk_user_id"))

        if not empleado_zk_user_id:
            employees_without_zk_user.append(
                {
                    "reason": "Empleado sin zk_user_id en BD.",
                    "employee": empleado,
                }
            )
            continue

        empleados_mismo_zk_id = empleados_por_zk_user_id.get(empleado_zk_user_id, [])

        if len(empleados_mismo_zk_id) > 1:
            conflicts.append(
                {
                    "type": "duplicated_zk_user_id_in_db",
                    "message": f"Más de un empleado tiene zk_user_id={empleado_zk_user_id}.",
                    "zk_user_id": empleado_zk_user_id,
                    "employees": empleados_mismo_zk_id,
                }
            )
            continue

        zk_user = zk_por_user_id.get(empleado_zk_user_id)

        if not zk_user:
            employees_without_zk_user.append(
                {
                    "reason": "Empleado tiene zk_user_id en BD, pero no existe en el reloj.",
                    "employee": empleado,
                }
            )
            continue

        matched.append(
            {
                "employee": empleado,
                "zk_user": zk_user,
                "warnings": _build_match_warnings(
                    employee=empleado,
                    zk_user=zk_user,
                ),
            }
        )

    for zk_user in zk_operativos:
        zk_user_id = _normalize_zk_user_id(zk_user.get("user_id"))

        if zk_user_id not in empleados_por_zk_user_id:
            zk_users_without_employee.append(
                {
                    "reason": "Usuario existe en reloj, pero ningún empleado tiene ese zk_user_id.",
                    "zk_user": zk_user,
                }
            )

    return {
        "ok": True,
        "summary": {
            "zk_users_total": len(zk_users),
            "zk_users_operational": len(zk_operativos),
            "employees_total": len(empleados),
            "matched": len(matched),
            "employees_without_zk_user": len(employees_without_zk_user),
            "zk_users_without_employee": len(zk_users_without_employee),
            "conflicts": len(conflicts),
        },
        "matched": matched,
        "employees_without_zk_user": employees_without_zk_user,
        "zk_users_without_employee": zk_users_without_employee,
        "conflicts": conflicts,
    }


def _build_match_warnings(
    *,
    employee: dict[str, Any],
    zk_user: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []

    employee_name = _clean_text(employee.get("nombre_completo")).lower()
    zk_name = _clean_text(zk_user.get("name")).lower()

    if employee_name and zk_name:
        employee_compact = employee_name.replace(" ", "")
        zk_compact = zk_name.replace(" ", "")

        if zk_compact not in employee_compact and employee_compact not in zk_compact:
            warnings.append(
                "El nombre del reloj no coincide claramente con el nombre del empleado."
            )

    estatus = _clean_text(employee.get("estatus")).lower()

    if estatus and estatus != "activo":
        warnings.append("El empleado no está activo en BD.")

    if not zk_user.get("has_pin"):
        warnings.append("El usuario del reloj no tiene PIN registrado.")

    return warnings