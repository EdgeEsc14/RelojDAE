"""
Repositorio para el módulo de Política de Asistencia.

Accede a asistencia.politicas_asistencia.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


# Columnas completas de asistencia.politicas_asistencia expuestas a
# los llamadores (motor de procesamiento y API de Configuración).
# Mantener en una sola lista evita que ambos consumidores diverjan
# sobre qué columnas trae cada fila.
_COLUMNAS_POLITICA = """
    id,
    codigo,
    version,
    nombre,
    descripcion,
    tipo_periodo,
    limite_tolerancia_segundos,
    limite_retardo_menor_segundos,
    limite_retardo_mayor_segundos,
    puntos_retardo_menor,
    puntos_retardo_mayor,
    puntos_para_descanso,
    max_dias_justificables_periodo,
    max_puntos_descontables_por_dia,
    descansos_para_revision_baja,
    faltas_consecutivas_revision_baja,
    vigencia_desde,
    vigencia_hasta,
    activo,
    fecha_creacion,
    fecha_modificacion
"""


def obtener_politicas_vigentes_para_fecha(
    db: Session,
    fecha: date,
) -> list[dict[str, Any]]:
    """
    Retorna las políticas activas cuya vigencia cubre la fecha dada.

    Contrato §5: la resolución usa activo, vigencia_desde y vigencia_hasta.
    Debe existir exactamente una política aplicable por fecha; el
    llamador es responsable de tratar 0 o >1 resultados como error.
    """
    rows = db.execute(
        text(
            f"""
            SELECT {_COLUMNAS_POLITICA}
            FROM asistencia.politicas_asistencia
            WHERE activo = TRUE
              AND vigencia_desde <= :fecha
              AND (vigencia_hasta IS NULL OR vigencia_hasta >= :fecha)
            ORDER BY id ASC
            """
        ),
        {"fecha": fecha},
    ).mappings().all()

    return [dict(row) for row in rows]


def obtener_politica_por_id(
    db: Session,
    politica_id: int,
) -> dict[str, Any] | None:
    """Retorna una política por id, o None si no existe."""
    row = db.execute(
        text(
            f"""
            SELECT {_COLUMNAS_POLITICA}
            FROM asistencia.politicas_asistencia
            WHERE id = :politica_id
            """
        ),
        {"politica_id": politica_id},
    ).mappings().first()

    return dict(row) if row is not None else None


# Campos editables desde Configuración (Requisitos del endpoint de
# política). No incluye codigo/version/vigencia/activo: cambiar esos
# campos puede crear solapamientos y está fuera de este alcance.
CAMPOS_EDITABLES_POLITICA = (
    "limite_tolerancia_segundos",
    "limite_retardo_menor_segundos",
    "limite_retardo_mayor_segundos",
    "puntos_retardo_menor",
    "puntos_retardo_mayor",
    "puntos_para_descanso",
    "descansos_para_revision_baja",
    "faltas_consecutivas_revision_baja",
)


def actualizar_politica(
    db: Session,
    politica_id: int,
    campos: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Actualiza los límites/puntos editables de una política existente.

    `campos` debe contener únicamente claves de CAMPOS_EDITABLES_POLITICA.
    Las validaciones de orden y coherencia (crecientes, no negativos,
    etc.) las aplica el schema/servicio antes de llegar aquí; el CHECK
    de PostgreSQL (migración 022) es la última línea de defensa.
    """
    columnas_set = ", ".join(
        f"{campo} = :{campo}" for campo in campos
    )

    try:
        row = db.execute(
            text(
                f"""
                UPDATE asistencia.politicas_asistencia
                SET
                    {columnas_set},
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = :politica_id
                RETURNING id
                """
            ),
            {**campos, "politica_id": politica_id},
        ).mappings().first()

        if row is None:
            db.rollback()
            return None

        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return obtener_politica_por_id(db=db, politica_id=politica_id)
