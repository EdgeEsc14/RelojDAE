import { ROLES } from "./roles";

/**
 * DataScope — Alcance de datos.
 *
 * Define QUÉ DATOS puede ver el usuario dentro de un módulo.
 * Estos valores corresponden exactamente a los reconocidos por
 * el backend en seguridad.permisos_rol.alcance_datos.
 */
export const DATA_SCOPES = Object.freeze({
  TOTAL: "TOTAL",
  AREA: "AREA",
  PROPIO: "PROPIO",
  NINGUNO: "NINGUNO",
});

/**
 * Mantener ACCESS_LEVELS como alias de DATA_SCOPES para
 * compatibilidad temporal con componentes que aún lo usen.
 *
 * @deprecated Usar DATA_SCOPES directamente.
 */
export const ACCESS_LEVELS = DATA_SCOPES;

/**
 * Identificadores oficiales de los módulos.
 *
 * Estos códigos deben corresponder con seguridad.modulos.codigo
 * en PostgreSQL. Cuando un módulo frontend no tiene equivalente
 * exacto en la DB, se documenta el mapeo.
 *
 * Mapeos:
 *   USUARIOS_SISTEMA → backend usa código "SEGURIDAD"
 */
export const MODULES = Object.freeze({
  DASHBOARD: "DASHBOARD",
  EMPLEADOS: "EMPLEADOS",
  ASISTENCIA: "ASISTENCIA",
  CHECADAS_CRUDAS: "CHECADAS_CRUDAS",
  INCIDENCIAS: "INCIDENCIAS",
  REPORTES: "REPORTES",
  DISPOSITIVOS: "DISPOSITIVOS",
  HORARIOS: "HORARIOS",
  USUARIOS_SISTEMA: "SEGURIDAD",
  AUDITORIA: "AUDITORIA",
  CONFIGURACION: "CONFIGURACION",
});

/**
 * Estructura de permisos por módulo.
 *
 * Cada entrada define:
 *   dataScope  — alcance de datos (TOTAL/AREA/PROPIO/NINGUNO)
 *   canRead    — puede consultar
 *   canCreate  — puede crear
 *   canEdit    — puede editar
 *   canDelete  — puede eliminar
 *   canApprove — puede aprobar
 *   canExport  — puede exportar
 *
 * Esta matriz refleja el seed de la migración 016 + 062.
 * La fuente de verdad es PostgreSQL; esta copia local se usa
 * únicamente para decisiones de UI (menú, botones, navegación).
 */

function perm(
  dataScope,
  {
    canRead = false,
    canCreate = false,
    canEdit = false,
    canDelete = false,
    canApprove = false,
    canExport = false,
  } = {},
) {
  return Object.freeze({
    dataScope,
    canRead,
    canCreate,
    canEdit,
    canDelete,
    canApprove,
    canExport,
  });
}

const TOTAL_ALL = perm(DATA_SCOPES.TOTAL, {
  canRead: true,
  canCreate: true,
  canEdit: true,
  canDelete: true,
  canApprove: true,
  canExport: true,
});

const NINGUNO = perm(DATA_SCOPES.NINGUNO);

