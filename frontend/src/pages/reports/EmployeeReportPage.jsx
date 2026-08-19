import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  FileSpreadsheet,
  FileText,
  Loader,
  ShieldCheck,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  getReporteEmpleadoJSON,
  descargarReporteEmpleadoCSV,
  descargarReporteEmpleadoPDF,
} from "../../api/reportesApi";

function getStatusClass(estatus) {
  if (estatus === "COMPLETO") return "badge success";
  if (estatus === "RETARDO_MENOR") return "badge warning";
  if (estatus === "RETARDO_MAYOR") return "badge warning";
  if (estatus === "FALTA") return "badge danger";
  if (estatus === "OMISION_SALIDA") return "badge neutral";
  return "badge neutral";
}

function getStatusLabel(estatus) {
  const labels = {
    COMPLETO: "Completo",
    RETARDO_MENOR: "Retardo menor",
    RETARDO_MAYOR: "Retardo mayor",
    FALTA: "Falta",
    OMISION_SALIDA: "Om. salida",
  };
  return labels[estatus] || estatus || "";
}

function formatTime(dt) {
  if (!dt) return "—";
  try {
    const d = new Date(dt);
    return d.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return dt;
  }
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

function minutosAHoras(min) {
  if (!min) return "00:00";
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function getDefaultDates() {
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  const fin = today.toISOString().split("T")[0];
  const inicio = firstDay.toISOString().split("T")[0];
  return { inicio, fin };
}

function EmployeeReportPage() {
  const { employeeId } = useParams();
  const employeeCode = employeeId; // La ruta usa :employeeId pero pasamos el código
  const defaults = getDefaultDates();

  const [fechaInicio, setFechaInicio] = useState(defaults.inicio);
  const [fechaFin, setFechaFin] = useState(defaults.fin);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState("");

  useEffect(() => {
    if (employeeCode && fechaInicio && fechaFin) {
      loadReport();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadReport() {
    if (!employeeCode || !fechaInicio || !fechaFin) return;

    setLoading(true);
    setError("");
    try {
      const data = await getReporteEmpleadoJSON(employeeCode, fechaInicio, fechaFin);
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
      await descargarReporteEmpleadoCSV(employeeCode, fechaInicio, fechaFin);
    } catch (err) {
      alert("Error al descargar CSV: " + err.message);
    } finally {
      setDownloading("");
    }
  }

  async function handleDownloadPDF() {
    setDownloading("pdf");
    try {
      await descargarReporteEmpleadoPDF(employeeCode, fechaInicio, fechaFin);
    } catch (err) {
      alert("Error al descargar PDF: " + err.message);
    } finally {
      setDownloading("");
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Reporte individual"
        description="Reporte de asistencia por empleado con exportación CSV y PDF."
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

      {/* Filtros de fecha */}
      <section className="panel-card">
        <div className="filters-row">
          <div className="filter-field">
            <label htmlFor="rep-fecha-inicio">Desde</label>
            <input
              id="rep-fecha-inicio"
              type="date"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
            />
          </div>

          <div className="filter-field">
            <label htmlFor="rep-fecha-fin">Hasta</label>
            <input
              id="rep-fecha-fin"
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
            <p>Consultando datos de asistencia del empleado.</p>
          </div>
        </div>
      )}

      {/* Reporte */}
      {!loading && report && (
        <section className="report-paper">
          <div className="report-institutional-header">
            <div className="report-logo-box">
              <ShieldCheck size={34} />
            </div>

            <div>
              <p>Dirección de Administración Escolar</p>
              <h1>Reporte de Asistencia</h1>
              <span>
                Periodo del {formatDate(report.fecha_inicio)} al {formatDate(report.fecha_fin)}
              </span>
            </div>
          </div>

          {/* Datos del empleado */}
          <section className="report-section">
            <div className="report-section-title">
              <FileText size={18} />
              <h2>Datos del empleado</h2>
            </div>

            <div className="report-info-grid">
              <div>
                <span>Código</span>
                <strong>{report.empleado.codigo_empleado}</strong>
              </div>
              <div>
                <span>Nombre</span>
                <strong>{report.empleado.nombre_completo}</strong>
              </div>
              <div>
                <span>Puesto</span>
                <strong>{report.empleado.puesto || "N/A"}</strong>
              </div>
              <div>
                <span>Área</span>
                <strong>{report.empleado.unidad_organizacional || "N/A"}</strong>
              </div>
            </div>
          </section>

          {/* Resumen */}
          <section className="report-section">
            <div className="report-section-title">
              <FileText size={18} />
              <h2>Resumen del periodo</h2>
            </div>

            <div className="report-summary-grid">
              <div>
                <span>Días en periodo</span>
                <strong>{report.resumen.dias_periodo}</strong>
              </div>
              <div>
                <span>Días completos</span>
                <strong>{report.resumen.dias_completos}</strong>
              </div>
              <div>
                <span>Retardos menores</span>
                <strong>{report.resumen.retardos_menores}</strong>
              </div>
              <div>
                <span>Retardos mayores</span>
                <strong>{report.resumen.retardos_mayores}</strong>
              </div>
              <div>
                <span>Faltas</span>
                <strong>{report.resumen.faltas}</strong>
              </div>
              <div>
                <span>Total puntos</span>
                <strong>{report.resumen.total_puntos}</strong>
              </div>
              <div>
                <span>Horas ordinarias</span>
                <strong>{minutosAHoras(report.resumen.total_minutos_ordinarios)}</strong>
              </div>
              <div>
                <span>Horas extra</span>
                <strong>{minutosAHoras(report.resumen.total_minutos_extra)}</strong>
              </div>
              <div>
                <span>Asistencia</span>
                <strong>{report.resumen.porcentaje_asistencia}%</strong>
              </div>
            </div>
          </section>

          {/* Detalle diario */}
          <section className="report-section">
            <div className="report-section-title">
              <FileText size={18} />
              <h2>Detalle diario</h2>
            </div>

            <div className="simple-table report-table">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Ent. prog.</th>
                    <th>Sal. prog.</th>
                    <th>Entrada</th>
                    <th>Salida</th>
                    <th>Retardo</th>
                    <th>Ordinario</th>
                    <th>Extra</th>
                    <th>Estatus</th>
                    <th>Puntos</th>
                  </tr>
                </thead>
                <tbody>
                  {report.dias.map((dia) => (
                    <tr key={dia.fecha}>
                      <td>{formatDate(dia.fecha)}</td>
                      <td>{formatTime(dia.entrada_programada)}</td>
                      <td>{formatTime(dia.salida_programada)}</td>
                      <td>{formatTime(dia.primera_entrada)}</td>
                      <td>{formatTime(dia.ultima_salida)}</td>
                      <td>{dia.minutos_retardo || 0} min</td>
                      <td>{minutosAHoras(dia.minutos_ordinarios)}</td>
                      <td>{minutosAHoras(dia.minutos_extra)}</td>
                      <td>
                        <span className={getStatusClass(dia.estatus)}>
                          {getStatusLabel(dia.estatus)}
                        </span>
                      </td>
                      <td>{dia.puntos_generados || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {report.dias.length === 0 && (
              <div className="empty-state">
                <p>No hay registros de asistencia en el periodo seleccionado.</p>
              </div>
            )}
          </section>

          {/* Firmas */}
          <section className="report-signatures">
            <div>
              <span>Empleado</span>
              <strong>{report.empleado.nombre_completo}</strong>
            </div>
            <div>
              <span>Supervisor / RH</span>
              <strong>Nombre y firma</strong>
            </div>
            <div>
              <span>Dirección</span>
              <strong>Nombre y firma</strong>
            </div>
          </section>
        </section>
      )}
    </div>
  );
}

export default EmployeeReportPage;
