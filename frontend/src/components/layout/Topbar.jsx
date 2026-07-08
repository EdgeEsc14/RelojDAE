import { Bell, LogOut, Search, UserRound } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { ROLE_LABELS } from "../../constants/roles";
import { useAuth } from "../../context/AuthContext";

function Topbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const roleLabel =
    user?.roleLabel ||
    ROLE_LABELS[user?.role] ||
    user?.role ||
    "Usuario";

  const displayName =
    user?.fullName ||
    user?.nombreUsuario ||
    user?.correo ||
    "Usuario";

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="topbar">
      <div className="topbar-search">
        <Search size={18} />
        <input type="text" placeholder="Buscar empleado, incidencia o reporte..." />
      </div>

      <div className="topbar-actions">
        <button className="icon-button" type="button" title="Notificaciones">
          <Bell size={18} />
        </button>

        <div className="user-chip">
          <div className="user-avatar">
            <UserRound size={18} />
          </div>

          <div>
            <strong>{roleLabel}</strong>
            <span>{displayName}</span>
          </div>
        </div>

        <button
          className="icon-button"
          type="button"
          title="Cerrar sesión"
          onClick={handleLogout}
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}

export default Topbar;