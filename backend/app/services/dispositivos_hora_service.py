"""
Servicio de gestión de hora para dispositivos ZKTeco.

Multi-dispositivo: opera sobre un dispositivo específico por ID.
Sin límites artificiales para sincronización manual.
Tolerancia configurable para sincronización automática.

Configuración:
    ZK_TIME_SYNC_TOLERANCE_SECONDS (default: 30)
"""

from __future__ import annotations

import os
from contextlib import suppress
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.zk_service import ZKDeviceService, ZKSettings


# Tolerancia configurable desde .env (default 30 segundos)
def _get_tolerance_seconds() -> int:
    try:
        return int(os.getenv("ZK_TIME_SYNC_TOLERANCE_SECONDS", "30"))
    except ValueError:
        return 30


def consultar_hora_dispositivo(
    db: Session,
    dispositivo_id: int,
) -> dict[str, Any]:
    """
    Consulta la hora actual del dispositivo ZKTeco sin modificarla.

    Retorna hora del dispositivo, hora del servidor, desfase.
    Persiste el resultado en la BD.
    """

    dispositivo = _obtener_dispositivo(db, dispositivo_id)
    if dispositivo is None:
        return {"ok": False, "error": f"No existe dispositivo con id {dispositivo_id}."}

    if not dispositivo["activo"]:
        return {"ok": False, "error": "Dispositivo deshabilitado.", "estado": "DESHABILITADO"}

    service = _build_service(dispositivo)
    inicio = datetime.now()

    try:
        with service.connection(disable_device=True) as conn:
            device_time = conn.get_time()

        server_time = datetime.now().replace(microsecond=0)

        if device_time:
            device_time = device_time.replace(microsecond=0)
            desfase = int((server_time - device_time).total_seconds())
        else:
            desfase = None

        duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)

        # Persistir
        _actualizar_estado_hora(
            db, dispositivo_id,
            desfase_segundos=desfase,
            resultado="HORA_OK" if desfase is not None and abs(desfase) <= _get_tolerance_seconds() else "DESFASE_DETECTADO",
            error=None,
        )

        return {
            "ok": True,
            "dispositivo_id": dispositivo_id,
            "hora_dispositivo": device_time.isoformat() if device_time else None,
            "hora_servidor": server_time.isoformat(),
            "desfase_segundos": desfase,
            "tolerancia_segundos": _get_tolerance_seconds(),
            "requiere_sincronizacion": desfase is not None and abs(desfase) > _get_tolerance_seconds(),
            "duracion_ms": duracion_ms,
        }

    except Exception as exc:
        _actualizar_estado_hora(
            db, dispositivo_id,
            desfase_segundos=None,
            resultado="ERROR",
            error=str(exc),
        )

        return {
            "ok": False,
            "dispositivo_id": dispositivo_id,
            "error": str(exc),
        }


def sincronizar_hora_dispositivo(
    db: Session,
    dispositivo_id: int,
    *,
    forzar: bool = False,
) -> dict[str, Any]:
    """
    Sincroniza la hora de un dispositivo ZKTeco.

    Si forzar=False, solo sincroniza si el desfase excede la tolerancia.
    Si forzar=True, siempre escribe la hora del servidor al dispositivo.

    No tiene límites de intentos (sincronización manual ilimitada).
    """

    dispositivo = _obtener_dispositivo(db, dispositivo_id)
    if dispositivo is None:
        return {"ok": False, "error": f"No existe dispositivo con id {dispositivo_id}."}

    if not dispositivo["activo"]:
        return {"ok": False, "error": "Dispositivo deshabilitado.", "estado": "DESHABILITADO"}

    service = _build_service(dispositivo)
    tolerancia = _get_tolerance_seconds()

    try:
        with service.connection(disable_device=True) as conn:
            # Leer hora antes
            hora_antes = conn.get_time()
            server_time = datetime.now().replace(microsecond=0)

            if hora_antes:
                hora_antes = hora_antes.replace(microsecond=0)
                desfase_antes = int((server_time - hora_antes).total_seconds())
            else:
                desfase_antes = None

            # Decidir si sincronizar
            debe_sincronizar = forzar or (desfase_antes is not None and abs(desfase_antes) > tolerancia)

            if debe_sincronizar:
                conn.set_time(server_time)
                # Leer hora después
                hora_despues = None
                with suppress(Exception):
                    hora_despues = conn.get_time()
                    if hora_despues:
                        hora_despues = hora_despues.replace(microsecond=0)

                desfase_despues = (
                    int((datetime.now().replace(microsecond=0) - hora_despues).total_seconds())
                    if hora_despues else None
                )

                _actualizar_estado_hora(
                    db, dispositivo_id,
                    desfase_segundos=desfase_despues,
                    resultado="SINCRONIZADA",
                    error=None,
                    registrar_sincronizacion=True,
                )

                return {
                    "ok": True,
                    "dispositivo_id": dispositivo_id,
                    "sincronizada": True,
                    "hora_antes": hora_antes.isoformat() if hora_antes else None,
                    "hora_servidor": server_time.isoformat(),
                    "hora_despues": hora_despues.isoformat() if hora_despues else None,
                    "desfase_antes_segundos": desfase_antes,
                    "desfase_despues_segundos": desfase_despues,
                    "tolerancia_segundos": tolerancia,
                    "motivo": "FORZADA" if forzar else "DESFASE_EXCEDE_TOLERANCIA",
                }
            else:
                # No requiere sincronización
                _actualizar_estado_hora(
                    db, dispositivo_id,
                    desfase_segundos=desfase_antes,
                    resultado="HORA_OK",
                    error=None,
                )

                return {
                    "ok": True,
                    "dispositivo_id": dispositivo_id,
                    "sincronizada": False,
                    "hora_antes": hora_antes.isoformat() if hora_antes else None,
                    "hora_servidor": server_time.isoformat(),
                    "desfase_antes_segundos": desfase_antes,
                    "tolerancia_segundos": tolerancia,
                    "motivo": "DENTRO_DE_TOLERANCIA",
                }

    except Exception as exc:
        _actualizar_estado_hora(
            db, dispositivo_id,
            desfase_segundos=None,
            resultado="ERROR",
            error=str(exc),
        )

        return {
            "ok": False,
            "dispositivo_id": dispositivo_id,
            "sincronizada": False,
            "error": str(exc),
        }


