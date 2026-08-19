import { useEffect, useMemo, useState } from "react";

import {
  ChevronLeft,
  ChevronRight,
  Download,
  Fingerprint,
  RefreshCw,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { getZkAttendanceFromDb } from "../../api/zkApi";

function getTodayValue() {
  return new Date().toISOString().slice(0, 10);
}

function formatDateTime(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("es-MX", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(new Date(value));
  } catch {
    return String(value);
  }
}

function getPunchBadge(punch, label) {
  const p = Number(punch);
  if (p === 0) return { className: "badge success", text: label || "Entrada" };
  if (p === 1) return { className: "badge warning", text: label || "Salida" };
  return { className: "badge neutral", text: label || `Punch ${punch}` };
}

function AttendanceRawPage() {
  const today = getTodayValue();

  // Data
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [userId, setUserId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  async function loadRecords() {
    setLoading(true);
    setError("");
    try {
      const result = await getZkAttendanceFromDb({
        limit: pageSize,
        userId: userId.trim(),
        dateFrom,
        dateTo,
      });
      setRecords(result.records || []);
      setTotal(result.total || 0);
    } catch (err) {
      setError(err.message || "Error al consultar marcaciones.");
      setRecords([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRecords();
  }, [page, pageSize]);

  function handleSearch(e) {
    e.preventDefault();
    setPage(1);
    loadRecords();
  }

  function clearFilters() {
    setSearchTerm("");
    setUserId("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  }

  // Local text filter on already-loaded records
  const filteredRecords = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return records;
    return records.filter((r) =>
      (r.empleado_nombre || "").toLowerCase().includes(term) ||
      (r.codigo_empleado || "").toLowerCase().includes(term) ||
      String(r.zk_user_id || "").includes(term) ||
      (r.punch_label || "").toLowerCase().includes(term) ||
      (r.fecha_hora || "").includes(term)
    );
  }, [records, searchTerm]);

  // Stats
  const entradas = records.filter((r) => Number(r.punch) === 0).length;
  const salidas = records.filter((r) => Number(r.punch) === 1).length;

  // Export CSV
  function handleExportCsv() {
    if (filteredRecords.length === 0) return;

    const headers = ["ID", "Empleado", "Código", "User ID ZK", "Fecha y hora", "Evento", "Status", "Dispositivo"];
    const rows = filteredRecords.map((r) => [
      r.id,
      r.empleado_nombre || "Sin vincular",
      r.codigo_empleado || "—",
      r.zk_user_id,
      r.fecha_hora,
      r.punch_label || `Punch ${r.punch}`,
      r.status_label || `Status ${r.status}`,
      r.dispositivo_ip || r.dispositivo_origen || "—",
    ]);

    const csv = [
      headers.join(","),
      ...rows.map((row) => row.map((v) => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",")),
    ].join("\n");

    const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `marcaciones_${today}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="page-stack">
      <PageHeader
        title="Marcaciones"
        description="Historial de checadas sincronizadas desde los relojes ZKTeco."
      >
        <div className="header-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={handleExportCsv}
            disabled={filteredRecords.length === 0}
          >
            <Download size={17} />
            Exportar CSV
          </button>
          <button
            className="primary-button"
            type="button"
            onClick={loadRecords}
            disabled={loading}
          >
            <RefreshCw size={17} />
            {loading ? "Consultando..." : "Actualizar"}
          </button>
        </div>
      </PageHeader>

      {/* Métricas */}
      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon"><Fingerprint size={22} /></div>
          <div>
            <p>Total registros</p>
            <strong>{total}</strong>
            <span>En PostgreSQL</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon"><Fingerprint size={22} /></div>
          <div>
            <p>Mostrando</p>
            <strong>{filteredRecords.length}</strong>
            <span>Página {page} de {totalPages}</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon" style={{ color: "#10b981" }}><Fingerprint size={22} /></div>
          <div>
            <p>Entradas</p>
            <strong>{entradas}</strong>
            <span>Punch 0</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon" style={{ color: "#f59e0b" }}><Fingerprint size={22} /></div>
          <div>
            <p>Salidas</p>
            <strong>{salidas}</strong>
            <span>Punch 1</span>
          </div>
        </article>
      </section>

      {/* Búsqueda y filtros */}
      <section className="panel-card">
        <form className="filters-row" onSubmit={handleSearch}>
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por nombre, código, User ID ZK..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="secondary-button" type="button" onClick={() => setShowFilters((v) => !v)}>
            <SlidersHorizontal size={17} />
            Filtros
          </button>
          <button className="primary-button" type="submit" disabled={loading}>
            <Search size={17} />
            Buscar
          </button>
        </form>

        {showFilters && (
          <div className="filters-row" style={{ marginTop: "12px" }}>
            <input
              type="text"
              placeholder="User ID ZKTeco"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              style={{ minHeight: "42px", borderRadius: "12px", border: "1px solid var(--color-border)", padding: "0 12px", minWidth: "140px" }}
            />
            <input
              type="date"
              value={dateFrom}
              max={today}
              onChange={(e) => setDateFrom(e.target.value)}
              style={{ minHeight: "42px", borderRadius: "12px", border: "1px solid var(--color-border)", padding: "0 12px" }}
            />
            <input
              type="date"
              value={dateTo}
              max={today}
              min={dateFrom || undefined}
              onChange={(e) => setDateTo(e.target.value)}
              style={{ minHeight: "42px", borderRadius: "12px", border: "1px solid var(--color-border)", padding: "0 12px" }}
            />
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
              style={{ minHeight: "42px", borderRadius: "12px", border: "1px solid var(--color-border)", padding: "0 12px", minWidth: "130px" }}
            >
              <option value={25}>25 por página</option>
              <option value={50}>50 por página</option>
              <option value={100}>100 por página</option>
              <option value={250}>250 por página</option>
            </select>
            <button className="secondary-button" type="button" onClick={clearFilters}>
              <X size={17} /> Limpiar
            </button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="empty-state" style={{ padding: "16px" }}>
            <p style={{ color: "var(--color-danger-text)" }}>{error}</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="empty-state">
            <RefreshCw size={32} />
            <p>Consultando marcaciones desde PostgreSQL...</p>
          </div>
        )}

        {/* Empty */}
        {!loading && !error && filteredRecords.length === 0 && (
          <div className="empty-state">
            <Fingerprint size={32} />
            <h3>Sin marcaciones</h3>
            <p>No hay registros con los filtros actuales. Sincroniza desde el Dashboard para traer marcaciones del reloj.</p>
          </div>
        )}

        {/* Tabla */}
        {!loading && filteredRecords.length > 0 && (
          <>
            <div className="simple-table">
              <table>
                <thead>
                  <tr>
                    <th>Empleado</th>
                    <th>User ID ZK</th>
                    <th>Fecha y hora</th>
                    <th>Evento</th>
                    <th>Verificación</th>
                    <th>Dispositivo</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRecords.map((record) => {
                    const punch = getPunchBadge(record.punch, record.punch_label);
                    return (
                      <tr key={record.id || `${record.zk_user_id}-${record.fecha_hora}`}>
                        <td>
                          <div className="employee-cell">
                            <div className="employee-avatar">
                              {(record.empleado_nombre || "?").charAt(0)}
                            </div>
                            <div>
                              <strong>{record.empleado_nombre || "Sin vincular"}</strong>
                              <span>{record.codigo_empleado || "—"}</span>
                            </div>
                          </div>
                        </td>
                        <td><strong>{record.zk_user_id || "—"}</strong></td>
                        <td>{formatDateTime(record.fecha_hora)}</td>
                        <td><span className={punch.className}>{punch.text}</span></td>
                        <td><span className="badge neutral">{record.status_label || `Status ${record.status}`}</span></td>
                        <td>{record.dispositivo_ip || record.dispositivo_origen || "—"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Paginación */}
            <div className="filters-row" style={{ marginTop: "16px", justifyContent: "center" }}>
              <button
                className="secondary-button"
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft size={17} />
                Anterior
              </button>
              <span style={{ padding: "11px 16px", fontWeight: 700 }}>
                Página {page} de {totalPages}
              </span>
              <button
                className="secondary-button"
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
                <ChevronRight size={17} />
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

export default AttendanceRawPage;
