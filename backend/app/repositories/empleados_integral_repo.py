from __future__ import annotations

import unicodedata
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    generate_random_password,
    hash_password,
)
from app.schemas.empleados_integral import (
    AltaIntegralEmpleadoRequest,
)


def crear_alta_integral_empleado(
    *,
    db: Session,
    payload: AltaIntegralEmpleadoRequest,
    solicitado_por_usuario_id: int,
) -> dict[str, Any]:
    """
    Crea en una sola transacción:

    - Empleado.
    - Asignación inicial de horario.
    - Usuario del sistema con rol EMPLEADO.
    - Relaciones pendientes con dispositivos.

    La escritura física en los relojes se ejecuta después,
    mediante el servicio de sincronización.
    """

    try:
        _validar_catalogos(
            db=db,
            payload=payload,
        )

        _validar_datos_unicos(
            db=db,
            rfc=payload.rfc,
            curp=payload.curp,
            correo_personal=payload.correo_personal,
        )

        rol = _obtener_rol(db, payload.rol_id)

        dispositivos = _obtener_dispositivos(
            db=db,
            registrar_en_reloj=(
                payload.registrar_en_reloj
            ),
            todos_dispositivos_activos=(
                payload.todos_dispositivos_activos
            ),
            dispositivo_ids=payload.dispositivo_ids,
        )

        codigo_empleado = db.execute(
            text(
                """
                SELECT
                    personal.generar_codigo_empleado_dae()
                """
            )
        ).scalar_one()

        empleado = db.execute(
            text(
                """
                INSERT INTO personal.empleados (
                    codigo_empleado,
                    nombres,
                    apellido_paterno,
                    apellido_materno,
                    rfc,
                    curp,
                    telefono,
                    correo,
                    correo_personal,
                    tipo_contratacion_id,
                    unidad_organizacional_id,
                    puesto_id,
                    supervisor_id,
                    fecha_ingreso,
                    estatus,
                    observaciones
                )
                VALUES (
                    :codigo_empleado,
                    :nombres,
                    :apellido_paterno,
                    :apellido_materno,
                    :rfc,
                    :curp,
                    :telefono,
                    :correo,
                    :correo_personal,
                    :tipo_contratacion_id,
                    :unidad_organizacional_id,
                    :puesto_id,
                    :supervisor_id,
                    :fecha_ingreso,
                    'ACTIVO',
                    :observaciones
                )
                RETURNING
                    id,
                    codigo_empleado,
                    nombre_completo,
                    rfc,
                    curp,
                    correo_personal,
                    estatus
                """
            ),
            {
                "codigo_empleado": codigo_empleado,
                "nombres": payload.nombres,
                "apellido_paterno": (
                    payload.apellido_paterno
                ),
                "apellido_materno": (
                    payload.apellido_materno
                ),
                "rfc": payload.rfc,
                "curp": payload.curp,
                "telefono": payload.telefono,
                # Compatibilidad temporal con vistas y
                # consultas que todavía utilizan e.correo.
                "correo": payload.correo_personal,
                "correo_personal": (
                    payload.correo_personal
                ),
                "tipo_contratacion_id": (
                    payload.tipo_contratacion_id
                ),
                "unidad_organizacional_id": (
                    payload.unidad_organizacional_id
                ),
                "puesto_id": payload.puesto_id,
                "supervisor_id": payload.supervisor_id,
                "fecha_ingreso": payload.fecha_ingreso,
                "observaciones": payload.observaciones,
            },
        ).mappings().one()

        asignacion = db.execute(
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
                    NULL,
                    'ACTIVA',
                    'Asignación inicial por alta integral'
                )
                RETURNING id
                """
            ),
            {
                "empleado_id": empleado["id"],
                "horario_id": payload.horario_id,
                "fecha_inicio": payload.fecha_ingreso,
            },
        ).mappings().one()

        horario = db.execute(
            text(
                """
                SELECT
                    id,
                    codigo,
                    nombre
                FROM asistencia.horarios
                WHERE id = :horario_id
                """
            ),
            {
                "horario_id": payload.horario_id,
            },
        ).mappings().one()

        password_temporal = generate_random_password(
            length=16
        )

        usuario = db.execute(
            text(
                """
                INSERT INTO seguridad.usuarios (
                    empleado_id,
                    rol_id,
                    correo,
                    correo_electronico,
                    password_hash,
                    nombre_usuario,
                    rol,
                    estatus,
                    correo_verificado,
                    requiere_cambio_password,
                    activo
                )
                VALUES (
                    :empleado_id,
                    :rol_id,
                    :correo,
                    :correo_electronico,
                    :password_hash,
                    :nombre_usuario,
                    :rol_codigo,
                    'ACTIVO',
                    FALSE,
                    TRUE,
                    TRUE
                )
                RETURNING
                    id,
                    nombre_usuario,
                    correo_electronico,
                    requiere_cambio_password
                """
            ),
            {
                "empleado_id": empleado["id"],
                "rol_id": rol["id"],
                "rol_codigo": rol["codigo"],
                "correo": payload.correo_personal,
                "correo_electronico": (
                    payload.correo_personal
                ),
                "password_hash": hash_password(
                    password_temporal
                ),
                "nombre_usuario": codigo_empleado,
            },
        ).mappings().one()

        dispositivos_creados: list[
            dict[str, Any]
        ] = []

        if dispositivos:
            zk_user_id = (
                payload.zk_user_id
                if payload.zk_user_id
                else _generar_siguiente_zk_user_id(db)
            )

            nombre_dispositivo = (
                _crear_nombre_para_dispositivo(
                    nombres=payload.nombres,
                    apellido_paterno=(
                        payload.apellido_paterno
                    ),
                )
            )

            for dispositivo in dispositivos:
                relacion = db.execute(
                    text(
                        """
                        INSERT INTO
                            dispositivos.empleado_dispositivo (
                                empleado_id,
                                dispositivo_id,
                                zk_uid,
                                zk_user_id,
                                nombre_en_dispositivo,
                                privilegio,
                                grupo,
                                tarjeta,
                                sincronizado,
                                estado_sincronizacion,
                                intentos_sincronizacion,
                                solicitado_por_usuario_id,
                                activo
                            )
                        VALUES (
                            :empleado_id,
                            :dispositivo_id,
                            NULL,
                            :zk_user_id,
                            :nombre_en_dispositivo,
                            0,
                            NULL,
                            NULL,
                            FALSE,
                            'PENDIENTE',
                            0,
                            :solicitado_por_usuario_id,
                            TRUE
                        )
                        RETURNING id
                        """
                    ),
                    {
                        "empleado_id": empleado["id"],
                        "dispositivo_id": (
                            dispositivo["id"]
                        ),
                        "zk_user_id": zk_user_id,
                        "nombre_en_dispositivo": (
                            nombre_dispositivo
                        ),
                        "solicitado_por_usuario_id": (
                            solicitado_por_usuario_id
                        ),
                    },
                ).mappings().one()

                dispositivos_creados.append(
                    {
                        "empleado_dispositivo_id": (
                            relacion["id"]
                        ),
                        "dispositivo_id": (
                            dispositivo["id"]
                        ),
                        "dispositivo_codigo": (
                            dispositivo["codigo"]
                        ),
                        "dispositivo_nombre": (
                            dispositivo["nombre"]
                        ),
                        "zk_user_id": zk_user_id,
                        "estado_sincronizacion": (
                            "PENDIENTE"
                        ),
                    }
                )

        db.commit()

        return {
            "empleado_id": empleado["id"],
            "codigo_empleado": (
                empleado["codigo_empleado"]
            ),
            "nombre_completo": (
                empleado["nombre_completo"]
            ),
            "rfc": empleado["rfc"],
            "curp": empleado["curp"],
            "correo_personal": (
                empleado["correo_personal"]
            ),
            "estatus": empleado["estatus"],
            "usuario_sistema": {
                "usuario_id": usuario["id"],
                "nombre_usuario": (
                    usuario["nombre_usuario"]
                ),
                "correo_electronico": (
                    usuario["correo_electronico"]
                ),
                "rol_codigo": rol["codigo"],
                "requiere_cambio_password": (
                    usuario[
                        "requiere_cambio_password"
                    ]
                ),
                # Se devuelve una sola vez.
                "password_temporal": (
                    password_temporal
                ),
            },
            "horario": {
                "asignacion_id": asignacion["id"],
                "horario_id": horario["id"],
                "horario_codigo": horario["codigo"],
                "horario_nombre": horario["nombre"],
                "fecha_inicio": payload.fecha_ingreso,
            },
            "sincronizacion_solicitada": (
                payload.registrar_en_reloj
            ),
            "dispositivos": dispositivos_creados,
        }

    except IntegrityError as exc:
        db.rollback()

        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )

        print()
        print("=" * 80)
        print("ERROR DE INTEGRIDAD EN ALTA INTEGRAL")
        print("Restricción:", constraint_name)
        print("Detalle:", exc.orig)
        print("=" * 80)
        print()

        detalle = str(exc.orig).lower()

        if "rfc" in detalle:
            raise ValueError(
                "El RFC ya está registrado."
            ) from exc

        if "curp" in detalle:
            raise ValueError(
                "La CURP ya está registrada."
            ) from exc

        if "correo" in detalle:
            raise ValueError(
                "El correo personal ya está registrado."
            ) from exc

        if "codigo_empleado" in detalle:
            raise ValueError(
                "No fue posible reservar el código "
                "de empleado."
            ) from exc

        raise ValueError(
            "No fue posible completar el alta por una "
            f"restricción de datos: {constraint_name or 'desconocida'}."
        ) from exc

        if "rfc" in detalle:
            raise ValueError(
                "El RFC ya está registrado."
            ) from exc

        if "curp" in detalle:
            raise ValueError(
                "La CURP ya está registrada."
            ) from exc

        if "correo" in detalle:
            raise ValueError(
                "El correo personal ya está registrado."
            ) from exc

        if "codigo_empleado" in detalle:
            raise ValueError(
                "No fue posible reservar el código "
                "de empleado."
            ) from exc

        raise ValueError(
            "No fue posible completar el alta "
            "por una restricción de datos."
        ) from exc

    except Exception:
        db.rollback()
        raise


def _validar_catalogos(
    *,
    db: Session,
    payload: AltaIntegralEmpleadoRequest,
) -> None:
    validaciones = [
        (
            """
            SELECT EXISTS (
                SELECT 1
                FROM personal.tipos_contratacion
                WHERE id = :id
                  AND activo = TRUE
            )
            """,
            payload.tipo_contratacion_id,
            "tipo de contratación",
        ),
        (
            """
            SELECT EXISTS (
                SELECT 1
                FROM organizacion.unidades_organizacionales
                WHERE id = :id
                  AND activo = TRUE
            )
            """,
            payload.unidad_organizacional_id,
            "unidad organizacional",
        ),
        (
            """
            SELECT EXISTS (
                SELECT 1
                FROM organizacion.puestos
                WHERE id = :id
                  AND activo = TRUE
            )
            """,
            payload.puesto_id,
            "puesto",
        ),
        (
            """
            SELECT EXISTS (
                SELECT 1
                FROM asistencia.horarios
                WHERE id = :id
                  AND activo = TRUE
            )
            """,
            payload.horario_id,
            "horario",
        ),
    ]

    for sql, identifier, label in validaciones:
        exists = db.execute(
            text(sql),
            {"id": identifier},
        ).scalar_one()

        if not exists:
            raise ValueError(
                f"No existe un {label} activo "
                f"con id {identifier}."
            )

    if payload.supervisor_id is not None:
        supervisor_exists = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM personal.empleados
                    WHERE id = :id
                      AND estatus = 'ACTIVO'
                )
                """
            ),
            {
                "id": payload.supervisor_id,
            },
        ).scalar_one()

        if not supervisor_exists:
            raise ValueError(
                "El jefe directo seleccionado "
                "no existe o no está activo."
            )


