from datetime import date
import re

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


RFC_PATTERN = re.compile(
    r"^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$"
)

CURP_PATTERN = re.compile(
    r"^[A-Z0-9]{18}$"
)


class AltaIntegralEmpleadoRequest(BaseModel):
    nombres: str = Field(
        min_length=1,
        max_length=120,
    )

    apellido_paterno: str = Field(
        min_length=1,
        max_length=80,
    )

    apellido_materno: str | None = Field(
        default=None,
        max_length=80,
    )

    rfc: str = Field(
        min_length=12,
        max_length=13,
    )

    curp: str | None = Field(
        default=None,
        max_length=18,
    )

    telefono: str | None = Field(
        default=None,
        max_length=30,
    )

    correo_personal: str = Field(
        min_length=3,
        max_length=254,
    )

    tipo_contratacion_id: int = Field(
        ge=1,
    )

    fecha_ingreso: date

    puesto_id: int = Field(
        ge=1,
    )

    unidad_organizacional_id: int = Field(
        ge=1,
    )

    supervisor_id: int | None = Field(
        default=None,
        ge=1,
    )

    horario_id: int = Field(
        ge=1,
    )

    observaciones: str | None = Field(
        default=None,
        max_length=2000,
    )

    registrar_en_reloj: bool = True

    todos_dispositivos_activos: bool = True

    dispositivo_ids: list[int] = Field(
        default_factory=list,
    )

    zk_user_id: str | None = Field(
        default=None,
        max_length=50,
        description="ZK User ID explícito. Si no se envía, se auto-genera.",
    )

    @field_validator(
        "nombres",
        "apellido_paterno",
        "apellido_materno",
        mode="before",
    )
    @classmethod
    def normalizar_nombre(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = " ".join(
            str(value).strip().split()
        )

        return normalized.upper() or None

    @field_validator("rfc", mode="before")
    @classmethod
    def normalizar_rfc(
        cls,
        value: str,
    ) -> str:
        normalized = str(value).strip().upper()

        if not RFC_PATTERN.fullmatch(normalized):
            raise ValueError(
                "El RFC no tiene un formato válido."
            )

        return normalized

    @field_validator("curp", mode="before")
    @classmethod
    def normalizar_curp(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip().upper()

        if not normalized:
            return None

        if not CURP_PATTERN.fullmatch(normalized):
            raise ValueError(
                "La CURP debe contener 18 caracteres "
                "alfanuméricos."
            )

        return normalized

    @field_validator(
        "telefono",
        "observaciones",
        mode="before",
    )
    @classmethod
    def limpiar_texto_opcional(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None

    @field_validator(
        "correo_personal",
        mode="before",
    )
    @classmethod
    def normalizar_correo(
        cls,
        value: str,
    ) -> str:
        normalized = str(value).strip().lower()

        if (
            "@" not in normalized
            or normalized.startswith("@")
            or normalized.endswith("@")
        ):
            raise ValueError(
                "El correo personal no es válido."
            )

        return normalized

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

    @model_validator(mode="after")
    def validar_seleccion_dispositivos(
        self,
    ) -> "AltaIntegralEmpleadoRequest":
        if (
            self.registrar_en_reloj
            and not self.todos_dispositivos_activos
            and not self.dispositivo_ids
        ):
            raise ValueError(
                "Selecciona al menos un dispositivo "
                "o activa todos_dispositivos_activos."
            )

        return self


class AltaIntegralUsuarioResponse(BaseModel):
    usuario_id: int
    nombre_usuario: str
    correo_electronico: str
    rol_codigo: str
    requiere_cambio_password: bool
    password_temporal: str


class AltaIntegralHorarioResponse(BaseModel):
    asignacion_id: int
    horario_id: int
    horario_codigo: str
    horario_nombre: str
    fecha_inicio: date


class AltaIntegralDispositivoResponse(BaseModel):
    empleado_dispositivo_id: int
    dispositivo_id: int
    dispositivo_codigo: str
    dispositivo_nombre: str
    zk_user_id: str
    estado_sincronizacion: str


class AltaIntegralEmpleadoResponse(BaseModel):
    empleado_id: int
    codigo_empleado: str
    nombre_completo: str
    rfc: str
    curp: str | None = None
    correo_personal: str
    estatus: str

    usuario_sistema: AltaIntegralUsuarioResponse
    horario: AltaIntegralHorarioResponse

    sincronizacion_solicitada: bool
    dispositivos: list[
        AltaIntegralDispositivoResponse
    ]
    sincronizacion_resultado: dict | None = None