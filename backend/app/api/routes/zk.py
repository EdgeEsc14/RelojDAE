import os
from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth_dependencies import require_roles
from app.core.database import get_db
from app.repositories.zk_attendance_repo import (
    insertar_marcaciones_crudas,
    listar_marcaciones_crudas_db,
)
from app.repositories.zk_employee_link_repo import (
    desvincular_empleado_de_zk,
    vincular_empleado_con_zk_user_id,
)
from app.repositories.zk_reconciliation_repo import conciliar_empleados_con_usuarios_zk
from app.schemas.zk import ZkEmployeeLinkRequest
from app.services.zk_service import ZKDeviceService
from app.services.zk_time_sync_service import sync_zk_time_if_allowed


router = APIRouter(
    prefix="/zk",
    tags=["ZKTeco"],
    dependencies=[
        Depends(require_roles("super_admin", "rh_admin")),
    ],
)


def _clean_text(value) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _get_punch_label(punch) -> str:
    """
    Etiquetas provisionales para códigos punch de ZKTeco.
    Se validarán con pruebas físicas del reloj.
    """
    labels = {
        0: "Entrada",
        1: "Salida",
        2: "Salida descanso",
        3: "Entrada descanso",
        4: "Entrada tiempo extra",
        5: "Salida tiempo extra",
    }

    try:
        return labels.get(int(punch), f"Punch {punch}")
    except Exception:
        return f"Punch {punch}"


def _get_status_label(status) -> str:
    """
    Etiquetas provisionales para status/verificación.
    En distintos modelos ZKTeco estos valores pueden variar.
    """
    labels = {
        0: "Desconocido",
        1: "Huella / verificación biométrica",
        2: "PIN / contraseña",
        3: "Password / tarjeta / evento especial",
        4: "Tarjeta",
        15: "Rostro / evento especial",
    }

    try:
        return labels.get(int(status), f"Status {status}")
    except Exception:
        return f"Status {status}"


def _attendance_to_dict(attendance) -> dict:
    timestamp = getattr(attendance, "timestamp", None)

    return {
        "uid": getattr(attendance, "uid", None),
        "user_id": _clean_text(getattr(attendance, "user_id", "")),
        "timestamp": timestamp.isoformat() if timestamp else None,
        "fecha": timestamp.date().isoformat() if timestamp else None,
        "hora": timestamp.time().isoformat(timespec="seconds") if timestamp else None,
        "status": getattr(attendance, "status", None),
        "status_label": _get_status_label(getattr(attendance, "status", None)),
        "punch": getattr(attendance, "punch", None),
        "punch_label": _get_punch_label(getattr(attendance, "punch", None)),
    }


@router.get("/health")
def zk_health():
    """
    Verifica conexión básica con el reloj ZKTeco.

    No modifica nada en el reloj.
    """
    try:
        service = ZKDeviceService()
        users = service.list_users(include_admin=True)

        return {
            "ok": True,
            "message": "Conexión exitosa con reloj ZKTeco.",
            "total_users": len(users),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ok": False,
                "message": "No se pudo conectar con el reloj ZKTeco.",
                "error": str(exc),
            },
        ) from exc


@router.get("/users")
def list_zk_users(
    include_admin: Annotated[
        bool,
        Query(description="Incluye usuarios administradores del reloj."),
    ] = True,
):
    """
    Lista usuarios reales del reloj ZKTeco.

    Seguridad:
    - No devuelve PINs.
    - Solo devuelve has_pin=True/False.
    - No crea, no edita y no borra usuarios.
    """
    try:
        service = ZKDeviceService()
        users = service.list_users(include_admin=include_admin)

        return {
            "ok": True,
            "total": len(users),
            "include_admin": include_admin,
            "users": users,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ok": False,
                "message": "No se pudieron leer usuarios del reloj ZKTeco.",
                "error": str(exc),
            },
        ) from exc


@router.get("/users/{user_id}")
def get_zk_user_by_user_id(user_id: str):
    """
    Busca un usuario específico del reloj por User ID.

    Ejemplo:
    /api/zk/users/1000
    """
    try:
        service = ZKDeviceService()
        user = service.get_user_by_user_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "ok": False,
                    "message": f"No existe usuario ZKTeco con user_id={user_id}.",
                },
            )

        return {
            "ok": True,
            "user": user,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ok": False,
                "message": "No se pudo consultar el usuario en el reloj ZKTeco.",
                "error": str(exc),
            },
        ) from exc


