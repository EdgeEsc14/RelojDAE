from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.core.auth_dependencies import require_module_access
from app.core.database import get_db
from app.repositories.empleados_integral_repo import (
    crear_alta_integral_empleado,
)
from app.repositories.empleados_repo import (
    listar_empleados,
    obtener_empleado_por_codigo,
    obtener_perfil_empleado_por_codigo,
)
from app.repositories.empleados_write_repo import (
    actualizar_empleado,
    actualizar_estatus_empleado,
    crear_empleado,
    generar_siguiente_codigo_empleado,
)
from app.schemas.empleados import (
    EmpleadoPerfilResponse,
    EmpleadoResumen,
    EmpleadosListadoResponse,
)
from app.schemas.empleados_integral import (
    AltaIntegralEmpleadoRequest,
    AltaIntegralEmpleadoResponse,
)
from app.schemas.empleados_write import (
    EmpleadoCreate,
    EmpleadoEstatusUpdate,
    EmpleadoUpdate,
    SiguienteCodigoEmpleadoResponse,
)
from app.schemas.empleados_sincronizacion import (
    SincronizarRelojesRequest,
    SincronizarRelojesResponse,
)
from app.services.empleados_sincronizacion_service import (
    sincronizar_empleado_relojes,
)
from app.services.institucion_config import obtener_configuracion_institucional

router = APIRouter(
    prefix="/empleados",
    tags=["Empleados"],
)


@router.post(
    "/alta-integral",
    response_model=AltaIntegralEmpleadoResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_alta_integral_empleado(
    payload: AltaIntegralEmpleadoRequest,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "crear",
            )
        ),
    ],
) -> dict:
    try:
        resultado = crear_alta_integral_empleado(
            db=db,
            payload=payload,
            solicitado_por_usuario_id=(
                access_scope.user_id
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Auto-sincronización con ZKTeco después del commit exitoso.
    # Si falla el reloj, el empleado queda creado con estado PENDIENTE/ERROR.
    # No hace rollback del empleado.
    sincronizacion_resultado = None

    if resultado.get("sincronizacion_solicitada") and resultado.get("dispositivos"):
        try:
            sincronizacion_resultado = sincronizar_empleado_relojes(
                db=db,
                codigo_empleado=resultado["codigo_empleado"],
                access_scope=access_scope,
            )
        except Exception as sync_exc:
            sincronizacion_resultado = {
                "ok": False,
                "error": str(sync_exc),
                "estado": "ERROR_SINCRONIZACION",
            }

    resultado["sincronizacion_resultado"] = sincronizacion_resultado

    return resultado
@router.post(
    "/{codigo_empleado}/sincronizar-relojes",
    response_model=SincronizarRelojesResponse,
)
def post_sincronizar_relojes_empleado(
    codigo_empleado: str,
    payload: SincronizarRelojesRequest,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "editar",
            )
        ),
    ],
) -> dict:
    try:
        return sincronizar_empleado_relojes(
            db=db,
            codigo_empleado=codigo_empleado,
            access_scope=access_scope,
            dispositivo_ids=payload.dispositivo_ids,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{codigo_empleado}/dispositivos/"
    "{dispositivo_id}/reintentar",
    response_model=SincronizarRelojesResponse,
)
def post_reintentar_sincronizacion_dispositivo(
    codigo_empleado: str,
    dispositivo_id: int,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "editar",
            )
        ),
    ],
) -> dict:
    try:
        return sincronizar_empleado_relojes(
            db=db,
            codigo_empleado=codigo_empleado,
            access_scope=access_scope,
            dispositivo_ids=[dispositivo_id],
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=EmpleadosListadoResponse,
)
def get_empleados(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "consultar",
            )
        ),
    ],
    q: Annotated[
        str | None,
        Query(
            description=(
                "Búsqueda por código, nombre o correo"
            )
        ),
    ] = None,
    estatus: Annotated[
        str | None,
        Query(
            description=(
                "Filtro por estatus del empleado"
            )
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=500),
    ] = 100,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
) -> dict:
    return listar_empleados(
        db=db,
        access_scope=access_scope,
        q=q,
        estatus=estatus,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/siguiente-codigo",
    response_model=SiguienteCodigoEmpleadoResponse,
)
def get_siguiente_codigo_empleado(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "crear",
            )
        ),
    ],
    prefijo: Annotated[
        str | None,
        Query(min_length=2, max_length=10),
    ] = None,
) -> dict:
    try:
        return generar_siguiente_codigo_empleado(
            db=db,
            prefijo=prefijo
            or obtener_configuracion_institucional()["prefijo_codigo_empleado"],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "/siguiente-zk-user-id",
)
def get_siguiente_zk_user_id(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "crear",
            )
        ),
    ],
) -> dict:
    """
    Calcula el siguiente zk_user_id disponible.

    Consulta:
    1. Máximo zk_user_id en dispositivos.empleado_dispositivo
    2. Máximo zk_user_id en personal.empleados
    3. (Opcional) Usuarios actuales del reloj si está conectado

    Retorna el siguiente disponible que no esté en uso.
    """
    from app.repositories.empleados_integral_repo import _generar_siguiente_zk_user_id
    from contextlib import suppress
    from app.services.zk_service import ZKDeviceService

    # ID sugerido por BD
    zk_id_bd = _generar_siguiente_zk_user_id(db)

    # Intentar verificar contra reloj real
    zk_id_final = zk_id_bd
    reloj_consultado = False
    reloj_ids_usados = []

    with suppress(Exception):
        service = ZKDeviceService()
        users = service.list_users(include_admin=True)
        reloj_consultado = True
        reloj_ids_usados = [
            int(u["user_id"])
            for u in users
            if u.get("user_id", "").isdigit()
        ]

        # Asegurar que el ID no esté en el reloj
        candidate = int(zk_id_bd)
        while candidate in reloj_ids_usados:
            candidate += 1
        zk_id_final = str(candidate)

    return {
        "zk_user_id": zk_id_final,
        "reloj_consultado": reloj_consultado,
        "fuente": "BD+RELOJ" if reloj_consultado else "BD",
    }


