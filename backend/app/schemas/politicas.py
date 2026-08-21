"""
Schemas para el módulo de Política de Asistencia (asistencia.politicas_asistencia).

Los límites de tiempo se transportan siempre en segundos, tal como los
exige el Contrato del Núcleo de Asistencia §5 (precisión de frontera,
p. ej. 08:10:59). El frontend es responsable de presentarlos en un
formato entendible (minutos/segundos) sin perder esa precisión al
convertir de vuelta.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class PoliticaAsistenciaResponse(BaseModel):
    id: int
    codigo: str
    version: int
    nombre: str
    descripcion: str | None = None
    tipo_periodo: str

    limite_tolerancia_segundos: int
    limite_retardo_menor_segundos: int
    limite_retardo_mayor_segundos: int

    puntos_retardo_menor: int
    puntos_retardo_mayor: int
    puntos_para_descanso: int

    max_dias_justificables_periodo: int
    max_puntos_descontables_por_dia: int

    descansos_para_revision_baja: int
    faltas_consecutivas_revision_baja: int

    vigencia_desde: date
    vigencia_hasta: date | None = None
    activo: bool

    fecha_creacion: datetime
    fecha_modificacion: datetime


class PoliticaAsistenciaUpdate(BaseModel):
    """
    Campos editables de la política ACTIVA vigente.

    No incluye codigo/version/vigencia/activo: modificar esos campos
    puede crear solapamientos entre políticas y queda fuera de este
    endpoint (requiere una herramienta de gestión de vigencias aparte).
    """

    limite_tolerancia_segundos: int = Field(..., ge=0)
    limite_retardo_menor_segundos: int = Field(..., ge=0)
    limite_retardo_mayor_segundos: int = Field(..., ge=0)

    puntos_retardo_menor: int = Field(..., ge=0)
    puntos_retardo_mayor: int = Field(..., ge=0)
    puntos_para_descanso: int = Field(..., gt=0)

    descansos_para_revision_baja: int = Field(..., gt=0)
    faltas_consecutivas_revision_baja: int = Field(..., gt=0)

    @model_validator(mode="after")
    def validar_coherencia(self) -> "PoliticaAsistenciaUpdate":
        # Refleja ck_politicas_orden_limites (migración 022): los tres
        # límites deben ser estrictamente crecientes.
        if not (
            self.limite_tolerancia_segundos
            < self.limite_retardo_menor_segundos
            < self.limite_retardo_mayor_segundos
        ):
            raise ValueError(
                "Los límites deben ser crecientes: "
                "limite_tolerancia_segundos < limite_retardo_menor_segundos "
                "< limite_retardo_mayor_segundos."
            )

        # Refleja ck_politicas_puntos.
        if self.puntos_retardo_mayor < self.puntos_retardo_menor:
            raise ValueError(
                "puntos_retardo_mayor no puede ser menor que "
                "puntos_retardo_menor."
            )

        return self
