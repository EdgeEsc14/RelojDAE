import { NavLink } from "react-router-dom";
import { Fingerprint } from "lucide-react";

import { menuItems } from "../../constants/menuItems";
import { currentUser } from "../../data/currentUser";
import { canAccessModule } from "../../utils/permissions";

function Sidebar() {
  const visibleMenuItems = menuItems.filter((item) =>
    canAccessModule(currentUser.role, item.module),
  );

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <Fingerprint size={24} />
        </div>

        <div>
          <h1>Reloj DAE</h1>
          <p>Control de asistencia</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {visibleMenuItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/dashboard"}
              className={({ isActive }) =>
                isActive ? "sidebar-link active" : "sidebar-link"
              }
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}

export default Sidebar;