@router.post(
    "",
    response_model=EmpleadoResumen,
    status_code=status.HTTP_201_CREATED,
)
def post_empleado(
    payload: EmpleadoCreate,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "crear",
            )
        ),
    ],
) -> dict:
    try:
        return crear_empleado(
            db=db,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/exportar-csv")
def get_exportar_empleados(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "consultar",
            )
        ),
    ],
) -> Response:
    """Exporta listado de empleados en formato CSV."""
    import csv
    import io

    from sqlalchemy import text as sql_text

    query = sql_text("""
        SELECT
            e.codigo_empleado,
            e.nombre_completo,
            e.rfc,
            COALESCE(e.correo, e.correo_personal, '') AS correo,
            COALESCE(uo.nombre, '') AS area,
            COALESCE(p.nombre, '') AS puesto,
            COALESCE(sup.nombre_completo, '') AS supervisor,
            COALESCE(h.nombre, '') AS horario,
            COALESCE(e.zk_user_id, '') AS zk_user_id,
            COALESCE(d.nombre, '') AS dispositivo,
            e.estatus
        FROM personal.empleados e
        LEFT JOIN organizacion.unidades_organizacionales uo ON uo.id = e.unidad_organizacional_id
        LEFT JOIN organizacion.puestos p ON p.id = e.puesto_id
        LEFT JOIN personal.empleados sup ON sup.id = e.supervisor_id
        LEFT JOIN asistencia.asignaciones_horario ah
            ON ah.empleado_id = e.id AND ah.estatus = 'ACTIVA'
           AND ah.fecha_inicio <= CURRENT_DATE AND (ah.fecha_fin IS NULL OR ah.fecha_fin >= CURRENT_DATE)
        LEFT JOIN asistencia.horarios h ON h.id = ah.horario_id
        LEFT JOIN dispositivos.empleado_dispositivo ed ON ed.empleado_id = e.id AND ed.activo = TRUE
        LEFT JOIN dispositivos.dispositivos d ON d.id = ed.dispositivo_id
        ORDER BY e.codigo_empleado
    """)

    rows = db.execute(query).mappings().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Codigo", "Nombre", "RFC", "Correo", "Area", "Puesto", "Supervisor", "Horario", "ZK User ID", "Dispositivo", "Estatus"])

    for row in rows:
        writer.writerow([
            row["codigo_empleado"], row["nombre_completo"], row["rfc"] or "",
            row["correo"], row["area"], row["puesto"], row["supervisor"],
            row["horario"], row["zk_user_id"], row["dispositivo"], row["estatus"],
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="empleados.csv"'},
    )


@router.get(
    "/{codigo_empleado}/perfil",
    response_model=EmpleadoPerfilResponse,
)
def get_perfil_empleado_por_codigo(
    codigo_empleado: str,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "consultar",
            )
        ),
    ],
) -> dict:
    perfil = obtener_perfil_empleado_por_codigo(
        db=db,
        codigo_empleado=codigo_empleado,
        access_scope=access_scope,
    )

    if perfil is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No existe el empleado solicitado "
                "o no tienes permiso para consultarlo."
            ),
        )

    return perfil


@router.put(
    "/{codigo_empleado}",
    response_model=EmpleadoResumen,
)
def put_empleado(
    codigo_empleado: str,
    payload: EmpleadoUpdate,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "editar",
            )
        ),
    ],
) -> dict:
    try:
        empleado = actualizar_empleado(
            db=db,
            codigo_empleado=codigo_empleado,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if empleado is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No existe empleado con código "
                f"{codigo_empleado}"
            ),
        )

    return empleado


