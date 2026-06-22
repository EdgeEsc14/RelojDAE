export const mockAuditLogs = [
  {
    id: 1,
    eventId: "AUD-20260515-0001",
    timestamp: "15/05/2026 08:45:12",
    user: "super.admin",
    role: "Super Admin",
    module: "Dispositivos",
    action: "Sincronización manual",
    entity: "Reloj principal",
    entityId: "DEV-001",
    result: "Correcto",
    ipAddress: "192.168.1.50",
    detail:
      "Se ejecutó sincronización manual mediante pyzk. Registros leídos: 32, insertados: 31, duplicados: 1.",
  },
  {
    id: 2,
    eventId: "AUD-20260515-0002",
    timestamp: "15/05/2026 09:10:44",
    user: "rh.admin",
    role: "RH/Admin",
    module: "Incidencias",
    action: "Aprobación",
    entity: "INC-202605-0006",
    entityId: "INC-0006",
    result: "Correcto",
    ipAddress: "192.168.1.61",
    detail:
      "Se aprobó incidencia de permiso administrativo para MARÍA LÓPEZ RAMÍREZ.",
  },
  {
    id: 3,
    eventId: "AUD-20260515-0003",
    timestamp: "15/05/2026 09:35:02",
    user: "super.admin",
    role: "Super Admin",
    module: "Reportes",
    action: "Exportación PDF",
    entity: "Reporte individual",
    entityId: "REP-202605-0001",
    result: "Correcto",
    ipAddress: "192.168.1.50",
    detail:
      "Se generó reporte individual de asistencia para HIPOLITO BARRETO AYALA.",
  },
  {
    id: 4,
    eventId: "AUD-20260515-0004",
    timestamp: "15/05/2026 10:05:21",
    user: "rh.admin",
    role: "RH/Admin",
    module: "Empleados",
    action: "Actualización",
    entity: "ANA GARCÍA TORRES",
    entityId: "EMP-0004",
    result: "Correcto",
    ipAddress: "192.168.1.61",
    detail:
      "Se actualizó horario asignado del empleado a Administrativo completo.",
  },
  {
    id: 5,
    eventId: "AUD-20260515-0005",
    timestamp: "15/05/2026 10:22:16",
    user: "supervisor.operaciones",
    role: "Supervisor",
    module: "Incidencias",
    action: "Consulta",
    entity: "INC-202605-0003",
    entityId: "INC-0003",
    result: "Correcto",
    ipAddress: "192.168.1.77",
    detail:
      "Se consultó incidencia de retardo correspondiente a JOSÉ HERNÁNDEZ CRUZ.",
  },
  {
    id: 6,
    eventId: "AUD-20260515-0006",
    timestamp: "15/05/2026 11:15:08",
    user: "system",
    role: "Servicio automático",
    module: "Dispositivos",
    action: "Sincronización programada",
    entity: "Reloj acceso norte",
    entityId: "DEV-002",
    result: "Advertencia",
    ipAddress: "Servidor local",
    detail:
      "El dispositivo respondió, pero no se encontraron registros nuevos en la sincronización programada.",
  },
  {
    id: 7,
    eventId: "AUD-20260515-0007",
    timestamp: "15/05/2026 11:32:50",
    user: "ana.garcia",
    role: "Empleado",
    module: "Autenticación",
    action: "Inicio de sesión",
    entity: "Cuenta de usuario",
    entityId: "USR-0005",
    result: "Bloqueado",
    ipAddress: "192.168.1.83",
    detail:
      "Intento de inicio de sesión rechazado porque el usuario se encuentra bloqueado.",
  },
  {
    id: 8,
    eventId: "AUD-20260515-0008",
    timestamp: "15/05/2026 12:04:11",
    user: "auditor.consulta",
    role: "Auditor",
    module: "Checadas crudas",
    action: "Consulta",
    entity: "attendance_raw",
    entityId: "RAW",
    result: "Correcto",
    ipAddress: "192.168.1.92",
    detail:
      "Se consultó vista de checadas crudas en modo solo lectura.",
  },
];

export const mockAuditSummary = [
  {
    id: 1,
    label: "Eventos correctos",
    value: 6,
    detail: "Operaciones finalizadas sin error",
  },
  {
    id: 2,
    label: "Advertencias",
    value: 1,
    detail: "Eventos que requieren revisión",
  },
  {
    id: 3,
    label: "Bloqueados",
    value: 1,
    detail: "Accesos o acciones rechazadas",
  },
  {
    id: 4,
    label: "Eventos críticos",
    value: 3,
    detail: "Acciones sensibles del sistema",
  },
];

export const mockCriticalEvents = [
  {
    id: 1,
    title: "Sincronización manual de reloj",
    module: "Dispositivos",
    risk: "Medio",
    description:
      "La sincronización manual modifica registros en attendance_raw mediante inserción de nuevos eventos.",
  },
  {
    id: 2,
    title: "Aprobación de incidencia",
    module: "Incidencias",
    risk: "Alto",
    description:
      "La aprobación modifica el tratamiento administrativo del día evaluado.",
  },
  {
    id: 3,
    title: "Cambio de horario de empleado",
    module: "Empleados / Horarios",
    risk: "Alto",
    description:
      "El cambio de horario puede alterar cálculo de retardos, faltas y tiempo extra.",
  },
  {
    id: 4,
    title: "Exportación de reportes",
    module: "Reportes",
    risk: "Medio",
    description:
      "La exportación genera documentos que pueden usarse para revisión administrativa o nómina.",
  },
];