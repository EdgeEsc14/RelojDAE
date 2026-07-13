from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope, DataScope


VALID_DATA_SCOPES: set[str] = {
    "TOTAL",
    "AREA",
    "PROPIO",
    "NINGUNO",
}


def _normalize_module_code(value: Any) -> str:
    return (
        str(value or "")
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )


def _normalize_role_code(value: Any) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def _normalize_data_scope(value: Any) -> DataScope:
    normalized = str(value or "NINGUNO").strip().upper()

    if normalized not in VALID_DATA_SCOPES:
        return "NINGUNO"

    return normalized  # type: ignore[return-value]


def _get_allowed_unit_ids(
    *,
    db: Session,
    user_id: int,
) -> tuple[int, ...]:
    """
    Obtiene las unidades organizacionales permitidas para un usuario.

    Incluye:

    - La unidad asignada directamente.
    - Sus descendientes cuando incluye_descendientes = TRUE.
    - Solamente asignaciones activas y vigentes.

    La CTE recursiva sigue la jerarquía mediante unidad_padre_id.
    """

    query = text(
        """
        WITH RECURSIVE unidades_permitidas AS (
            SELECT
                uu.unidad_organizacional_id AS unidad_id,
                uu.incluye_descendientes AS puede_expandir
            FROM seguridad.usuarios_unidades uu
            WHERE uu.usuario_id = :user_id
              AND uu.activo = TRUE
              AND uu.fecha_inicio <= CURRENT_DATE
              AND (
                    uu.fecha_fin IS NULL
                    OR uu.fecha_fin >= CURRENT_DATE
              )

            UNION

            SELECT
                hija.id AS unidad_id,
                unidades_permitidas.puede_expandir
            FROM organizacion.unidades_organizacionales hija
            INNER JOIN unidades_permitidas
                ON hija.unidad_padre_id =
                   unidades_permitidas.unidad_id
            WHERE unidades_permitidas.puede_expandir = TRUE
        )
        SELECT DISTINCT unidad_id
        FROM unidades_permitidas
        ORDER BY unidad_id
        """
    )

    rows = db.execute(
        query,
        {
            "user_id": user_id,
        },
    ).mappings().all()

    return tuple(
        int(row["unidad_id"])
        for row in rows
        if row["unidad_id"] is not None
    )


def build_access_scope(
    *,
    db: Session,
    current_user: dict,
    module_code: str,
) -> AccessScope:
    """
    Construye los permisos efectivos de un usuario para un módulo.

    La fuente de verdad es:

    seguridad.usuarios
        -> seguridad.roles
        -> seguridad.permisos_rol
        -> seguridad.modulos

    Para alcance AREA también consulta:

    seguridad.usuarios_unidades
        -> organizacion.unidades_organizacionales
    """

    user_id = int(current_user["id"])

    raw_employee_id = current_user.get("empleado_id")
    employee_id = (
        int(raw_employee_id)
        if raw_employee_id is not None
        else None
    )

    raw_role_id = current_user.get("rol_id")
    role_id = (
        int(raw_role_id)
        if raw_role_id is not None
        else None
    )

    role_code = _normalize_role_code(
        current_user.get("rol")
        or current_user.get("rol_codigo")
    )

    normalized_module_code = _normalize_module_code(
        module_code
    )

    permission_row = None

    if role_id is not None:
        query = text(
            """
            SELECT
                pr.alcance_datos,
                pr.puede_consultar,
                pr.puede_crear,
                pr.puede_editar,
                pr.puede_eliminar,
                pr.puede_aprobar,
                pr.puede_exportar
            FROM seguridad.permisos_rol pr
            INNER JOIN seguridad.modulos m
                ON m.id = pr.modulo_id
            WHERE pr.rol_id = :role_id
              AND m.codigo = :module_code
              AND m.activo = TRUE
            LIMIT 1
            """
        )

        permission_row = db.execute(
            query,
            {
                "role_id": role_id,
                "module_code": normalized_module_code,
            },
        ).mappings().first()

    if permission_row is None:
        return AccessScope(
            user_id=user_id,
            employee_id=employee_id,
            role_id=role_id,
            role_code=role_code,
            module_code=normalized_module_code,
            data_scope="NINGUNO",
            can_read=False,
            can_create=False,
            can_edit=False,
            can_delete=False,
            can_approve=False,
            can_export=False,
            allowed_unit_ids=(),
        )

    data_scope = _normalize_data_scope(
        permission_row["alcance_datos"]
    )

    allowed_unit_ids: tuple[int, ...] = ()

    if data_scope == "AREA":
        allowed_unit_ids = _get_allowed_unit_ids(
            db=db,
            user_id=user_id,
        )

    return AccessScope(
        user_id=user_id,
        employee_id=employee_id,
        role_id=role_id,
        role_code=role_code,
        module_code=normalized_module_code,
        data_scope=data_scope,
        can_read=bool(
            permission_row["puede_consultar"]
        ),
        can_create=bool(
            permission_row["puede_crear"]
        ),
        can_edit=bool(
            permission_row["puede_editar"]
        ),
        can_delete=bool(
            permission_row["puede_eliminar"]
        ),
        can_approve=bool(
            permission_row["puede_aprobar"]
        ),
        can_export=bool(
            permission_row["puede_exportar"]
        ),
        allowed_unit_ids=allowed_unit_ids,
    )