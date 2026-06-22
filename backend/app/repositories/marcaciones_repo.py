from sqlalchemy import text
from sqlalchemy.orm import Session


def listar_marcaciones(
    db: Session,
    fecha=None,
    q: str | None = None,
    dispositivo_id: int | None = None,
    empleado_id: int | None = None,
    procesada: bool | None = None,
    tipo_marcacion_codigo: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    filtros = []
    params: dict = {
        "limit": limit,
        "offset": offset,
    }

    if fecha is not None:
        filtros.append("m.fecha = :fecha")
        params["fecha"] = fecha

    if q:
        filtros.append(
            """
            (
                e.codigo_empleado ILIKE :q
                OR e.nombre_completo ILIKE :q
                OR e.correo ILIKE :q
                OR m.zk_user_id ILIKE :q
                OR ed.nombre_en_dispositivo ILIKE :q
                OR d.codigo ILIKE :q
                OR d.nombre ILIKE :q
            )
            """
        )
        params["q"] = f"%{q}%"

    if dispositivo_id is not None:
        filtros.append("m.dispositivo_id = :dispositivo_id")
        params["dispositivo_id"] = dispositivo_id

    if empleado_id is not None:
        filtros.append("m.empleado_id = :empleado_id")
        params["empleado_id"] = empleado_id

    if procesada is not None:
        filtros.append("m.procesada = :procesada")
        params["procesada"] = procesada

    if tipo_marcacion_codigo:
        filtros.append("tm.codigo = :tipo_marcacion_codigo")
        params["tipo_marcacion_codigo"] = tipo_marcacion_codigo

    where_sql = ""

    if filtros:
        where_sql = "WHERE " + " AND ".join(filtros)

    query_total = text(
        f"""
        SELECT
            COUNT(*) AS total
        FROM asistencia.marcaciones m

        LEFT JOIN personal.empleados e
            ON e.id = m.empleado_id

        LEFT JOIN dispositivos.empleado_dispositivo ed
            ON ed.id = m.empleado_dispositivo_id

        INNER JOIN dispositivos.dispositivos d
            ON d.id = m.dispositivo_id

        INNER JOIN asistencia.tipos_marcacion tm
            ON tm.id = m.tipo_marcacion_id

        {where_sql}
        """
    )

    query_items = text(
        f"""
        SELECT
            m.id,
            m.fecha,
            m.fecha_hora,

            e.id AS empleado_id,
            e.codigo_empleado,
            e.nombre_completo,
            e.estatus AS empleado_estatus,

            ed.id AS empleado_dispositivo_id,
            m.zk_user_id,
            m.zk_uid,
            ed.nombre_en_dispositivo,

            d.id AS dispositivo_id,
            d.codigo AS dispositivo_codigo,
            d.nombre AS dispositivo_nombre,
            d.ip::text AS dispositivo_ip,
            d.puerto AS dispositivo_puerto,

            tm.id AS tipo_marcacion_id,
            tm.codigo AS tipo_marcacion_codigo,
            tm.nombre AS tipo_marcacion_nombre,
            tm.categoria AS tipo_marcacion_categoria,
            tm.es_entrada,
            tm.es_salida,
            tm.es_tiempo_extra,

            m.punch_original,
            m.estado_verificacion,
            m.codigo_trabajo,
            m.origen,

            m.raw_data,

            m.procesada,
            m.fecha_procesamiento,
            m.observaciones,

            s.id AS sincronizacion_id,
            s.estatus AS sincronizacion_estatus,
            s.tipo_sincronizacion AS sincronizacion_tipo,

            m.fecha_sincronizacion,
            m.fecha_creacion

        FROM asistencia.marcaciones m

        LEFT JOIN personal.empleados e
            ON e.id = m.empleado_id

        LEFT JOIN dispositivos.empleado_dispositivo ed
            ON ed.id = m.empleado_dispositivo_id

        INNER JOIN dispositivos.dispositivos d
            ON d.id = m.dispositivo_id

        INNER JOIN asistencia.tipos_marcacion tm
            ON tm.id = m.tipo_marcacion_id

        LEFT JOIN dispositivos.sincronizaciones s
            ON s.id = m.sincronizacion_id

        {where_sql}

        ORDER BY
            m.fecha_hora DESC,
            m.id DESC

        LIMIT :limit
        OFFSET :offset
        """
    )

    total = db.execute(query_total, params).scalar_one()
    rows = db.execute(query_items, params).mappings().all()

    return {
        "total": total,
        "fecha": fecha,
        "limit": limit,
        "offset": offset,
        "items": [dict(row) for row in rows],
    }