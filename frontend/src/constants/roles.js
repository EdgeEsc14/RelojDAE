/**
 * Roles disponibles dentro del sistema.
 *
 * Usamos valores estandarizados para evitar diferencias como:
 * "Super Admin", "super-admin", "SuperAdmin", etc.
 */
export const ROLES = Object.freeze({
  SUPER_ADMIN: "super_admin",
  RH_ADMIN: "rh_admin",
  SUPERVISOR: "supervisor",
  EMPLEADO: "empleado",
  AUDITOR: "auditor",
});

/**
 * Nombres que se mostrarán en la interfaz.
 */
export const ROLE_LABELS = Object.freeze({
  [ROLES.SUPER_ADMIN]: "Super Admin",
  [ROLES.RH_ADMIN]: "RH / Admin",
  [ROLES.SUPERVISOR]: "Supervisor",
  [ROLES.EMPLEADO]: "Empleado",
  [ROLES.AUDITOR]: "Auditor",
});

/**
 * Lista preparada para utilizarse en componentes select.
 *
 * Resultado:
 * [
 *   { value: "super_admin", label: "Super Admin" },
 *   { value: "rh_admin", label: "RH / Admin" },
 *   ...
 * ]
 */
export const ROLE_OPTIONS = Object.freeze(
  Object.entries(ROLE_LABELS).map(([value, label]) => ({
    value,
    label,
  }))
);

/**
 * Obtiene el nombre visible de un rol.
 *
 * @param {string} role
 * @returns {string}
 */
export function getRoleLabel(role) {
  return ROLE_LABELS[role] ?? "Rol desconocido";
}

/**
 * Valida si un valor corresponde a un rol oficial.
 *
 * @param {string} role
 * @returns {boolean}
 */
export function isValidRole(role) {
  return Object.values(ROLES).includes(role);
}