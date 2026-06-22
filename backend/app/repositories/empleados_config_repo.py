import base64
import hashlib
import secrets
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.empleados_config import (
    AsignarDispositivoEmpleadoRequest,
    AsignarHorarioEmpleadoRequest,
    CrearUsuarioSistemaEmpleadoRequest,
)


def asignar_horario_empleado(
    db: Session,
    codigo_empleado: str,
    payload: AsignarHorarioEmpleadoRequest,
) -> dict | None:
    empleado = _obtener_empleado_por_codigo(db, codigo_empleado)

    if empleado is None:
        return None

    _validar_horario_activo(db, payload.horario_id)

    try:
        if payload.cerrar_asignaciones_activas:
            db.execute(
                text(
                    """
                    UPDATE asistencia.asignaciones_horario
                    SET
                        estatus = 'INACTIVA',
                        fecha_fin = CASE
                            WHEN fecha_fin IS NULL OR fecha_fin >= :fecha_inicio
                                THEN CAST(:fecha_inicio AS date) - 1
                            ELSE fecha_fin
                        END,
                        fecha_modificacion = CURRENT_TIMESTAMP
                    WHERE empleado_id = :empleado_id
                      AND estatus = 'ACTIVA'
                    """
                ),
                {
                    "empleado_id": empleado["id"],
                    "fecha_inicio": payload.fecha_inicio,
                },
            )

        row = db.execute(
            text(
                """
                INSERT INTO asistencia.asignaciones_horario (
                    empleado_id,
                    horario_id,
                    fecha_inicio,
                    fecha_fin,
                    estatus,
                    motivo
                )
                VALUES (
                    :empleado_id,
                    :horario_id,
                    :fecha_inicio,
                    :fecha_fin,
                    'ACTIVA',
                    :motivo
                )
                RETURNING id
                """
            ),
            {
                "empleado_id": empleado["id"],
                "horario_id": payload.horario_id,
                "fecha_inicio": payload.fecha_inicio,
                "fecha_fin": payload.fecha_fin,
                "motivo": _limpiar_texto(payload.motivo),
            },
        ).mappings().one()

        asignacion_id = row["id"]
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_asignacion_horario_por_id(db, asignacion_id)


def obtener_asignacion_horario_por_id(
    db: Session,
    asignacion_id: int,
) -> dict:
    row = db.execute(
        text(
            """
            SELECT
                ah.id,
                e.id AS empleado_id,
                e.codigo_empleado,
                h.id AS horario_id,
                h.codigo AS horario_codigo,
                h.nombre AS horario_nombre,
                tt.codigo AS tipo_turno_codigo,
                tt.nombre AS tipo_turno_nombre,
                ah.fecha_inicio,
                ah.fecha_fin,
                ah.estatus,
                ah.motivo
            FROM asistencia.asignaciones_horario ah
            INNER JOIN personal.empleados e
                ON e.id = ah.empleado_id
            INNER JOIN asistencia.horarios h
                ON h.id = ah.horario_id
            LEFT JOIN asistencia.tipos_turno tt
                ON tt.id = h.tipo_turno_id
            WHERE ah.id = :asignacion_id
            """
        ),
        {
            "asignacion_id": asignacion_id,
        },
    ).mappings().one()

    return dict(row)


def asignar_dispositivo_empleado(
    db: Session,
    codigo_empleado: str,
    payload: AsignarDispositivoEmpleadoRequest,
) -> dict | None:
    empleado = _obtener_empleado_por_codigo(db, codigo_empleado)

    if empleado is None:
        return None

    _validar_dispositivo_activo(db, payload.dispositivo_id)

    zk_user_id = payload.zk_user_id.strip()

    if not zk_user_id:
        raise ValueError("zk_user_id no puede estar vacío.")

    _validar_zk_user_id_disponible(
        db=db,
        dispositivo_id=payload.dispositivo_id,
        zk_user_id=zk_user_id,
        empleado_id_actual=empleado["id"],
    )

    try:
        existente = db.execute(
            text(
                """
                SELECT id
                FROM dispositivos.empleado_dispositivo
                WHERE empleado_id = :empleado_id
                  AND dispositivo_id = :dispositivo_id
                LIMIT 1
                """
            ),
            {
                "empleado_id": empleado["id"],
                "dispositivo_id": payload.dispositivo_id,
            },
        ).mappings().first()

        params = {
            "empleado_id": empleado["id"],
            "dispositivo_id": payload.dispositivo_id,
            "zk_uid": payload.zk_uid,
            "zk_user_id": zk_user_id,
            "nombre_en_dispositivo": _limpiar_texto(payload.nombre_en_dispositivo),
            "privilegio": payload.privilegio,
            "grupo": _limpiar_texto(payload.grupo),
            "tarjeta": _limpiar_texto(payload.tarjeta),
            "activo": payload.activo,
        }

        if existente:
            row = db.execute(
                text(
                    """
                    UPDATE dispositivos.empleado_dispositivo
                    SET
                        zk_uid = :zk_uid,
                        zk_user_id = :zk_user_id,
                        nombre_en_dispositivo = :nombre_en_dispositivo,
                        privilegio = :privilegio,
                        grupo = :grupo,
                        tarjeta = :tarjeta,
                        activo = :activo,
                        sincronizado = false,
                        fecha_modificacion = CURRENT_TIMESTAMP
                    WHERE id = :id
                    RETURNING id
                    """
                ),
                {
                    **params,
                    "id": existente["id"],
                },
            ).mappings().one()

        else:
            row = db.execute(
                text(
                    """
                    INSERT INTO dispositivos.empleado_dispositivo (
                        empleado_id,
                        dispositivo_id,
                        zk_uid,
                        zk_user_id,
                        nombre_en_dispositivo,
                        privilegio,
                        grupo,
                        tarjeta,
                        sincronizado,
                        activo
                    )
                    VALUES (
                        :empleado_id,
                        :dispositivo_id,
                        :zk_uid,
                        :zk_user_id,
                        :nombre_en_dispositivo,
                        :privilegio,
                        :grupo,
                        :tarjeta,
                        false,
                        :activo
                    )
                    RETURNING id
                    """
                ),
                params,
            ).mappings().one()

        empleado_dispositivo_id = row["id"]
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_empleado_dispositivo_por_id(db, empleado_dispositivo_id)


