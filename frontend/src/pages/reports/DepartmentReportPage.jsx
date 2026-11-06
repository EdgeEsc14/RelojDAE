import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  FileSpreadsheet,
  FileText,
  Loader,
  Users,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  getReporteDepartamentalJSON,
  descargarReporteDepartamentalCSV,
  descargarReporteDepartamentalPDF,
} from "../../api/reportesApi";
import { catalogosApi } from "../../api/catalogosApi";

function minutosAHoras(min) {
  if (!min) return "00:00";
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function getDefaultDates() {
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  const fin = today.toLocaleDateString("sv");
  const inicio = firstDay.toLocaleDateString("sv");
  return { inicio, fin };
}

function DepartmentReportPage() {
  const defaults = getDefaultDates();

  const [fechaInicio, setFechaInicio] = useState(defaults.inicio);
  const [fechaFin, setFechaFin] = useState(defaults.fin);
  const [departamentos, setDepartamentos] = useState([]);
  const [unidadOrganizacionalId, setUnidadOrganizacionalId] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState("");

  useEffect(() => {
    if (fechaInicio && fechaFin) {
      loadReport();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    catalogosApi
      .listarUnidadesOrganizacionales()
      .then((items) => {
        const soloDepartamentos = (items || []).filter(
          (u) => u.tipo_unidad_codigo === "DEPARTAMENTO"
        );
        setDepartamentos(soloDepartamentos);
      })
      .catch(() => setDepartamentos([]));
  }, []);

  async function loadReport() {
    if (!fechaInicio || !fechaFin) return;

    setLoading(true);
    setError("");
    try {
      const data = await getReporteDepartamentalJSON(
        fechaInicio,
        fechaFin,
        unidadOrganizacionalId || undefined
      );
      setReport(data);
    } catch (err) {
      setError(err.message || "Error al generar reporte.");
      setReport(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleDownloadCSV() {
    setDownloading("csv");
    try {
      await descargarReporteDepartamentalCSV(fechaInicio, fechaFin, unidadOrganizacionalId || undefined);
    } catch (err) {
      alert("Error al descargar CSV: " + err.message);
    } finally {
      setDownloading("");
    }
  }

  async function handleDownloadPDF() {
    setDownloading("pdf");
    try {
      await descargarReporteDepartamentalPDF(fechaInicio, fechaFin, unidadOrganizacionalId || undefined);
    } catch (err) {
      alert("Error al descargar PDF: " + err.message);
    } finally {
      setDownloading("");
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Reporte por departamento"
        description="Concentrado de asistencia por área con exportación CSV y PDF."
      >
        <div className="header-actions">
          <Link className="secondary-button link-button" to="/reports">
            <ArrowLeft size={17} />
            Volver
          </Link>

          {report && (
            <>
              <button
                className="secondary-button"
                type="button"
                onClick={handleDownloadCSV}
                disabled={!!downloading}
              >
                <FileSpreadsheet size={17} />
                {downloading === "csv" ? "Descargando..." : "CSV"}
              </button>

              <button
                className="primary-button"
                type="button"
                onClick={handleDownloadPDF}
                disabled={!!downloading}
              >
                <Download size={17} />
                {downloading === "pdf" ? "Descargando..." : "PDF"}
              </button>
            </>
          )}
        </div>
      </PageHeader>

      {/* Filtros */}
      <section className="panel-card">
        <div className="filters-row">
          <div className="filter-field">
            <label htmlFor="dept-unidad">Departamento</label>
            <select
              id="dept-unidad"
              value={unidadOrganizacionalId}
              onChange={(e) => setUnidadOrganizacionalId(e.target.value)}
            >
              <option value="">Todos los departamentos</option>
              {departamentos.map((depto) => (
                <option key={depto.id} value={depto.id}>
                  {depto.nombre}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-field">
            <label htmlFor="dept-fecha-inicio">Desde</label>
            <input
              id="dept-fecha-inicio"
              type="date"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
            />
          </div>

          <div className="filter-field">
            <label htmlFor="dept-fecha-fin">Hasta</label>
            <input
              id="dept-fecha-fin"
              type="date"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
            />
          </div>

          <button
            className="primary-button"
            type="button"
            onClick={loadReport}
            disabled={loading}
          >
            {loading ? <Loader size={17} /> : <FileText size={17} />}
            {loading ? "Generando..." : "Generar reporte"}
          </button>
        </div>
      </section>

      {/* Error */}
      {error && (
        <div className="panel-card">
          <div className="empty-state">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="panel-card">
          <div className="empty-state">
            <h3>Generando reporte...</h3>
            <p>Consultando datos de asistencia por departamento.</p>
          </div>
        </div>
      )}

      {/* Reporte */}
      {!loading && report && (
        <>
          {/* Métricas */}
          <section className="metrics-grid three-columns">
            <article className="metric-card">
              <div className="metric-icon">
                <Users size={22} />
              </div>
              <div>
                <p>Departamentos</p>
                <strong>{report.totales.departamentos}</strong>
                <span>Áreas con registros</span>
              </div>
            </article>

            <article className="metric-card">
              <div className="metric-icon">
                <Users size={22} />
              </div>
              <div>
                <p>Empleados</p>
                <strong>{report.totales.empleados}</strong>
                <span>Con asistencia procesada</span>
              </div>
            </article>

            <article className="metric-card">
              <div className="metric-icon">
                <Users size={22} />
              </div>
              <div>
                <p>Faltas</p>
                <strong>{report.totales.faltas}</strong>
                <span>Total en el periodo</span>
              </div>
            </article>
          </section>

          {/* Tabla */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Concentrado por departamento</h3>
                <p>Periodo {report.fecha_inicio} a {report.fecha_fin}</p>
              </div>
            </div>

            <div className="simple-table desktop-table">
              <table>
                <thead>
                  <tr>
                    <th>Departamento</th>
                    <th>Empleados</th>
                    <th>Completos</th>
                    <th>Tolerancia</th>
                    <th>Ret. menores</th>
                    <th>Ret. mayores</th>
                    <th>Faltas</th>
                    <th>Om. entrada</th>
                    <th>Om. salida</th>
                    <th>No laborales</th>
                    <th>Revisar</th>
                    <th>Puntos</th>
                    <th>Hrs. ordinarias</th>
                    <th>Hrs. extra</th>
                  </tr>
                </thead>
                <tbody>
                  {report.departamentos.map((dept) => (
                    <tr key={dept.unidad_id || dept.unidad_nombre}>
                      <td>
                        <strong>{dept.unidad_nombre || "Sin departamento (nivel superior)"}</strong>
                      </td>
                      <td>{dept.total_empleados}</td>
                      <td>{dept.dias_completos}</td>
                      <td>{dept.tolerancias}</td>
                      <td>{dept.retardos_menores}</td>
                      <td>{dept.retardos_mayores}</td>
                      <td>{dept.faltas}</td>
                      <td>{dept.omisiones_entrada}</td>
                      <td>{dept.omisiones_salida}</td>
                      <td>{dept.dias_no_laborales}</td>
                      <td>{dept.dias_requieren_revision}</td>
                      <td>{dept.total_puntos}</td>
                      <td>{minutosAHoras(dept.total_minutos_ordinarios)}</td>
                      <td>{minutosAHoras(dept.total_minutos_extra)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile */}
            <div className="mobile-card-list">
              {report.departamentos.map((dept) => (
                <article className="mobile-data-card" key={`${dept.unidad_id}-mobile`}>
                  <h4>{dept.unidad_nombre || "Sin departamento (nivel superior)"}</h4>
                  <div className="mobile-data-grid">
                    <div>
                      <span>Empleados</span>
                      <strong>{dept.total_empleados}</strong>
                    </div>
                    <div>
                      <span>Completos</span>
                      <strong>{dept.dias_completos}</strong>
                    </div>
                    <div>
                      <span>Faltas</span>
                      <strong>{dept.faltas}</strong>
                    </div>
                    <div>
                      <span>Retardos</span>
                      <strong>{dept.retardos_menores + dept.retardos_mayores}</strong>
                    </div>
                    <div>
                      <span>Puntos</span>
                      <strong>{dept.total_puntos}</strong>
                    </div>
                    <div>
                      <span>Hrs. extra</span>
                      <strong>{minutosAHoras(dept.total_minutos_extra)}</strong>
                    </div>
                  </div>
                </article>
              ))}
            </div>

            {report.departamentos.length === 0 && (
              <div className="empty-state">
                <p>No hay datos de asistencia procesada para el periodo seleccionado.</p>
              </div>
            )}
          </section>

          {/* Detalle por empleado */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Detalle por empleado</h3>
                <p>Empleados incluidos en el concentrado anterior.</p>
              </div>
            </div>

            <div className="simple-table desktop-table">
              <table>
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Nombre</th>
                    <th>Departamento</th>
                    <th>Completos</th>
                    <th>Tolerancia</th>
                    <th>Ret. menores</th>
                    <th>Ret. mayores</th>
                    <th>Faltas</th>
                    <th>Revisar</th>
                    <th>Puntos</th>
                  </tr>
                </thead>
                <tbody>
                  {(report.detalle_empleados || []).map((emp) => (
                    <tr key={emp.empleado_id}>
                      <td>{emp.codigo_empleado}</td>
                      <td>{emp.nombre_completo}</td>
                      <td>{emp.unidad_nombre || "Sin departamento (nivel superior)"}</td>
                      <td>{emp.dias_completos}</td>
                      <td>{emp.tolerancias ?? 0}</td>
                      <td>{emp.retardos_menores}</td>
                      <td>{emp.retardos_mayores}</td>
                      <td>{emp.faltas}</td>
                      <td>{emp.dias_requieren_revision}</td>
                      <td>{emp.total_puntos}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {(report.detalle_empleados || []).length === 0 && (
              <div className="empty-state">
                <p>No hay empleados con asistencia procesada para el periodo seleccionado.</p>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

export default DepartmentReportPage;
