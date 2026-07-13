from __future__ import annotations

import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.horarios import HorarioCreate


def _limpiar_texto(value: Any) -> str | None:
    if value is None:
        return None

    text_value = str(value).strip()

    if not text_value:
        return None

    return text_value


def _normalizar_codigo(value: str) -> str:
    clean_value = value.strip().upper()
    clean_value = re.sub(r"[^A-Z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")

    if not clean_value:
        raise ValueError("El código del horario no puede estar vacío.")

    return clean_value


def listar_horarios_admin(db: Session) -> dict:
    query = text(
        """
        SELECT
            h.id,
            h.codigo,
            h.nombre,
            h.descripcion,
            h.tolerancia_entrada_minutos,
            h.descanso_minutos,
            h.permite_tiempo_extra,
            h.activo,
            h.fecha_creacion,
            h.fecha_modificacion,
            h.hora_entrada,
            h.hora_salida,

            tt.id AS tipo_turno_id,
            tt.codigo AS tipo_turno_codigo,
            tt.nombre AS tipo_turno_nombre,
            tt.hora_entrada_desde,
            tt.hora_entrada_hasta,
            tt.duracion_jornada_minutos,
            tt.modalidad_tiempo_extra,

            COUNT(ah.id) FILTER (
                WHERE ah.estatus = 'ACTIVA'
                  AND ah.fecha_inicio <= CURRENT_DATE
                  AND (
                        ah.fecha_fin IS NULL
                        OR ah.fecha_fin >= CURRENT_DATE
                      )
            ) AS empleados_asignados

        FROM asistencia.horarios h

        INNER JOIN asistencia.tipos_turno tt
            ON tt.id = h.tipo_turno_id

        LEFT JOIN asistencia.asignaciones_horario ah
            ON ah.horario_id = h.id

        GROUP BY
            h.id,
            h.codigo,
            h.nombre,
            h.descripcion,
            h.tolerancia_entrada_minutos,
            h.descanso_minutos,
            h.permite_tiempo_extra,
            h.activo,
            h.fecha_creacion,
            h.fecha_modificacion,
            h.hora_entrada,
            h.hora_salida,
            tt.id,
            tt.codigo,
            tt.nombre,
            tt.hora_entrada_desde,
            tt.hora_entrada_hasta,
            tt.duracion_jornada_minutos,
            tt.modalidad_tiempo_extra

        ORDER BY
            h.activo DESC,
            h.nombre
        """
    )

    rows = db.execute(query).mappings().all()

    return {
        "total": len(rows),
        "items": [dict(row) for row in rows],
    }


def obtener_horario_por_id(
    db: Session,
    horario_id: int,
) -> dict | None:
    query = text(
        """
        SELECT
            h.id,
            h.codigo,
            h.nombre,
            h.descripcion,
            h.tolerancia_entrada_minutos,
            h.descanso_minutos,
            h.permite_tiempo_extra,
            h.activo,
            h.fecha_creacion,
            h.fecha_modificacion,
            h.hora_entrada,
            h.hora_salida,

            tt.id AS tipo_turno_id,
            tt.codigo AS tipo_turno_codigo,
            tt.nombre AS tipo_turno_nombre,
            tt.hora_entrada_desde,
            tt.hora_entrada_hasta,
            tt.duracion_jornada_minutos,
            tt.modalidad_tiempo_extra,

            COUNT(ah.id) FILTER (
                WHERE ah.estatus = 'ACTIVA'
                  AND ah.fecha_inicio <= CURRENT_DATE
                  AND (
                        ah.fecha_fin IS NULL
                        OR ah.fecha_fin >= CURRENT_DATE
                      )
            ) AS empleados_asignados

        FROM asistencia.horarios h

        INNER JOIN asistencia.tipos_turno tt
            ON tt.id = h.tipo_turno_id

        LEFT JOIN asistencia.asignaciones_horario ah
            ON ah.horario_id = h.id

        WHERE h.id = :horario_id

        GROUP BY
            h.id,
            h.codigo,
            h.nombre,
            h.descripcion,
            h.tolerancia_entrada_minutos,
            h.descanso_minutos,
            h.permite_tiempo_extra,
            h.activo,
            h.fecha_creacion,
            h.fecha_modificacion,
            h.hora_entrada,
            h.hora_salida,
            tt.id,
            tt.codigo,
            tt.nombre,
            tt.hora_entrada_desde,
            tt.hora_entrada_hasta,
            tt.duracion_jornada_minutos,
            tt.modalidad_tiempo_extra

        LIMIT 1
        """
    )

    row = db.execute(
        query,
        {
            "horario_id": horario_id,
        },
    ).mappings().first()

    if row is None:
        return None

    return dict(row)


