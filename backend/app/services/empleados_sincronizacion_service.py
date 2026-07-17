from __future__ import annotations
from ipaddress import ip_address
from dataclasses import replace
import unicodedata
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.access_control import AccessScope
from app.services.zk_service import (
    ZKDeviceService,
    ZKSettings,
)


def sincronizar_empleado_relojes(
    *,
    db: Session,
    codigo_empleado: str,
    access_scope: AccessScope,
    dispositivo_ids: list[int] | None = None,
) -> dict[str, Any]:
    """
    Concilia las relaciones pendientes del empleado con
    los usuarios existentes en los relojes físicos.

    El flujo por dispositivo es:

    PENDIENTE/ERROR/SINCRONIZADO
        -> SINCRONIZANDO
        -> crear o verificar usuario
        -> SINCRONIZADO o ERROR
    """

    empleado = _obtener_empleado_autorizado(
        db=db,
        codigo_empleado=codigo_empleado,
        access_scope=access_scope,
    )

    if empleado is None:
        raise LookupError(
            "No existe el empleado solicitado o no tienes "
            "permiso para sincronizarlo."
        )

    requested_ids = sorted(
        {
            int(value)
            for value in (dispositivo_ids or [])
            if int(value) > 0
        }
    )

    relaciones = _obtener_relaciones_dispositivo(
        db=db,
        empleado_id=int(empleado["id"]),
        dispositivo_ids=requested_ids,
    )

    if requested_ids:
        found_ids = {
            int(row["dispositivo_id"])
            for row in relaciones
        }

        missing_ids = (
            set(requested_ids) - found_ids
        )

        if missing_ids:
            missing_text = ", ".join(
                str(value)
                for value in sorted(missing_ids)
            )

            raise ValueError(
                "El empleado no tiene una relación activa "
                "con los siguientes dispositivos: "
                f"{missing_text}."
            )

    if not relaciones:
        raise ValueError(
            "El empleado no tiene relojes activos asignados."
        )

    resultados: list[dict[str, Any]] = []

    for relacion in relaciones:
        resultado = _sincronizar_relacion(
            db=db,
            relacion=relacion,
        )

        resultados.append(resultado)

    exitosos = sum(
        1
        for item in resultados
        if item["exitoso"]
    )

    return {
        "empleado_id": empleado["id"],
        "codigo_empleado": empleado["codigo_empleado"],
        "nombre_completo": empleado["nombre_completo"],
        "total_dispositivos": len(resultados),
        "exitosos": exitosos,
        "errores": len(resultados) - exitosos,
        "resultados": resultados,
    }


def _obtener_empleado_autorizado(
    *,
    db: Session,
    codigo_empleado: str,
    access_scope: AccessScope,
) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT
                e.id,
                e.codigo_empleado,
                e.nombre_completo,
                e.unidad_organizacional_id
            FROM personal.empleados e
            WHERE e.codigo_empleado = :codigo_empleado
              AND (
                    :data_scope = 'TOTAL'

                    OR (
                        :data_scope = 'PROPIO'
                        AND e.id = :access_employee_id
                    )

                    OR (
                        :data_scope = 'AREA'
                        AND e.unidad_organizacional_id = ANY(
                            CAST(:allowed_unit_ids AS BIGINT[])
                        )
                    )
              )
            LIMIT 1
            """
        ),
        {
            "codigo_empleado": codigo_empleado,
            "data_scope": access_scope.data_scope,
            "access_employee_id": (
                access_scope.employee_id
            ),
            "allowed_unit_ids": list(
                access_scope.allowed_unit_ids
            ),
        },
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def _obtener_relaciones_dispositivo(
    *,
    db: Session,
    empleado_id: int,
    dispositivo_ids: list[int],
) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                ed.id AS empleado_dispositivo_id,
                ed.empleado_id,
                ed.dispositivo_id,
                ed.zk_user_id,
                ed.zk_uid,
                ed.nombre_en_dispositivo,
                ed.password_reloj,
                ed.grupo,
                ed.privilegio,
                ed.estado_sincronizacion,

                d.codigo AS dispositivo_codigo,
                d.nombre AS dispositivo_nombre,
                HOST(d.ip) AS dispositivo_ip,
                d.puerto AS dispositivo_puerto,
                d.password_comunicacion

            FROM dispositivos.empleado_dispositivo ed

            INNER JOIN dispositivos.dispositivos d
                ON d.id = ed.dispositivo_id

            WHERE ed.empleado_id = :empleado_id
              AND ed.activo = TRUE
              AND d.activo = TRUE
              AND (
                    :filtrar_dispositivos = FALSE
                    OR ed.dispositivo_id = ANY(
                        CAST(:dispositivo_ids AS BIGINT[])
                    )
              )

            ORDER BY
                d.es_predeterminado DESC,
                d.id
            """
        ),
        {
            "empleado_id": empleado_id,
            "filtrar_dispositivos": bool(
                dispositivo_ids
            ),
            "dispositivo_ids": dispositivo_ids,
        },
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]


