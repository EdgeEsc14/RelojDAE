from datetime import date

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