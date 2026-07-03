import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Fingerprint,
  RefreshCcw,
  Search,
  ShieldCheck,
  UserCheck,
  Users,
} from "lucide-react";

import { getZkHealth, getZkUsers } from "../../api/zkApi";

function safeText(value, fallback = "-") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  return String(value);
}

function getPrivilegeBadgeClass(user) {
  if (user.is_admin) return "badge warning";
  if (user.is_protected) return "badge warning";
  return "badge neutral";
}

function getPinBadgeClass(hasPin) {
  return hasPin ? "badge success" : "badge neutral";
}

export default function ZkUsersPanel() {
  const [users, setUsers] = useState([]);
  const [health, setHealth] = useState(null);
  const [includeAdmin, setIncludeAdmin] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadZkData() {
    setLoading(true);
    setError("");

    try {
      const [healthResponse, usersResponse] = await Promise.all([
        getZkHealth(),
        getZkUsers({ includeAdmin }),
      ]);

      setHealth(healthResponse);
      setUsers(usersResponse.users || []);
    } catch (err) {
      setError(err.message || "No se pudo consultar el reloj ZKTeco.");
      setHealth(null);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadZkData();
  }, [includeAdmin]);

  const filteredUsers = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    if (!term) return users;

    return users.filter((user) => {
      return (
        safeText(user.uid).toLowerCase().includes(term) ||
        safeText(user.user_id).toLowerCase().includes(term) ||
        safeText(user.name).toLowerCase().includes(term) ||
        safeText(user.privilege).toLowerCase().includes(term) ||
        safeText(user.group_id).toLowerCase().includes(term)
      );
    });
  }, [users, searchTerm]);

  const protectedUsers = users.filter((user) => user.is_protected).length;
  const usersWithPin = users.filter((user) => user.has_pin).length;

  return (
    <section className="panel-card">
      <div className="section-header">
        <div>
          <h2>Usuarios del reloj ZKTeco</h2>
          <p>
            Lectura directa desde el dispositivo físico. Esta vista solo consulta;
            no crea, edita ni borra usuarios.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={loadZkData}
          disabled={loading}
        >
          <RefreshCcw size={17} />
          {loading ? "Actualizando..." : "Actualizar"}
        </button>
      </div>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Fingerprint size={22} />
          </div>
          <div>
            <p>Estado conexión</p>
            <strong>{health?.ok ? "Conectado" : "Sin validar"}</strong>
            <span>Reloj físico ZKTeco</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Users size={22} />
          </div>
          <div>
            <p>Usuarios detectados</p>
            <strong>{users.length}</strong>
            <span>Leídos desde el reloj</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <UserCheck size={22} />
          </div>
          <div>
            <p>Usuarios con PIN</p>
            <strong>{usersWithPin}</strong>
            <span>No se muestra el PIN real</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <ShieldCheck size={22} />
          </div>
          <div>
            <p>Protegidos</p>
            <strong>{protectedUsers}</strong>
            <span>Admin o usuarios bloqueados</span>
          </div>
        </article>
      </section>

      <div className="filters-row">
        <div className="filter-search">
          <Search size={18} />
          <input
            type="text"
            placeholder="Buscar por UID, User ID, nombre, privilegio o grupo..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </div>

        <label className="secondary-button" style={{ cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={includeAdmin}
            onChange={(event) => setIncludeAdmin(event.target.checked)}
          />
          Incluir admin
        </label>
      </div>

      {error && (
        <section className="warning-banner">
          <AlertTriangle size={22} />
          <div>
            <strong>Error al consultar reloj</strong>
            <p>{error}</p>
          </div>
        </section>
      )}

      <div className="device-card-grid">
        {filteredUsers.map((user) => (
          <article className="device-card" key={`${user.uid}-${user.user_id}`}>
            <div className="device-card-header">
              <div className="device-card-icon">
                <Fingerprint size={24} />
              </div>

              <div>
                <h3>{safeText(user.name, "Usuario sin nombre")}</h3>
                <p>User ID {safeText(user.user_id)} · UID interno {safeText(user.uid)}</p>
              </div>

              <span className={getPrivilegeBadgeClass(user)}>
                {safeText(user.privilege)}
              </span>
            </div>

            <div className="device-info-grid">
              <div>
                <span>UID interno</span>
                <strong>{safeText(user.uid)}</strong>
              </div>

              <div>
                <span>User ID ZKTeco</span>
                <strong>{safeText(user.user_id)}</strong>
              </div>

              <div>
                <span>Nombre reloj</span>
                <strong>{safeText(user.name, "Sin nombre")}</strong>
              </div>

              <div>
                <span>Grupo</span>
                <strong>{safeText(user.group_id)}</strong>
              </div>

              <div>
                <span>PIN</span>
                <strong>
                  <span className={getPinBadgeClass(user.has_pin)}>
                    {user.has_pin ? "Sí" : "No"}
                  </span>
                </strong>
              </div>

              <div>
                <span>Protegido</span>
                <strong>
                  <span className={user.is_protected ? "badge warning" : "badge neutral"}>
                    {user.is_protected ? "Sí" : "No"}
                  </span>
                </strong>
              </div>
            </div>
          </article>
        ))}

        {!loading && filteredUsers.length === 0 && (
          <article className="device-card">
            <div className="device-card-header">
              <div>
                <h3>No se encontraron usuarios</h3>
                <p>No hay resultados con los filtros actuales.</p>
              </div>

              <span className="badge neutral">Vacío</span>
            </div>
          </article>
        )}

        {loading && (
          <article className="device-card">
            <div className="device-card-header">
              <div>
                <h3>Cargando usuarios</h3>
                <p>Consultando información directamente desde el reloj ZKTeco.</p>
              </div>

              <span className="badge warning">Leyendo</span>
            </div>
          </article>
        )}
      </div>
    </section>
  );
}