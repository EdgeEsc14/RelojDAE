import { Navigate } from "react-router-dom";

import {
  ACCESS_LEVELS,
} from "../constants/permissions";

import { currentUser } from "../data/currentUser";
import { getModuleAccess } from "../utils/permissions";

/**
 * Protege una ruta según:
 *
 * 1. El rol del usuario actual.
 * 2. El módulo solicitado.
 * 3. Opcionalmente, los niveles de acceso permitidos.
 */
function ProtectedRoute({
  requiredModule,
  allowedAccessLevels,
  children,
}) {
  const accessLevel = getModuleAccess(
    currentUser.role,
    requiredModule,
  );

  const hasModuleAccess =
    accessLevel !== ACCESS_LEVELS.NINGUNO;

  const hasAllowedAccessLevel =
    !allowedAccessLevels ||
    allowedAccessLevels.includes(accessLevel);

  if (!hasModuleAccess || !hasAllowedAccessLevel) {
    return <Navigate to="/access-denied" replace />;
  }

  return children;
}

export default ProtectedRoute;