def obtener_empleado_dispositivo_por_id(
    db: Session,
    empleado_dispositivo_id: int,
) -> dict:
    row = db.execute(
        text(
            """
            SELECT
                ed.id,
                e.id AS empleado_id,
                e.codigo_empleado,
                d.id AS dispositivo_id,
                d.codigo AS dispositivo_codigo,
                d.nombre AS dispositivo_nombre,
                d.ip::text AS dispositivo_ip,
                d.puerto AS dispositivo_puerto,
                ed.zk_uid,
                ed.zk_user_id,
                ed.nombre_en_dispositivo,
                ed.privilegio,
                ed.grupo,
                ed.tarjeta,
                ed.sincronizado,
                ed.fecha_ultima_sincronizacion,
                ed.activo
            FROM dispositivos.empleado_dispositivo ed
            INNER JOIN personal.empleados e
                ON e.id = ed.empleado_id
            INNER JOIN dispositivos.dispositivos d
                ON d.id = ed.dispositivo_id
            WHERE ed.id = :empleado_dispositivo_id
            """
        ),
        {
            "empleado_dispositivo_id": empleado_dispositivo_id,
        },
    ).mappings().one()

    return dict(row)


def crear_usuario_sistema_empleado(
    db: Session,
    codigo_empleado: str,
    payload: CrearUsuarioSistemaEmpleadoRequest,
) -> dict | None:
    empleado = _obtener_empleado_por_codigo(db, codigo_empleado)

    if empleado is None:
        return None

    rol = _obtener_rol_activo(db, payload.rol_id)

    if rol is None:
        raise ValueError(f"No existe un rol activo con id {payload.rol_id}.")

    _validar_empleado_sin_usuario(db, empleado["id"])

    correo = _normalizar_correo(payload.correo_electronico or empleado["correo"])

    if correo is None:
        raise ValueError("El empleado no tiene correo y no se envió correo_electronico.")

    nombre_usuario = _normalizar_nombre_usuario(
        payload.nombre_usuario or empleado["codigo_empleado"]
    )

    _validar_correo_usuario_disponible(db, correo)
    _validar_nombre_usuario_disponible(db, nombre_usuario)

    password_hash = _hash_password_pbkdf2(payload.password_temporal)

    try:
        row = db.execute(
            text(
                """
                INSERT INTO seguridad.usuarios (
                    empleado_id,
                    rol_id,
                    correo_electronico,
                    password_hash,
                    nombre_usuario,
                    requiere_cambio_password,
                    activo
                )
                VALUES (
                    :empleado_id,
                    :rol_id,
                    :correo_electronico,
                    :password_hash,
                    :nombre_usuario,
                    :requiere_cambio_password,
                    :activo
                )
                RETURNING id
                """
            ),
            {
                "empleado_id": empleado["id"],
                "rol_id": payload.rol_id,
                "correo_electronico": correo,
                "password_hash": password_hash,
                "nombre_usuario": nombre_usuario,
                "requiere_cambio_password": payload.requiere_cambio_password,
                "activo": payload.activo,
            },
        ).mappings().one()

        usuario_id = row["id"]
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_usuario_sistema_por_id(db, usuario_id)


