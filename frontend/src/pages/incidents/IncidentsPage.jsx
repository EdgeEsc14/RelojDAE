import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Download,
  Eye,
  FileWarning,
  Plus,
  Search,
  SlidersHorizontal,
  X,
  XCircle,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { getIncidencias, getContadores } from "../../api/incidenciasApi";

function getStatusClass(estatus) {
  const s = (estatus || "").toUpperCase();
  if (s === "PENDIENTE") return "badge warning";
  if (s === "SIN_JUSTIFICAR") return "badge danger";
  if (s === "JUSTIFICADA") return "badge success";
  if (s === "APROBADA") return "badge success";
  if (s === "RECHAZADA") return "badge danger";
  if (s === "CANCELADA") return "badge neutral";
  return "badge neutral";
}

function getStatusLabel(estatus) {
  const labels = {
    PENDIENTE: "Pendiente",
    SIN_JUSTIFICAR: "Sin justificar",
    JUSTIFICADA: "Justificada",
    APROBADA: "Aprobada",
    RECHAZADA: "Rechazada",
    CANCELADA: "Cancelada",
  };
  return labels[(estatus || "").toUpperCase()] || estatus || "";
}

function getCategoriaClass(categoria) {
  const c = (categoria || "").toUpperCase();
  if (c === "FALTA") return "badge danger";
  if (c === "RETARDO") return "badge warning";
  if (c === "OMISION") return "badge warning";
  if (c === "TIEMPO_EXTRA") return "badge success";
  if (c === "SANCION") return "badge danger";
  return "badge neutral";
}

