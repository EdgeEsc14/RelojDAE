import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3,
  Download,
  FileSpreadsheet,
  FileText,
  Loader,
  Users,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { empleadosApi } from "../../api/empleadosApi";
import { descargarReporteEmpleadoPDF } from "../../api/reportesApi";

function getDefaultDates() {
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  return {
    inicio: firstDay.toISOString().split("T")[0],
    fin: today.toISOString().split("T")[0],
  };
}

function ReportsPage() {
  const defaults = getDefaultDates();

  const [employees, setEmployees] = useState([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);

  // Form reporte individual
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [fechaInicio, setFechaInicio] = useState(defaults.inicio);
  const [fechaFin, setFechaFin] = useState(defaults.fin);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");
  const [downloadSuccess, setDownloadSuccess] = useState("");

  useEffect(() => {
    async function loadEmployees() {
      setLoadingEmployees(true);
      try {
        const response = await empleadosApi.listar({ limit: 100, estatus: "ACTIVO" });
        const items = response?.items ?? response?.data ?? response ?? [];
        setEmployees(Array.isArray(items) ? items : []);
      } catch {
        setEmployees([]);
      } finally {
        setLoadingEmployees(false);
      }
    }
    loadEmployees();
  }, []);

  async function handleDownloadPDF(e) {
    e.preventDefault();
    setDownloadError("");
    setDownloadSuccess("");

    if (!selectedEmployee) {
      setDownloadError("Selecciona un empleado.");
      return;
    }
    if (!fechaInicio || !fechaFin) {
      setDownloadError("Selecciona fecha inicio y fecha fin.");
      return;
    }
    if (fechaInicio > fechaFin) {
      setDownloadError("La fecha inicio no puede ser mayor que la fecha fin.");
      return;
    }

    setDownloading(true);
    try {
      await descargarReporteEmpleadoPDF(selectedEmployee, fechaInicio, fechaFin);
      setDownloadSuccess("PDF descargado correctamente.");
      setTimeout(() => setDownloadSuccess(""), 4000);
    } catch (err) {
      setDownloadError(err.message || "Error al generar PDF.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Reportes"
        description="Genera reportes PDF profesionales de asistencia por empleado o departamento."
      />

      {/* Métricas */}
      <section className="metrics-grid three-columns">
        <article className="metric-card">
          <div className="metric-icon"><FileText size={22} /></div>
          <div>
            <p>Tipos de reporte</p>
            <strong>2</strong>
            <span>Individual y departamental</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon"><FileSpreadsheet size={22} /></div>
          <div>
            <p>Formatos</p>
            <strong>PDF</strong>
            <span>Diseño institucional</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon"><BarChart3 size={22} /></div>
          <div>
            <p>Alcance</p>
            <strong>Por periodo</strong>
            <span>Selecciona rango de fechas</span>
          </div>
        </article>
      </section>

      {/* Generación rápida de reporte individual PDF */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Generar reporte PDF por empleado</h3>
            <p>Selecciona empleado y rango de fechas para descargar el reporte institucional en PDF.</p>
          </div>
          <Download size={22} />
        </div>

        <form onSubmit={handleDownloadPDF}>
          <div className="form-grid">
            <label>
              Empleado
              <select
                value={selectedEmployee}
                onChange={(e) => setSelectedEmployee(e.target.value)}
                disabled={loadingEmployees}
              >
                <option value="">
                  {loadingEmployees ? "Cargando empleados..." : "Selecciona un empleado"}
                </option>
                {employees.map((emp) => (
                  <option key={emp.codigo_empleado || emp.id} value={emp.codigo_empleado}>
                    {emp.codigo_empleado} — {emp.nombre_completo || `${emp.nombres} ${emp.apellido_paterno}`}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Fecha inicio
              <input
                type="date"
                value={fechaInicio}
                onChange={(e) => setFechaInicio(e.target.value)}
              />
            </label>

            <label>
              Fecha fin
              <input
                type="date"
                value={fechaFin}
                onChange={(e) => setFechaFin(e.target.value)}
              />
            </label>
          </div>

          {downloadError && (
            <p style={{ color: "var(--color-danger-text)", marginTop: "12px", fontSize: "13px" }}>
              {downloadError}
            </p>
          )}
          {downloadSuccess && (
            <p style={{ color: "var(--color-success-text)", marginTop: "12px", fontSize: "13px" }}>
              {downloadSuccess}
            </p>
          )}

          <div className="form-actions" style={{ marginTop: "16px" }}>
            <button className="primary-button" type="submit" disabled={downloading}>
              {downloading ? <Loader size={17} /> : <Download size={17} />}
              {downloading ? "Generando PDF..." : "Descargar reporte PDF"}
            </button>
          </div>
        </form>
      </section>

      {/* Otros reportes */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Otros reportes</h3>
            <p>Accede a reportes detallados con vista previa.</p>
          </div>
        </div>

        <div className="report-card-grid">
          <Link className="report-card" to="/reports/department">
            <div className="report-card-icon">
              <Users size={24} />
            </div>
            <div>
              <span className="badge neutral">Consolidado</span>
              <h3>Reporte por departamento</h3>
              <p>Concentrado de empleados, faltas, retardos y tiempo extra por área.</p>
            </div>
          </Link>
        </div>
      </section>
    </div>
  );
}

export default ReportsPage;
