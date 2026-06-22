import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  FileWarning,
  Save,
  UserRound,
  XCircle,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { mockIncidents } from "../../data/mockIncidents";

function getStatusClass(status) {
  if (status === "Pendiente") return "badge warning";
  if (status === "Aprobada") return "badge success";
  if (status === "Rechazada") return "badge danger";
  if (status === "Sin justificar") return "badge danger";
  return "badge neutral";
}

function IncidentDetailPage() {
  const { incidentId } = useParams();

  const incident = mockIncidents.find((item) => item.id === Number(incidentId));

  if (!incident) {
    return (
      <div className="page-stack">
        <PageHeader
          title="Incidencia no encontrada"
          description="No existe una incidencia con el identificador solicitado."
        />

        <Link className="secondary-button link-button fit-content" to="/incidents">
          <ArrowLeft size={17} />
          Volver a incidencias
        </Link>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <PageHeader
        title={incident.folio}
        description="Detalle de incidencia, evidencia de asistencia y resolución administrativa."
      >
        <div className="header-actions">
          <Link className="secondary-button link-button" to="/incidents">
            <ArrowLeft size={17} />
            Volver
          </Link>

          <button className="primary-button" type="button">
            <Save size={17} />
            Guardar resolución
          </button>
        </div>
      </PageHeader>

      <section className="incident-detail-grid">
        <article className="panel-card incident-main-card">
          <div className="incident-title-row">
            <div className="incident-icon">
              <FileWarning size={26} />
            </div>

            <div>
              <h3>{incident.type}</h3>
              <p>{incident.reason}</p>
            </div>
          </div>

          <div className="incident-status-row">
            <span className={getStatusClass(incident.status)}>
              {incident.status}
            </span>
            <span className="badge neutral">Prioridad {incident.priority}</span>
            <span className="badge neutral">Origen {incident.generatedBy}</span>
          </div>
        </article>

        <article className="panel-card employee-profile-card">
          <div className="large-avatar">
            <UserRound size={42} />
          </div>

          <h3>{incident.employeeName}</h3>
          <p>{incident.department}</p>

          <div className="profile-badges">
            <span className="badge neutral">{incident.employeeCode}</span>
            <span className="badge neutral">{incident.date}</span>
          </div>
        </article>
      </section>

      <section className="metrics-grid three-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>
          <div>
            <p>Horario esperado</p>
            <strong className="metric-text">{incident.expectedSchedule}</strong>
            <span>Jornada asignada</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <p>Entrada / Salida</p>
            <strong className="metric-text">
              {incident.entryTime || "—"} / {incident.exitTime || "—"}
            </strong>
            <span>Registros del día</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>
          <div>
            <p>Tiempo extra</p>
            <strong>{incident.extraTime}</strong>
            <span>
              {incident.extraStart || "Sin inicio"} - {incident.extraEnd || "Sin fin"}
            </span>
          </div>
        </article>
      </section>

      <section className="incident-review-grid">
        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Datos de la incidencia</h3>
              <p>Información generada por el sistema o capturada manualmente.</p>
            </div>
          </div>

          <div className="info-grid">
            <div>
              <span>Folio</span>
              <strong>{incident.folio}</strong>
            </div>

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
              <span>Estatus</span>
              <strong>{incident.status}</strong>
            </div>

            <div>
              <span>Fuente</span>
              <strong>{incident.source}</strong>
            </div>

            <div>
              <span>Solicitado por</span>
              <strong>{incident.requestedBy}</strong>
            </div>

            <div>
              <span>Revisado por</span>
              <strong>{incident.reviewedBy || "Pendiente"}</strong>
            </div>

            <div>
              <span>Fecha de revisión</span>
              <strong>{incident.reviewedAt || "Pendiente"}</strong>
            </div>
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Resolución administrativa</h3>
              <p>Captura visual para aprobar, rechazar o justificar.</p>
            </div>
          </div>

          <div className="form-section">
            <div className="form-grid one-column">
              <label>
                Estatus de resolución
                <select defaultValue={incident.status}>
                  <option>Pendiente</option>
                  <option>Aprobada</option>
                  <option>Rechazada</option>
                  <option>Sin justificar</option>
                </select>
              </label>

              <label>
                Tratamiento / Justificación
                <textarea
                  rows="6"
                  placeholder="Escribe la justificación, resolución o comentario administrativo..."
                  defaultValue={incident.justification}
                />
              </label>

              <label>
                Observaciones internas
                <textarea
                  rows="4"
                  placeholder="Notas internas para RH o Super Admin..."
                />
              </label>
            </div>

            <div className="incident-actions">
              <button className="secondary-button" type="button">
                <XCircle size={17} />
                Rechazar
              </button>

              <button className="primary-button" type="button">
                <CheckCircle2 size={17} />
                Aprobar
              </button>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}

export default IncidentDetailPage;