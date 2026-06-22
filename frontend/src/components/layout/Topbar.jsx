import { Bell, Search, UserRound } from "lucide-react";
import { currentUser } from "../../data/currentUser";
import { ROLE_LABELS } from "../../constants/roles";

function Topbar() {
  return (
    <header className="topbar">
      <div className="topbar-search">
        <Search size={18} />
        <input type="text" placeholder="Buscar empleado, incidencia o reporte..." />
      </div>

      <div className="topbar-actions">
        <button className="icon-button" type="button">
          <Bell size={18} />
        </button>
        <div className="user-chip">
          <div className="user-avatar">
            <UserRound size={18} />
          </div>

          <div>
            <strong>{ROLE_LABELS[currentUser.role]}</strong>
            <span>{currentUser.fullName}</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Topbar;