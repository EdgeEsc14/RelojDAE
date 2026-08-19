"""
Servicio de Calendario Laboral.

Determina si una fecha es laborable para el procesamiento de asistencia.

Orden de prioridad para resolución de conflictos:
    1. Evento calendario con menor número de prioridad gana.
    2. Si no hay eventos de calendario, se usa horario_dias del empleado.
    3. Si no hay horario_dias, se considera laborable por defecto.

El calendario es opt-in: si no tiene eventos configurados, el
procesamiento actual no se ve afectado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.calendario_repo import obtener_eventos_para_fecha


@dataclass
class ResolucionDia:
    """Resultado de la resolución de un día."""

    fecha: date
    es_laborable: bool
    fuente: str  # "CALENDARIO", "HORARIO_DIAS", "DEFAULT"
    eventos: list[dict[str, Any]]


def resolver_fecha_laborable(
    db: Session,
    fecha: date,
    empleado_id: int | None = None,
) -> ResolucionDia:
    """
    Determina si una fecha es laborable.

    Flujo:
    1. Consulta eventos de calendario activos para la fecha.
    2. Si hay eventos que afectan asistencia → el de mayor prioridad
       (menor número) decide.
    3. Si no hay eventos de calendario → consulta horario_dias del empleado.
    4. Si no hay horario_dias → se considera laborable (default).

    Un evento LABORABLE_EXTRAORDINARIO con prioridad baja puede
    sobreescribir un día normalmente no laborable.
    """

    # Paso 1: Consultar calendario
    eventos = obtener_eventos_para_fecha(db, fecha)

    # Filtrar solo los que afectan asistencia
    eventos_asistencia = [e for e in eventos if e["afecta_asistencia"]]

    if eventos_asistencia:
        # El evento con menor prioridad (mayor importancia) decide
        evento_decisivo = eventos_asistencia[0]
        return ResolucionDia(
            fecha=fecha,
            es_laborable=evento_decisivo["es_laborable"],
            fuente="CALENDARIO",
            eventos=eventos,
        )

    # Paso 2: Si no hay eventos, consultar horario_dias
    if empleado_id is not None:
        es_laboral_horario = _consultar_horario_dias(db, fecha, empleado_id)

        if es_laboral_horario is not None:
            return ResolucionDia(
                fecha=fecha,
                es_laborable=es_laboral_horario,
                fuente="HORARIO_DIAS",
                eventos=eventos,
            )

    # Paso 3: Default — considerar laborable
    return ResolucionDia(
        fecha=fecha,
        es_laborable=True,
        fuente="DEFAULT",
        eventos=eventos,
    )


def _consultar_horario_dias(
    db: Session,
    fecha: date,
    empleado_id: int,
) -> bool | None:
    """
    Consulta horario_dias para determinar si el día de la semana
    es laboral según el horario asignado al empleado.

    Retorna:
    - True: día laboral según horario
    - False: día no laboral según horario
    - None: no hay asignación de horario o no hay horario_dias
    """

    # dia_semana en PostgreSQL: 1=Lunes ... 7=Domingo (ISO)
    dia_semana_iso = fecha.isoweekday()  # 1=Lun, 7=Dom

    row = db.execute(
        text(
            """
            SELECT hd.es_laboral
            FROM asistencia.horario_dias hd
            INNER JOIN asistencia.asignaciones_horario ah
                ON ah.horario_id = hd.horario_id
            WHERE ah.empleado_id = :empleado_id
              AND ah.estatus = 'ACTIVA'
              AND ah.fecha_inicio <= :fecha
              AND (ah.fecha_fin IS NULL OR ah.fecha_fin >= :fecha)
              AND hd.dia_semana = :dia_semana
            LIMIT 1
            """
        ),
        {
            "empleado_id": empleado_id,
            "fecha": fecha,
            "dia_semana": dia_semana_iso,
        },
    ).mappings().first()

    if row is None:
        return None

    return bool(row["es_laboral"])


def consultar_dia(
    db: Session,
    fecha: date,
    empleado_id: int | None = None,
) -> dict[str, Any]:
    """
    Consulta pública para el endpoint GET /calendario/dia/{fecha}.

    Retorna toda la información de resolución de la fecha.
    """

    resolucion = resolver_fecha_laborable(db, fecha, empleado_id)

    return {
        "fecha": fecha.isoformat(),
        "es_laborable": resolucion.es_laborable,
        "fuente": resolucion.fuente,
        "eventos": resolucion.eventos,
    }
