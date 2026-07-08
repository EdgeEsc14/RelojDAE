import { Navigate, useLocation } from "react-router-dom";

import { ACCESS_LEVELS } from "../constants/permissions";
import { useAuth } from "../context/AuthContext";
import { getModuleAccess } from "../utils/permissions";

/**
 * Protege una ruta según:
 *
 * 1. Si hay sesión real.
 * 2. El rol del usuario autenticado.
 * 3. El módulo solicitado.
 * 4. Opcionalmente, los niveles de acceso permitidos.
 */
function ProtectedRoute({
  requiredModule,
  allowedAccessLevels,
  children,
}) {
  const location = useLocation();
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <div className="page-stack">
        <p>Cargando sesión...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location }}
      />
    );
  }

  const accessLevel = getModuleAccess(
    user.role,
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