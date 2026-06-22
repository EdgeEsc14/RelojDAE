import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Download,
  Eye,
  FileWarning,
  Plus,
  Search,
  SlidersHorizontal,
  XCircle,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import StatusBadge from "../../components/ui/StatusBadge";
import { mockIncidents } from "../../data/mockIncidents";



function IncidentsPage() {
  const total = mockIncidents.length;
  const pending = mockIncidents.filter((item) => item.status === "Pendiente").length;
  const approved = mockIncidents.filter((item) => item.status === "Aprobada").length;
  const unjustified = mockIncidents.filter(
    (item) => item.status === "Sin justificar"
  ).length;

  return (
    <div className="page-stack">
      <PageHeader
        title="Incidencias"
        description="Gestión de faltas, retardos, omisiones, permisos, vacaciones y tiempo extra."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button">
            <Download size={17} />
            Exportar
          </button>

          <button className="primary-button" type="button">
            <Plus size={17} />
            Nueva incidencia
          </button>
        </div>
      </PageHeader>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <FileWarning size={22} />
          </div>
          <div>
            <p>Total incidencias</p>
            <strong>{total}</strong>
            <span>Periodo visible</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>
          <div>
            <p>Pendientes</p>
            <strong>{pending}</strong>
            <span>Requieren revisión</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <p>Aprobadas</p>
            <strong>{approved}</strong>
            <span>Con autorización</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <XCircle size={22} />
          </div>
          <div>
            <p>Sin justificar</p>
            <strong>{unjustified}</strong>
            <span>Atención requerida</span>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="filters-row">
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por folio, empleado, área, tipo, estatus o fecha..."
            />
          </div>

          <button className="secondary-button" type="button">
            <SlidersHorizontal size={17} />
            Filtros
          </button>
        </div>

        <div className="simple-table desktop-table">
          <table>
            <thead>
              <tr>
                <th>Folio</th>
                <th>Empleado</th>
                <th>Fecha</th>
                <th>Tipo</th>
                <th>Prioridad</th>
                <th>Estatus</th>
                <th>Origen</th>
                <th>Fuente</th>
                <th>Acciones</th>
              </tr>
            </thead>

            <tbody>
              {mockIncidents.map((incident) => (
                <tr key={incident.id}>
                  <td>
                    <strong>{incident.folio}</strong>
                  </td>

                  <td>
                    <div className="employee-cell">
                      <div className="employee-avatar">
                        {incident.employeeName.charAt(0)}
                      </div>
                      <div>
                        <strong>{incident.employeeName}</strong>
                        <span>{incident.department}</span>
                      </div>
                    </div>
                  </td>

                  <td>
                    <strong>{incident.date}</strong>
                    <span className="table-subtext">{incident.day}</span>
                  </td>

                  <td>{incident.type}</td>

                  <td>
                    <StatusBadge status={incident.priority} />
                  </td>

                  <td>
                    <StatusBadge status={incident.status} />
                  </td>

                  <td>{incident.generatedBy}</td>
                  <td>{incident.source}</td>

                  <td>
                    <Link
                      className="table-action"
                      to={`/incidents/${incident.id}`}
                    >
                      <Eye size={16} />
                      Revisar
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mobile-card-list">
          {mockIncidents.map((incident) => (
            <article className="mobile-data-card" key={`${incident.id}-mobile`}>
              <h4>{incident.folio}</h4>
              <p>{incident.employeeName}</p>

              <div className="mobile-data-grid">
                <div>
                  <span>Fecha</span>
                  <strong>
                    {incident.date} / {incident.day}
                  </strong>
                </div>

                <div>
                  <span>Tipo</span>
                  <strong>{incident.type}</strong>
                </div>

                <div>
                  <span>Prioridad</span>
                  <strong>{incident.priority}</strong>
                </div>

                <div>
                  <span>Estatus</span>
                  <strong>{incident.status}</strong>
                </div>

                <div>
                  <span>Fuente</span>
                  <strong>{incident.source}</strong>
                </div>
              </div>

              <Link
                className="primary-button link-button mobile-card-action"
                to={`/incidents/${incident.id}`}
              >
                <Eye size={16} />
                Revisar incidencia
              </Link>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default IncidentsPage;