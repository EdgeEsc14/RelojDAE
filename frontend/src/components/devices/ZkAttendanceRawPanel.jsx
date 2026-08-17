import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarDays,
  Clock3,
  Database,
  Download,
  Fingerprint,
  RefreshCcw,
  RotateCcw,
  Search,
} from "lucide-react";

import {
  getZkAttendanceFromDb,
  getZkAttendanceRaw,
  getZkUsers,
  syncZkAttendanceToDb,
} from "../../api/zkApi";

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
  if ([2, 3, 4, 5].includes(punchNumber)) return "badge neutral";

  return "badge danger";
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
  const [source, setSource] = useState("db");
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncMessage, setSyncMessage] = useState("");
  async function loadAttendance(sourceOverride = source) {
    setLoading(true);
    setError("");
    setSyncMessage("");

    try {
      const attendanceRequest =
        sourceOverride === "db"
          ? getZkAttendanceFromDb({
              limit,
              userId,
              dateFrom,
              dateTo,
            })
          : getZkAttendanceRaw({
              limit,
              userId,
              dateFrom,
              dateTo,
            });

      const [attendanceResponse, usersResponse] = await Promise.all([
        attendanceRequest,
        getZkUsers({ includeAdmin: true }),
      ]);

      const normalizedRecords = (attendanceResponse.records || []).map((record) => ({
        ...record,
        uid: record.uid ?? record.zk_uid_registro,
        user_id: record.user_id ?? record.zk_user_id,
        timestamp: record.timestamp ?? record.fecha_hora,
      }));

      setRecords(normalizedRecords);
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

  async function handleSyncToDb() {
    setSyncLoading(true);
    setError("");
    setSyncMessage("");

    try {
      const response = await syncZkAttendanceToDb({
        limit: 1000,
        userId,
        dateFrom,
        dateTo,
      });

      const result = response.result || {};

      setSyncMessage(
        `Sincronización completada. Insertadas: ${result.insertadas || 0}, duplicadas: ${
          result.duplicadas || 0
        }, omitidas: ${result.omitidas || 0}.`
      );

      setSource("db");

      await loadAttendance("db");
    } catch (err) {
      setError(err.message || "No se pudo sincronizar a PostgreSQL.");
    } finally {
      setSyncLoading(false);
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

  function escapeCsvValue(value) {
  const text = safeText(value, "");

  if (
    text.includes(",") ||
    text.includes('"') ||
    text.includes("\n") ||
    text.includes("\r")
  ) {
    return `"${text.replaceAll('"', '""')}"`;
  }

  return text;
}

function handleExportCsv() {
  const rowsToExport = filteredRecords;

  if (rowsToExport.length === 0) {
    setError("No hay registros para exportar.");
    return;
  }

  const headers = [
    "Fuente",
    "ID BD",
    "UID registro ZKTeco",
    "User ID ZKTeco",
    "Usuario ZKTeco",
    "Codigo empleado",
    "Empleado",
    "Fecha",
    "Hora",
    "Fecha hora",
    "Punch",
    "Punch label",
    "Status",
    "Status label",
    "Sync run",
  ];

  const rows = rowsToExport.map((record) => {
    const zkUserName = getZkUserName(record.user_id);
    const sourceLabel = source === "db" ? "PostgreSQL" : "Reloj en vivo";

    return [
      sourceLabel,
      record.id,
      record.uid,
      record.user_id,
      zkUserName,
      record.codigo_empleado,
      record.empleado_nombre,
      record.fecha,
      record.hora,
      record.timestamp,
      record.punch,
      record.punch_label,
      record.status,
      record.status_label,
      record.sync_run_id,
    ];
  });

  const csvContent = [
    headers.map(escapeCsvValue).join(","),
    ...rows.map((row) => row.map(escapeCsvValue).join(",")),
  ].join("\n");

  const blob = new Blob([`\uFEFF${csvContent}`], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  const todayText = getTodayInputValue();
  const sourceText = source === "db" ? "postgresql" : "reloj";

  link.href = url;
  link.download = `checadas_crudas_${sourceText}_${todayText}.csv`;
  link.click();

  URL.revokeObjectURL(url);
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
  const otrosPunchCount = records.filter(
    (record) => ![0, 1].includes(Number(record.punch))
  ).length;
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


          <select
            value={source}
            onChange={(event) => {
              const newSource = event.target.value;
              setSource(newSource);
              loadAttendance(newSource);
            }}
            disabled={loading || syncLoading}
            style={{
              minHeight: "42px",
              borderRadius: "12px",
              border: "1px solid #ddd",
              padding: "0 12px",
              minWidth: "190px",
            }}
          >
            <option value="live">Reloj en vivo</option>
            <option value="db">PostgreSQL</option>
          </select>

          <button
            className="primary-button"
            type="button"
            onClick={handleSyncToDb}
            disabled={loading || syncLoading}
          >
            {syncLoading ? "Sincronizando..." : "Sincronizar a BD"}
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={handleExportCsv}
            disabled={loading || syncLoading || filteredRecords.length === 0}
          >
            <Download size={17} />
            Exportar CSV
          </button>
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
            Recargar sección
          </button>
        </div>
      </div>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Fingerprint size={22} />
          </div>
          <div>
            <p>{source === "db" ? "Total en BD" : "Total filtrado"}</p>
            <strong>{total}</strong>
            <span>{source === "db" ? "Desde PostgreSQL" : "Desde reloj ZKTeco"}</span>
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
            <p>Salidas / otros</p>
            <strong>{salidaCount} / {otrosPunchCount}</strong>
            <span>Punch 1 / Punch 2+</span>
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
      {syncMessage && (
        <section className="warning-banner">
          <Database size={22} />
          <div>
            <strong>Sincronización a PostgreSQL</strong>
            <p>{syncMessage}</p>
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