"""
Servicio de Política de Asistencia.

Resuelve la política de asistencia vigente para una fecha (Contrato §5).

Debe existir EXACTAMENTE una política aplicable:
    - Cero políticas vigentes  -> error explícito (SIN_POLITICA).
    - Múltiples políticas vigentes con rangos de vigencia solapados
      -> error explícito (MULTIPLES_POLITICAS). No se elige una
      automáticamente.

No depende del empleado: las políticas de asistencia no están
actualmente segmentadas por empleado/unidad en el esquema, solo por
vigencia y estado activo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.politica_repo import (
    CAMPOS_EDITABLES_POLITICA,
    actualizar_politica,
    obtener_politicas_vigentes_para_fecha,
)
from app.schemas.politicas import PoliticaAsistenciaUpdate


@dataclass
class ResolucionPolitica:
    """Resultado de resolver la política de asistencia vigente para una fecha."""

    fecha: date
    estado: str  # "OK", "SIN_POLITICA", "MULTIPLES_POLITICAS"
    politica: dict[str, Any] | None = None
    candidatos: list[dict[str, Any]] = field(default_factory=list)


def resolver_politica_vigente(
    db: Session,
    fecha: date,
) -> ResolucionPolitica:
    """Resuelve la política de asistencia vigente para una fecha."""

    candidatos = obtener_politicas_vigentes_para_fecha(db, fecha)

    if len(candidatos) == 0:
        return ResolucionPolitica(fecha=fecha, estado="SIN_POLITICA")

    if len(candidatos) > 1:
        return ResolucionPolitica(
            fecha=fecha,
            estado="MULTIPLES_POLITICAS",
            candidatos=candidatos,
        )

    return ResolucionPolitica(fecha=fecha, estado="OK", politica=candidatos[0])


class PoliticaSinResolucionUnica(Exception):
    """
    Se intentó leer/editar "la" política activa vigente pero la
    resolución para la fecha no produjo exactamente una (0 o >1).

    `estado` es "SIN_POLITICA" o "MULTIPLES_POLITICAS" (mismos valores
    que ResolucionPolitica.estado) y `resolucion` conserva el detalle
    para que el llamador (endpoint) arme una respuesta HTTP explícita.
    """

    def __init__(self, resolucion: ResolucionPolitica):
        self.resolucion = resolucion
        self.estado = resolucion.estado
        super().__init__(
            f"No fue posible resolver una única política vigente "
            f"para {resolucion.fecha}: {resolucion.estado}."
        )


def obtener_politica_activa(
    db: Session,
    fecha: date | None = None,
) -> dict[str, Any]:
    """
    Resuelve y retorna la política ACTIVA vigente para `fecha`
    (por defecto hoy). Fuente canónica para Configuración: reutiliza
    la misma resolución que usa el motor de procesamiento (Contrato §5).

    Lanza PoliticaSinResolucionUnica si no hay exactamente una política
    aplicable — nunca elige silenciosamente entre varias ni sustituye
    con valores por defecto.
    """
    resolucion = resolver_politica_vigente(db, fecha or date.today())

    if resolucion.estado != "OK" or resolucion.politica is None:
        raise PoliticaSinResolucionUnica(resolucion)

    return resolucion.politica


def actualizar_politica_activa(
    db: Session,
    payload: PoliticaAsistenciaUpdate,
    fecha: date | None = None,
) -> dict[str, Any]:
    """
    Edita los límites/puntos de la política ACTIVA vigente para `fecha`
    (por defecto hoy).

    Reutiliza obtener_politica_activa para localizar el registro a
    editar: si la resolución no es única (SIN_POLITICA o
    MULTIPLES_POLITICAS), se rechaza con error explícito en vez de
    adivinar cuál política modificar (mismo criterio del Contrato §5
    para el motor de procesamiento).
    """
    politica_actual = obtener_politica_activa(db, fecha)

    campos = {
        campo: getattr(payload, campo)
        for campo in CAMPOS_EDITABLES_POLITICA
    }

    politica_actualizada = actualizar_politica(
        db=db,
        politica_id=politica_actual["id"],
        campos=campos,
    )

    if politica_actualizada is None:
        # No debería ocurrir: obtener_politica_activa ya confirmó
        # que el id existe en la misma transacción de lectura.
        raise ValueError(
            f"No fue posible actualizar la política "
            f"{politica_actual['id']}: ya no existe."
        )

    return politica_actualizada