export const ROLE_PERMISSIONS = Object.freeze({
  [ROLES.SUPER_ADMIN]: {
    [MODULES.DASHBOARD]: TOTAL_ALL,
    [MODULES.EMPLEADOS]: TOTAL_ALL,
    [MODULES.ASISTENCIA]: TOTAL_ALL,
    [MODULES.CHECADAS_CRUDAS]: TOTAL_ALL,
    [MODULES.INCIDENCIAS]: TOTAL_ALL,
    [MODULES.REPORTES]: TOTAL_ALL,
    [MODULES.DISPOSITIVOS]: TOTAL_ALL,
    [MODULES.HORARIOS]: TOTAL_ALL,
    [MODULES.USUARIOS_SISTEMA]: TOTAL_ALL,
    [MODULES.AUDITORIA]: TOTAL_ALL,
    [MODULES.CONFIGURACION]: TOTAL_ALL,
  },

  [ROLES.RH_ADMIN]: {
    [MODULES.DASHBOARD]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.EMPLEADOS]: perm(DATA_SCOPES.TOTAL, { canRead: true, canCreate: true, canEdit: true, canExport: true }),
    [MODULES.ASISTENCIA]: perm(DATA_SCOPES.TOTAL, { canRead: true, canCreate: true, canEdit: true, canApprove: true, canExport: true }),
    [MODULES.CHECADAS_CRUDAS]: perm(DATA_SCOPES.TOTAL, { canRead: true, canCreate: true, canEdit: true, canExport: true }),
    [MODULES.INCIDENCIAS]: perm(DATA_SCOPES.TOTAL, { canRead: true, canCreate: true, canEdit: true, canApprove: true, canExport: true }),
    [MODULES.REPORTES]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.DISPOSITIVOS]: perm(DATA_SCOPES.TOTAL, { canRead: true }),
    [MODULES.HORARIOS]: perm(DATA_SCOPES.TOTAL, { canRead: true, canCreate: true, canEdit: true, canExport: true }),
    [MODULES.USUARIOS_SISTEMA]: NINGUNO,
    [MODULES.AUDITORIA]: NINGUNO,
    [MODULES.CONFIGURACION]: perm(DATA_SCOPES.TOTAL, { canRead: true }),
  },

  [ROLES.SUPERVISOR]: {
    [MODULES.DASHBOARD]: perm(DATA_SCOPES.AREA, { canRead: true, canExport: true }),
    [MODULES.EMPLEADOS]: perm(DATA_SCOPES.AREA, { canRead: true, canExport: true }),
    [MODULES.ASISTENCIA]: perm(DATA_SCOPES.AREA, { canRead: true, canExport: true }),
    [MODULES.CHECADAS_CRUDAS]: NINGUNO,
    [MODULES.INCIDENCIAS]: perm(DATA_SCOPES.AREA, { canRead: true, canExport: true }),
    [MODULES.REPORTES]: perm(DATA_SCOPES.AREA, { canRead: true, canExport: true }),
    [MODULES.DISPOSITIVOS]: NINGUNO,
    [MODULES.HORARIOS]: NINGUNO,
    [MODULES.USUARIOS_SISTEMA]: NINGUNO,
    [MODULES.AUDITORIA]: NINGUNO,
    [MODULES.CONFIGURACION]: NINGUNO,
  },

  [ROLES.EMPLEADO]: {
    [MODULES.DASHBOARD]: perm(DATA_SCOPES.PROPIO, { canRead: true }),
    [MODULES.EMPLEADOS]: perm(DATA_SCOPES.PROPIO, { canRead: true }),
    [MODULES.ASISTENCIA]: perm(DATA_SCOPES.PROPIO, { canRead: true }),
    [MODULES.CHECADAS_CRUDAS]: NINGUNO,
    [MODULES.INCIDENCIAS]: perm(DATA_SCOPES.PROPIO, { canRead: true }),
    [MODULES.REPORTES]: perm(DATA_SCOPES.PROPIO, { canRead: true, canExport: true }),
    [MODULES.DISPOSITIVOS]: NINGUNO,
    [MODULES.HORARIOS]: NINGUNO,
    [MODULES.USUARIOS_SISTEMA]: NINGUNO,
    [MODULES.AUDITORIA]: NINGUNO,
    [MODULES.CONFIGURACION]: NINGUNO,
  },

  [ROLES.AUDITOR]: {
    [MODULES.DASHBOARD]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.EMPLEADOS]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.ASISTENCIA]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.CHECADAS_CRUDAS]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.INCIDENCIAS]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.REPORTES]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.DISPOSITIVOS]: perm(DATA_SCOPES.TOTAL, { canRead: true }),
    [MODULES.HORARIOS]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.USUARIOS_SISTEMA]: perm(DATA_SCOPES.TOTAL, { canRead: true }),
    [MODULES.AUDITORIA]: perm(DATA_SCOPES.TOTAL, { canRead: true, canExport: true }),
    [MODULES.CONFIGURACION]: perm(DATA_SCOPES.TOTAL, { canRead: true }),
  },
});
