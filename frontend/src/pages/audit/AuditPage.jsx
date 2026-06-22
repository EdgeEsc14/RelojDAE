import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileSearch,
  LockKeyhole,
  Search,
  ShieldAlert,
  SlidersHorizontal,
  XCircle,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  mockAuditLogs,
  mockAuditSummary,
  mockCriticalEvents,
} from "../../data/mockAudit";

function getResultClass(result) {
  if (result === "Correcto") return "badge success";
  if (result === "Advertencia") return "badge warning";
  if (result === "Bloqueado") return "badge danger";
  if (result === "Error") return "badge danger";
  return "badge neutral";
}

function getRiskClass(risk) {
  if (risk === "Alto") return "badge danger";
  if (risk === "Medio") return "badge warning";
  if (risk === "Bajo") return "badge success";
  return "badge neutral";
}

function getSummaryIcon(label) {
  if (label === "Eventos correctos") return CheckCircle2;
  if (label === "Advertencias") return AlertTriangle;
  if (label === "Bloqueados") return XCircle;
  return ShieldAlert;
}

function AuditPage() {
  return (
    <div className="page-stack">
      <PageHeader
        title="Auditoría"
        description="Bitácora de acciones, cambios, accesos, sincronizaciones y eventos sensibles del sistema."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button">
            <Download size={17} />
            Exportar bitácora
          </button>

          <button className="primary-button" type="button">
            <FileSearch size={17} />
            Generar revisión
          </button>
        </div>
      </PageHeader>

      <section className="metrics-grid four-columns">
        {mockAuditSummary.map((item) => {
          const Icon = getSummaryIcon(item.label);

          return (
            <article className="metric-card" key={item.id}>
              <div className="metric-icon">
                <Icon size={22} />
              </div>

              <div>
                <p>{item.label}</p>
                <strong>{item.value}</strong>
                <span>{item.detail}</span>
              </div>
            </article>
          );
        })}
      </section>

      <section className="warning-banner">
        <LockKeyhole size={22} />
        <div>
          <strong>Registro de auditoría no editable</strong>
          <p>
            La bitácora debe funcionar como evidencia técnica y administrativa.
            Los eventos registrados no deben modificarse ni eliminarse desde la
            interfaz del sistema.
          </p>
        </div>
      </section>

      <section className="audit-grid">
        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Eventos críticos monitoreados</h3>
              <p>Acciones sensibles que deben quedar registradas.</p>
            </div>
            <ShieldAlert size={22} />
          </div>

          <div className="critical-event-list">
            {mockCriticalEvents.map((event) => (
              <article className="critical-event-card" key={event.id}>
                <div>
                  <h4>{event.title}</h4>
                  <p>{event.description}</p>
                </div>

                <div className="critical-event-meta">
                  <span className={getRiskClass(event.risk)}>{event.risk}</span>
                  <strong>{event.module}</strong>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Controles recomendados</h3>
              <p>Reglas mínimas para trazabilidad y seguridad.</p>
            </div>
            <LockKeyhole size={22} />
          </div>

          <div className="audit-control-list">
            <div>
              <span>Checadas crudas</span>
              <strong>Solo lectura; no edición directa</strong>
            </div>

            <div>
              <span>Incidencias</span>
              <strong>Aprobación/rechazo con usuario y fecha</strong>
            </div>

            <div>
              <span>Dispositivos</span>
              <strong>Registrar cada sincronización con resultado</strong>
            </div>

            <div>
              <span>Usuarios</span>
              <strong>Registrar altas, bloqueos y cambios de rol</strong>
            </div>

            <div>
              <span>Reportes</span>
              <strong>Registrar exportaciones PDF/Excel</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Bitácora de eventos</h3>
            <p>Registro cronológico de operaciones realizadas en el sistema.</p>
          </div>
        </div>

        <div className="filters-row">
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por usuario, módulo, acción, folio, resultado o IP..."
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
                <th>Evento</th>
                <th>Fecha/hora</th>
                <th>Usuario</th>
                <th>Rol</th>
                <th>Módulo</th>
                <th>Acción</th>
                <th>Entidad</th>
                <th>Resultado</th>
                <th>IP</th>
                <th>Detalle</th>
              </tr>
            </thead>

            <tbody>
              {mockAuditLogs.map((log) => (
                <tr key={log.id}>
                  <td>
                    <strong>{log.eventId}</strong>
                  </td>

                  <td>{log.timestamp}</td>

                  <td>
                    <strong>{log.user}</strong>
                  </td>

                  <td>{log.role}</td>
                  <td>{log.module}</td>
                  <td>{log.action}</td>

                  <td>
                    <strong>{log.entity}</strong>
                    <span className="table-subtext">{log.entityId}</span>
                  </td>

                  <td>
                    <span className={getResultClass(log.result)}>
                      {log.result}
                    </span>
                  </td>

                  <td>{log.ipAddress}</td>
                  <td>{log.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mobile-card-list">
          {mockAuditLogs.map((log) => (
            <article className="mobile-data-card" key={`${log.id}-mobile`}>
              <h4>{log.eventId}</h4>
              <p>{log.detail}</p>

              <div className="mobile-data-grid">
                <div>
                  <span>Fecha/hora</span>
                  <strong>{log.timestamp}</strong>
                </div>

                <div>
                  <span>Usuario</span>
                  <strong>{log.user}</strong>
                </div>

                <div>
                  <span>Rol</span>
                  <strong>{log.role}</strong>
                </div>

                <div>
                  <span>Módulo</span>
                  <strong>{log.module}</strong>
                </div>

                <div>
                  <span>Acción</span>
                  <strong>{log.action}</strong>
                </div>

                <div>
                  <span>Resultado</span>
                  <strong>{log.result}</strong>
                </div>

                <div>
                  <span>IP</span>
                  <strong>{log.ipAddress}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default AuditPage;