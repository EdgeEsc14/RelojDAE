from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.catalogos_repo import (
    listar_dispositivos,
    listar_horarios,
    listar_puestos,
    listar_roles,
    listar_tipos_incidencia,
    listar_tipos_marcacion,
    listar_tipos_turno,
    listar_unidades_organizacionales,
    obtener_todos_catalogos,
)
from app.schemas.catalogos import (
    CatalogosTodosResponse,
    DispositivoCatalogoItem,
    HorarioCatalogoItem,
    PuestoCatalogoItem,
    RolCatalogoItem,
    TipoIncidenciaCatalogoItem,
    TipoMarcacionCatalogoItem,
    TipoTurnoCatalogoItem,
    UnidadOrganizacionalCatalogoItem,
)
from app.core.auth_dependencies import get_current_user

router = APIRouter(
    prefix="/catalogos",
    tags=["Catálogos"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.get("/todos", response_model=CatalogosTodosResponse)
def get_todos_catalogos(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return obtener_todos_catalogos(db=db)


@router.get(
    "/unidades-organizacionales",
    response_model=list[UnidadOrganizacionalCatalogoItem],
)
def get_unidades_organizacionales(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(description="Buscar por código, nombre o clave orgánica")] = None,
    activo: Annotated[bool | None, Query(description="Filtrar por activo/inactivo")] = True,
) -> list[dict]:
    return listar_unidades_organizacionales(
        db=db,
        q=q,
        activo=activo,
    )


@router.get(
    "/puestos",
    response_model=list[PuestoCatalogoItem],
)
def get_puestos(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(description="Buscar por código o nombre")] = None,
    activo: Annotated[bool | None, Query(description="Filtrar por activo/inactivo")] = True,
) -> list[dict]:
    return listar_puestos(
        db=db,
        q=q,
        activo=activo,
    )


@router.get(
    "/tipos-turno",
    response_model=list[TipoTurnoCatalogoItem],
)
def get_tipos_turno(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(description="Buscar por código o nombre")] = None,
    activo: Annotated[bool | None, Query(description="Filtrar por activo/inactivo")] = True,
) -> list[dict]:
    return listar_tipos_turno(
        db=db,
        q=q,
        activo=activo,
    )


@router.get(
    "/horarios",
    response_model=list[HorarioCatalogoItem],
)
def get_horarios(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(description="Buscar por código, nombre o tipo de turno")] = None,
    activo: Annotated[bool | None, Query(description="Filtrar por activo/inactivo")] = True,
) -> list[dict]:
    return listar_horarios(
        db=db,
        q=q,
        activo=activo,
    )


@router.get(
    "/dispositivos",
    response_model=list[DispositivoCatalogoItem],
)
def get_dispositivos(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(description="Buscar por código, nombre, IP, ubicación, modelo o serie")] = None,
    activo: Annotated[bool | None, Query(description="Filtrar por activo/inactivo")] = True,
) -> list[dict]:
    return listar_dispositivos(
        db=db,
        q=q,
        activo=activo,
    )


@router.get(
    "/roles",
    response_model=list[RolCatalogoItem],
)
def get_roles(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(description="Buscar por código o nombre")] = None,
    activo: Annotated[bool | None, Query(description="Filtrar por activo/inactivo")] = True,
) -> list[dict]:
    return listar_roles(
        db=db,
        q=q,
        activo=activo,
    )


@router.get(
    "/tipos-marcacion",
    response_model=list[TipoMarcacionCatalogoItem],
)
def get_tipos_marcacion(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(description="Buscar por código o nombre")] = None,
    activo: Annotated[bool | None, Query(description="Filtrar por activo/inactivo")] = True,
) -> list[dict]:
    return listar_tipos_marcacion(
        db=db,
        q=q,
        activo=activo,
    )


@router.get(
    "/tipos-incidencia",
    response_model=list[TipoIncidenciaCatalogoItem],
)
def get_tipos_incidencia(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(description="Buscar por código o nombre")] = None,
    activo: Annotated[bool | None, Query(description="Filtrar por activo/inactivo")] = True,
) -> list[dict]:
    return listar_tipos_incidencia(
        db=db,
        q=q,
        activo=activo,
    )