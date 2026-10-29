import { Bell, LogOut, Search, UserRound } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { empleadosApi } from "../../api/empleadosApi";
import { ROLE_LABELS } from "../../constants/roles";
import { useAuth } from "../../context/AuthContext";

function getEmployeeName(emp) {
  return (
    emp.nombre_completo ||
    [emp.nombres, emp.apellido_paterno, emp.apellido_materno]
      .filter(Boolean)
      .join(" ") ||
    "Sin nombre"
  );
}

function Topbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [searchValue, setSearchValue] = useState("");
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const wrapperRef = useRef(null);
  const debounceRef = useRef(null);

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

  useEffect(() => {
    function handleOutsideClick(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  useEffect(() => {
    const q = searchValue.trim();

    if (q.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        setIsLoading(true);
        const data = await empleadosApi.listar({ q, limit: 7 });
        const items = Array.isArray(data)
          ? data
          : Array.isArray(data?.items)
          ? data.items
          : [];
        setResults(items);
        setIsOpen(true);
      } catch {
        setResults([]);
        setIsOpen(false);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(debounceRef.current);
  }, [searchValue]);

  function handleSelect(emp) {
    navigate(`/employees/${encodeURIComponent(emp.codigo_empleado)}`);
    setSearchValue("");
    setIsOpen(false);
  }

  function handleKeyDown(e) {
    if (e.key === "Escape") {
      setIsOpen(false);
      setSearchValue("");
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    const q = searchValue.trim();
    if (q) {
      navigate(`/employees?q=${encodeURIComponent(q)}`);
      setIsOpen(false);
    }
  }

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  const showDropdown = isOpen || (isLoading && searchValue.trim().length >= 2);

  return (
    <header className="topbar">
      <div className="topbar-search-wrapper" ref={wrapperRef}>
        <form className="topbar-search" role="search" onSubmit={handleSubmit}>
          <Search size={18} />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Buscar empleado, incidencia o reporte..."
            autoComplete="off"
          />
        </form>

        {showDropdown && (
          <div className="topbar-search-dropdown">
            {isLoading ? (
              <p className="topbar-search-status">Buscando...</p>
            ) : results.length === 0 ? (
              <p className="topbar-search-status">Sin resultados</p>
            ) : (
              results.map((emp) => {
                const name = getEmployeeName(emp);
                const puesto = emp.puesto ?? emp.puesto_nombre ?? null;
                const area = emp.area_principal ?? emp.unidad_organizacional ?? null;
                const subtitle = [emp.codigo_empleado, puesto, area]
                  .filter(Boolean)
                  .join(" · ");

                return (
                  <button
                    key={emp.codigo_empleado}
                    className="topbar-search-result"
                    type="button"
                    onClick={() => handleSelect(emp)}
                  >
                    <div className="topbar-search-avatar">
                      {name.charAt(0).toUpperCase()}
                    </div>
                    <div className="topbar-search-result-info">
                      <strong>{name}</strong>
                      <span>{subtitle}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        )}
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
