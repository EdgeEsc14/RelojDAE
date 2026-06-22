from datetime import date

from pydantic import BaseModel, Field


class SiguienteCodigoEmpleadoResponse(BaseModel):
    prefijo: str
    ultimo_numero: int
    siguiente_numero: int
    codigo_empleado: str


class EmpleadoCreate(BaseModel):
    codigo_empleado: str | None = Field(
        default=None,
        max_length=30,
        description="Código manual. Si no se envía, se genera automáticamente.",
    )
    generar_codigo: bool = True

    nombres: str = Field(min_length=1, max_length=120)
    apellido_paterno: str = Field(min_length=1, max_length=80)
    apellido_materno: str | None = Field(default=None, max_length=80)

    rfc: str | None = Field(default=None, max_length=13)
    correo: str | None = Field(default=None, max_length=320)

    unidad_organizacional_id: int
    puesto_id: int
    supervisor_id: int | None = None

    fecha_ingreso: date | None = None
    estatus: str = Field(default="ACTIVO", max_length=20)


class EmpleadoUpdate(BaseModel):
    nombres: str | None = Field(default=None, min_length=1, max_length=120)
    apellido_paterno: str | None = Field(default=None, min_length=1, max_length=80)
    apellido_materno: str | None = Field(default=None, max_length=80)

    rfc: str | None = Field(default=None, max_length=13)
    correo: str | None = Field(default=None, max_length=320)

    unidad_organizacional_id: int | None = None
    puesto_id: int | None = None
    supervisor_id: int | None = None

    fecha_ingreso: date | None = None
    fecha_baja: date | None = None
    estatus: str | None = Field(default=None, max_length=20)


class EmpleadoEstatusUpdate(BaseModel):
    estatus: str = Field(max_length=20)