@router.patch(
    "/{codigo_empleado}/estatus",
    response_model=EmpleadoResumen,
)
def patch_estatus_empleado(
    codigo_empleado: str,
    payload: EmpleadoEstatusUpdate,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "editar",
            )
        ),
    ],
) -> dict:
    try:
        empleado = actualizar_estatus_empleado(
            db=db,
            codigo_empleado=codigo_empleado,
            estatus=payload.estatus,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if empleado is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No existe empleado con código "
                f"{codigo_empleado}"
            ),
        )

    return empleado


@router.get(
    "/{codigo_empleado}",
    response_model=EmpleadoResumen,
)
def get_empleado_por_codigo(
    codigo_empleado: str,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "consultar",
            )
        ),
    ],
) -> dict:
    empleado = obtener_empleado_por_codigo(
        db=db,
        codigo_empleado=codigo_empleado,
        access_scope=access_scope,
    )

    if empleado is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No existe el empleado solicitado "
                "o no tienes permiso para consultarlo."
            ),
        )

    return empleado







@router.get("/{codigo_empleado}/verificar-zk")
def get_verificar_zk_empleado(
    codigo_empleado: str,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    _access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "EMPLEADOS",
                "consultar",
            )
        ),
    ],
) -> dict:
    """
    Verifica si el empleado existe realmente en el reloj ZKTeco.

    Consulta get_users() en el dispositivo asignado y busca el zk_user_id.
    """
    from contextlib import suppress
    from sqlalchemy import text as sql_text
    from app.services.zk_service import ZKDeviceService, ZKSettings

    # Obtener empleado con su relación de dispositivo
    row = db.execute(sql_text("""
        SELECT
            e.id, e.codigo_empleado, e.nombre_completo, e.zk_user_id,
            ed.zk_user_id AS ed_zk_user_id, ed.estado_sincronizacion,
            ed.dispositivo_id, ed.nombre_en_dispositivo,
            HOST(d.ip) AS ip, d.puerto, d.password_comunicacion, d.nombre AS dispositivo_nombre
        FROM personal.empleados e
        LEFT JOIN dispositivos.empleado_dispositivo ed
            ON ed.empleado_id = e.id AND ed.activo = TRUE
        LEFT JOIN dispositivos.dispositivos d
            ON d.id = ed.dispositivo_id AND d.activo = TRUE
        WHERE e.codigo_empleado = :codigo
        LIMIT 1
    """), {"codigo": codigo_empleado}).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado.")

    zk_user_id = row["ed_zk_user_id"] or row["zk_user_id"]

    if not zk_user_id:
        return {
            "ok": True,
            "existe_en_reloj": False,
            "estado": "SIN_ZK_USER_ID",
            "mensaje": "El empleado no tiene zk_user_id asignado.",
        }

    if not row["ip"]:
        return {
            "ok": True,
            "existe_en_reloj": False,
            "estado": "SIN_DISPOSITIVO",
            "mensaje": "El empleado no tiene un dispositivo activo asignado.",
        }

    try:
        settings = ZKSettings(
            ip=row["ip"], port=row["puerto"], password=row["password_comunicacion"],
            timeout=10, force_udp=False, ommit_ping=True,
            allow_writes=False, protected_user_ids=set(), protected_names=set(),
        )
        service = ZKDeviceService(settings=settings)
        users = service.list_users(include_admin=True)

        found = next((u for u in users if str(u["user_id"]) == str(zk_user_id)), None)

        if found:
            # Verificar si tiene plantillas biométricas (huellas)
            huella_estado = "NO_VERIFICABLE"

            return {
                "ok": True,
                "existe_en_reloj": True,
                "estado": "ENCONTRADO",
                "zk_user_id": zk_user_id,
                "nombre_en_reloj": found.get("name"),
                "uid": found.get("uid"),
                "dispositivo": row["dispositivo_nombre"],
                "huella": huella_estado,
                "mensaje": f"Usuario {zk_user_id} encontrado en el reloj.",
            }
        else:
            return {
                "ok": True,
                "existe_en_reloj": False,
                "estado": "NO_ENCONTRADO",
                "zk_user_id": zk_user_id,
                "dispositivo": row["dispositivo_nombre"],
                "mensaje": f"Usuario {zk_user_id} NO encontrado en el reloj.",
            }

    except Exception as exc:
        return {
            "ok": False,
            "existe_en_reloj": False,
            "estado": "ERROR_CONEXION",
            "error": str(exc),
            "mensaje": "No se pudo conectar al dispositivo.",
        }
