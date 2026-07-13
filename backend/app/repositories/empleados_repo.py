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
        "access_data_scope": (
            access_scope.data_scope
        ),
        "access_employee_id": (
            access_scope.employee_id
        ),
        "access_unit_ids": list(
            access_scope.allowed_unit_ids
        ),
    }

def listar_empleados(
    db: Session,
    access_scope: AccessScope,
    q: str | None = None,
    estatus: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    where_conditions: list[str] = [
        ACCESS_SCOPE_SQL,
    ]

    params: dict = {
        "limit": limit,
        "offset": offset,
        **_get_access_params(access_scope),
    }

    if q:
        where_conditions.append(
            """
            (
                e.codigo_empleado ILIKE :q
                OR e.nombres ILIKE :q
                OR e.apellido_paterno ILIKE :q
                OR e.apellido_materno ILIKE :q
                OR e.nombre_completo ILIKE :q
                OR e.correo ILIKE :q
            )
            """
        )
        params["q"] = f"%{q}%"

    if estatus:
        where_conditions.append("e.estatus = :estatus")
        params["estatus"] = estatus

    where_sql = ""
    if where_conditions:
        where_sql = "WHERE " + " AND ".join(where_conditions)

    query_total = text(
        f"""
        SELECT
            COUNT(*) AS total
        FROM personal.empleados e
        {where_sql}
        """
    )

    query_items = text(
        f"""
        SELECT
            e.id,
            e.codigo_empleado,
            e.nombres,
            e.apellido_paterno,
            e.apellido_materno,
            CONCAT_WS(' ', e.apellido_paterno, e.apellido_materno) AS apellidos,
            e.nombre_completo,
            e.correo,
            e.estatus,

            uo.id AS unidad_organizacional_id,
            uo.codigo AS unidad_organizacional_codigo,
            uo.nombre AS unidad_organizacional,
            tu.nombre AS unidad_organizacional_tipo,

            uo_padre.id AS area_principal_id,
            uo_padre.codigo AS area_principal_codigo,
            COALESCE(uo_padre.nombre, uo.nombre) AS area_principal,

            p.id AS puesto_id,
            p.codigo AS puesto_codigo,
            p.nombre AS puesto,
            p.nivel_jerarquico AS puesto_nivel_jerarquico,

            sup.id AS supervisor_id,
            sup.codigo_empleado AS supervisor_codigo_empleado,
            sup.nombre_completo AS supervisor,

            h.id AS horario_id,
            h.codigo AS horario_codigo,
            h.nombre AS horario,
            tt.nombre AS turno,
            tt.codigo AS turno_codigo,
            ah.fecha_inicio AS horario_fecha_inicio,
            ah.fecha_fin AS horario_fecha_fin,

            ed.id AS empleado_dispositivo_id,
            ed.dispositivo_id,
            d.codigo AS dispositivo_codigo,
            d.nombre AS dispositivo,
            ed.zk_uid,
            ed.zk_user_id,
            ed.nombre_en_dispositivo,
            ed.sincronizado AS dispositivo_sincronizado

        FROM personal.empleados e

        LEFT JOIN organizacion.unidades_organizacionales uo
            ON uo.id = e.unidad_organizacional_id

        LEFT JOIN organizacion.tipos_unidad tu
            ON tu.id = uo.tipo_unidad_id

        LEFT JOIN organizacion.unidades_organizacionales uo_padre
            ON uo_padre.id = uo.unidad_padre_id

        LEFT JOIN organizacion.puestos p
            ON p.id = e.puesto_id

        LEFT JOIN personal.empleados sup
            ON sup.id = e.supervisor_id

        LEFT JOIN LATERAL (
            SELECT
                ah_inner.id,
                ah_inner.empleado_id,
                ah_inner.horario_id,
                ah_inner.fecha_inicio,
                ah_inner.fecha_fin,
                ah_inner.estatus
            FROM asistencia.asignaciones_horario ah_inner
            WHERE ah_inner.empleado_id = e.id
              AND ah_inner.estatus = 'ACTIVA'
            ORDER BY ah_inner.fecha_inicio DESC, ah_inner.id DESC
            LIMIT 1
        ) ah ON true

        LEFT JOIN asistencia.horarios h
            ON h.id = ah.horario_id

        LEFT JOIN asistencia.tipos_turno tt
            ON tt.id = h.tipo_turno_id

        LEFT JOIN LATERAL (
            SELECT
                ed_inner.id,
                ed_inner.empleado_id,
                ed_inner.dispositivo_id,
                ed_inner.zk_uid,
                ed_inner.zk_user_id,
                ed_inner.nombre_en_dispositivo,
                ed_inner.sincronizado,
                ed_inner.activo
            FROM dispositivos.empleado_dispositivo ed_inner
            WHERE ed_inner.empleado_id = e.id
              AND ed_inner.activo = true
            ORDER BY ed_inner.id DESC
            LIMIT 1
        ) ed ON true

        LEFT JOIN dispositivos.dispositivos d
            ON d.id = ed.dispositivo_id

        {where_sql}

        ORDER BY e.id
        LIMIT :limit
        OFFSET :offset
        """
    )

    total_result = db.execute(query_total, params).mappings().first()
    items_result = db.execute(query_items, params).mappings().all()

    return {
        "total": total_result["total"] if total_result else 0,
        "limit": limit,
        "offset": offset,
        "items": [dict(row) for row in items_result],
    }

def obtener_empleado_por_codigo(
    db: Session,
    codigo_empleado: str,
    access_scope: AccessScope,
) -> dict | None:
    query = text(
        f"""
        SELECT
            e.id,
            e.codigo_empleado,
            e.nombres,
            e.apellido_paterno,
            e.apellido_materno,
            NULLIF(
                TRIM(
                    CONCAT_WS(
                        ' ',
                        e.apellido_paterno,
                        e.apellido_materno
                    )
                ),
                ''
            ) AS apellidos,
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
def obtener_perfil_empleado_por_codigo(
    db: Session,
    codigo_empleado: str,
    access_scope: AccessScope,
) -> dict | None:
    params = {
        "codigo_empleado": codigo_empleado,
        **_get_access_params(access_scope),
    }

    query = text(
        f"""
        SELECT
            e.id AS empleado_id,
            e.codigo_empleado,
            e.nombres,
            e.apellido_paterno,
            e.apellido_materno,
            NULLIF(
                TRIM(CONCAT_WS(' ', e.apellido_paterno, e.apellido_materno)),
                ''
            ) AS apellidos,
            e.nombre_completo,
            e.correo,
            e.estatus,
            e.fecha_ingreso,
            e.fecha_baja,

            uo.id AS unidad_id,
            uo.codigo AS unidad_codigo,
            uo.nombre AS unidad_nombre,
            uo.clave_organica AS unidad_clave_organica,
            tu.codigo AS tipo_unidad_codigo,
            tu.nombre AS tipo_unidad_nombre,

            p.id AS puesto_id,
            p.codigo AS puesto_codigo,
            p.nombre AS puesto_nombre,
            p.nivel_jerarquico AS puesto_nivel_jerarquico,

            sup.id AS supervisor_id,
            sup.codigo_empleado AS supervisor_codigo_empleado,
            sup.nombre_completo AS supervisor_nombre_completo,
            sup.correo AS supervisor_correo,

            us.id AS usuario_id,
            us.nombre_usuario,
            us.correo_electronico,
            us.requiere_cambio_password,
            us.ultimo_acceso,
            us.activo AS usuario_activo,
            r.id AS rol_id,
            r.codigo AS rol_codigo,
            r.nombre AS rol_nombre,

            ha.asignacion_id AS horario_asignacion_id,
            ha.horario_id,
            ha.horario_codigo,
            ha.horario_nombre,
            ha.horario_descripcion,
            ha.horario_fecha_inicio,
            ha.horario_fecha_fin,
            ha.horario_estatus,
            ha.tipo_turno_id,
            ha.tipo_turno_codigo,
            ha.tipo_turno_nombre,

            dz.empleado_dispositivo_id,
            dz.dispositivo_id,
            dz.dispositivo_codigo,
            dz.dispositivo_nombre,
            dz.dispositivo_ip,
            dz.dispositivo_puerto,
            dz.dispositivo_ubicacion,
            dz.dispositivo_modelo,
            dz.dispositivo_firmware,
            dz.zk_uid,
            dz.zk_user_id,
            dz.nombre_en_dispositivo,
            dz.privilegio,
            dz.grupo,
            dz.tarjeta,
            dz.sincronizado,
            dz.fecha_ultima_sincronizacion,
            dz.empleado_dispositivo_activo

        FROM personal.empleados e

        LEFT JOIN organizacion.unidades_organizacionales uo
            ON uo.id = e.unidad_organizacional_id

        LEFT JOIN organizacion.tipos_unidad tu
            ON tu.id = uo.tipo_unidad_id

        LEFT JOIN organizacion.puestos p
            ON p.id = e.puesto_id

        LEFT JOIN personal.empleados sup
            ON sup.id = e.supervisor_id

        LEFT JOIN seguridad.usuarios us
            ON us.empleado_id = e.id

        LEFT JOIN seguridad.roles r
            ON r.id = us.rol_id

        LEFT JOIN LATERAL (
            SELECT
                ah.id AS asignacion_id,
                h.id AS horario_id,
                h.codigo AS horario_codigo,
                h.nombre AS horario_nombre,
                h.descripcion AS horario_descripcion,
                ah.fecha_inicio AS horario_fecha_inicio,
                ah.fecha_fin AS horario_fecha_fin,
                ah.estatus AS horario_estatus,
                tt.id AS tipo_turno_id,
                tt.codigo AS tipo_turno_codigo,
                tt.nombre AS tipo_turno_nombre
            FROM asistencia.asignaciones_horario ah
            INNER JOIN asistencia.horarios h
                ON h.id = ah.horario_id
            LEFT JOIN asistencia.tipos_turno tt
                ON tt.id = h.tipo_turno_id
            WHERE ah.empleado_id = e.id
              AND ah.estatus = 'ACTIVA'
              AND ah.fecha_inicio <= CURRENT_DATE
              AND (
                    ah.fecha_fin IS NULL
                    OR ah.fecha_fin >= CURRENT_DATE
                  )
            ORDER BY
                ah.fecha_inicio DESC,
                ah.id DESC
            LIMIT 1
        ) ha ON TRUE

        LEFT JOIN LATERAL (
            SELECT
                ed.id AS empleado_dispositivo_id,
                d.id AS dispositivo_id,
                d.codigo AS dispositivo_codigo,
                d.nombre AS dispositivo_nombre,
                d.ip::text AS dispositivo_ip,
                d.puerto AS dispositivo_puerto,
                d.ubicacion AS dispositivo_ubicacion,
                d.modelo AS dispositivo_modelo,
                d.firmware AS dispositivo_firmware,
                ed.zk_uid,
                ed.zk_user_id,
                ed.nombre_en_dispositivo,
                ed.privilegio,
                ed.grupo,
                ed.tarjeta,
                ed.sincronizado,
                ed.fecha_ultima_sincronizacion,
                ed.activo AS empleado_dispositivo_activo
            FROM dispositivos.empleado_dispositivo ed
            INNER JOIN dispositivos.dispositivos d
                ON d.id = ed.dispositivo_id
            WHERE ed.empleado_id = e.id
            ORDER BY
                ed.activo DESC,
                ed.fecha_ultima_sincronizacion DESC NULLS LAST,
                ed.id DESC
            LIMIT 1
        ) dz ON TRUE

        WHERE e.codigo_empleado = :codigo_empleado
            AND {ACCESS_SCOPE_SQL}
        LIMIT 1
        """
    )

    row = db.execute(
        query,
        params,
    ).mappings().first()

    if row is None:
        return None

    data = dict(row)

    empleado = {
        "id": data["empleado_id"],
        "codigo_empleado": data["codigo_empleado"],
        "nombres": data["nombres"],
        "apellido_paterno": data["apellido_paterno"],
        "apellido_materno": data["apellido_materno"],
        "apellidos": data["apellidos"],
        "nombre_completo": data["nombre_completo"],
        "correo": data["correo"],
        "estatus": data["estatus"],
    }

    unidad_organizacional = None
    if data["unidad_id"] is not None:
        unidad_organizacional = {
            "id": data["unidad_id"],
            "codigo": data["unidad_codigo"],
            "nombre": data["unidad_nombre"],
            "clave_organica": data["unidad_clave_organica"],
            "tipo_unidad_codigo": data["tipo_unidad_codigo"],
            "tipo_unidad_nombre": data["tipo_unidad_nombre"],
        }

    puesto = None
    if data["puesto_id"] is not None:
        puesto = {
            "id": data["puesto_id"],
            "codigo": data["puesto_codigo"],
            "nombre": data["puesto_nombre"],
            "nivel_jerarquico": data["puesto_nivel_jerarquico"],
        }

    supervisor = None
    if data["supervisor_id"] is not None:
        supervisor = {
            "id": data["supervisor_id"],
            "codigo_empleado": data["supervisor_codigo_empleado"],
            "nombre_completo": data["supervisor_nombre_completo"],
            "correo": data["supervisor_correo"],
        }

    usuario_sistema = None
    if data["usuario_id"] is not None:
        usuario_sistema = {
            "id": data["usuario_id"],
            "nombre_usuario": data["nombre_usuario"],
            "correo_electronico": data["correo_electronico"],
            "requiere_cambio_password": data["requiere_cambio_password"],
            "ultimo_acceso": data["ultimo_acceso"],
            "activo": data["usuario_activo"],
            "rol_id": data["rol_id"],
            "rol_codigo": data["rol_codigo"],
            "rol_nombre": data["rol_nombre"],
        }

    horario_actual = None
    if data["horario_id"] is not None:
        horario_actual = {
            "asignacion_id": data["horario_asignacion_id"],
            "horario_id": data["horario_id"],
            "codigo": data["horario_codigo"],
            "nombre": data["horario_nombre"],
            "descripcion": data["horario_descripcion"],
            "fecha_inicio": data["horario_fecha_inicio"],
            "fecha_fin": data["horario_fecha_fin"],
            "estatus": data["horario_estatus"],
            "tipo_turno_id": data["tipo_turno_id"],
            "tipo_turno_codigo": data["tipo_turno_codigo"],
            "tipo_turno_nombre": data["tipo_turno_nombre"],
        }

    dispositivo = None
    if data["empleado_dispositivo_id"] is not None:
        dispositivo = {
            "empleado_dispositivo_id": data["empleado_dispositivo_id"],
            "dispositivo_id": data["dispositivo_id"],
            "codigo": data["dispositivo_codigo"],
            "nombre": data["dispositivo_nombre"],
            "ip": data["dispositivo_ip"],
            "puerto": data["dispositivo_puerto"],
            "ubicacion": data["dispositivo_ubicacion"],
            "modelo": data["dispositivo_modelo"],
            "firmware": data["dispositivo_firmware"],
            "zk_uid": data["zk_uid"],
            "zk_user_id": data["zk_user_id"],
            "nombre_en_dispositivo": data["nombre_en_dispositivo"],
            "privilegio": data["privilegio"],
            "grupo": data["grupo"],
            "tarjeta": data["tarjeta"],
            "sincronizado": data["sincronizado"],
            "fecha_ultima_sincronizacion": data["fecha_ultima_sincronizacion"],
            "activo": data["empleado_dispositivo_activo"],
        }

    return {
        "empleado": empleado,
        "unidad_organizacional": unidad_organizacional,
        "puesto": puesto,
        "supervisor": supervisor,
        "usuario_sistema": usuario_sistema,
        "horario_actual": horario_actual,
        "dispositivo": dispositivo,
    }