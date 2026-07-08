from pydantic import BaseModel, Field


class AuthLoginRequest(BaseModel):
    correo: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)


class AuthUserResponse(BaseModel):
    id: int
    correo: str
    nombre_usuario: str | None = None
    rol_id: int | None = None
    rol: str
    rol_codigo: str | None = None
    rol_nombre: str | None = None
    estatus: str
    correo_verificado: bool
    empleado_id: int | None = None
    codigo_empleado: str | None = None
    nombre_empleado: str | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse