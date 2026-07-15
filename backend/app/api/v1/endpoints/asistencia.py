from datetime import date
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
from app.repositories.asistencia_procesamiento_repo import (
    procesar_asistencia_diaria,
)
from app.repositories.asistencia_repo import (
    listar_asistencia_diaria,
    obtener_resumen_asistencia_empleado,
)
from app.schemas.asistencia import (
    AsistenciaDiariaListadoResponse,
    AsistenciaEmpleadoResumenResponse,
)
from app.schemas.asistencia_procesamiento import (
    ProcesarAsistenciaRequest,
    ProcesarAsistenciaResponse,
)


router = APIRouter(
    prefix="/asistencia",
    tags=["Asistencia"],
)


@router.get(
    "/diaria",
    response_model=AsistenciaDiariaListadoResponse,
)
def get_asistencia_diaria(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "ASISTENCIA",
                "consultar",
            )
        ),
    ],
    fecha: Annotated[
        date,
        Query(
            description=(
                "Fecha de asistencia en formato YYYY-MM-DD"
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
                "Filtro por estatus de asistencia"
            )
        ),
    ] = None,
    unidad_organizacional_id: Annotated[
        int | None,
        Query(
            ge=1,
            description=(
                "Filtro por unidad organizacional"
            ),
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
    return listar_asistencia_diaria(
        db=db,
        fecha=fecha,
        access_scope=access_scope,
        q=q,
        estatus=estatus,
        unidad_organizacional_id=(
            unidad_organizacional_id
        ),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/empleados/{codigo_empleado}/resumen",
    response_model=AsistenciaEmpleadoResumenResponse,
)
def get_resumen_asistencia_empleado(
    codigo_empleado: str,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "ASISTENCIA",
                "consultar",
            )
        ),
    ],
    limite: Annotated[
        int,
        Query(ge=1, le=30),
    ] = 10,
) -> dict:
    resumen = obtener_resumen_asistencia_empleado(
        db=db,
        codigo_empleado=codigo_empleado,
        access_scope=access_scope,
        limite=limite,
    )

    if resumen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No existe el empleado solicitado "
                "o no tienes permiso para consultar "
                "su asistencia."
            ),
        )

    return resumen


@router.post(
    "/procesar",
    response_model=ProcesarAsistenciaResponse,
)
def post_procesar_asistencia(
    payload: ProcesarAsistenciaRequest,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    access_scope: Annotated[
        AccessScope,
        Depends(
            require_module_access(
                "ASISTENCIA",
                "editar",
            )
        ),
    ],
) -> dict:
    # El procesamiento actual trabaja sobre todos los empleados
    # encontrados en el periodo. Por seguridad, hasta que el
    # procesador soporte AREA, solamente se permite alcance TOTAL.
    if not access_scope.has_complete_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El procesamiento global de asistencia "
                "requiere alcance total."
            ),
        )

    return procesar_asistencia_diaria(
        db=db,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
    )