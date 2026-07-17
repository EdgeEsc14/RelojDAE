from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class SincronizarRelojesRequest(BaseModel):
    dispositivo_ids: list[int] = Field(
        default_factory=list,
        description=(
            "Lista vacía para procesar todos los relojes "
            "asignados al empleado."
        ),
    )

    @field_validator(
        "dispositivo_ids",
        mode="after",
    )
    @classmethod
    def normalizar_dispositivos(
        cls,
        values: list[int],
    ) -> list[int]:
        return sorted(
            {
                int(value)
                for value in values
                if int(value) > 0
            }
        )


class SincronizacionDispositivoResultado(BaseModel):
    empleado_dispositivo_id: int
    dispositivo_id: int
    dispositivo_codigo: str
    dispositivo_nombre: str
    zk_user_id: str
    zk_uid: int | None = None

    estado_anterior: str
    estado_final: str

    exitoso: bool
    creado_en_reloj: bool
    ya_existia_en_reloj: bool
    mensaje: str


class SincronizarRelojesResponse(BaseModel):
    empleado_id: int
    codigo_empleado: str
    nombre_completo: str

    total_dispositivos: int
    exitosos: int
    errores: int

    resultados: list[
        SincronizacionDispositivoResultado
    ]