import { Link } from "react-router-dom";
import {
  BarChart3,
  Download,
  FileSpreadsheet,
  FileText,
  Search,
  SlidersHorizontal,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { mockReportCards } from "../../data/mockReports";

function ReportsPage() {
  return (
    <div className="page-stack">
      <PageHeader
        title="Reportes"
        description="Centro de reportes operativos, administrativos, consolidados y de auditoría."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button">
            <Download size={17} />
            Exportaciones
          </button>

          <button className="primary-button" type="button">
            <FileText size={17} />
            Generar reporte
          </button>
        </div>
      </PageHeader>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <FileText size={22} />
          </div>
          <div>
            <p>Reportes disponibles</p>
            <strong>4</strong>
            <span>Plantillas principales</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <FileSpreadsheet size={22} />
          </div>
          <div>
            <p>Formatos</p>
            <strong>PDF / Excel</strong>
            <span>Exportación operativa</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <BarChart3 size={22} />
          </div>
          <div>
            <p>Periodo activo</p>
            <strong>Mayo 2026</strong>
            <span>01/05/2026 - 15/05/2026</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Download size={22} />
          </div>
          <div>
            <p>Exportaciones</p>
            <strong>12</strong>
            <span>Generadas este mes</span>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="filters-row">
          <div className="filter-search">
            <Search size={18} />
            <input type="text" placeholder="Buscar reporte por nombre, módulo o categoría..." />
          </div>

          <button className="secondary-button" type="button">
            <SlidersHorizontal size={17} />
            Filtros
          </button>
        </div>

        <div className="report-card-grid">
          {mockReportCards.map((report) => (
            <Link className="report-card" to={report.path} key={report.id}>
              <div className="report-card-icon">
                <FileText size={24} />
              </div>

              <div>
                <span className="badge neutral">{report.category}</span>
                <h3>{report.title}</h3>
                <p>{report.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

export default ReportsPage;