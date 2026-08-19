import { Navigate, useLocation } from "react-router-dom";

import { DATA_SCOPES } from "../constants/permissions";
import { useAuth } from "../context/AuthContext";
import { getModulePermissions } from "../utils/permissions";

/**
 * Protege una ruta según:
 *
 * 1. Si hay sesión real.
 * 2. El rol del usuario autenticado.
 * 3. El módulo solicitado (dataScope !== NINGUNO).
 * 4. Opcionalmente, los DataScopes permitidos para esta ruta.
 * 5. Opcionalmente, capacidades requeridas.
 */
function ProtectedRoute({
  requiredModule,
  allowedAccessLevels,
  requiredCapability,
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

  const permissions = getModulePermissions(
    user.role,
    requiredModule,
  );

  // El módulo no es accesible si dataScope es NINGUNO
  const hasModuleAccess =
    permissions.dataScope !== DATA_SCOPES.NINGUNO;

  // Filtro opcional por DataScope (para rutas que requieren
  // un nivel específico, ej. solo TOTAL puede procesar asistencia)
  const hasAllowedScope =
    !allowedAccessLevels ||
    allowedAccessLevels.includes(permissions.dataScope);

  // Filtro opcional por capacidad específica
  const hasRequiredCapability =
    !requiredCapability ||
    permissions[requiredCapability] === true;

  if (!hasModuleAccess || !hasAllowedScope || !hasRequiredCapability) {
    return <Navigate to="/access-denied" replace />;
  }

  return children;
}

export default ProtectedRoute;
