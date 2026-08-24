import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.empleados_write import EmpleadoCreate, EmpleadoUpdate
from app.services.institucion_config import obtener_configuracion_institucional


ESTATUS_EMPLEADO_PERMITIDOS = {
    "ACTIVO",
    "INACTIVO",
    "BAJA",
}


def generar_siguiente_codigo_empleado(
    db: Session,
    prefijo: str = "EMP",
) -> dict:
    prefijo_limpio = _normalizar_prefijo(prefijo)

    query = text(
        """
        SELECT
            COALESCE(
                MAX(
                    SUBSTRING(codigo_empleado FROM '[0-9]+$')::integer
                ),
                0
            ) AS ultimo_numero
        FROM personal.empleados
        WHERE codigo_empleado ~ :patron
        """
    )

    patron = f"^{prefijo_limpio}-[0-9]+$"

    ultimo_numero = db.execute(
        query,
        {
            "patron": patron,
        },
    ).scalar_one()

    siguiente_numero = int(ultimo_numero) + 1
    codigo_empleado = f"{prefijo_limpio}-{siguiente_numero:04d}"

    return {
        "prefijo": prefijo_limpio,
        "ultimo_numero": int(ultimo_numero),
        "siguiente_numero": siguiente_numero,
        "codigo_empleado": codigo_empleado,
    }


def crear_empleado(
    db: Session,
    payload: EmpleadoCreate,
) -> dict:
    data = payload.model_dump()

    codigo_empleado = _normalizar_codigo_empleado(data.get("codigo_empleado"))

    if not codigo_empleado:
        if not payload.generar_codigo:
            raise ValueError("Debe enviar codigo_empleado o activar generar_codigo.")

        prefijo_efectivo = payload.prefijo or obtener_configuracion_institucional()[
            "prefijo_codigo_empleado"
        ]

        codigo_empleado = generar_siguiente_codigo_empleado(
            db=db,
            prefijo=prefijo_efectivo,
        )["codigo_empleado"]

    estatus = _normalizar_estatus(data["estatus"])

    _validar_estatus_empleado(estatus)
    _validar_unidad_organizacional(db, data["unidad_organizacional_id"])
    _validar_puesto(db, data["puesto_id"])
    _validar_supervisor(db, data.get("supervisor_id"))
    _validar_codigo_disponible(db, codigo_empleado)
    _validar_correo_disponible(db, data.get("correo"))

    query = text(
        """
        INSERT INTO personal.empleados (
            codigo_empleado,
            nombres,
            apellido_paterno,
            apellido_materno,
            rfc,
            correo,
            unidad_organizacional_id,
            puesto_id,
            supervisor_id,
            fecha_ingreso,
            estatus
        )
        VALUES (
            :codigo_empleado,
            :nombres,
            :apellido_paterno,
            :apellido_materno,
            :rfc,
            :correo,
            :unidad_organizacional_id,
            :puesto_id,
            :supervisor_id,
            :fecha_ingreso,
            :estatus
        )
        RETURNING
            id,
            codigo_empleado,
            nombres,
            apellido_paterno,
            apellido_materno,
            NULLIF(
                TRIM(CONCAT_WS(' ', apellido_paterno, apellido_materno)),
                ''
            ) AS apellidos,
            nombre_completo,
            correo,
            estatus
        """
    )

    params = {
        "codigo_empleado": codigo_empleado,
        "nombres": data["nombres"].strip(),
        "apellido_paterno": data["apellido_paterno"].strip(),
        "apellido_materno": _limpiar_texto(data.get("apellido_materno")),
        "rfc": _normalizar_rfc(data.get("rfc")),
        "correo": _normalizar_correo(data.get("correo")),
        "unidad_organizacional_id": data["unidad_organizacional_id"],
        "puesto_id": data["puesto_id"],
        "supervisor_id": data.get("supervisor_id"),
        "fecha_ingreso": data.get("fecha_ingreso"),
        "estatus": estatus,
    }

    try:
        row = db.execute(query, params).mappings().one()
        db.commit()
        return dict(row)

    except SQLAlchemyError:
        db.rollback()
        raise


