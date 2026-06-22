from datetime import date, datetime

from pydantic import BaseModel


class EmpleadoAsistenciaResumen(BaseModel):
    id: int
    codigo_empleado: str
    nombre_completo: str
    correo: str | None = None
    estatus: str


class PeriodoEvaluacionResumen(BaseModel):
    id: int
    codigo: str
    nombre: str
    tipo_periodo: str
    anio: int
    numero_periodo: int
    fecha_inicio: date
    fecha_fin: date
    estatus: str


class ResumenPeriodoEmpleado(BaseModel):
    id: int | None = None
    dias_laborales: int = 0
    dias_completos: int = 0
    dias_tolerancia: int = 0
    retardos_menores: int = 0
    retardos_mayores: int = 0
    faltas: int = 0
    faltas_justificadas: int = 0
    omisiones_entrada: int = 0
    omisiones_salida: int = 0
    dias_con_tiempo_extra: int = 0
    minutos_ordinarios: int = 0
    minutos_extra: int = 0
    minutos_retardo: int = 0
    puntos_brutos: int = 0
    puntos_justificados: int = 0
    puntos_ajuste: int = 0
    puntos_efectivos: int = 0
    justificantes_solicitados: int = 0
    justificantes_aprobados: int = 0
    dias_justificados: int = 0
    descansos_obligatorios_generados: int = 0
    faltas_consecutivas_max: int = 0
    requiere_revision_baja: bool = False
    motivo_revision_baja: str | None = None
    estatus: str | None = None
    fecha_calculo: datetime | None = None
    fecha_cierre: datetime | None = None


class AsistenciaDiariaItem(BaseModel):
    id: int
    fecha: date
    estatus: str
    entrada_programada: datetime | None = None
    salida_programada: datetime | None = None
    primera_entrada: datetime | None = None
    ultima_salida: datetime | None = None
    minutos_retardo: int = 0
    minutos_ordinarios: int = 0
    minutos_extra: int = 0
    puntos_generados: int = 0
    procesada: bool = False
    requiere_revision: bool = False
    observaciones: str | None = None


class IncidenciaItem(BaseModel):
    id: int
    fecha: date
    tipo_codigo: str | None = None
    tipo_nombre: str | None = None
    categoria: str | None = None
    descripcion: str | None = None
    puntos_originales: int = 0
    puntos_justificados: int = 0
    puntos_efectivos: int = 0
    estatus: str
    origen: str
    requiere_revision: bool = False


class MovimientoPuntosItem(BaseModel):
    id: int
    fecha: date
    tipo_movimiento: str
    concepto: str
    puntos: int
    descripcion: str | None = None
    origen: str
    fecha_creacion: datetime


class AsistenciaEmpleadoResumenResponse(BaseModel):
    empleado: EmpleadoAsistenciaResumen
    periodo_actual: PeriodoEvaluacionResumen | None = None
    resumen_periodo: ResumenPeriodoEmpleado | None = None
    asistencias_recientes: list[AsistenciaDiariaItem]
    incidencias_recientes: list[IncidenciaItem]
    movimientos_puntos_recientes: list[MovimientoPuntosItem]


class AsistenciaDiariaListadoItem(BaseModel):
    asistencia_id: int
    fecha: date

    empleado_id: int
    codigo_empleado: str
    nombre_completo: str
    correo: str | None = None
    empleado_estatus: str

    unidad_organizacional_id: int | None = None
    unidad_codigo: str | None = None
    unidad_nombre: str | None = None

    puesto_id: int | None = None
    puesto_codigo: str | None = None
    puesto_nombre: str | None = None

    horario_id: int | None = None
    horario_codigo: str | None = None
    horario_nombre: str | None = None

    entrada_programada: datetime | None = None
    salida_programada: datetime | None = None
    primera_entrada: datetime | None = None
    ultima_salida: datetime | None = None

    minutos_retardo: int = 0
    minutos_ordinarios: int = 0
    minutos_extra: int = 0

    estatus: str
    puntos_generados: int = 0
    procesada: bool = False
    requiere_revision: bool = False
    observaciones: str | None = None

    total_incidencias: int = 0
    puntos_efectivos_incidencias: int = 0


class AsistenciaDiariaListadoResponse(BaseModel):
    total: int
    fecha: date | None = None
    limit: int
    offset: int
    items: list[AsistenciaDiariaListadoItem]