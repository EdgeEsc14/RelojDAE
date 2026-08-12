"""
Endpoints para gestión de dispositivos ZKTeco.

CRUD + probar conexión + información del dispositivo.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.core.auth_dependencies import require_module_access
from app.core.database import get_db
from app.repositories.dispositivos_repo import (
    actualizar_dispositivo,
    actualizar_estado_conexion,
    crear_dispositivo,
    listar_dispositivos,
    obtener_dispositivo_por_id,
)
from app.services.zk_service import ZKDeviceService, ZKSettings
from app.services.dispositivos_hora_service import (
    consultar_hora_dispositivo,
    sincronizar_hora_dispositivo,
    sincronizar_hora_todos_activos,
)


router = APIRouter(
    prefix="/dispositivos",
    tags=["Dispositivos"],
)


def _probar_conexion_dispositivo(ip: str, puerto: int, password: int, timeout: int = 10) -> dict:
    """
    Intenta conectarse a un dispositivo ZKTeco y obtener su información.
    Retorna dict con resultado de la prueba.
    """

    settings = ZKSettings(
        ip=ip,
        port=puerto,
        password=password,
        timeout=timeout,
        force_udp=False,
        ommit_ping=True,
        allow_writes=False,
        protected_user_ids=set(),
        protected_names=set(),
    )

    service = ZKDeviceService(settings=settings)
    inicio = datetime.now()

    try:
        with service.connection(disable_device=False) as conn:
            firmware = None
            serial = None
            platform = None
            device_name = None
            total_users = 0
            device_time = None

            with suppress(Exception):
                firmware = conn.get_firmware_version()

            with suppress(Exception):
                serial = conn.get_serialnumber()

            with suppress(Exception):
                platform = conn.get_platform()

            with suppress(Exception):
                device_name = conn.get_device_name()

            with suppress(Exception):
                users = conn.get_users()
                total_users = len(users) if users else 0

            with suppress(Exception):
                device_time = conn.get_time()

        duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)

        return {
            "ok": True,
            "estado": "CONECTADO",
            "firmware": firmware,
            "numero_serie": serial,
            "plataforma": platform,
            "nombre_dispositivo": device_name,
            "total_usuarios": total_users,
            "hora_dispositivo": device_time.isoformat() if device_time else None,
            "hora_servidor": datetime.now().isoformat(),
            "desfase_segundos": (
                int((datetime.now() - device_time).total_seconds())
                if device_time else None
            ),
            "duracion_ms": duracion_ms,
            "error": None,
        }

    except Exception as exc:
        duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
        return {
            "ok": False,
            "estado": "ERROR",
            "firmware": None,
            "numero_serie": None,
            "plataforma": None,
            "nombre_dispositivo": None,
            "total_usuarios": 0,
            "hora_dispositivo": None,
            "hora_servidor": datetime.now().isoformat(),
            "desfase_segundos": None,
            "duracion_ms": duracion_ms,
            "error": str(exc),
        }


# ============================================================
# GET /dispositivos — Listar
# ============================================================


@router.get("")
def get_dispositivos(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("DISPOSITIVOS", "consultar")),
    ],
    activo: bool | None = Query(default=None),
    busqueda: str | None = Query(default=None, max_length=100),
) -> list[dict]:
    """Lista dispositivos registrados en la base de datos."""

    return listar_dispositivos(db, activo=activo, busqueda=busqueda)


# ============================================================
# GET /dispositivos/{id} — Detalle
# ============================================================


@router.get("/{dispositivo_id}")
def get_dispositivo(
    dispositivo_id: int,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("DISPOSITIVOS", "consultar")),
    ],
) -> dict:
    """Obtiene detalle completo de un dispositivo."""

    dispositivo = obtener_dispositivo_por_id(db, dispositivo_id)

    if dispositivo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe dispositivo con id {dispositivo_id}.",
        )

    return dispositivo


# ============================================================
# POST /dispositivos — Crear
# ============================================================


@router.post("", status_code=status.HTTP_201_CREATED)
def post_dispositivo(
    payload: dict,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("DISPOSITIVOS", "crear")),
    ],
) -> dict:
    """Crea un nuevo dispositivo."""

    nombre = (payload.get("nombre") or "").strip()
    ip = (payload.get("ip") or "").strip()
    codigo = (payload.get("codigo") or "").strip().upper()

    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio.")
    if not ip:
        raise HTTPException(status_code=400, detail="La IP es obligatoria.")
    if not codigo:
        # Generar código automático
        codigo = "ZK_" + ip.replace(".", "_")

    try:
        dispositivo = crear_dispositivo(
            db,
            codigo=codigo,
            nombre=nombre,
            ip=ip,
            puerto=payload.get("puerto", 4370),
            password_comunicacion=payload.get("password_comunicacion", 0),
            ubicacion=payload.get("ubicacion"),
            descripcion=payload.get("descripcion"),
            modelo=payload.get("modelo"),
            numero_serie=payload.get("numero_serie"),
            firmware=payload.get("firmware"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear dispositivo: {exc}",
        ) from exc

    return dispositivo


# ============================================================
# PATCH /dispositivos/{id} — Actualizar
# ============================================================


@router.patch("/{dispositivo_id}")
def patch_dispositivo(
    dispositivo_id: int,
    payload: dict,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("DISPOSITIVOS", "editar")),
    ],
) -> dict:
    """Actualiza campos de un dispositivo."""

    dispositivo = actualizar_dispositivo(
        db,
        dispositivo_id,
        nombre=payload.get("nombre"),
        ip=payload.get("ip"),
        puerto=payload.get("puerto"),
        password_comunicacion=payload.get("password_comunicacion"),
        ubicacion=payload.get("ubicacion"),
        descripcion=payload.get("descripcion"),
        modelo=payload.get("modelo"),
        numero_serie=payload.get("numero_serie"),
        firmware=payload.get("firmware"),
        activo=payload.get("activo"),
    )

    if dispositivo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe dispositivo con id {dispositivo_id}.",
        )

    return dispositivo


# ============================================================
# POST /dispositivos/{id}/probar-conexion — Probar conexión
# ============================================================


@router.post("/{dispositivo_id}/probar-conexion")
def post_probar_conexion(
    dispositivo_id: int,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("DISPOSITIVOS", "consultar")),
    ],
) -> dict:
    """
    Prueba conexión real con un dispositivo ZKTeco por su ID.

    Obtiene firmware, serial, usuarios, hora del dispositivo.
    Actualiza el estado de conexión en la base de datos.
    """

    dispositivo = obtener_dispositivo_por_id(db, dispositivo_id)

    if dispositivo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe dispositivo con id {dispositivo_id}.",
        )

    if not dispositivo["activo"]:
        return {
            "dispositivo_id": dispositivo_id,
            "ok": False,
            "estado": "DESHABILITADO",
            "error": "El dispositivo está deshabilitado.",
        }

    resultado = _probar_conexion_dispositivo(
        ip=dispositivo["ip"],
        puerto=dispositivo["puerto"],
        password=dispositivo["password_comunicacion"],
    )

    # Persistir resultado en BD
    actualizar_estado_conexion(
        db,
        dispositivo_id,
        estado_conexion=resultado["estado"],
        ultimo_error=resultado.get("error"),
        modelo=resultado.get("plataforma") or resultado.get("nombre_dispositivo"),
        firmware=resultado.get("firmware"),
        numero_serie=resultado.get("numero_serie"),
    )

    resultado["dispositivo_id"] = dispositivo_id
    return resultado


# ============================================================
# POST /dispositivos/probar-conexion-libre — Probar IP sin guardar
# ============================================================


@router.post("/probar-conexion-libre")
def post_probar_conexion_libre(
    payload: dict,
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("DISPOSITIVOS", "crear")),
    ],
) -> dict:
    """
    Prueba conexión a una IP/puerto sin necesidad de dispositivo guardado.
    Útil para el formulario de agregar dispositivo.
    """

    ip = (payload.get("ip") or "").strip()
    puerto = payload.get("puerto", 4370)
    password = payload.get("password_comunicacion", 0)

    if not ip:
        raise HTTPException(status_code=400, detail="La IP es obligatoria.")

    return _probar_conexion_dispositivo(ip=ip, puerto=puerto, password=password)


# ============================================================
# GET /dispositivos/{id}/hora — Consultar hora del dispositivo
# ============================================================


@router.get("/{dispositivo_id}/hora")
def get_hora_dispositivo(
    dispositivo_id: int,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("DISPOSITIVOS", "consultar")),
    ],
) -> dict:
    """
    Consulta la hora actual del dispositivo sin modificarla.
    Retorna hora del dispositivo, hora del servidor y desfase.
    """

    return consultar_hora_dispositivo(db, dispositivo_id)


# ============================================================
# POST /dispositivos/{id}/sincronizar-hora — Sincronizar hora
# ============================================================


@router.post("/{dispositivo_id}/sincronizar-hora")
def post_sincronizar_hora(
    dispositivo_id: int,
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("DISPOSITIVOS", "editar")),
    ],
    forzar: bool = Query(default=False, description="Forzar sincronización aunque esté dentro de tolerancia."),
) -> dict:
    """
    Sincroniza la hora del dispositivo ZKTeco.

    Sin límites de intentos. Puede ejecutarse las veces necesarias.
    Solo escribe si el desfase excede la tolerancia (30s por defecto),
    a menos que se pase forzar=true.
    """

    return sincronizar_hora_dispositivo(db, dispositivo_id, forzar=forzar)


# ============================================================
# POST /dispositivos/sincronizar-hora-todos — Sync automático
# ============================================================


@router.post("/sincronizar-hora-todos")
def post_sincronizar_hora_todos(
    db: Annotated[Session, Depends(get_db)],
    _access_scope: Annotated[
        AccessScope,
        Depends(require_module_access("DISPOSITIVOS", "editar")),
    ],
) -> dict:
    """
    Sincroniza hora de todos los dispositivos activos.
    Diseñado para tarea automática diaria o ejecución manual masiva.
    Solo sincroniza donde el desfase excede la tolerancia.
    """

    return sincronizar_hora_todos_activos(db)
