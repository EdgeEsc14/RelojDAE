from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    value_text = _clean_text(value)

    if not value_text:
        return None

    return datetime.fromisoformat(value_text)


def insertar_marcaciones_crudas(
    *,
    db: Session,
    records: list[dict[str, Any]],
    sync_run_id: str,
    dispositivo_ip: str | None = None,
    dispositivo_origen: str = "ZKTeco",
) -> dict[str, Any]:
    """
    Inserta marcaciones crudas en asistencia.marcaciones_crudas.

    Seguridad:
    - No modifica el reloj.
    - No borra datos del reloj.
    - No duplica marcaciones si se ejecuta varias veces.
    """

    insert_query = text(
        """
        INSERT INTO asistencia.marcaciones_crudas (
            dispositivo_origen,
            dispositivo_ip,
            zk_uid_registro,
            zk_user_id,
            fecha_hora,
            punch,
            punch_label,
            status,
            status_label,
            empleado_id,
            codigo_empleado,
            raw_payload,
            sync_run_id
        )
        SELECT
            :dispositivo_origen,
            :dispositivo_ip,
            :zk_uid_registro,
            :zk_user_id,
            :fecha_hora,
            :punch,
            :punch_label,
            :status,
            :status_label,
            empleado_match.id,
            empleado_match.codigo_empleado,
            CAST(:raw_payload AS jsonb),
            :sync_run_id
        FROM (
            SELECT
                e.id,
                e.codigo_empleado
            FROM personal.empleados e
            WHERE e.zk_user_id = :zk_user_id
            LIMIT 1
        ) AS empleado_match
        RIGHT JOIN (SELECT 1 AS dummy) AS base ON TRUE
        ON CONFLICT DO NOTHING
        RETURNING id
        """
    )

    total_recibidas = len(records)
    insertadas = 0
    duplicadas = 0
    omitidas = 0
    errores: list[dict[str, Any]] = []

    for record in records:
        try:
            zk_user_id = _clean_text(record.get("user_id"))
            fecha_hora = _parse_timestamp(record.get("timestamp"))

            if not zk_user_id or fecha_hora is None:
                omitidas += 1
                errores.append(
                    {
                        "reason": "Marcación sin zk_user_id o timestamp.",
                        "record": record,
                    }
                )
                continue

            result = db.execute(
                insert_query,
                {
                    "dispositivo_origen": dispositivo_origen,
                    "dispositivo_ip": dispositivo_ip,
                    "zk_uid_registro": record.get("uid"),
                    "zk_user_id": zk_user_id,
                    "fecha_hora": fecha_hora,
                    "punch": record.get("punch"),
                    "punch_label": record.get("punch_label"),
                    "status": record.get("status"),
                    "status_label": record.get("status_label"),
                    "raw_payload": _json_payload(record),
                    "sync_run_id": sync_run_id,
                },
            ).first()

            if result is None:
                duplicadas += 1
            else:
                insertadas += 1

        except Exception as exc:
            omitidas += 1
            errores.append(
                {
                    "reason": str(exc),
                    "record": record,
                }
            )

    db.commit()

    return {
        "total_recibidas": total_recibidas,
        "insertadas": insertadas,
        "duplicadas": duplicadas,
        "omitidas": omitidas,
        "errores": errores,
    }


def listar_marcaciones_crudas_db(
    *,
    db: Session,
    limit: int = 100,
    zk_user_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """
    Lista marcaciones crudas ya sincronizadas en PostgreSQL.
    """

    filters = []
    params: dict[str, Any] = {
        "limit": limit,
    }

    if zk_user_id:
        filters.append("mc.zk_user_id = :zk_user_id")
        params["zk_user_id"] = _clean_text(zk_user_id)

    if date_from:
        filters.append("mc.fecha >= CAST(:date_from AS date)")
        params["date_from"] = date_from

    if date_to:
        filters.append("mc.fecha <= CAST(:date_to AS date)")
        params["date_to"] = date_to

    where_clause = ""

    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    count_query = text(
        f"""
        SELECT COUNT(*) AS total
        FROM asistencia.marcaciones_crudas mc
        {where_clause}
        """
    )

    rows_query = text(
        f"""
        SELECT
            mc.id,
            mc.dispositivo_origen,
            mc.dispositivo_ip,
            mc.zk_uid_registro,
            mc.zk_user_id,
            mc.fecha_hora,
            mc.fecha,
            mc.hora,
            mc.punch,
            mc.punch_label,
            mc.status,
            mc.status_label,
            mc.empleado_id,
            mc.codigo_empleado,
            e.nombre_completo AS empleado_nombre,
            mc.sync_run_id,
            mc.sincronizado_en,
            mc.creado_en
        FROM asistencia.marcaciones_crudas mc
        LEFT JOIN personal.empleados e
            ON e.id = mc.empleado_id
        {where_clause}
        ORDER BY mc.fecha_hora DESC, mc.id DESC
        LIMIT :limit
        """
    )

    total = db.execute(count_query, params).scalar() or 0
    rows = db.execute(rows_query, params).mappings().all()

    records = []

    for row in rows:
        fecha_hora = row["fecha_hora"]
        sincronizado_en = row["sincronizado_en"]
        creado_en = row["creado_en"]

        records.append(
            {
                "id": row["id"],
                "dispositivo_origen": row["dispositivo_origen"],
                "dispositivo_ip": row["dispositivo_ip"],
                "zk_uid_registro": row["zk_uid_registro"],
                "zk_user_id": row["zk_user_id"],
                "fecha_hora": fecha_hora.isoformat() if fecha_hora else None,
                "fecha": row["fecha"].isoformat() if row["fecha"] else None,
                "hora": row["hora"].isoformat() if row["hora"] else None,
                "punch": row["punch"],
                "punch_label": row["punch_label"],
                "status": row["status"],
                "status_label": row["status_label"],
                "empleado_id": row["empleado_id"],
                "codigo_empleado": row["codigo_empleado"],
                "empleado_nombre": row["empleado_nombre"],
                "sync_run_id": row["sync_run_id"],
                "sincronizado_en": sincronizado_en.isoformat()
                if sincronizado_en
                else None,
                "creado_en": creado_en.isoformat() if creado_en else None,
            }
        )

    return {
        "total": total,
        "limit": limit,
        "records": records,
    }


def _json_payload(record: dict[str, Any]) -> str:
    """
    Convierte el payload a JSON string sin depender de tipos especiales.
    """
    import json

    return json.dumps(record, default=str, ensure_ascii=False)