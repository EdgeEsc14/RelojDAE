from datetime import date, datetime

from pydantic import BaseModel, Field


class AsignarHorarioEmpleadoRequest(BaseModel):
    horario_id: int
    fecha_inicio: date
    fecha_fin: date | None = None
    motivo: str | None = Field(default=None, max_length=300)
    cerrar_asignaciones_activas: bool = True


class AsignacionHorarioEmpleadoResponse(BaseModel):
    id: int
    empleado_id: int
    codigo_empleado: str
    horario_id: int
    horario_codigo: str
    horario_nombre: str
    tipo_turno_codigo: str | None = None
    tipo_turno_nombre: str | None = None
    fecha_inicio: date
    fecha_fin: date | None = None
    estatus: str
    motivo: str | None = None


class AsignarDispositivoEmpleadoRequest(BaseModel):
    dispositivo_id: int
    zk_user_id: str = Field(min_length=1, max_length=50)
    zk_uid: int | None = None
    nombre_en_dispositivo: str | None = Field(default=None, max_length=150)
    privilegio: int | None = None
    grupo: str | None = Field(default=None, max_length=50)
    tarjeta: str | None = Field(default=None, max_length=80)
    activo: bool = True


class DispositivoEmpleadoResponse(BaseModel):
    id: int
    empleado_id: int
    codigo_empleado: str
    dispositivo_id: int
    dispositivo_codigo: str
    dispositivo_nombre: str
    dispositivo_ip: str
    dispositivo_puerto: int
    zk_uid: int | None = None
    zk_user_id: str
    nombre_en_dispositivo: str | None = None
    privilegio: int | None = None
    grupo: str | None = None
    tarjeta: str | None = None
    sincronizado: bool
    fecha_ultima_sincronizacion: datetime | None = None
    activo: bool


class CrearUsuarioSistemaEmpleadoRequest(BaseModel):
    rol_id: int
    correo_electronico: str | None = Field(default=None, max_length=150)
    nombre_usuario: str | None = Field(default=None, max_length=80)
    password_temporal: str = Field(min_length=8, max_length=200)
    requiere_cambio_password: bool = True
    activo: bool = True


class UsuarioSistemaEmpleadoResponse(BaseModel):
    id: int
    empleado_id: int
    codigo_empleado: str
    nombre_empleado: str
    rol_id: int
    rol_codigo: str
    rol_nombre: str
    correo_electronico: str
    nombre_usuario: str | None = None
    requiere_cambio_password: bool
    ultimo_acceso: datetime | None = None
    activo: bool