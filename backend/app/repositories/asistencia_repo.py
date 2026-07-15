from sqlalchemy import text
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


def _get_access_params(
    access_scope: AccessScope,
) -> dict:
    return {
        "access_data_scope": access_scope.data_scope,
        "access_employee_id": access_scope.employee_id,
        "access_unit_ids": list(
            access_scope.allowed_unit_ids
        ),
    }



def obtener_resumen_asistencia_empleado(
    db: Session,
    codigo_empleado: str,
    access_scope: AccessScope,
    limite: int = 10,
) -> dict | None:
    empleado = _obtener_empleado(
        db=db,
        codigo_empleado=codigo_empleado,
        access_scope=access_scope,
    )

    if empleado is None:
        return None

    periodo_actual = _obtener_periodo_actual(db)

    resumen_periodo = None
    asistencias_recientes = []
    incidencias_recientes = []
    movimientos_puntos_recientes = []

    if periodo_actual is not None:
        resumen_periodo = _obtener_resumen_periodo(
            db=db,
            empleado_id=empleado["id"],
            periodo_id=periodo_actual["id"],
        )

        asistencias_recientes = _obtener_asistencias_recientes(
            db=db,
            empleado_id=empleado["id"],
            fecha_inicio=periodo_actual["fecha_inicio"],
            fecha_fin=periodo_actual["fecha_fin"],
            limite=limite,
        )

        incidencias_recientes = _obtener_incidencias_recientes(
            db=db,
            empleado_id=empleado["id"],
            periodo_id=periodo_actual["id"],
            limite=limite,
        )

        movimientos_puntos_recientes = (
            _obtener_movimientos_puntos_recientes(
                db=db,
                empleado_id=empleado["id"],
                periodo_id=periodo_actual["id"],
                limite=limite,
            )
        )
    else:
        asistencias_recientes = _obtener_asistencias_recientes(
            db=db,
            empleado_id=empleado["id"],
            fecha_inicio=None,
            fecha_fin=None,
            limite=limite,
        )

        incidencias_recientes = _obtener_incidencias_recientes(
            db=db,
            empleado_id=empleado["id"],
            periodo_id=None,
            limite=limite,
        )

        movimientos_puntos_recientes = (
            _obtener_movimientos_puntos_recientes(
                db=db,
                empleado_id=empleado["id"],
                periodo_id=None,
                limite=limite,
            )
        )

    return {
        "empleado": empleado,
        "periodo_actual": periodo_actual,
        "resumen_periodo": resumen_periodo,
        "asistencias_recientes": asistencias_recientes,
        "incidencias_recientes": incidencias_recientes,
        "movimientos_puntos_recientes": (
            movimientos_puntos_recientes
        ),
    }


def _obtener_empleado(
    db: Session,
    codigo_empleado: str,
    access_scope: AccessScope,
) -> dict | None:
    query = text(
        f"""
        SELECT
            e.id,
            e.codigo_empleado,
            e.nombre_completo,
            e.correo,
            e.estatus
        FROM personal.empleados e
        WHERE e.codigo_empleado = :codigo_empleado
          AND {ACCESS_SCOPE_SQL}
        LIMIT 1
        """
    )

    params = {
        "codigo_empleado": codigo_empleado,
        **_get_access_params(access_scope),
    }

    row = db.execute(
        query,
        params,
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def _obtener_periodo_actual(db: Session) -> dict | None:
    query = text(
        """
        SELECT
            id,
            codigo,
            nombre,
            tipo_periodo,
            anio,
            numero_periodo,
            fecha_inicio,
            fecha_fin,
            estatus
        FROM asistencia.periodos_evaluacion
        WHERE estatus = 'ABIERTO'
          AND CURRENT_DATE BETWEEN fecha_inicio AND fecha_fin
        ORDER BY
            fecha_inicio DESC,
            id DESC
        LIMIT 1
        """
    )

    row = db.execute(query).mappings().first()

    if row is None:
        return None

    return dict(row)


def _obtener_resumen_periodo(
    db: Session,
    empleado_id: int,
    periodo_id: int,
) -> dict | None:
    query = text(
        """
        SELECT
            id,
            dias_laborales,
            dias_completos,
            dias_tolerancia,
            retardos_menores,
            retardos_mayores,
            faltas,
            faltas_justificadas,
            omisiones_entrada,
            omisiones_salida,
            dias_con_tiempo_extra,
            minutos_ordinarios,
            minutos_extra,
            minutos_retardo,
            puntos_brutos,
            puntos_justificados,
            puntos_ajuste,
            puntos_efectivos,
            justificantes_solicitados,
            justificantes_aprobados,
            dias_justificados,
            descansos_obligatorios_generados,
            faltas_consecutivas_max,
            requiere_revision_baja,
            motivo_revision_baja,
            estatus,
            fecha_calculo,
            fecha_cierre
        FROM asistencia.resumen_periodo_empleado
        WHERE empleado_id = :empleado_id
          AND periodo_evaluacion_id = :periodo_id
        LIMIT 1
        """
    )

    row = db.execute(
        query,
        {
            "empleado_id": empleado_id,
            "periodo_id": periodo_id,
        },
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def _obtener_asistencias_recientes(
    db: Session,
    empleado_id: int,
    fecha_inicio,
    fecha_fin,
    limite: int,
) -> list[dict]:
    params = {
        "empleado_id": empleado_id,
        "limite": limite,
    }

    filtro_periodo = ""

    if fecha_inicio is not None and fecha_fin is not None:
        filtro_periodo = """
          AND fecha BETWEEN :fecha_inicio AND :fecha_fin
        """
        params["fecha_inicio"] = fecha_inicio
        params["fecha_fin"] = fecha_fin

    query = text(
        f"""
        SELECT
            id,
            fecha,
            estatus,
            entrada_programada,
            salida_programada,
            primera_entrada,
            ultima_salida,
            minutos_retardo,
            minutos_ordinarios,
            minutos_extra,
            puntos_generados,
            procesada,
            requiere_revision,
            observaciones
        FROM asistencia.asistencias_diarias
        WHERE empleado_id = :empleado_id
        {filtro_periodo}
        ORDER BY fecha DESC
        LIMIT :limite
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def _obtener_incidencias_recientes(
    db: Session,
    empleado_id: int,
    periodo_id: int | None,
    limite: int,
) -> list[dict]:
    params = {
        "empleado_id": empleado_id,
        "limite": limite,
    }

    filtro_periodo = ""

    if periodo_id is not None:
        filtro_periodo = """
          AND i.periodo_evaluacion_id = :periodo_id
        """
        params["periodo_id"] = periodo_id

    query = text(
        f"""
        SELECT
            i.id,
            i.fecha,
            ti.codigo AS tipo_codigo,
            ti.nombre AS tipo_nombre,
            ti.categoria,
            i.descripcion,
            i.puntos_originales,
            i.puntos_justificados,
            i.puntos_efectivos,
            i.estatus,
            i.origen,
            i.requiere_revision
        FROM asistencia.incidencias i
        INNER JOIN asistencia.tipos_incidencia ti
            ON ti.id = i.tipo_incidencia_id
        WHERE i.empleado_id = :empleado_id
        {filtro_periodo}
        ORDER BY
            i.fecha DESC,
            i.id DESC
        LIMIT :limite
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def _obtener_movimientos_puntos_recientes(
    db: Session,
    empleado_id: int,
    periodo_id: int | None,
    limite: int,
) -> list[dict]:
    params = {
        "empleado_id": empleado_id,
        "limite": limite,
    }

    filtro_periodo = ""

    if periodo_id is not None:
        filtro_periodo = """
          AND periodo_evaluacion_id = :periodo_id
        """
        params["periodo_id"] = periodo_id

    query = text(
        f"""
        SELECT
            id,
            fecha,
            tipo_movimiento,
            concepto,
            puntos,
            descripcion,
            origen,
            fecha_creacion
        FROM asistencia.movimientos_puntos
        WHERE empleado_id = :empleado_id
        {filtro_periodo}
        ORDER BY
            fecha DESC,
            id DESC
        LIMIT :limite
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]
def listar_asistencia_diaria(
    db: Session,
    fecha,
    access_scope: AccessScope,
    q: str | None = None,
    estatus: str | None = None,
    unidad_organizacional_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    filtros = [
        "ad.fecha = :fecha",
        ACCESS_SCOPE_SQL,
    ]

    params: dict = {
        "fecha": fecha,
        "limit": limit,
        "offset": offset,
        **_get_access_params(access_scope),
    }

    if q:
        filtros.append(
            """
            (
                e.codigo_empleado ILIKE :q
                OR e.nombre_completo ILIKE :q
                OR e.correo ILIKE :q
            )
            """
        )
        params["q"] = f"%{q}%"

    if estatus:
        filtros.append("ad.estatus = :estatus")
        params["estatus"] = estatus

    if unidad_organizacional_id:
        filtros.append("e.unidad_organizacional_id = :unidad_organizacional_id")
        params["unidad_organizacional_id"] = unidad_organizacional_id

    where_sql = "WHERE " + " AND ".join(filtros)

    query_total = text(
        f"""
        SELECT
            COUNT(*) AS total
        FROM asistencia.asistencias_diarias ad
        INNER JOIN personal.empleados e
            ON e.id = ad.empleado_id
        {where_sql}
        """
    )

    query_items = text(
        f"""
        SELECT
            ad.id AS asistencia_id,
            ad.fecha,

            e.id AS empleado_id,
            e.codigo_empleado,
            e.nombre_completo,
            e.correo,
            e.estatus AS empleado_estatus,

            uo.id AS unidad_organizacional_id,
            uo.codigo AS unidad_codigo,
            uo.nombre AS unidad_nombre,

            p.id AS puesto_id,
            p.codigo AS puesto_codigo,
            p.nombre AS puesto_nombre,

            h.id AS horario_id,
            h.codigo AS horario_codigo,
            h.nombre AS horario_nombre,

            ad.entrada_programada,
            ad.salida_programada,
            ad.primera_entrada,
            ad.ultima_salida,

            ad.minutos_retardo,
            ad.minutos_ordinarios,
            ad.minutos_extra,

            ad.estatus,
            ad.puntos_generados,
            ad.procesada,
            ad.requiere_revision,
            ad.observaciones,

            COALESCE(inc.total_incidencias, 0) AS total_incidencias,
            COALESCE(inc.puntos_efectivos_incidencias, 0) AS puntos_efectivos_incidencias

        FROM asistencia.asistencias_diarias ad

        INNER JOIN personal.empleados e
            ON e.id = ad.empleado_id

        LEFT JOIN organizacion.unidades_organizacionales uo
            ON uo.id = e.unidad_organizacional_id

        LEFT JOIN organizacion.puestos p
            ON p.id = e.puesto_id

        LEFT JOIN asistencia.horarios h
            ON h.id = ad.horario_id

        LEFT JOIN LATERAL (
            SELECT
                COUNT(*) AS total_incidencias,
                COALESCE(SUM(i.puntos_efectivos), 0) AS puntos_efectivos_incidencias
            FROM asistencia.incidencias i
            WHERE i.asistencia_diaria_id = ad.id
        ) inc ON TRUE

        {where_sql}

        ORDER BY
            e.nombre_completo,
            e.codigo_empleado

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