def _sincronizar_relacion(
    *,
    db: Session,
    relacion: dict[str, Any],
) -> dict[str, Any]:
    relacion_id = int(
        relacion["empleado_dispositivo_id"]
    )

    estado_anterior = str(
        relacion["estado_sincronizacion"]
    )

    db.execute(
        text(
            """
            UPDATE dispositivos.empleado_dispositivo
            SET
                estado_sincronizacion = 'SINCRONIZANDO',
                sincronizado = FALSE,
                intentos_sincronizacion =
                    intentos_sincronizacion + 1,
                fecha_ultimo_intento = CURRENT_TIMESTAMP,
                ultimo_error = NULL,
                fecha_modificacion = CURRENT_TIMESTAMP
            WHERE id = :relacion_id
            """
        ),
        {
            "relacion_id": relacion_id,
        },
    )

    db.commit()

    try:
        service = _crear_servicio_dispositivo(
            relacion
        )

        zk_user_id = str(
            relacion["zk_user_id"]
        ).strip()

        expected_name = _normalizar_nombre_reloj(
            relacion["nombre_en_dispositivo"]
        )

        if not expected_name:
            raise ValueError(
                "La relación no tiene un nombre válido "
                "para registrar en el reloj."
            )

        existing = service.get_user_by_user_id(
            zk_user_id
        )

        creado_en_reloj = False
        ya_existia_en_reloj = existing is not None

        if existing is not None:
            existing_name = _normalizar_nombre_reloj(
                existing.get("name")
            )

            if existing_name != expected_name:
                raise ValueError(
                    f"El ZK User ID {zk_user_id} ya está "
                    "ocupado en el reloj por "
                    f"'{existing.get('name')}'."
                )

            user = existing

        else:
            user = service.create_user(
                name=expected_name,
                user_id=zk_user_id,
                password=str(
                    relacion["password_reloj"] or ""
                ),
                group_id=str(
                    relacion["grupo"] or ""
                ),
                privilege="user",
            )

            creado_en_reloj = True

        zk_uid = (
            int(user["uid"])
            if user.get("uid") is not None
            else None
        )

        db.execute(
            text(
                """
                UPDATE dispositivos.empleado_dispositivo
                SET
                    zk_uid = :zk_uid,
                    sincronizado = TRUE,
                    estado_sincronizacion = 'SINCRONIZADO',
                    fecha_ultima_sincronizacion =
                        CURRENT_TIMESTAMP,
                    ultimo_error = NULL,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :relacion_id
                """
            ),
            {
                "relacion_id": relacion_id,
                "zk_uid": zk_uid,
            },
        )

                # Mantener compatibilidad temporal con el vínculo
        # histórico personal.empleados.zk_user_id.
        db.execute(
            text(
                """
                UPDATE personal.empleados
                SET
                    zk_user_id = :zk_user_id,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :empleado_id
                """
            ),
            {
                "empleado_id": relacion["empleado_id"],
                "zk_user_id": zk_user_id,
            },
        )

        db.execute(
            text(
                """
                UPDATE dispositivos.dispositivos
                SET
                    ultima_conexion = CURRENT_TIMESTAMP,
                    ultima_sincronizacion =
                        CURRENT_TIMESTAMP,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :dispositivo_id
                """
            ),
            {
                "dispositivo_id": (
                    relacion["dispositivo_id"]
                ),
            },
        )

        db.commit()

        if creado_en_reloj:
            mensaje = (
                "Usuario creado y verificado "
                "correctamente en el reloj."
            )
        else:
            mensaje = (
                "El usuario ya existía en el reloj "
                "y fue verificado correctamente."
            )

        return {
            "empleado_dispositivo_id": relacion_id,
            "dispositivo_id": relacion["dispositivo_id"],
            "dispositivo_codigo": (
                relacion["dispositivo_codigo"]
            ),
            "dispositivo_nombre": (
                relacion["dispositivo_nombre"]
            ),
            "zk_user_id": zk_user_id,
            "zk_uid": zk_uid,
            "estado_anterior": estado_anterior,
            "estado_final": "SINCRONIZADO",
            "exitoso": True,
            "creado_en_reloj": creado_en_reloj,
            "ya_existia_en_reloj": (
                ya_existia_en_reloj
            ),
            "mensaje": mensaje,
        }

    except Exception as exc:
        db.rollback()

        error_message = (
            f"{type(exc).__name__}: {str(exc)}"
        )[:2000]

        db.execute(
            text(
                """
                UPDATE dispositivos.empleado_dispositivo
                SET
                    sincronizado = FALSE,
                    estado_sincronizacion = 'ERROR',
                    ultimo_error = :ultimo_error,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :relacion_id
                """
            ),
            {
                "relacion_id": relacion_id,
                "ultimo_error": error_message,
            },
        )

        db.commit()

        return {
            "empleado_dispositivo_id": relacion_id,
            "dispositivo_id": relacion["dispositivo_id"],
            "dispositivo_codigo": (
                relacion["dispositivo_codigo"]
            ),
            "dispositivo_nombre": (
                relacion["dispositivo_nombre"]
            ),
            "zk_user_id": str(
                relacion["zk_user_id"]
            ),
            "zk_uid": relacion["zk_uid"],
            "estado_anterior": estado_anterior,
            "estado_final": "ERROR",
            "exitoso": False,
            "creado_en_reloj": False,
            "ya_existia_en_reloj": False,
            "mensaje": error_message,
        }


def _crear_servicio_dispositivo(
    relacion: dict[str, Any],
) -> ZKDeviceService:
    base_settings = ZKSettings.from_env()

    raw_ip = str(
        relacion["dispositivo_ip"]
    ).strip()

    # Protección adicional por si alguna fuente entrega
    # la dirección con máscara, por ejemplo 10.0.0.1/32.
    raw_ip = raw_ip.split("/", 1)[0]

    try:
        device_ip = str(
            ip_address(raw_ip)
        )
    except ValueError as exc:
        raise ValueError(
            "La dirección IP configurada para el "
            f"dispositivo no es válida: {raw_ip!r}."
        ) from exc

    device_settings = replace(
        base_settings,
        ip=device_ip,
        port=int(
            relacion["dispositivo_puerto"]
        ),
        password=int(
            relacion["password_comunicacion"]
        ),
    )

    return ZKDeviceService(
        settings=device_settings
    )


def _normalizar_nombre_reloj(
    value: Any,
) -> str:
    raw_name = str(value or "").strip()

    normalized = unicodedata.normalize(
        "NFKD",
        raw_name,
    )

    ascii_name = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    return " ".join(
        ascii_name.upper().split()
    )[:24]