def crear_horario(
    db: Session,
    payload: HorarioCreate,
) -> dict:
    codigo = _normalizar_codigo(payload.codigo)
    nombre = _limpiar_texto(payload.nombre)

    if nombre is None:
        raise ValueError("El nombre del horario no puede estar vacío.")

    _validar_horas_horario(
        hora_entrada=payload.hora_entrada,
        hora_salida=payload.hora_salida,
    )

    _validar_tipo_turno_activo(
        db=db,
        tipo_turno_id=payload.tipo_turno_id,
    )

    _validar_codigo_disponible(
        db=db,
        codigo=codigo,
    )

    _validar_nombre_disponible(
        db=db,
        nombre=nombre,
    )

    try:
        row = db.execute(
            text(
                """
                INSERT INTO asistencia.horarios (
                    codigo,
                    nombre,
                    descripcion,
                    tolerancia_entrada_minutos,
                    descanso_minutos,
                    permite_tiempo_extra,
                    activo,
                    tipo_turno_id,
                    hora_entrada,
                    hora_salida
                )
                VALUES (
                    :codigo,
                    :nombre,
                    :descripcion,
                    :tolerancia_entrada_minutos,
                    :descanso_minutos,
                    :permite_tiempo_extra,
                    :activo,
                    :tipo_turno_id,
                    :hora_entrada,
                    :hora_salida
                )
                RETURNING id
                """
            ),
            {
                "codigo": codigo,
                "nombre": nombre,
                "descripcion": _limpiar_texto(payload.descripcion),
                "tolerancia_entrada_minutos": payload.tolerancia_entrada_minutos,
                "descanso_minutos": payload.descanso_minutos,
                "permite_tiempo_extra": payload.permite_tiempo_extra,
                "activo": payload.activo,
                "tipo_turno_id": payload.tipo_turno_id,
                "hora_entrada": payload.hora_entrada,
                "hora_salida": payload.hora_salida,
            },
        ).mappings().one()

        horario_id = row["id"]
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    horario = obtener_horario_por_id(
        db=db,
        horario_id=horario_id,
    )

    if horario is None:
        raise ValueError("No fue posible recuperar el horario creado.")

    return horario


def actualizar_estatus_horario(
    db: Session,
    horario_id: int,
    activo: bool,
) -> dict | None:
    try:
        row = db.execute(
            text(
                """
                UPDATE asistencia.horarios
                SET
                    activo = :activo,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :horario_id
                RETURNING id
                """
            ),
            {
                "horario_id": horario_id,
                "activo": activo,
            },
        ).mappings().first()

        if row is None:
            db.rollback()
            return None

        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_horario_por_id(
        db=db,
        horario_id=horario_id,
    )


def _validar_horas_horario(
    hora_entrada,
    hora_salida,
) -> None:
    if hora_entrada is None:
        raise ValueError("La hora de entrada es obligatoria.")

    if hora_salida is None:
        raise ValueError("La hora de salida es obligatoria.")

    if hora_entrada == hora_salida:
        raise ValueError(
            "La hora de entrada y la hora de salida no pueden ser iguales."
        )


def _validar_tipo_turno_activo(
    db: Session,
    tipo_turno_id: int,
) -> None:
    existe = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM asistencia.tipos_turno
                WHERE id = :tipo_turno_id
                  AND activo = true
            )
            """
        ),
        {
            "tipo_turno_id": tipo_turno_id,
        },
    ).scalar_one()

    if not existe:
        raise ValueError(
            f"No existe un tipo de turno activo con id {tipo_turno_id}."
        )


def _validar_codigo_disponible(
    db: Session,
    codigo: str,
) -> None:
    existe = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM asistencia.horarios
                WHERE codigo = :codigo
            )
            """
        ),
        {
            "codigo": codigo,
        },
    ).scalar_one()

    if existe:
        raise ValueError(f"Ya existe un horario con código {codigo}.")


def _validar_nombre_disponible(
    db: Session,
    nombre: str,
) -> None:
    existe = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM asistencia.horarios
                WHERE lower(btrim(nombre)) = lower(btrim(:nombre))
            )
            """
        ),
        {
            "nombre": nombre,
        },
    ).scalar_one()

    if existe:
        raise ValueError(f"Ya existe un horario con nombre {nombre}.")