def sincronizar_hora_todos_activos(db: Session) -> dict[str, Any]:
    """
    Sincroniza hora de todos los dispositivos activos.

    Diseñada para tarea automática diaria (06:00).
    Solo sincroniza si el desfase excede la tolerancia.
    """

    rows = db.execute(text(
        "SELECT id FROM dispositivos.dispositivos WHERE activo = TRUE ORDER BY id"
    )).scalars().all()

    resultados = []
    sincronizados = 0
    errores = 0

    for device_id in rows:
        resultado = sincronizar_hora_dispositivo(db, device_id, forzar=False)
        resultados.append(resultado)
        if resultado.get("sincronizada"):
            sincronizados += 1
        if not resultado.get("ok"):
            errores += 1

    return {
        "ok": errores == 0,
        "dispositivos_revisados": len(rows),
        "sincronizados": sincronizados,
        "errores": errores,
        "resultados": resultados,
    }


# ============================================================
# Helpers internos
# ============================================================


def _obtener_dispositivo(db: Session, dispositivo_id: int) -> dict[str, Any] | None:
    row = db.execute(text("""
        SELECT id, HOST(ip) AS ip, puerto, password_comunicacion, activo
        FROM dispositivos.dispositivos
        WHERE id = :id
    """), {"id": dispositivo_id}).mappings().first()

    if row is None:
        return None

    return dict(row)


def _build_service(dispositivo: dict) -> ZKDeviceService:
    settings = ZKSettings(
        ip=dispositivo["ip"],
        port=dispositivo["puerto"],
        password=dispositivo["password_comunicacion"],
        timeout=10,
        force_udp=False,
        ommit_ping=True,
        allow_writes=True,  # Necesario para set_time
        protected_user_ids=set(),
        protected_names=set(),
    )
    return ZKDeviceService(settings=settings)


def _actualizar_estado_hora(
    db: Session,
    dispositivo_id: int,
    *,
    desfase_segundos: int | None,
    resultado: str,
    error: str | None,
    registrar_sincronizacion: bool = False,
) -> None:
    """Persiste el estado de hora del dispositivo."""

    sets = [
        "ultimo_desfase_segundos = :desfase",
        "ultimo_resultado_hora = :resultado",
        "ultimo_error_hora = :error",
        "ultima_comprobacion = CURRENT_TIMESTAMP",
        "fecha_modificacion = CURRENT_TIMESTAMP",
    ]
    params: dict[str, Any] = {
        "id": dispositivo_id,
        "desfase": desfase_segundos,
        "resultado": resultado,
        "error": error,
    }

    if registrar_sincronizacion:
        sets.append("ultima_sincronizacion_hora = CURRENT_TIMESTAMP")

    try:
        db.execute(text(
            f"UPDATE dispositivos.dispositivos SET {', '.join(sets)} WHERE id = :id"
        ), params)
        db.commit()
    except Exception:
        db.rollback()
