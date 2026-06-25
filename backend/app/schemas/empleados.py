from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class EmpleadoResumen(BaseModel):
    id: int
    codigo_empleado: str
    nombres: str | None = None
    apellido_paterno: str | None = None
    apellido_materno: str | None = None
    apellidos: str | None = None
    nombre_completo: str | None = None
    correo: str | None = None
    estatus: str | None = None

    # Organización
    unidad_organizacional_id: int | None = None
    unidad_organizacional: str | None = None
    unidad_organizacional_codigo: str | None = None
    unidad_organizacional_tipo: str | None = None

    area_principal_id: int | None = None
    area_principal: str | None = None
    area_principal_codigo: str | None = None

    # Puesto
    puesto_id: int | None = None
    puesto: str | None = None
    puesto_codigo: str | None = None
    puesto_nivel_jerarquico: int | None = None

    # Supervisor
    supervisor_id: int | None = None
    supervisor_codigo_empleado: str | None = None
    supervisor: str | None = None

    # Horario actual
    horario_id: int | None = None
    horario: str | None = None
    horario_codigo: str | None = None
    turno: str | None = None
    turno_codigo: str | None = None
    horario_fecha_inicio: date | None = None
    horario_fecha_fin: date | None = None

    # ZKTeco / dispositivo
    empleado_dispositivo_id: int | None = None
    dispositivo_id: int | None = None
    dispositivo_codigo: str | None = None
    dispositivo: str | None = None
    zk_uid: int | None = None
    zk_user_id: str | None = None
    nombre_en_dispositivo: str | None = None
    dispositivo_sincronizado: bool | None = None

class EmpleadosListadoResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[EmpleadoResumen]


class UnidadOrganizacionalResumen(BaseModel):
    id: int | None = None
    codigo: str | None = None
    nombre: str | None = None
    clave_organica: str | None = None
    tipo_unidad_codigo: str | None = None
    tipo_unidad_nombre: str | None = None


class PuestoResumen(BaseModel):
    id: int | None = None
    codigo: str | None = None
    nombre: str | None = None
    nivel_jerarquico: int | None = None


class SupervisorResumen(BaseModel):
    id: int | None = None
    codigo_empleado: str | None = None
    nombre_completo: str | None = None
    correo: str | None = None


class UsuarioSistemaResumen(BaseModel):
    id: int | None = None
    nombre_usuario: str | None = None
    correo_electronico: str | None = None
    requiere_cambio_password: bool | None = None
    ultimo_acceso: datetime | None = None
    activo: bool | None = None
    rol_id: int | None = None
    rol_codigo: str | None = None
    rol_nombre: str | None = None


class HorarioActualResumen(BaseModel):
    asignacion_id: int | None = None
    horario_id: int | None = None
    codigo: str | None = None
    nombre: str | None = None
    descripcion: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    estatus: str | None = None
    tipo_turno_id: int | None = None
    tipo_turno_codigo: str | None = None
    tipo_turno_nombre: str | None = None


class DispositivoEmpleadoResumen(BaseModel):
    empleado_dispositivo_id: int | None = None
    dispositivo_id: int | None = None
    codigo: str | None = None
    nombre: str | None = None
    ip: str | None = None
    puerto: int | None = None
    ubicacion: str | None = None
    modelo: str | None = None
    firmware: str | None = None
    zk_uid: int | None = None
    zk_user_id: str | None = None
    nombre_en_dispositivo: str | None = None
    privilegio: int | None = None
    grupo: str | None = None
    tarjeta: str | None = None
    sincronizado: bool | None = None
    fecha_ultima_sincronizacion: datetime | None = None
    activo: bool | None = None


class EmpleadoPerfilResponse(BaseModel):
    empleado: EmpleadoResumen
    unidad_organizacional: UnidadOrganizacionalResumen | None = None
    puesto: PuestoResumen | None = None
    supervisor: SupervisorResumen | None = None
    usuario_sistema: UsuarioSistemaResumen | None = None
    horario_actual: HorarioActualResumen | None = None
    dispositivo: DispositivoEmpleadoResumen | None = None