def actualizar_empleado(
    db: Session,
    codigo_empleado: str,
    payload: EmpleadoUpdate,
) -> dict | None:
    empleado_actual = _obtener_empleado_interno_por_codigo(db, codigo_empleado)

    if empleado_actual is None:
        return None

    empleado_id = empleado_actual["id"]
    data = payload.model_dump(exclude_unset=True)

    if not data:
        raise ValueError("No se enviaron campos para actualizar.")

    if "estatus" in data and data["estatus"] is not None:
        data["estatus"] = _normalizar_estatus(data["estatus"])
        _validar_estatus_empleado(data["estatus"])

    if "unidad_organizacional_id" in data and data["unidad_organizacional_id"] is not None:
        _validar_unidad_organizacional(db, data["unidad_organizacional_id"])

    if "puesto_id" in data and data["puesto_id"] is not None:
        _validar_puesto(db, data["puesto_id"])

    if "supervisor_id" in data:
        _validar_supervisor(
            db=db,
            supervisor_id=data["supervisor_id"],
            empleado_id_actual=empleado_id,
        )

    if "correo" in data:
        data["correo"] = _normalizar_correo(data["correo"])
        _validar_correo_disponible(
            db=db,
            correo=data["correo"],
            empleado_id_excluir=empleado_id,
        )

    if "rfc" in data:
        data["rfc"] = _normalizar_rfc(data["rfc"])

    for campo in ("nombres", "apellido_paterno", "apellido_materno"):
        if campo in data:
            data[campo] = _limpiar_texto(data[campo])

    campos_permitidos = {
        "nombres",
        "apellido_paterno",
        "apellido_materno",
        "rfc",
        "correo",
        "unidad_organizacional_id",
        "puesto_id",
        "supervisor_id",
        "fecha_ingreso",
        "fecha_baja",
        "estatus",
    }

    campos_update = {
        campo: valor
        for campo, valor in data.items()
        if campo in campos_permitidos
    }

    if not campos_update:
        raise ValueError("No hay campos válidos para actualizar.")

    set_sql = ", ".join(
        f"{campo} = :{campo}"
        for campo in campos_update.keys()
    )

    query = text(
        f"""
        UPDATE personal.empleados
        SET
            {set_sql},
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE id = :empleado_id
        RETURNING
            id,
            codigo_empleado,
            nombres,
            apellido_paterno,
            apellido_materno,
            NULLIF(
                TRIM(CONCAT_WS(' ', apellido_paterno, apellido_materno)),
                ''
            ) AS apellidos,
            nombre_completo,
            correo,
            estatus
        """
    )

    params = {
        **campos_update,
        "empleado_id": empleado_id,
    }

    try:
        row = db.execute(query, params).mappings().one()
        db.commit()
        return dict(row)

    except SQLAlchemyError:
        db.rollback()
        raise


def actualizar_estatus_empleado(
    db: Session,
    codigo_empleado: str,
    estatus: str,
) -> dict | None:
    empleado_actual = _obtener_empleado_interno_por_codigo(db, codigo_empleado)

    if empleado_actual is None:
        return None

    estatus_normalizado = _normalizar_estatus(estatus)
    _validar_estatus_empleado(estatus_normalizado)

    query = text(
        """
        UPDATE personal.empleados
        SET
            estatus = CAST(:estatus AS VARCHAR),
            fecha_baja = CASE
                WHEN CAST(:estatus AS VARCHAR) = 'BAJA' THEN COALESCE(fecha_baja, CURRENT_DATE)
                ELSE fecha_baja
            END,
            fecha_modificacion = CURRENT_TIMESTAMP
        WHERE id = :empleado_id
        RETURNING
            id,
            codigo_empleado,
            nombres,
            apellido_paterno,
            apellido_materno,
            NULLIF(
                TRIM(CONCAT_WS(' ', apellido_paterno, apellido_materno)),
                ''
            ) AS apellidos,
            nombre_completo,
            correo,
            estatus
        """
    )

    try:
        row = db.execute(
            query,
            {
                "empleado_id": empleado_actual["id"],
                "estatus": estatus_normalizado,
            },
        ).mappings().one()

        db.commit()
        return dict(row)

    except SQLAlchemyError:
        db.rollback()
        raise


