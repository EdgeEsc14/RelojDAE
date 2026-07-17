from sqlalchemy import text
from sqlalchemy.orm import Session


def _crear_filtros_basicos(
    q: str | None,
    activo: bool | None,
    alias: str = "",
) -> tuple[str, dict]:
    filtros = []
    params: dict = {}

    prefijo = f"{alias}." if alias else ""

    if q:
        filtros.append(
            f"""
            (
                {prefijo}codigo ILIKE :q
                OR {prefijo}nombre ILIKE :q
            )
            """
        )
        params["q"] = f"%{q}%"

    if activo is not None:
        filtros.append(f"{prefijo}activo = :activo")
        params["activo"] = activo

    where_sql = ""

    if filtros:
        where_sql = "WHERE " + " AND ".join(filtros)

    return where_sql, params


def listar_unidades_organizacionales(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:
    filtros = []
    params: dict = {}

    if q:
        filtros.append(
            """
            (
                uo.codigo ILIKE :q
                OR uo.nombre ILIKE :q
                OR uo.clave_organica ILIKE :q
            )
            """
        )
        params["q"] = f"%{q}%"

    if activo is not None:
        filtros.append("uo.activo = :activo")
        params["activo"] = activo

    where_sql = ""

    if filtros:
        where_sql = "WHERE " + " AND ".join(filtros)

    query = text(
        f"""
        SELECT
            uo.id,
            uo.codigo,
            uo.nombre,
            uo.descripcion,
            uo.unidad_padre_id,
            uo.activo,
            uo.tipo_unidad_id,
            tu.codigo AS tipo_unidad_codigo,
            tu.nombre AS tipo_unidad_nombre,
            uo.clave_organica,
            uo.orden_visual
        FROM organizacion.unidades_organizacionales uo
        INNER JOIN organizacion.tipos_unidad tu
            ON tu.id = uo.tipo_unidad_id
        {where_sql}
        ORDER BY
            uo.orden_visual,
            uo.codigo,
            uo.nombre
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def listar_puestos(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:
    where_sql, params = _crear_filtros_basicos(
        q=q,
        activo=activo,
    )

    query = text(
        f"""
        SELECT
            id,
            codigo,
            nombre,
            descripcion,
            nivel_jerarquico,
            activo
        FROM organizacion.puestos
        {where_sql}
        ORDER BY
            nivel_jerarquico,
            nombre
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def listar_tipos_turno(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:
    where_sql, params = _crear_filtros_basicos(
        q=q,
        activo=activo,
    )

    query = text(
        f"""
        SELECT
            id,
            codigo,
            nombre,
            descripcion,
            hora_entrada_desde,
            hora_entrada_hasta,
            duracion_jornada_minutos,
            modalidad_tiempo_extra,
            activo
        FROM asistencia.tipos_turno
        {where_sql}
        ORDER BY
            codigo,
            nombre
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def listar_horarios(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:
    filtros = []
    params: dict = {}

    if q:
        filtros.append(
            """
            (
                h.codigo ILIKE :q
                OR h.nombre ILIKE :q
                OR tt.codigo ILIKE :q
                OR tt.nombre ILIKE :q
            )
            """
        )
        params["q"] = f"%{q}%"

    if activo is not None:
        filtros.append("h.activo = :activo")
        params["activo"] = activo

    where_sql = ""

    if filtros:
        where_sql = "WHERE " + " AND ".join(filtros)

    query = text(
        f"""
        SELECT
            h.id,
            h.codigo,
            h.nombre,
            h.descripcion,
            h.tolerancia_entrada_minutos,
            h.descanso_minutos,
            h.permite_tiempo_extra,
            h.activo,
            h.tipo_turno_id,
            tt.codigo AS tipo_turno_codigo,
            tt.nombre AS tipo_turno_nombre
        FROM asistencia.horarios h
        INNER JOIN asistencia.tipos_turno tt
            ON tt.id = h.tipo_turno_id
        {where_sql}
        ORDER BY
            h.codigo,
            h.nombre
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def listar_dispositivos(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:
    filtros = []
    params: dict = {}

    if q:
        filtros.append(
            """
            (
                codigo ILIKE :q
                OR nombre ILIKE :q
                OR ubicacion ILIKE :q
                OR modelo ILIKE :q
                OR firmware ILIKE :q
                OR numero_serie ILIKE :q
                OR ip::text ILIKE :q
            )
            """
        )
        params["q"] = f"%{q}%"

    if activo is not None:
        filtros.append("activo = :activo")
        params["activo"] = activo

    where_sql = ""

    if filtros:
        where_sql = "WHERE " + " AND ".join(filtros)

    query = text(
        f"""
        SELECT
            id,
            codigo,
            nombre,
            ip::text AS ip,
            puerto,
            numero_serie,
            modelo,
            firmware,
            ubicacion,
            activo,
            ultima_conexion,
            ultima_sincronizacion
        FROM dispositivos.dispositivos
        {where_sql}
        ORDER BY
            codigo,
            nombre
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def listar_roles(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:
    where_sql, params = _crear_filtros_basicos(
        q=q,
        activo=activo,
    )

    query = text(
        f"""
        SELECT
            id,
            codigo,
            nombre,
            descripcion,
            es_sistema,
            orden_visual,
            activo
        FROM seguridad.roles
        {where_sql}
        ORDER BY
            orden_visual,
            nombre
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def listar_tipos_marcacion(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:
    where_sql, params = _crear_filtros_basicos(
        q=q,
        activo=activo,
    )

    query = text(
        f"""
        SELECT
            id,
            codigo,
            nombre,
            descripcion,
            categoria,
            es_entrada,
            es_salida,
            es_tiempo_extra,
            requiere_pareja,
            activo
        FROM asistencia.tipos_marcacion
        {where_sql}
        ORDER BY
            categoria,
            codigo,
            nombre
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def listar_tipos_incidencia(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:
    where_sql, params = _crear_filtros_basicos(
        q=q,
        activo=activo,
    )

    query = text(
        f"""
        SELECT
            id,
            codigo,
            nombre,
            descripcion,
            categoria,
            genera_puntos,
            puntos_default,
            requiere_justificacion,
            requiere_aprobacion,
            afecta_asistencia,
            activo,
            orden_visual
        FROM asistencia.tipos_incidencia
        {where_sql}
        ORDER BY
            orden_visual,
            categoria,
            nombre
        """
    )

    rows = db.execute(query, params).mappings().all()

    return [dict(row) for row in rows]

def listar_tipos_contratacion(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:

    where_sql, params = _crear_filtros_basicos(
        q=q,
        activo=activo,
    )

    query = text(
        f"""
        SELECT
            id,
            codigo,
            nombre,
            descripcion,
            activo
        FROM personal.tipos_contratacion
        {where_sql}
        ORDER BY
            codigo,
            nombre
        """
    )

    rows = db.execute(
        query,
        params,
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]



def obtener_todos_catalogos(db: Session) -> dict:
    return {
        "unidades_organizacionales": listar_unidades_organizacionales(db=db),
        "puestos": listar_puestos(db=db),
        "tipos_turno": listar_tipos_turno(db=db),
        "horarios": listar_horarios(db=db),
        "dispositivos": listar_dispositivos(db=db),
        "roles": listar_roles(db=db),
        "tipos_marcacion": listar_tipos_marcacion(db=db),
        "tipos_incidencia": listar_tipos_incidencia(db=db),
        "tipos_contratacion": listar_tipos_contratacion(db=db),
    }

def listar_tipos_contratacion(
    db: Session,
    q: str | None = None,
    activo: bool | None = True,
) -> list[dict]:
    where_sql, params = _crear_filtros_basicos(
        q=q,
        activo=activo,
    )

    query = text(
        f"""
        SELECT
            id,
            codigo,
            nombre,
            descripcion,
            activo
        FROM personal.tipos_contratacion
        {where_sql}
        ORDER BY
            codigo,
            nombre
        """
    )

    rows = db.execute(
        query,
        params,
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]