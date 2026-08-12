"""
Repositorio para el módulo de Calendario Laboral.

Accede a asistencia.calendarios y asistencia.calendario_eventos.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


# ============================================================
# Calendarios (catálogo)
# ============================================================


def obtener_calendario_activo(db: Session) -> dict[str, Any] | None:
    """Obtiene el calendario activo principal."""
    row = db.execute(
        text(
            """
            SELECT id, codigo, nombre, descripcion, activo
            FROM asistencia.calendarios
            WHERE activo = TRUE
            ORDER BY id ASC
            LIMIT 1
            """
        )
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def listar_calendarios(db: Session) -> list[dict[str, Any]]:
    """Lista todos los calendarios."""
    rows = db.execute(
        text(
            """
            SELECT id, codigo, nombre, descripcion, activo,
                   fecha_creacion, fecha_modificacion
            FROM asistencia.calendarios
            ORDER BY activo DESC, nombre ASC
            """
        )
    ).mappings().all()

    return [dict(row) for row in rows]


# ============================================================
# Eventos del calendario
# ============================================================


def listar_eventos(
    db: Session,
    *,
    calendario_id: int | None = None,
    anio: int | None = None,
    mes: int | None = None,
    tipo_evento: str | None = None,
    activo: bool | None = True,
    page: int = 1,
    page_size: int = 100,
) -> dict[str, Any]:
    """Lista eventos con filtros opcionales y paginación."""

    conditions: list[str] = []
    params: dict[str, Any] = {}

    if calendario_id is not None:
        conditions.append("ce.calendario_id = :calendario_id")
        params["calendario_id"] = calendario_id
    else:
        # Por defecto solo del calendario activo
        conditions.append(
            "ce.calendario_id = (SELECT id FROM asistencia.calendarios WHERE activo = TRUE LIMIT 1)"
        )

    if activo is not None:
        conditions.append("ce.activo = :activo")
        params["activo"] = activo

    if tipo_evento:
        conditions.append("ce.tipo_evento = :tipo_evento")
        params["tipo_evento"] = tipo_evento.strip().upper()

    if anio and mes:
        # Eventos que aplican a un mes/año específico
        conditions.append(
            """
            (
                (ce.tipo_recurrencia = 'ANUAL_FIJA' AND ce.mes = :mes)
                OR (ce.tipo_recurrencia = 'FECHA_ESPECIFICA'
                    AND EXTRACT(YEAR FROM ce.fecha_inicio) = :anio
                    AND EXTRACT(MONTH FROM ce.fecha_inicio) = :mes)
                OR (ce.tipo_recurrencia = 'PERIODO'
                    AND ce.fecha_inicio <= make_date(:anio, :mes, 1) + INTERVAL '1 month' - INTERVAL '1 day'
                    AND ce.fecha_fin >= make_date(:anio, :mes, 1))
            )
            """
        )
        params["anio"] = anio
        params["mes"] = mes
    elif anio:
        conditions.append(
            """
            (
                (ce.tipo_recurrencia = 'ANUAL_FIJA')
                OR (ce.tipo_recurrencia = 'FECHA_ESPECIFICA'
                    AND EXTRACT(YEAR FROM ce.fecha_inicio) = :anio)
                OR (ce.tipo_recurrencia = 'PERIODO'
                    AND EXTRACT(YEAR FROM ce.fecha_inicio) <= :anio
                    AND EXTRACT(YEAR FROM ce.fecha_fin) >= :anio)
            )
            """
        )
        params["anio"] = anio

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Count
    total = db.execute(
        text(f"SELECT COUNT(*) FROM asistencia.calendario_eventos ce {where_clause}"),
        params,
    ).scalar_one()

    # Fetch
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = db.execute(
        text(
            f"""
            SELECT
                ce.id,
                ce.calendario_id,
                ce.nombre,
                ce.descripcion,
                ce.tipo_evento,
                ce.tipo_recurrencia,
                ce.fecha_inicio,
                ce.fecha_fin,
                ce.mes,
                ce.dia,
                ce.afecta_asistencia,
                ce.es_laborable,
                ce.prioridad,
                ce.activo,
                ce.fecha_creacion,
                ce.fecha_modificacion
            FROM asistencia.calendario_eventos ce
            {where_clause}
            ORDER BY ce.prioridad ASC, ce.fecha_inicio ASC NULLS LAST, ce.mes ASC NULLS LAST, ce.dia ASC NULLS LAST
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def obtener_evento_por_id(
    db: Session,
    evento_id: int,
) -> dict[str, Any] | None:
    """Obtiene un evento por su ID."""
    row = db.execute(
        text(
            """
            SELECT
                ce.id,
                ce.calendario_id,
                c.nombre AS calendario_nombre,
                ce.nombre,
                ce.descripcion,
                ce.tipo_evento,
                ce.tipo_recurrencia,
                ce.fecha_inicio,
                ce.fecha_fin,
                ce.mes,
                ce.dia,
                ce.afecta_asistencia,
                ce.es_laborable,
                ce.prioridad,
                ce.activo,
                ce.fecha_creacion,
                ce.fecha_modificacion
            FROM asistencia.calendario_eventos ce
            INNER JOIN asistencia.calendarios c ON c.id = ce.calendario_id
            WHERE ce.id = :evento_id
            """
        ),
        {"evento_id": evento_id},
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def crear_evento(
    db: Session,
    *,
    calendario_id: int,
    nombre: str,
    descripcion: str | None,
    tipo_evento: str,
    tipo_recurrencia: str,
    fecha_inicio: date | None,
    fecha_fin: date | None,
    mes: int | None,
    dia: int | None,
    afecta_asistencia: bool,
    es_laborable: bool,
    prioridad: int,
) -> dict[str, Any]:
    """Crea un nuevo evento en el calendario."""

    # Validar que el calendario existe
    cal_exists = db.execute(
        text("SELECT EXISTS (SELECT 1 FROM asistencia.calendarios WHERE id = :id)"),
        {"id": calendario_id},
    ).scalar_one()

    if not cal_exists:
        raise ValueError(f"No existe calendario con id {calendario_id}.")

    try:
        row = db.execute(
            text(
                """
                INSERT INTO asistencia.calendario_eventos (
                    calendario_id, nombre, descripcion,
                    tipo_evento, tipo_recurrencia,
                    fecha_inicio, fecha_fin, mes, dia,
                    afecta_asistencia, es_laborable, prioridad, activo
                )
                VALUES (
                    :calendario_id, :nombre, :descripcion,
                    :tipo_evento, :tipo_recurrencia,
                    :fecha_inicio, :fecha_fin, :mes, :dia,
                    :afecta_asistencia, :es_laborable, :prioridad, TRUE
                )
                RETURNING id
                """
            ),
            {
                "calendario_id": calendario_id,
                "nombre": nombre,
                "descripcion": descripcion,
                "tipo_evento": tipo_evento,
                "tipo_recurrencia": tipo_recurrencia,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "mes": mes,
                "dia": dia,
                "afecta_asistencia": afecta_asistencia,
                "es_laborable": es_laborable,
                "prioridad": prioridad,
            },
        ).mappings().one()

        db.commit()
        return obtener_evento_por_id(db, row["id"])

    except SQLAlchemyError:
        db.rollback()
        raise


def actualizar_evento(
    db: Session,
    evento_id: int,
    *,
    nombre: str | None = None,
    descripcion: str | None = None,
    tipo_evento: str | None = None,
    tipo_recurrencia: str | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    mes: int | None = None,
    dia: int | None = None,
    afecta_asistencia: bool | None = None,
    es_laborable: bool | None = None,
    prioridad: int | None = None,
    activo: bool | None = None,
) -> dict[str, Any] | None:
    """Actualiza campos de un evento existente."""

    current = obtener_evento_por_id(db, evento_id)
    if current is None:
        return None

    sets: list[str] = []
    params: dict[str, Any] = {"evento_id": evento_id}

    if nombre is not None:
        sets.append("nombre = :nombre")
        params["nombre"] = nombre

    if descripcion is not None:
        sets.append("descripcion = :descripcion")
        params["descripcion"] = descripcion if descripcion else None

    if tipo_evento is not None:
        sets.append("tipo_evento = :tipo_evento")
        params["tipo_evento"] = tipo_evento

    if tipo_recurrencia is not None:
        sets.append("tipo_recurrencia = :tipo_recurrencia")
        params["tipo_recurrencia"] = tipo_recurrencia

    if fecha_inicio is not None:
        sets.append("fecha_inicio = :fecha_inicio")
        params["fecha_inicio"] = fecha_inicio

    if fecha_fin is not None:
        sets.append("fecha_fin = :fecha_fin")
        params["fecha_fin"] = fecha_fin

    if mes is not None:
        sets.append("mes = :mes")
        params["mes"] = mes

    if dia is not None:
        sets.append("dia = :dia")
        params["dia"] = dia

    if afecta_asistencia is not None:
        sets.append("afecta_asistencia = :afecta_asistencia")
        params["afecta_asistencia"] = afecta_asistencia

    if es_laborable is not None:
        sets.append("es_laborable = :es_laborable")
        params["es_laborable"] = es_laborable

    if prioridad is not None:
        sets.append("prioridad = :prioridad")
        params["prioridad"] = prioridad

    if activo is not None:
        sets.append("activo = :activo")
        params["activo"] = activo

    if not sets:
        return current

    sets.append("fecha_modificacion = CURRENT_TIMESTAMP")

    try:
        db.execute(
            text(
                f"""
                UPDATE asistencia.calendario_eventos
                SET {', '.join(sets)}
                WHERE id = :evento_id
                """
            ),
            params,
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_evento_por_id(db, evento_id)


def desactivar_evento(
    db: Session,
    evento_id: int,
) -> dict[str, Any] | None:
    """Desactiva un evento (soft delete)."""

    current = obtener_evento_por_id(db, evento_id)
    if current is None:
        return None

    try:
        db.execute(
            text(
                """
                UPDATE asistencia.calendario_eventos
                SET activo = FALSE, fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :evento_id
                """
            ),
            {"evento_id": evento_id},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_evento_por_id(db, evento_id)


# ============================================================
# Consultas para resolución de fecha
# ============================================================


def obtener_eventos_para_fecha(
    db: Session,
    fecha: date,
) -> list[dict[str, Any]]:
    """
    Retorna todos los eventos activos que aplican a una fecha específica.
    Ordenados por prioridad (menor número = mayor prioridad).

    Busca:
    - FECHA_ESPECIFICA: fecha_inicio = fecha
    - ANUAL_FIJA: mes y dia coinciden con la fecha
    - PERIODO: fecha está entre fecha_inicio y fecha_fin
    """

    rows = db.execute(
        text(
            """
            SELECT
                ce.id,
                ce.nombre,
                ce.tipo_evento,
                ce.tipo_recurrencia,
                ce.afecta_asistencia,
                ce.es_laborable,
                ce.prioridad
            FROM asistencia.calendario_eventos ce
            INNER JOIN asistencia.calendarios c
                ON c.id = ce.calendario_id
               AND c.activo = TRUE
            WHERE ce.activo = TRUE
              AND (
                  -- FECHA_ESPECIFICA: coincide exactamente
                  (ce.tipo_recurrencia = 'FECHA_ESPECIFICA'
                   AND ce.fecha_inicio = :fecha)

                  -- ANUAL_FIJA: mes y dia coinciden
                  OR (ce.tipo_recurrencia = 'ANUAL_FIJA'
                      AND ce.mes = :fecha_mes
                      AND ce.dia = :fecha_dia)

                  -- PERIODO: fecha dentro del rango
                  OR (ce.tipo_recurrencia = 'PERIODO'
                      AND ce.fecha_inicio <= :fecha
                      AND ce.fecha_fin >= :fecha)
              )
            ORDER BY ce.prioridad ASC, ce.id ASC
            """
        ),
        {
            "fecha": fecha,
            "fecha_mes": fecha.month,
            "fecha_dia": fecha.day,
        },
    ).mappings().all()

    return [dict(row) for row in rows]


def obtener_eventos_en_rango(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
) -> list[dict[str, Any]]:
    """
    Retorna eventos que aplican en un rango de fechas.
    Útil para la vista mensual del frontend.
    """

    rows = db.execute(
        text(
            """
            SELECT
                ce.id,
                ce.nombre,
                ce.descripcion,
                ce.tipo_evento,
                ce.tipo_recurrencia,
                ce.fecha_inicio,
                ce.fecha_fin,
                ce.mes,
                ce.dia,
                ce.afecta_asistencia,
                ce.es_laborable,
                ce.prioridad,
                ce.activo
            FROM asistencia.calendario_eventos ce
            INNER JOIN asistencia.calendarios c
                ON c.id = ce.calendario_id
               AND c.activo = TRUE
            WHERE ce.activo = TRUE
              AND (
                  -- FECHA_ESPECIFICA dentro del rango
                  (ce.tipo_recurrencia = 'FECHA_ESPECIFICA'
                   AND ce.fecha_inicio BETWEEN :fecha_inicio AND :fecha_fin)

                  -- ANUAL_FIJA: mes está en el rango (simplificado)
                  OR (ce.tipo_recurrencia = 'ANUAL_FIJA')

                  -- PERIODO: se solapa con el rango
                  OR (ce.tipo_recurrencia = 'PERIODO'
                      AND ce.fecha_inicio <= :fecha_fin
                      AND ce.fecha_fin >= :fecha_inicio)
              )
            ORDER BY ce.prioridad ASC, ce.mes ASC NULLS LAST, ce.dia ASC NULLS LAST
            """
        ),
        {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    ).mappings().all()

    return [dict(row) for row in rows]
