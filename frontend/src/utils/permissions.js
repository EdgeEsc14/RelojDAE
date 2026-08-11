import {
  DATA_SCOPES,
  ROLE_PERMISSIONS,
} from "../constants/permissions";

/**
 * Obtiene el objeto completo de permisos de un rol para un módulo.
 *
 * Retorna: { dataScope, canRead, canCreate, canEdit, canDelete, canApprove, canExport }
 */
export function getModulePermissions(role, module) {
  const rolePermissions = ROLE_PERMISSIONS[role];

  if (!rolePermissions) {
    return {
      dataScope: DATA_SCOPES.NINGUNO,
      canRead: false,
      canCreate: false,
      canEdit: false,
      canDelete: false,
      canApprove: false,
      canExport: false,
    };
  }

  return rolePermissions[module] ?? {
    dataScope: DATA_SCOPES.NINGUNO,
    canRead: false,
    canCreate: false,
    canEdit: false,
    canDelete: false,
    canApprove: false,
    canExport: false,
  };
}

/**
 * Obtiene solo el DataScope de un rol para un módulo.
 *
 * @deprecated Preferir getModulePermissions() para acceder al modelo completo.
 */
export function getModuleAccess(role, module) {
  return getModulePermissions(role, module).dataScope;
}

/**
 * Indica si el rol puede acceder al módulo (aparece en menú).
 *
 * Un módulo es accesible si su dataScope es diferente de NINGUNO.
 */
export function canAccessModule(role, module) {
  return getModulePermissions(role, module).dataScope !== DATA_SCOPES.NINGUNO;
}

/**
 * Indica si el rol puede consultar datos del módulo.
 */
export function canRead(role, module) {
  return getModulePermissions(role, module).canRead;
}

/**
 * Indica si el rol puede crear registros en el módulo.
 */
export function canCreate(role, module) {
  return getModulePermissions(role, module).canCreate;
}

/**
 * Indica si el rol puede editar registros en el módulo.
 */
export function canEdit(role, module) {
  return getModulePermissions(role, module).canEdit;
}

/**
 * Indica si el rol puede eliminar registros en el módulo.
 */
export function canDelete(role, module) {
  return getModulePermissions(role, module).canDelete;
}

/**
 * Indica si el rol puede exportar datos del módulo.
 */
export function canExport(role, module) {
  return getModulePermissions(role, module).canExport;
}

/**
 * Indica si el rol solamente puede consultar (sin crear/editar/eliminar).
 *
 * Útil para ocultar botones de acción en la UI.
 */
export function isReadOnly(role, module) {
  const perms = getModulePermissions(role, module);

  return (
    perms.canRead &&
    !perms.canCreate &&
    !perms.canEdit &&
    !perms.canDelete
  );
}

/**
 * Indica si el acceso está limitado al área del usuario.
 */
export function hasAreaAccess(role, module) {
  return getModulePermissions(role, module).dataScope === DATA_SCOPES.AREA;
}

/**
 * Indica si el usuario solamente puede consultar su propia información.
 */
export function hasOwnAccess(role, module) {
  return getModulePermissions(role, module).dataScope === DATA_SCOPES.PROPIO;
}

/**
 * @deprecated Usar isReadOnly() en su lugar.
 */
export function hasReadOnlyAccess(role, module) {
  return isReadOnly(role, module);
}