@router.get("/reconciliation/employees")
def reconcile_zk_users_with_employees(
    db: Annotated[Session, Depends(get_db)],
):
    """
    Compara usuarios reales del reloj ZKTeco contra empleados registrados en PostgreSQL.

    Solo lectura:
    - No modifica empleados.
    - No crea usuarios en el reloj.
    - No borra usuarios en el reloj.
    """
    try:
        service = ZKDeviceService()
        zk_users = service.list_users(include_admin=True)

        return conciliar_empleados_con_usuarios_zk(
            db=db,
            zk_users=zk_users,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ok": False,
                "message": "No se pudo conciliar empleados contra usuarios ZKTeco.",
                "error": str(exc),
            },
        ) from exc


@router.patch("/reconciliation/employees/{codigo_empleado}/link")
def link_employee_with_zk_user(
    codigo_empleado: str,
    payload: ZkEmployeeLinkRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Vincula un empleado de PostgreSQL con un User ID existente en el reloj ZKTeco.

    Solo modifica:
    - personal.empleados.zk_user_id

    No modifica el reloj físico.
    """
    try:
        service = ZKDeviceService()

        zk_user = service.get_user_by_user_id(payload.zk_user_id)

        if not zk_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "ok": False,
                    "message": f"No existe usuario ZKTeco con user_id={payload.zk_user_id}.",
                },
            )

        if zk_user.get("is_admin") or zk_user.get("is_protected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "ok": False,
                    "message": "No se puede vincular un usuario admin/protegido del reloj.",
                    "zk_user": zk_user,
                },
            )

        employee = vincular_empleado_con_zk_user_id(
            db=db,
            codigo_empleado=codigo_empleado,
            zk_user_id=payload.zk_user_id,
        )

        return {
            "ok": True,
            "message": "Empleado vinculado correctamente con usuario ZKTeco.",
            "employee": employee,
            "zk_user": zk_user,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ok": False,
                "message": str(exc),
            },
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ok": False,
                "message": "No se pudo vincular empleado con usuario ZKTeco.",
                "error": str(exc),
            },
        ) from exc


@router.patch("/reconciliation/employees/{codigo_empleado}/unlink")
def unlink_employee_from_zk_user(
    codigo_empleado: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Desvincula un empleado de su User ID ZKTeco en PostgreSQL.

    Solo modifica:
    - personal.empleados.zk_user_id = NULL

    No modifica el reloj físico.
    """
    try:
        employee = desvincular_empleado_de_zk(
            db=db,
            codigo_empleado=codigo_empleado,
        )

        return {
            "ok": True,
            "message": "Empleado desvinculado correctamente de usuario ZKTeco.",
            "employee": employee,
        }

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ok": False,
                "message": str(exc),
            },
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ok": False,
                "message": "No se pudo desvincular empleado de usuario ZKTeco.",
                "error": str(exc),
            },
        ) from exc


@router.get("/attendance/raw")
def list_zk_attendance_raw(
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    user_id: Annotated[
        str | None,
        Query(description="Filtrar por User ID ZKTeco"),
    ] = None,
    date_from: Annotated[
        str | None,
        Query(description="Fecha inicial YYYY-MM-DD"),
    ] = None,
    date_to: Annotated[
        str | None,
        Query(description="Fecha final YYYY-MM-DD"),
    ] = None,
):
    """
    Lista marcaciones crudas directamente desde el reloj ZKTeco.

    Solo lectura:
    - No guarda en BD.
    - No borra marcaciones.
    - No modifica el reloj.
    """
    try:
        parsed_date_from = None
        parsed_date_to = None

        if date_from:
            parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d").date()

        if date_to:
            parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

        service = ZKDeviceService()

        with service.connection(disable_device=True) as conn:
            raw_attendances = conn.get_attendance()

        records = [_attendance_to_dict(item) for item in raw_attendances]

        if user_id:
            user_id_clean = _clean_text(user_id)

            records = [
                record
                for record in records
                if record["user_id"] == user_id_clean
            ]

        if parsed_date_from:
            records = [
                record
                for record in records
                if record["fecha"]
                and datetime.strptime(record["fecha"], "%Y-%m-%d").date()
                >= parsed_date_from
            ]

        if parsed_date_to:
            records = [
                record
                for record in records
                if record["fecha"]
                and datetime.strptime(record["fecha"], "%Y-%m-%d").date()
                <= parsed_date_to
            ]

        records = sorted(
            records,
            key=lambda item: item["timestamp"] or "",
            reverse=True,
        )

        limited_records = records[:limit]

        return {
            "ok": True,
            "total": len(records),
            "limit": limit,
            "filters": {
                "user_id": user_id,
                "date_from": date_from,
                "date_to": date_to,
            },
            "records": limited_records,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ok": False,
                "message": "Formato de fecha inválido. Usa YYYY-MM-DD.",
                "error": str(exc),
            },
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ok": False,
                "message": "No se pudieron leer marcaciones del reloj ZKTeco.",
                "error": str(exc),
            },
        ) from exc
    
