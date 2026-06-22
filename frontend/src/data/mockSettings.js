export const mockSystemSettings = {
  institution: {
    name: "Dirección de Administración Escolar",
    shortName: "DAE",
    parentInstitution: "Instituto Politécnico Nacional",
    logoMode: "Institucional",
    reportFooter:
      "Documento generado por el sistema de control de asistencia DAE.",
  },

  attendance: {
    activePeriod: "Mayo 2026",
    periodStart: "01/05/2026",
    periodEnd: "31/05/2026",
    timezone: "America/Mexico_City",
    defaultToleranceMinutes: 10,
    absenceRule: "Sin entrada ni salida en día laborable",
    missingExitRule: "Entrada registrada sin salida asociada",
    extraTimeRule: "Tiempo posterior a salida esperada con autorización",
  },

  pyzk: {
    defaultPort: 4370,
    defaultCommKey: "0",
    connectionTimeout: "10 segundos",
    syncMode: "Manual / Programada",
    duplicatePolicy: "Ignorar duplicados por device_id + user_id + timestamp",
    rawPolicy: "No modificar ni eliminar checadas crudas",
  },

  security: {
    passwordPolicy: "Mínimo 8 caracteres",
    twoFactorAuth: "Opcional",
    sessionTimeout: "30 minutos",
    maxLoginAttempts: 5,
    blockedUserPolicy: "Bloqueo manual por Super Admin",
  },

  exports: {
    pdfEnabled: true,
    excelEnabled: true,
    includeAuditStamp: true,
    includeSignatures: true,
    defaultReportFormat: "PDF",
  },

  backup: {
    frequency: "Diario",
    retention: "90 días",
    lastBackup: "15/05/2026 23:00:00",
    status: "Correcto",
  },
};

export const mockSettingsCards = [
  {
    id: 1,
    title: "Institución",
    description: "Nombre institucional, encabezados, logos y pie de reportes.",
    status: "Configurado",
  },
  {
    id: 2,
    title: "Asistencia",
    description: "Periodo activo, zona horaria, tolerancias y reglas globales.",
    status: "Configurado",
  },
  {
    id: 3,
    title: "pyzk / ZKTeco",
    description: "Puerto, clave de comunicación, timeout y política de sincronización.",
    status: "Configurado",
  },
  {
    id: 4,
    title: "Seguridad",
    description: "Sesiones, contraseñas, 2FA y bloqueo de usuarios.",
    status: "Pendiente",
  },
  {
    id: 5,
    title: "Exportaciones",
    description: "PDF, Excel, firmas, sellos de auditoría y formatos predeterminados.",
    status: "Configurado",
  },
  {
    id: 6,
    title: "Respaldos",
    description: "Frecuencia, retención y último respaldo de base de datos.",
    status: "Correcto",
  },
];

export const mockGlobalRules = [
  {
    id: 1,
    parameter: "Tolerancia general",
    value: "10 minutos",
    module: "Asistencia",
    description: "Margen permitido posterior a la hora de entrada.",
  },
  {
    id: 2,
    parameter: "Política de checadas crudas",
    value: "Inmutable",
    module: "Auditoría",
    description: "Los registros originales no se editan ni eliminan.",
  },
  {
    id: 3,
    parameter: "Duplicados pyzk",
    value: "Ignorar",
    module: "Dispositivos",
    description:
      "Si ya existe una checada con mismo dispositivo, usuario y timestamp, no se inserta de nuevo.",
  },
  {
    id: 4,
    parameter: "Tiempo extra",
    value: "Requiere autorización",
    module: "Incidencias",
    description: "El tiempo extra debe ser aprobado antes de reflejarse como autorizado.",
  },
  {
    id: 5,
    parameter: "Exportación de reportes",
    value: "Registrar en auditoría",
    module: "Reportes",
    description: "Cada PDF o Excel generado debe dejar evidencia en la bitácora.",
  },
];