"""
Repositorio para gestión de incidencias.

Accede a asistencia.incidencias, asistencia.tipos_incidencia,
asistencia.justificantes y tablas relacionadas.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope


ACCESS_SCOPE_SQL = """
(
    :access_data_scope = 'TOTAL'

    OR (
        :access_data_scope = 'PROPIO'
        AND e.id = :access_employee_id
    )

    OR (
        :access_data_scope = 'AREA'
        AND e.unidad_organizacional_id = ANY(
            CAST(:access_unit_ids AS BIGINT[])
        )
    )
)
"""


def _get_access_params(access_scope: AccessScope) -> dict:
    return {
        "access_data_scope": access_scope.data_scope,
        "access_employee_id": access_scope.employee_id,
        "access_unit_ids": list(access_scope.allowed_unit_ids),
    }


# ============================================================
# Listar incidencias
# ============================================================


def listar_incidencias(
    db: Session,
    access_scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = 20,
    estatus: str | None = None,
    tipo_incidencia_id: int | None = None,
    empleado_id: int | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    busqueda: str | None = None,
) -> dict[str, Any]:
    """Lista incidencias con filtros, paginación y control de acceso."""

    access_params = _get_access_params(access_scope)
    conditions = [ACCESS_SCOPE_SQL]
    params: dict[str, Any] = {**access_params}

    if estatus:
        conditions.append("i.estatus = :estatus")
        params["estatus"] = estatus.strip().upper()

    if tipo_incidencia_id:
        conditions.append("i.tipo_incidencia_id = :tipo_incidencia_id")
        params["tipo_incidencia_id"] = tipo_incidencia_id

    if empleado_id:
        conditions.append("i.empleado_id = :empleado_id")
        params["empleado_id"] = empleado_id

    if fecha_inicio:
        conditions.append("i.fecha >= :fecha_inicio")
        params["fecha_inicio"] = fecha_inicio

    if fecha_fin:
        conditions.append("i.fecha <= :fecha_fin")
        params["fecha_fin"] = fecha_fin

    if busqueda:
        busqueda_like = f"%{busqueda.strip().lower()}%"
        conditions.append(
            """
            (
                LOWER(e.nombre_completo) LIKE :busqueda
                OR LOWER(e.codigo_empleado) LIKE :busqueda
                OR LOWER(ti.nombre) LIKE :busqueda
            )
            """
        )
        params["busqueda"] = busqueda_like

    where_clause = "WHERE " + " AND ".join(conditions)

    # Count
    count_query = text(
        f"""
        SELECT COUNT(*) AS total
        FROM asistencia.incidencias i
        INNER JOIN personal.empleados e ON e.id = i.empleado_id
        INNER JOIN asistencia.tipos_incidencia ti ON ti.id = i.tipo_incidencia_id
        {where_clause}
        """
    )
    total = db.execute(count_query, params).scalar_one()

    # Data
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    data_query = text(
        f"""
        SELECT
            i.id,
            i.empleado_id,
            e.codigo_empleado,
            e.nombre_completo AS nombre_empleado,
            uo.nombre AS departamento,
            i.tipo_incidencia_id,
            ti.codigo AS tipo_codigo,
            ti.nombre AS tipo_nombre,
            ti.categoria AS tipo_categoria,
            i.fecha,
            i.descripcion,
            i.puntos_originales,
            i.puntos_justificados,
            i.puntos_efectivos,
            i.estatus,
            i.origen,
            i.requiere_revision,
            i.fecha_creacion,
            i.fecha_revision
        FROM asistencia.incidencias i
        INNER JOIN personal.empleados e ON e.id = i.empleado_id
        INNER JOIN asistencia.tipos_incidencia ti ON ti.id = i.tipo_incidencia_id
        LEFT JOIN organizacion.unidades_organizacionales uo
            ON uo.id = e.unidad_organizacional_id
        {where_clause}
        ORDER BY i.fecha DESC, i.fecha_creacion DESC
        LIMIT :limit OFFSET :offset
        """
    )

    rows = db.execute(data_query, params).mappings().all()

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============================================================
# Obtener incidencia por ID
# ============================================================


def obtener_incidencia_por_id(
    db: Session,
    incidencia_id: int,
    access_scope: AccessScope,
) -> dict[str, Any] | None:
    """Obtiene detalle completo de una incidencia con verificación de acceso."""

    access_params = _get_access_params(access_scope)

    query = text(
        f"""
        SELECT
            i.id,
            i.empleado_id,
            e.codigo_empleado,
            e.nombre_completo AS nombre_empleado,
            uo.nombre AS departamento,
            i.tipo_incidencia_id,
            ti.codigo AS tipo_codigo,
            ti.nombre AS tipo_nombre,
            ti.categoria AS tipo_categoria,
            ti.genera_puntos,
            ti.requiere_justificacion,
            ti.requiere_aprobacion,
            i.asistencia_diaria_id,
            i.periodo_evaluacion_id,
            i.fecha,
            i.fecha_inicio,
            i.fecha_fin,
            i.descripcion,
            i.puntos_originales,
            i.puntos_justificados,
            i.puntos_efectivos,
            i.estatus,
            i.origen,
            i.requiere_revision,
            i.creada_por_usuario_id,
            i.revisada_por_usuario_id,
            i.fecha_revision,
            i.comentario_revision,
            i.fecha_creacion,
            i.fecha_modificacion
        FROM asistencia.incidencias i
        INNER JOIN personal.empleados e ON e.id = i.empleado_id
        INNER JOIN asistencia.tipos_incidencia ti ON ti.id = i.tipo_incidencia_id
        LEFT JOIN organizacion.unidades_organizacionales uo
            ON uo.id = e.unidad_organizacional_id
        WHERE i.id = :incidencia_id
          AND {ACCESS_SCOPE_SQL}
        """
    )

    row = db.execute(
        query,
        {"incidencia_id": incidencia_id, **access_params},
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


# ============================================================
# Crear incidencia manual
# ============================================================


def crear_incidencia(
    db: Session,
    *,
    empleado_id: int,
    tipo_incidencia_id: int,
    fecha: date,
    descripcion: str | None = None,
    puntos_originales: int = 0,
    creada_por_usuario_id: int | None = None,
) -> dict[str, Any]:
    """Crea una incidencia manual."""

    # Validar que el empleado existe
    emp_exists = db.execute(
        text("SELECT EXISTS (SELECT 1 FROM personal.empleados WHERE id = :id)"),
        {"id": empleado_id},
    ).scalar_one()

    if not emp_exists:
        raise ValueError(f"No existe empleado con id {empleado_id}.")

    # Validar tipo de incidencia
    tipo = db.execute(
        text(
            """
            SELECT id, codigo, puntos_default
            FROM asistencia.tipos_incidencia
            WHERE id = :id AND activo = TRUE
            """
        ),
        {"id": tipo_incidencia_id},
    ).mappings().first()

    if tipo is None:
        raise ValueError(f"No existe tipo de incidencia activo con id {tipo_incidencia_id}.")

    # Usar puntos_default del tipo si no se especifican
    if puntos_originales == 0 and tipo["puntos_default"] > 0:
        puntos_originales = tipo["puntos_default"]

    # Buscar periodo abierto
    periodo_id = db.execute(
        text(
            """
            SELECT id FROM asistencia.periodos_evaluacion
            WHERE estatus = 'ABIERTO'
              AND :fecha BETWEEN fecha_inicio AND fecha_fin
            LIMIT 1
            """
        ),
        {"fecha": fecha},
    ).scalar_one_or_none()

    try:
        row = db.execute(
            text(
                """
                INSERT INTO asistencia.incidencias (
                    empleado_id,
                    periodo_evaluacion_id,
                    tipo_incidencia_id,
                    fecha,
                    descripcion,
                    puntos_originales,
                    estatus,
                    origen,
                    creada_por_usuario_id
                )
                VALUES (
                    :empleado_id,
                    :periodo_evaluacion_id,
                    :tipo_incidencia_id,
                    :fecha,
                    :descripcion,
                    :puntos_originales,
                    'PENDIENTE',
                    'MANUAL',
                    :creada_por_usuario_id
                )
                RETURNING id
                """
            ),
            {
                "empleado_id": empleado_id,
                "tipo_incidencia_id": tipo_incidencia_id,
                "fecha": fecha,
                "descripcion": descripcion,
                "puntos_originales": puntos_originales,
                "periodo_evaluacion_id": periodo_id,
                "creada_por_usuario_id": creada_por_usuario_id,
            },
        ).mappings().one()

        db.commit()
        return {"id": row["id"]}

    except SQLAlchemyError:
        db.rollback()
        raise


# ============================================================
# Revisar incidencia (aprobar / rechazar)
# ============================================================


def revisar_incidencia(
    db: Session,
    incidencia_id: int,
    *,
    estatus: str,
    comentario_revision: str | None = None,
    revisada_por_usuario_id: int | None = None,
) -> dict[str, Any] | None:
    """Aprueba, rechaza o cancela una incidencia."""

    # Verificar que existe y está pendiente
    current = db.execute(
        text(
            "SELECT estatus FROM asistencia.incidencias WHERE id = :id"
        ),
        {"id": incidencia_id},
    ).mappings().first()

    if current is None:
        return None

    if current["estatus"] not in ("PENDIENTE", "SIN_JUSTIFICAR"):
        raise ValueError(
            f"La incidencia tiene estatus '{current['estatus']}' y no puede revisarse."
        )

    estatus_upper = estatus.strip().upper()
    valid_statuses = {"APROBADA", "RECHAZADA", "JUSTIFICADA", "CANCELADA"}
    if estatus_upper not in valid_statuses:
        raise ValueError(f"Estatus de revisión debe ser uno de: {', '.join(sorted(valid_statuses))}")

    try:
        db.execute(
            text(
                """
                UPDATE asistencia.incidencias
                SET
                    estatus = :estatus,
                    comentario_revision = :comentario_revision,
                    revisada_por_usuario_id = :revisada_por_usuario_id,
                    fecha_revision = CURRENT_TIMESTAMP,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {
                "id": incidencia_id,
                "estatus": estatus_upper,
                "comentario_revision": comentario_revision,
                "revisada_por_usuario_id": revisada_por_usuario_id,
            },
        )
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return {"id": incidencia_id, "estatus": estatus_upper}


# ============================================================
# Contar incidencias por estatus (para métricas)
# ============================================================


def contar_incidencias_por_estatus(
    db: Session,
    access_scope: AccessScope,
) -> dict[str, int]:
    """Retorna contadores de incidencias agrupados por estatus."""

    access_params = _get_access_params(access_scope)

    rows = db.execute(
        text(
            f"""
            SELECT
                i.estatus,
                COUNT(*) AS cantidad
            FROM asistencia.incidencias i
            INNER JOIN personal.empleados e ON e.id = i.empleado_id
            WHERE {ACCESS_SCOPE_SQL}
            GROUP BY i.estatus
            """
        ),
        access_params,
    ).mappings().all()

    result = {
        "PENDIENTE": 0,
        "SIN_JUSTIFICAR": 0,
        "JUSTIFICADA": 0,
        "APROBADA": 0,
        "RECHAZADA": 0,
        "CANCELADA": 0,
    }

    for row in rows:
        result[row["estatus"]] = row["cantidad"]

    result["total"] = sum(result.values())

    return result
