from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
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
        return crear_alta_integral_empleado(
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
        Query(ge=1, le=100),
    ] = 20,
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
        str,
        Query(min_length=2, max_length=10),
    ] = "DAE",
) -> dict:
    try:
        return generar_siguiente_codigo_empleado(
            db=db,
            prefijo=prefijo,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


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