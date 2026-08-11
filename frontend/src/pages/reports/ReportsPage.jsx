import { Link } from "react-router-dom";
import {
  BarChart3,
  FileSpreadsheet,
  FileText,
  Users,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";

const reportCards = [
  {
    id: "employee",
    title: "Reporte individual por empleado",
    description:
      "Detalle diario de asistencia, retardos, faltas, puntos y horas trabajadas.",
    path: "/reports/department",
    category: "Operativo",
    icon: FileText,
  },
  {
    id: "department",
    title: "Reporte por departamento",
    description:
      "Concentrado de empleados, faltas, retardos y tiempo extra por área.",
    path: "/reports/department",
    category: "Consolidado",
    icon: Users,
  },
];

function ReportsPage() {
  return (
    <div className="page-stack">
      <PageHeader
        title="Reportes"
        description="Centro de reportes con exportación a CSV y PDF."
      />

      <section className="metrics-grid three-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <FileText size={22} />
          </div>
          <div>
            <p>Tipos de reporte</p>
            <strong>2</strong>
            <span>Individual y departamental</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <FileSpreadsheet size={22} />
          </div>
          <div>
            <p>Formatos</p>
            <strong>CSV / PDF</strong>
            <span>Descarga directa</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <BarChart3 size={22} />
          </div>
          <div>
            <p>Alcance</p>
            <strong>Por periodo</strong>
            <span>Selecciona rango de fechas</span>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Reportes disponibles</h3>
            <p>Selecciona un tipo de reporte para generar.</p>
          </div>
        </div>

        <div className="report-card-grid">
          {reportCards.map((report) => {
            const Icon = report.icon;
            return (
              <Link className="report-card" to={report.path} key={report.id}>
                <div className="report-card-icon">
                  <Icon size={24} />
                </div>

                <div>
                  <span className="badge neutral">{report.category}</span>
                  <h3>{report.title}</h3>
                  <p>{report.description}</p>
                </div>
              </Link>
            );
          })}
        </div>

        <div className="report-instructions">
          <h4>Reporte individual por empleado</h4>
          <p>
            Para generar un reporte individual, navega al detalle de un empleado
            desde la sección de Empleados y utiliza la opción "Generar reporte",
            o accede directamente a <code>/reports/employee/CODIGO_EMPLEADO</code>.
          </p>
        </div>
      </section>
    </div>
  );
}

export default ReportsPage;
