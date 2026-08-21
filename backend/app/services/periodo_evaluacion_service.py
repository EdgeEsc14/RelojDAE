"""
Servicio de resolución del Periodo de Evaluación vigente.

Resuelve asistencia.periodos_evaluacion aplicable a una fecha, con el
mismo criterio de unicidad que app.services.politica_service (política
de asistencia): debe existir EXACTAMENTE un periodo ABIERTO cuyo rango
de fechas cubra la fecha dada.

    - Cero periodos ABIERTO aplicables -> SIN_PERIODO.
    - Múltiples periodos ABIERTO aplicables (rangos solapados) ->
      MULTIPLES_PERIODOS. No se elige uno arbitrariamente.

Nunca se debe sustituir por un id fijo (p. ej. periodo_evaluacion_id =
1): ese atajo viola fk_movimientos_puntos_periodo en cuanto la base de
datos no tenga un periodo con ese id — causa raíz del 500 en
POST /asistencia/procesar que este servicio corrige.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class ResolucionPeriodo:
    """Resultado de resolver el periodo de evaluación vigente para una fecha."""

    fecha: date
    estado: str  # "OK", "SIN_PERIODO", "MULTIPLES_PERIODOS"
    periodo: dict[str, Any] | None = None
    candidatos: list[dict[str, Any]] = field(default_factory=list)


def obtener_periodos_vigentes_para_fecha(
    db: Session,
    fecha: date,
) -> list[dict[str, Any]]:
    """
    Retorna los periodos de evaluación ABIERTO cuyo rango cubre la
    fecha dada. El llamador es responsable de tratar 0 o >1 resultados
    como error explícito (ver resolver_periodo_vigente).
    """
    rows = db.execute(
        text(
            """
            SELECT
                id,
                codigo,
                nombre,
                tipo_periodo,
                anio,
                numero_periodo,
                fecha_inicio,
                fecha_fin,
                estatus
            FROM asistencia.periodos_evaluacion
            WHERE estatus = 'ABIERTO'
              AND :fecha BETWEEN fecha_inicio AND fecha_fin
            ORDER BY id ASC
            """
        ),
        {"fecha": fecha},
    ).mappings().all()

    return [dict(row) for row in rows]


def resolver_periodo_vigente(
    db: Session,
    fecha: date,
) -> ResolucionPeriodo:
    """Resuelve el periodo de evaluación vigente para una fecha."""

    candidatos = obtener_periodos_vigentes_para_fecha(db, fecha)

    if len(candidatos) == 0:
        return ResolucionPeriodo(fecha=fecha, estado="SIN_PERIODO")

    if len(candidatos) > 1:
        return ResolucionPeriodo(
            fecha=fecha,
            estado="MULTIPLES_PERIODOS",
            candidatos=candidatos,
        )

    return ResolucionPeriodo(fecha=fecha, estado="OK", periodo=candidatos[0])