def _obtener_empleado_interno_por_codigo(
    db: Session,
    codigo_empleado: str,
) -> dict | None:
    query = text(
        """
        SELECT
            id,
            codigo_empleado,
            correo
        FROM personal.empleados
        WHERE codigo_empleado = :codigo_empleado
        LIMIT 1
        """
    )

    row = db.execute(
        query,
        {
            "codigo_empleado": codigo_empleado,
        },
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def _normalizar_prefijo(prefijo: str) -> str:
    prefijo_limpio = prefijo.strip().upper()

    if not re.fullmatch(r"[A-Z0-9]{2,10}", prefijo_limpio):
        raise ValueError("El prefijo debe tener entre 2 y 10 caracteres alfanuméricos.")

    return prefijo_limpio


def _normalizar_codigo_empleado(codigo_empleado: str | None) -> str | None:
    if codigo_empleado is None:
        return None

    codigo_limpio = codigo_empleado.strip().upper()

    if not codigo_limpio:
        return None

    if len(codigo_limpio) > 30:
        raise ValueError("El código de empleado no puede exceder 30 caracteres.")

    return codigo_limpio


def _normalizar_estatus(estatus: str) -> str:
    return estatus.strip().upper()


def _validar_estatus_empleado(estatus: str) -> None:
    if estatus not in ESTATUS_EMPLEADO_PERMITIDOS:
        raise ValueError(
            f"Estatus inválido: {estatus}. Valores permitidos: "
            f"{', '.join(sorted(ESTATUS_EMPLEADO_PERMITIDOS))}."
        )


def _limpiar_texto(valor: Any) -> str | None:
    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    return texto


def _normalizar_rfc(rfc: str | None) -> str | None:
    rfc_limpio = _limpiar_texto(rfc)

    if rfc_limpio is None:
        return None

    return rfc_limpio.upper()


def _normalizar_correo(correo: str | None) -> str | None:
    correo_limpio = _limpiar_texto(correo)

    if correo_limpio is None:
        return None

    return correo_limpio.lower()


def _validar_unidad_organizacional(
    db: Session,
    unidad_organizacional_id: int,
) -> None:
    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM organizacion.unidades_organizacionales
            WHERE id = :id
              AND activo = true
        )
        """
    )

    existe = db.execute(
        query,
        {
            "id": unidad_organizacional_id,
        },
    ).scalar_one()

    if not existe:
        raise ValueError(
            f"No existe una unidad organizacional activa con id {unidad_organizacional_id}."
        )


def _validar_puesto(
    db: Session,
    puesto_id: int,
) -> None:
    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM organizacion.puestos
            WHERE id = :id
              AND activo = true
        )
        """
    )

    existe = db.execute(
        query,
        {
            "id": puesto_id,
        },
    ).scalar_one()

    if not existe:
        raise ValueError(f"No existe un puesto activo con id {puesto_id}.")


def _validar_supervisor(
    db: Session,
    supervisor_id: int | None,
    empleado_id_actual: int | None = None,
) -> None:
    if supervisor_id is None:
        return

    if empleado_id_actual is not None and supervisor_id == empleado_id_actual:
        raise ValueError("El empleado no puede ser su propio supervisor.")

    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM personal.empleados
            WHERE id = :id
              AND estatus = 'ACTIVO'
        )
        """
    )

    existe = db.execute(
        query,
        {
            "id": supervisor_id,
        },
    ).scalar_one()

    if not existe:
        raise ValueError(f"No existe un supervisor activo con id {supervisor_id}.")


def _validar_codigo_disponible(
    db: Session,
    codigo_empleado: str,
) -> None:
    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM personal.empleados
            WHERE codigo_empleado = :codigo_empleado
        )
        """
    )

    existe = db.execute(
        query,
        {
            "codigo_empleado": codigo_empleado,
        },
    ).scalar_one()

    if existe:
        raise ValueError(f"Ya existe un empleado con código {codigo_empleado}.")


def _validar_correo_disponible(
    db: Session,
    correo: str | None,
    empleado_id_excluir: int | None = None,
) -> None:
    if correo is None:
        return

    if empleado_id_excluir is None:
        query = text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM personal.empleados
                WHERE lower(correo) = lower(:correo)
            )
            """
        )

        params = {
            "correo": correo,
        }

    else:
        query = text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM personal.empleados
                WHERE lower(correo) = lower(:correo)
                  AND id <> :empleado_id_excluir
            )
            """
        )

        params = {
            "correo": correo,
            "empleado_id_excluir": empleado_id_excluir,
        }

    existe = db.execute(query, params).scalar_one()

    if existe:
        raise ValueError(f"Ya existe un empleado con correo {correo}.")