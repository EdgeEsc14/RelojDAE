import {
  Database,
  Download,
  Fingerprint,
  LockKeyhole,
  Search,
  SlidersHorizontal,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { mockRawPunches } from "../../data/mockAttendance";

function AttendanceRawPage() {
  return (
    <div className="page-stack">
      <PageHeader
        title="Checadas crudas"
        description="Registros originales recibidos desde los relojes ZKTeco. Estos datos deben conservarse sin modificación."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button">
            <Download size={17} />
            Exportar raw
          </button>

          <button className="primary-button" type="button">
            <Database size={17} />
            Sincronizar ahora
          </button>
        </div>
      </PageHeader>

      <section className="warning-banner">
        <LockKeyhole size={22} />
        <div>
          <strong>Registro inmutable</strong>
          <p>
            Esta vista representa la evidencia original descargada del reloj.
            No debe editarse ni eliminarse; cualquier corrección debe realizarse
            mediante incidencias o reprocesamiento.
          </p>
        </div>
      </section>

      <section className="metrics-grid three-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Database size={22} />
          </div>
          <div>
            <p>Checadas crudas</p>
            <strong>{mockRawPunches.length}</strong>
            <span>Registros originales visibles</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Fingerprint size={22} />
          </div>
          <div>
            <p>Dispositivos origen</p>
            <strong>2</strong>
            <span>Relojes ZKTeco identificados</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <LockKeyhole size={22} />
          </div>
          <div>
            <p>Modo auditoría</p>
            <strong>Activo</strong>
            <span>Datos solo lectura</span>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="filters-row">
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por dispositivo, usuario ZK, empleado, fecha o corrida de sincronización..."
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
                <th>ID Raw</th>
                <th>Dispositivo</th>
                <th>Usuario ZK</th>
                <th>Empleado</th>
                <th>Fecha/hora</th>
                <th>Tipo</th>
                <th>Código</th>
                <th>Verificación</th>
                <th>Sync</th>
                <th>Estatus</th>
              </tr>
            </thead>

            <tbody>
              {mockRawPunches.map((row) => (
                <tr key={row.id}>
                  <td>
                    <strong>RAW-{row.id}</strong>
                  </td>
                  <td>
                    <strong>{row.deviceName}</strong>
                    <span className="table-subtext">{row.deviceIp}</span>
                  </td>
                  <td>{row.zkUserId}</td>
                  <td>{row.employeeName}</td>
                  <td>{row.punchTime}</td>
                  <td>{row.punchType}</td>
                  <td>{row.statusCode}</td>
                  <td>{row.verificationMode}</td>
                  <td>{row.syncRun}</td>
                  <td>
                    <span className="badge neutral">{row.rawStatus}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mobile-card-list">
          {mockRawPunches.map((row) => (
            <article className="mobile-data-card" key={`${row.id}-mobile`}>
              <h4>RAW-{row.id}</h4>
              <p>{row.employeeName}</p>

              <div className="mobile-data-grid">
                <div>
                  <span>Dispositivo</span>
                  <strong>{row.deviceName}</strong>
                </div>
                <div>
                  <span>IP</span>
                  <strong>{row.deviceIp}</strong>
                </div>
                <div>
                  <span>Usuario ZK</span>
                  <strong>{row.zkUserId}</strong>
                </div>
                <div>
                  <span>Fecha/hora</span>
                  <strong>{row.punchTime}</strong>
                </div>
                <div>
                  <span>Tipo</span>
                  <strong>{row.punchType}</strong>
                </div>
                <div>
                  <span>Verificación</span>
                  <strong>{row.verificationMode}</strong>
                </div>
                <div>
                  <span>Sync</span>
                  <strong>{row.syncRun}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default AttendanceRawPage;