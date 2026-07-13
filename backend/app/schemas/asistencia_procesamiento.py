from datetime import date

from pydantic import BaseModel


class ProcesarAsistenciaRequest(BaseModel):
    fecha_inicio: date
    fecha_fin: date


class ProcesarAsistenciaResponse(BaseModel):
    fecha_inicio: str
    fecha_fin: str
    registros_encontrados: int
    procesadas: int
    errores: list[dict]