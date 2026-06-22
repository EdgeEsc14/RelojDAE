import {
  ACCESS_LEVELS,
  ROLE_PERMISSIONS,
} from "../constants/permissions";

/**
 * Obtiene todos los permisos de un rol.
 */
export function getRolePermissions(role) {
  return ROLE_PERMISSIONS[role] ?? {};
}

/**
 * Obtiene el nivel de acceso de un rol para un módulo.
 */
export function getModuleAccess(role, module) {
  const rolePermissions = getRolePermissions(role);

  return rolePermissions[module] ?? ACCESS_LEVELS.NINGUNO;
}

/**
 * Indica si el rol puede acceder al módulo.
 *
 * Cualquier nivel diferente de "ninguno" permite que
 * el módulo aparezca en el menú.
 */
export function canAccessModule(role, module) {
  return getModuleAccess(role, module) !== ACCESS_LEVELS.NINGUNO;
}

/**
 * Indica si el rol solamente puede consultar el módulo.
 */
export function hasReadOnlyAccess(role, module) {
  return getModuleAccess(role, module) === ACCESS_LEVELS.LECTURA;
}

/**
 * Indica si el acceso está limitado al área del usuario.
 */
export function hasAreaAccess(role, module) {
  return getModuleAccess(role, module) === ACCESS_LEVELS.AREA;
}

/**
 * Indica si el usuario solamente puede consultar
 * su propia información.
 */
export function hasOwnAccess(role, module) {
  return getModuleAccess(role, module) === ACCESS_LEVELS.PROPIO;
}