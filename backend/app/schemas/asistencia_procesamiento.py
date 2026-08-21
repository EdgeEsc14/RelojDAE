from datetime import date
from typing import Any

from pydantic import BaseModel, model_validator


class ProcesarAsistenciaRequest(BaseModel):
    fecha_inicio: date
    fecha_fin: date

    @model_validator(mode="after")
    def validar_periodo(
        self,
    ) -> "ProcesarAsistenciaRequest":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError(
                "fecha_fin no puede ser anterior "
                "a fecha_inicio."
            )

        dias = (
            self.fecha_fin - self.fecha_inicio
        ).days + 1

        if dias > 31:
            raise ValueError(
                "El procesamiento permite un máximo "
                "de 31 días por solicitud."
            )

        return self


class ProcesarAsistenciaResponse(BaseModel):
    fecha_inicio: str
    fecha_fin: str
    registros_encontrados: int
    procesadas: int
    errores: list[dict]
    # La acumulación de puntos corre después de procesar asistencia y
    # nunca debe convertir un procesamiento exitoso en un 500: si falla
    # (p. ej. periodo de evaluación sin resolver), se reporta aquí en
    # vez de propagar la excepción (ver post_procesar_asistencia).
    acumulacion_puntos: dict[str, Any] | None = None