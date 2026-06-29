from fastapi import APIRouter, HTTPException, Query, status

from app.services.zk_service import ZKDeviceService


router = APIRouter(
    prefix="/zk",
    tags=["ZKTeco"],
)


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
        )


@router.get("/users")
def list_zk_users(
    include_admin: bool = Query(
        default=True,
        description="Incluye usuarios administradores del reloj.",
    )
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
        )


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
        )