def _validar_datos_unicos(
    *,
    db: Session,
    rfc: str,
    curp: str | None,
    correo_personal: str,
) -> None:
    rfc_exists = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM personal.empleados
                WHERE UPPER(BTRIM(rfc)) =
                      UPPER(BTRIM(:rfc))
            )
            """
        ),
        {"rfc": rfc},
    ).scalar_one()

    if rfc_exists:
        raise ValueError(
            "El RFC ya está registrado."
        )

    if curp:
        curp_exists = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM personal.empleados
                    WHERE UPPER(BTRIM(curp)) =
                          UPPER(BTRIM(:curp))
                )
                """
            ),
            {"curp": curp},
        ).scalar_one()

        if curp_exists:
            raise ValueError(
                "La CURP ya está registrada."
            )

    email_exists = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM personal.empleados
                WHERE LOWER(BTRIM(correo_personal)) =
                      LOWER(BTRIM(:correo))

                UNION ALL

                SELECT 1
                FROM seguridad.usuarios
                WHERE LOWER(BTRIM(correo_electronico)) =
                      LOWER(BTRIM(:correo))
            )
            """
        ),
        {"correo": correo_personal},
    ).scalar_one()

    if email_exists:
        raise ValueError(
            "El correo personal ya está registrado."
        )


def _obtener_rol(
    db: Session,
    rol_id: int | None = None,
) -> dict[str, Any]:
    """
    Obtiene un rol activo.

    Si se proporciona rol_id, busca ese rol específico.
    Si no, busca el rol 'empleado' por defecto.
    """
    if rol_id is not None:
        row = db.execute(
            text(
                """
                SELECT
                    id,
                    LOWER(codigo) AS codigo
                FROM seguridad.roles
                WHERE id = :rol_id
                  AND activo = TRUE
                LIMIT 1
                """
            ),
            {"rol_id": rol_id},
        ).mappings().first()

        if row is None:
            raise ValueError(
                f"No existe un rol activo con id {rol_id}."
            )

        return dict(row)

    row = db.execute(
        text(
            """
            SELECT
                id,
                LOWER(codigo) AS codigo
            FROM seguridad.roles
            WHERE LOWER(codigo) = 'empleado'
              AND activo = TRUE
            LIMIT 1
            """
        )
    ).mappings().first()

    if row is None:
        raise ValueError(
            "No existe el rol EMPLEADO activo."
        )

    return dict(row)


def _obtener_dispositivos(
    *,
    db: Session,
    registrar_en_reloj: bool,
    todos_dispositivos_activos: bool,
    dispositivo_ids: list[int],
) -> list[dict[str, Any]]:
    if not registrar_en_reloj:
        return []

    if todos_dispositivos_activos:
        rows = db.execute(
            text(
                """
                SELECT
                    id,
                    codigo,
                    nombre
                FROM dispositivos.dispositivos
                WHERE activo = TRUE
                ORDER BY
                    es_predeterminado DESC,
                    id
                """
            )
        ).mappings().all()

        if not rows:
            raise ValueError(
                "No existen relojes activos."
            )

        return [
            dict(row)
            for row in rows
        ]

    rows = db.execute(
        text(
            """
            SELECT
                id,
                codigo,
                nombre
            FROM dispositivos.dispositivos
            WHERE activo = TRUE
              AND id = ANY(
                  CAST(:ids AS BIGINT[])
              )
            ORDER BY
                es_predeterminado DESC,
                id
            """
        ),
        {
            "ids": dispositivo_ids,
        },
    ).mappings().all()

    found_ids = {
        int(row["id"])
        for row in rows
    }

    missing_ids = (
        set(dispositivo_ids) - found_ids
    )

    if missing_ids:
        missing_text = ", ".join(
            str(value)
            for value in sorted(missing_ids)
        )

        raise ValueError(
            "Los siguientes dispositivos no existen "
            f"o están inactivos: {missing_text}."
        )

    return [
        dict(row)
        for row in rows
    ]


def _generar_siguiente_zk_user_id(
    db: Session,
) -> str:
    value = db.execute(
        text(
            """
            WITH ids AS (
                SELECT
                    zk_user_id
                FROM dispositivos.empleado_dispositivo
                WHERE zk_user_id ~ '^[0-9]+$'

                UNION ALL

                SELECT
                    zk_user_id
                FROM personal.empleados
                WHERE zk_user_id ~ '^[0-9]+$'
            )
            SELECT
                COALESCE(
                    MAX(zk_user_id::BIGINT),
                    0
                ) + 1
            FROM ids
            """
        )
    ).scalar_one()

    return str(int(value))


def _crear_nombre_para_dispositivo(
    *,
    nombres: str,
    apellido_paterno: str,
) -> str:
    raw_name = (
        f"{nombres} {apellido_paterno}"
    )

    normalized = unicodedata.normalize(
        "NFKD",
        raw_name,
    )

    ascii_name = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    clean_name = " ".join(
        ascii_name.upper().split()
    )

    # Límite conservador para terminales ZK/FCX.
    return clean_name[:24]