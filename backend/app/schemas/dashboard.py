from pydantic import BaseModel


class DashboardEmpleadosResumen(BaseModel):
    total: int
    activos: int
    inactivos: int
    con_zk: int
    sin_zk: int


class DashboardMarcacionesResumen(BaseModel):
    total: int
    hoy: int
    ultima_fecha_hora: str | None = None


class DashboardDispositivosResumen(BaseModel):
    total: int
    activos: int
    inactivos: int


class DashboardUltimaMarcacion(BaseModel):
    id: int
    zk_user_id: str | None = None
    codigo_empleado: str | None = None
    empleado_nombre: str | None = None
    fecha_hora: str | None = None
    fecha: str | None = None
    hora: str | None = None
    punch: int | None = None
    punch_label: str | None = None
    status: int | None = None
    status_label: str | None = None
    dispositivo_origen: str | None = None
    dispositivo_ip: str | None = None

class DashboardTopEmpleadoFaltas(BaseModel):
    empleado_id: int
    codigo_empleado: str | None = None
    empleado_nombre: str | None = None
    faltas: int
    requieren_revision: int
    dias_procesados: int


class DashboardTopEmpleadoRetardos(BaseModel):
    empleado_id: int
    codigo_empleado: str | None = None
    empleado_nombre: str | None = None
    retardos_menores: int
    retardos_mayores: int
    total_retardos: int
    puntos_generados: int
    dias_procesados: int
class DashboardResumenResponse(BaseModel):
    empleados: DashboardEmpleadosResumen
    marcaciones: DashboardMarcacionesResumen
    dispositivos: DashboardDispositivosResumen
    ultimas_marcaciones: list[DashboardUltimaMarcacion]
    asistencia_hoy: DashboardAsistenciaHoyResumen
    alertas: DashboardAlertasResumen
    asistencia_ultimos_dias: list[DashboardAsistenciaDiaSerie]
    top_empleados_faltas: list[DashboardTopEmpleadoFaltas]
    top_empleados_retardos: list[DashboardTopEmpleadoRetardos]
    departamentos_incidencias: list[DashboardDepartamentoIncidencias]

class DashboardAsistenciaHoyResumen(BaseModel):
    total: int
    completos: int
    retardos_menores: int
    retardos_mayores: int
    faltas: int
    requieren_revision: int
    puntos_generados: int

class DashboardAlertasResumen(BaseModel):
    empleados_sin_zk: int
    empleados_sin_horario: int
    marcaciones_sin_empleado_hoy: int
    asistencias_revision_hoy: int
    faltas_hoy: int
    retardos_mayores_hoy: int

class DashboardAsistenciaDiaSerie(BaseModel):
    fecha: str
    total: int
    completos: int
    retardos: int
    faltas: int
    requieren_revision: int

class DashboardDepartamentoIncidencias(BaseModel):
    unidad_organizacional_id: int | None = None
    departamento_nombre: str | None = None
    faltas: int
    retardos: int
    retardos_menores: int
    retardos_mayores: int
    omisiones: int
    requieren_revision: int
    total_incidencias: int
    empleados_involucrados: int