@router.post("/attendance/sync")
def sync_zk_attendance_to_db(
    
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
    user_id: Annotated[
        str | None,
        Query(description="Filtrar por User ID ZKTeco antes de sincronizar"),
    ] = None,
    date_from: Annotated[
        str | None,
        Query(description="Fecha inicial YYYY-MM-DD"),
    ] = None,
    date_to: Annotated[
        str | None,
        Query(description="Fecha final YYYY-MM-DD"),
    ] = None,
):
    sync_zk_time_if_allowed()
    """
    Sincroniza marcaciones crudas desde el reloj hacia PostgreSQL.

    Seguridad:
    - No borra marcaciones del reloj.
    - No modifica marcaciones del reloj.
    - Solo inserta copia cruda en asistencia.marcaciones_crudas.
    - No duplica marcaciones ya sincronizadas.
    """
    try:
        parsed_date_from = None
        parsed_date_to = None

        if date_from:
            parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d").date()

        if date_to:
            parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

        service = ZKDeviceService()

        with service.connection(disable_device=True) as conn:
            raw_attendances = conn.get_attendance()

        records = [_attendance_to_dict(item) for item in raw_attendances]

        if user_id:
            user_id_clean = _clean_text(user_id)
            records = [
                record
                for record in records
                if record["user_id"] == user_id_clean
            ]

        if parsed_date_from:
            records = [
                record
                for record in records
                if record["fecha"]
                and datetime.strptime(record["fecha"], "%Y-%m-%d").date()
                >= parsed_date_from
            ]

        if parsed_date_to:
            records = [
                record
                for record in records
                if record["fecha"]
                and datetime.strptime(record["fecha"], "%Y-%m-%d").date()
                <= parsed_date_to
            ]

        records = sorted(
            records,
            key=lambda item: item["timestamp"] or "",
            reverse=True,
        )

        limited_records = records[:limit]

        sync_run_id = f"ZK-SYNC-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"

        result = insertar_marcaciones_crudas(
            db=db,
            records=limited_records,
            sync_run_id=sync_run_id,
            dispositivo_ip=os.getenv("ZK_IP"),
            dispositivo_origen="ZKTeco",
        )

        return {
            "ok": True,
            "message": "Sincronización de marcaciones crudas completada.",
            "sync_run_id": sync_run_id,
            "filters": {
                "limit": limit,
                "user_id": user_id,
                "date_from": date_from,
                "date_to": date_to,
            },
            "result": result,
        }

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ok": False,
                "message": "Formato de fecha inválido. Usa YYYY-MM-DD.",
                "error": str(exc),
            },
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ok": False,
                "message": "No se pudieron sincronizar marcaciones del reloj ZKTeco.",
                "error": str(exc),
            },
        ) from exc
    
@router.get("/attendance/db")
def list_zk_attendance_from_db(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 100,
    user_id: Annotated[
        str | None,
        Query(description="Filtrar por User ID ZKTeco"),
    ] = None,
    date_from: Annotated[
        str | None,
        Query(description="Fecha inicial YYYY-MM-DD"),
    ] = None,
    date_to: Annotated[
        str | None,
        Query(description="Fecha final YYYY-MM-DD"),
    ] = None,
):
    """
    Lista marcaciones crudas ya sincronizadas en PostgreSQL.
    """
    try:
        if date_from:
            datetime.strptime(date_from, "%Y-%m-%d").date()

        if date_to:
            datetime.strptime(date_to, "%Y-%m-%d").date()

        result = listar_marcaciones_crudas_db(
            db=db,
            limit=limit,
            zk_user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )

        return {
            "ok": True,
            "filters": {
                "limit": limit,
                "user_id": user_id,
                "date_from": date_from,
                "date_to": date_to,
            },
            **result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ok": False,
                "message": "Formato de fecha inválido. Usa YYYY-MM-DD.",
                "error": str(exc),
            },
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ok": False,
                "message": "No se pudieron consultar marcaciones crudas desde PostgreSQL.",
                "error": str(exc),
            },
        ) from exc
    
@router.post("/time/sync")
def sync_zk_time(force: bool = False):
    """
    Revisa y corrige la hora del reloj ZKTeco.

    Por defecto respeta el límite diario configurado.
    Si force=true, fuerza la revisión.
    """
    return sync_zk_time_if_allowed(force=force)