function formatDate(value) {
  if (!value) return "";
  try {
    const d = new Date(value + "T00:00:00");
    return d.toLocaleDateString("es-MX", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return value;
  }
}

function IncidentsPage() {
  const [incidencias, setIncidencias] = useState([]);
  const [total, setTotal] = useState(0);
  const [contadores, setContadores] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Filters
  const [busqueda, setBusqueda] = useState("");
  const [filtroEstatus, setFiltroEstatus] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  useEffect(() => {
    loadContadores();
  }, []);

  useEffect(() => {
    loadIncidencias();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, filtroEstatus]);

  async function loadContadores() {
    try {
      const data = await getContadores();
      setContadores(data);
    } catch (err) {
      console.error("Error cargando contadores:", err.message);
    }
  }

  async function loadIncidencias() {
    setLoading(true);
    setError("");
    try {
      const data = await getIncidencias({
        page,
        pageSize,
        estatus: filtroEstatus || undefined,
        busqueda: busqueda.trim() || undefined,
      });
      setIncidencias(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message || "Error al cargar incidencias.");
      setIncidencias([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e) {
    e.preventDefault();
    setPage(1);
    loadIncidencias();
  }

  function clearFilters() {
    setBusqueda("");
    setFiltroEstatus("");
    setPage(1);
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const firstRecord = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastRecord = Math.min(page * pageSize, total);

  return (
    <div className="page-stack">
      <PageHeader
        title="Incidencias"
        description="Gestión de faltas, retardos, omisiones, permisos y tiempo extra."
      >
        <div className="header-actions">
          <button className="primary-button" type="button">
            <Plus size={17} />
            Nueva incidencia
          </button>
        </div>
      </PageHeader>

      {/* Métricas */}
      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <FileWarning size={22} />
          </div>
          <div>
            <p>Total</p>
            <strong>{contadores.total || 0}</strong>
            <span>Incidencias registradas</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>
          <div>
            <p>Pendientes</p>
            <strong>{contadores.PENDIENTE || 0}</strong>
            <span>Requieren revisión</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <p>Aprobadas</p>
            <strong>{contadores.APROBADA || 0}</strong>
            <span>Con autorización</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <AlertTriangle size={22} />
          </div>
          <div>
            <p>Sin justificar</p>
            <strong>{contadores.SIN_JUSTIFICAR || 0}</strong>
            <span>Requieren justificante</span>
          </div>
        </article>
      </section>

      {/* Tabla */}
      <section className="panel-card">
        <form className="filters-row" onSubmit={handleSearch}>
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por empleado, código o tipo..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </div>

          <button className="secondary-button" type="submit">
            <Search size={17} />
            Buscar
          </button>

          <button
            className="secondary-button"
            type="button"
            onClick={() => setShowFilters((v) => !v)}
          >
            <SlidersHorizontal size={17} />
            Filtros
          </button>
        </form>

        {showFilters && (
          <div className="advanced-filters">
            <div className="filter-field">
              <label htmlFor="filter-estatus-inc">Estatus</label>
              <select
                id="filter-estatus-inc"
                value={filtroEstatus}
                onChange={(e) => {
                  setFiltroEstatus(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Todos</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="SIN_JUSTIFICAR">Sin justificar</option>
                <option value="JUSTIFICADA">Justificada</option>
                <option value="APROBADA">Aprobada</option>
                <option value="RECHAZADA">Rechazada</option>
                <option value="CANCELADA">Cancelada</option>
              </select>
            </div>

            <div className="filter-actions">
              <button className="secondary-button" type="button" onClick={clearFilters}>
                <X size={17} />
                Limpiar
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="empty-state">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        )}

        {loading && (
          <div className="empty-state">
            <h3>Cargando incidencias...</h3>
            <p>Consultando la base de datos.</p>
          </div>
        )}

        {!loading && !error && incidencias.length === 0 && (
          <div className="empty-state">
            <h3>No se encontraron incidencias</h3>
            <p>No existen incidencias con los filtros seleccionados.</p>
          </div>
        )}

        {!loading && incidencias.length > 0 && (
          <>
            <div className="simple-table">
              <table>
                <thead>
                  <tr>
                    <th>Empleado</th>
                    <th>Fecha</th>
                    <th>Tipo</th>
                    <th>Categoría</th>
                    <th>Puntos</th>
                    <th>Estatus</th>
                    <th>Origen</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {incidencias.map((inc) => (
                    <tr key={inc.id}>
                      <td>
                        <div className="employee-cell">
                          <div className="employee-avatar">
                            {(inc.nombre_empleado || "?").charAt(0)}
                          </div>
                          <div>
                            <strong>{inc.nombre_empleado}</strong>
                            <span>{inc.codigo_empleado}</span>
                          </div>
                        </div>
                      </td>

                      <td>{formatDate(inc.fecha)}</td>

                      <td>
                        <strong>{inc.tipo_nombre}</strong>
                      </td>

                      <td>
                        <span className={getCategoriaClass(inc.tipo_categoria)}>
                          {inc.tipo_categoria}
                        </span>
                      </td>

                      <td>
                        {inc.puntos_efectivos > 0 ? (
                          <strong>{inc.puntos_efectivos}</strong>
                        ) : (
                          <span className="muted-table-text">0</span>
                        )}
                      </td>

                      <td>
                        <span className={getStatusClass(inc.estatus)}>
                          {getStatusLabel(inc.estatus)}
                        </span>
                      </td>

                      <td>
                        <span className="muted-table-text">
                          {inc.origen === "PROCESAMIENTO" ? "Automático" : "Manual"}
                        </span>
                      </td>

                      <td>
                        <Link className="table-action" to={`/incidents/${inc.id}`}>
                          <Eye size={16} />
                          Ver
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Paginación */}
            <div className="pagination-bar">
              <div className="pagination-summary">
                Mostrando <strong>{firstRecord}</strong> – <strong>{lastRecord}</strong> de{" "}
                <strong>{total}</strong> incidencias
              </div>

              <div className="pagination-size">
                <label htmlFor="inc-per-page">Filas por página</label>
                <select
                  id="inc-per-page"
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>

              <div className="pagination-controls">
                <button
                  className="pagination-button"
                  type="button"
                  disabled={page === 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  <ChevronLeft size={17} />
                </button>

                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let start = Math.max(1, page - 2);
                  if (start + 4 > totalPages) start = Math.max(1, totalPages - 4);
                  const num = start + i;
                  if (num > totalPages) return null;
                  return (
                    <button
                      key={num}
                      className={num === page ? "pagination-button active" : "pagination-button"}
                      type="button"
                      onClick={() => setPage(num)}
                    >
                      {num}
                    </button>
                  );
                })}

                <button
                  className="pagination-button"
                  type="button"
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  <ChevronRight size={17} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

export default IncidentsPage;
