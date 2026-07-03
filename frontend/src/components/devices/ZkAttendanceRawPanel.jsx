import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarDays,
  Clock3,
  Fingerprint,
  RefreshCcw,
  RotateCcw,
  Search,
} from "lucide-react";

import { getZkAttendanceRaw, getZkUsers } from "../../api/zkApi";

function safeText(value, fallback = "-") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  return String(value);
}

function getTodayInputValue() {
  const now = new Date();
  const localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000);

  return localDate.toISOString().slice(0, 10);
}

function getPunchBadgeClass(punch) {
  const punchNumber = Number(punch);

  if (punchNumber === 0) return "badge success";
  if (punchNumber === 1) return "badge warning";

  return "badge neutral";
}

export default function ZkAttendanceRawPanel() {
  const today = getTodayInputValue();

  const [records, setRecords] = useState([]);
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(100);
  const [userId, setUserId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadAttendance() {
    setLoading(true);
    setError("");

    try {
      const [attendanceResponse, usersResponse] = await Promise.all([
        getZkAttendanceRaw({
          limit,
          userId,
          dateFrom,
          dateTo,
        }),
        getZkUsers({ includeAdmin: true }),
      ]);

      setRecords(attendanceResponse.records || []);
      setTotal(attendanceResponse.total || 0);
      setUsers(usersResponse.users || []);
    } catch (err) {
      setError(err.message || "No se pudieron consultar las marcaciones.");
      setRecords([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAttendance();
  }, []);

  const usersByUserId = useMemo(() => {
    const map = new Map();

    users.forEach((user) => {
      map.set(safeText(user.user_id), user);
    });

    return map;
  }, [users]);

  function getZkUserName(recordUserId) {
    const user = usersByUserId.get(safeText(recordUserId));

    return safeText(user?.name, `Usuario ZK ${safeText(recordUserId)}`);
  }

  function handleDateFromChange(value) {
    if (value > today) {
      setDateFrom(today);
      return;
    }

    setDateFrom(value);

    if (dateTo && value && dateTo < value) {
      setDateTo(value);
    }
  }

  function handleDateToChange(value) {
    if (value > today) {
      setDateTo(today);
      return;
    }

    setDateTo(value);

    if (dateFrom && value && value < dateFrom) {
      setDateFrom(value);
    }
  }

  function handleClearFilters() {
    setUserId("");
    setDateFrom("");
    setDateTo("");
    setSearchTerm("");
    setLimit(100);
  }

  const filteredRecords = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    if (!term) return records;

    return records.filter((record) => {
      const zkUserName = getZkUserName(record.user_id);

      return (
        safeText(record.user_id).toLowerCase().includes(term) ||
        safeText(zkUserName).toLowerCase().includes(term) ||
        safeText(record.fecha).toLowerCase().includes(term) ||
        safeText(record.hora).toLowerCase().includes(term) ||
        safeText(record.punch_label).toLowerCase().includes(term) ||
        safeText(record.status_label).toLowerCase().includes(term) ||
        safeText(record.uid).toLowerCase().includes(term)
      );
    });
  }, [records, searchTerm, usersByUserId]);

  const entradaCount = records.filter((record) => Number(record.punch) === 0).length;
  const salidaCount = records.filter((record) => Number(record.punch) === 1).length;

  return (
    <section className="panel-card">
      <div className="section-header">
        <div>
          <h2>Checadas crudas del reloj</h2>
          <p>
            Lectura directa de marcaciones desde ZKTeco. Esta vista no guarda ni borra
            registros; solo consulta el dispositivo.
          </p>
        </div>

        <div className="header-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={loadAttendance}
            disabled={loading}
          >
            <RefreshCcw size={17} />
            {loading ? "Consultando..." : "Actualizar checadas"}
          </button>

          <button
            className="secondary-button"
            type="button"
            onClick={() => window.location.reload()}
            disabled={loading}
          >
            <RotateCcw size={17} />
            Recargar página
          </button>
        </div>
      </div>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Fingerprint size={22} />
          </div>
          <div>
            <p>Total filtrado</p>
            <strong>{total}</strong>
            <span>Marcaciones encontradas</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock3 size={22} />
          </div>
          <div>
            <p>Mostradas</p>
            <strong>{records.length}</strong>
            <span>Límite actual: {limit}</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <CalendarDays size={22} />
          </div>
          <div>
            <p>Entradas</p>
            <strong>{entradaCount}</strong>
            <span>Punch 0</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <CalendarDays size={22} />
          </div>
          <div>
            <p>Salidas</p>
            <strong>{salidaCount}</strong>
            <span>Punch 1</span>
          </div>
        </article>
      </section>

      <div className="filters-row">
        <div className="filter-search">
          <Search size={18} />
          <input
            type="text"
            placeholder="Buscar por nombre, User ID, fecha, punch, status o UID..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </div>
      </div>

      <div className="filters-row">
        <input
          type="text"
          placeholder="User ID ZKTeco"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          style={{
            minHeight: "42px",
            borderRadius: "12px",
            border: "1px solid #ddd",
            padding: "0 12px",
            minWidth: "160px",
          }}
        />

        <input
          type="date"
          value={dateFrom}
          max={today}
          onChange={(event) => handleDateFromChange(event.target.value)}
          style={{
            minHeight: "42px",
            borderRadius: "12px",
            border: "1px solid #ddd",
            padding: "0 12px",
          }}
        />

        <input
          type="date"
          value={dateTo}
          max={today}
          min={dateFrom || undefined}
          onChange={(event) => handleDateToChange(event.target.value)}
          style={{
            minHeight: "42px",
            borderRadius: "12px",
            border: "1px solid #ddd",
            padding: "0 12px",
          }}
        />

        <select
          value={limit}
          onChange={(event) => setLimit(Number(event.target.value))}
          style={{
            minHeight: "42px",
            borderRadius: "12px",
            border: "1px solid #ddd",
            padding: "0 12px",
            minWidth: "140px",
          }}
        >
          <option value={10}>10 registros</option>
          <option value={25}>25 registros</option>
          <option value={50}>50 registros</option>
          <option value={100}>100 registros</option>
          <option value={250}>250 registros</option>
          <option value={500}>500 registros</option>
        </select>

        <button
          className="primary-button"
          type="button"
          onClick={loadAttendance}
          disabled={loading}
        >
          Aplicar filtros
        </button>

        <button
          className="secondary-button"
          type="button"
          onClick={handleClearFilters}
          disabled={loading}
        >
          Limpiar filtros
        </button>
      </div>

      {error && (
        <section className="warning-banner">
          <AlertTriangle size={22} />
          <div>
            <strong>Error al consultar checadas</strong>
            <p>{error}</p>
          </div>
        </section>
      )}

      <div className="device-card-grid">
        {filteredRecords.map((record) => {
          const zkUserName = getZkUserName(record.user_id);

          return (
            <article
              className="device-card"
              key={`${record.uid}-${record.user_id}-${record.timestamp}`}
            >
              <div className="device-card-header">
                <div className="device-card-icon">
                  <Fingerprint size={24} />
                </div>

                <div>
                  <h3>
                    {zkUserName} · {safeText(record.fecha)}
                  </h3>
                  <p>
                    User ID {safeText(record.user_id)} · {safeText(record.hora)} · UID
                    registro {safeText(record.uid)}
                  </p>
                </div>

                <span className={getPunchBadgeClass(record.punch)}>
                  {safeText(record.punch_label)}
                </span>
              </div>

              <div className="device-info-grid">
                <div>
                  <span>Fecha</span>
                  <strong>{safeText(record.fecha)}</strong>
                </div>

                <div>
                  <span>Hora</span>
                  <strong>{safeText(record.hora)}</strong>
                </div>

                <div>
                  <span>Usuario ZKTeco</span>
                  <strong>{zkUserName}</strong>
                </div>

                <div>
                  <span>User ID ZKTeco</span>
                  <strong>{safeText(record.user_id)}</strong>
                </div>

                <div>
                  <span>UID registro</span>
                  <strong>{safeText(record.uid)}</strong>
                </div>

                <div>
                  <span>Punch</span>
                  <strong>
                    {safeText(record.punch)} · {safeText(record.punch_label)}
                  </strong>
                </div>

                <div>
                  <span>Status</span>
                  <strong>
                    {safeText(record.status)} · {safeText(record.status_label)}
                  </strong>
                </div>
              </div>
            </article>
          );
        })}

        {!loading && filteredRecords.length === 0 && (
          <article className="device-card">
            <div className="device-card-header">
              <div>
                <h3>Sin marcaciones</h3>
                <p>No hay registros con los filtros actuales.</p>
              </div>

              <span className="badge neutral">Vacío</span>
            </div>
          </article>
        )}

        {loading && (
          <article className="device-card">
            <div className="device-card-header">
              <div>
                <h3>Consultando marcaciones</h3>
                <p>Leyendo registros crudos directamente desde el reloj ZKTeco.</p>
              </div>

              <span className="badge warning">Leyendo</span>
            </div>
          </article>
        )}
      </div>
    </section>
  );
}