def obtener_usuario_sistema_por_id(
    db: Session,
    usuario_id: int,
) -> dict:
    row = db.execute(
        text(
            """
            SELECT
                u.id,
                e.id AS empleado_id,
                e.codigo_empleado,
                e.nombre_completo AS nombre_empleado,
                r.id AS rol_id,
                r.codigo AS rol_codigo,
                r.nombre AS rol_nombre,
                u.correo_electronico,
                u.nombre_usuario,
                u.requiere_cambio_password,
                u.ultimo_acceso,
                u.activo
            FROM seguridad.usuarios u
            INNER JOIN personal.empleados e
                ON e.id = u.empleado_id
            INNER JOIN seguridad.roles r
                ON r.id = u.rol_id
            WHERE u.id = :usuario_id
            """
        ),
        {
            "usuario_id": usuario_id,
        },
    ).mappings().one()

    return dict(row)


def _obtener_empleado_por_codigo(
    db: Session,
    codigo_empleado: str,
) -> dict | None:
    row = db.execute(
        text(
            """
            SELECT
                id,
                codigo_empleado,
                nombre_completo,
                correo,
                estatus
            FROM personal.empleados
            WHERE codigo_empleado = :codigo_empleado
            LIMIT 1
            """
        ),
        {
            "codigo_empleado": codigo_empleado,
        },
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def _validar_horario_activo(
    db: Session,
    horario_id: int,
) -> None:
    existe = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM asistencia.horarios
                WHERE id = :horario_id
                  AND activo = true
            )
            """
        ),
        {
            "horario_id": horario_id,
        },
    ).scalar_one()

    if not existe:
        raise ValueError(f"No existe un horario activo con id {horario_id}.")


def _validar_dispositivo_activo(
    db: Session,
    dispositivo_id: int,
) -> None:
    existe = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM dispositivos.dispositivos
                WHERE id = :dispositivo_id
                  AND activo = true
            )
            """
        ),
        {
            "dispositivo_id": dispositivo_id,
        },
    ).scalar_one()

    if not existe:
        raise ValueError(f"No existe un dispositivo activo con id {dispositivo_id}.")


def _validar_zk_user_id_disponible(
    db: Session,
    dispositivo_id: int,
    zk_user_id: str,
    empleado_id_actual: int,
) -> None:
    existe = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM dispositivos.empleado_dispositivo
                WHERE dispositivo_id = :dispositivo_id
                  AND zk_user_id = :zk_user_id
                  AND empleado_id <> :empleado_id_actual
                  AND activo = true
            )
            """
        ),
        {
            "dispositivo_id": dispositivo_id,
            "zk_user_id": zk_user_id,
            "empleado_id_actual": empleado_id_actual,
        },
    ).scalar_one()

    if existe:
        raise ValueError(
            f"El zk_user_id {zk_user_id} ya está asignado a otro empleado "
            f"en el dispositivo {dispositivo_id}."
        )


def _obtener_rol_activo(
    db: Session,
    rol_id: int,
) -> dict | None:
    row = db.execute(
        text(
            """
            SELECT
                id,
                codigo,
                nombre
            FROM seguridad.roles
            WHERE id = :rol_id
              AND activo = true
            LIMIT 1
            """
        ),
        {
            "rol_id": rol_id,
        },
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def _validar_empleado_sin_usuario(
    db: Session,
    empleado_id: int,
) -> None:
    existe = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM seguridad.usuarios
                WHERE empleado_id = :empleado_id
            )
            """
        ),
        {
            "empleado_id": empleado_id,
        },
    ).scalar_one()

    if existe:
        raise ValueError("El empleado ya tiene usuario de sistema.")


def _validar_correo_usuario_disponible(
    db: Session,
    correo: str,
) -> None:
    existe = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM seguridad.usuarios
                WHERE lower(correo_electronico) = lower(:correo)
            )
            """
        ),
        {
            "correo": correo,
        },
    ).scalar_one()

    if existe:
        raise ValueError(f"Ya existe un usuario con correo {correo}.")


def _validar_nombre_usuario_disponible(
    db: Session,
    nombre_usuario: str,
) -> None:
    existe = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM seguridad.usuarios
                WHERE lower(nombre_usuario) = lower(:nombre_usuario)
            )
            """
        ),
        {
            "nombre_usuario": nombre_usuario,
        },
    ).scalar_one()

    if existe:
        raise ValueError(f"Ya existe un usuario con nombre_usuario {nombre_usuario}.")


def _hash_password_pbkdf2(password: str) -> str:
    iterations = 390000
    salt = secrets.token_bytes(16)

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )

    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(derived_key).decode("ascii")

    return f"pbkdf2_sha256${iterations}${salt_b64}${hash_b64}"


def _limpiar_texto(valor: Any) -> str | None:
    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    return texto


def _normalizar_correo(correo: str | None) -> str | None:
    correo_limpio = _limpiar_texto(correo)

    if correo_limpio is None:
        return None

    return correo_limpio.lower()


def _normalizar_nombre_usuario(nombre_usuario: str) -> str:
    nombre_limpio = nombre_usuario.strip().lower()

    if not nombre_limpio:
        raise ValueError("nombre_usuario no puede estar vacío.")

    if len(nombre_limpio) > 80:
        raise ValueError("nombre_usuario no puede exceder 80 caracteres.")

    return nombre_limpio