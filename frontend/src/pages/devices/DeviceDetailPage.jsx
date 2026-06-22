import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  Database,
  Fingerprint,
  PlugZap,
  RefreshCcw,
  Server,
  UserRound,
  Wifi,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  mockConnectionChecks,
  mockDevices,
  mockDeviceUsers,
  mockSyncLogs,
} from "../../data/mockDevices";

function getStatusClass(status) {
  if (status === "Conectado") return "badge success";
  if (status === "Correcto") return "badge success";
  if (status === "Advertencia") return "badge warning";
  if (status === "Revisar") return "badge warning";
  if (status === "Desconectado") return "badge danger";
  return "badge neutral";
}

function DeviceDetailPage() {
  const { deviceId } = useParams();

  const device = mockDevices.find((item) => item.id === Number(deviceId));

  if (!device) {
    return (
      <div className="page-stack">
        <PageHeader
          title="Dispositivo no encontrado"
          description="No existe un reloj checador con el identificador solicitado."
        />

        <Link className="secondary-button link-button fit-content" to="/devices">
          <ArrowLeft size={17} />
          Volver a dispositivos
        </Link>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <PageHeader
        title={device.name}
        description="Detalle técnico del reloj checador, conexión pyzk, usuarios y sincronizaciones."
      >
        <div className="header-actions">
          <Link className="secondary-button link-button" to="/devices">
            <ArrowLeft size={17} />
            Volver
          </Link>

          <button className="secondary-button" type="button">
            <PlugZap size={17} />
            Probar conexión
          </button>

          <button className="primary-button" type="button">
            <RefreshCcw size={17} />
            Sincronizar ahora
          </button>
        </div>
      </PageHeader>

      <section className="device-detail-grid">
        <article className="panel-card device-hero-card">
          <div className="device-hero-icon">
            <Fingerprint size={44} />
          </div>

          <div>
            <span className={getStatusClass(device.status)}>{device.status}</span>
            <h3>{device.name}</h3>
            <p>{device.notes}</p>
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Configuración de conexión</h3>
              <p>Parámetros utilizados por el servicio pyzk.</p>
            </div>
          </div>

          <div className="info-grid">
            <div>
              <span>IP</span>
              <strong>{device.ipAddress}</strong>
            </div>

            <div>
              <span>Puerto</span>
              <strong>{device.port}</strong>
            </div>

            <div>
              <span>Comm key</span>
              <strong>{device.commKey}</strong>
            </div>

            <div>
              <span>Modo</span>
              <strong>{device.syncMode}</strong>
            </div>

            <div>
              <span>Número de serie</span>
              <strong>{device.serialNumber}</strong>
            </div>

            <div>
              <span>Firmware</span>
              <strong>{device.firmware}</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <UserRound size={22} />
          </div>
          <div>
            <p>Usuarios leídos</p>
            <strong>{device.usersRead}</strong>
            <span>Usuarios registrados en reloj</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Database size={22} />
          </div>
          <div>
            <p>Checadas históricas</p>
            <strong>{device.punchesRead}</strong>
            <span>Registros descargados</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <RefreshCcw size={22} />
          </div>
          <div>
            <p>Último lote</p>
            <strong>{device.lastSyncRecords}</strong>
            <span>Registros nuevos</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Wifi size={22} />
          </div>
          <div>
            <p>Última sync</p>
            <strong className="metric-text">{device.lastSyncAt}</strong>
            <span>Fecha de sincronización</span>
          </div>
        </article>
      </section>

      <section className="device-panels-grid">
        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Diagnóstico de conexión</h3>
              <p>Validaciones esperadas antes de leer checadas.</p>
            </div>
            <Server size={22} />
          </div>

          <div className="simple-table desktop-table">
            <table>
              <thead>
                <tr>
                  <th>Prueba</th>
                  <th>Resultado</th>
                  <th>Detalle</th>
                </tr>
              </thead>

              <tbody>
                {mockConnectionChecks.map((row) => (
                  <tr key={row.check}>
                    <td>{row.check}</td>
                    <td>
                      <span className={getStatusClass(row.result)}>
                        {row.result}
                      </span>
                    </td>
                    <td>{row.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mobile-card-list">
            {mockConnectionChecks.map((row) => (
              <article className="mobile-data-card" key={`${row.check}-mobile`}>
                <h4>{row.check}</h4>
                <p>{row.detail}</p>

                <div className="mobile-data-grid">
                  <div>
                    <span>Resultado</span>
                    <strong>{row.result}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Usuarios del reloj</h3>
              <p>Usuarios leídos desde el dispositivo.</p>
            </div>
            <UserRound size={22} />
          </div>

          <div className="simple-table desktop-table">
            <table>
              <thead>
                <tr>
                  <th>ZK User ID</th>
                  <th>UID</th>
                  <th>Nombre</th>
                  <th>Privilegio</th>
                  <th>Grupo</th>
                  <th>Estatus</th>
                </tr>
              </thead>

              <tbody>
                {mockDeviceUsers.map((user) => (
                  <tr key={user.id}>
                    <td>{user.zkUserId}</td>
                    <td>{user.uid}</td>
                    <td>{user.name}</td>
                    <td>{user.privilege}</td>
                    <td>{user.groupId}</td>
                    <td>
                      <span className="badge success">{user.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mobile-card-list">
            {mockDeviceUsers.map((user) => (
              <article className="mobile-data-card" key={`${user.id}-mobile`}>
                <h4>{user.name}</h4>
                <p>Usuario ZKTeco {user.zkUserId}</p>

                <div className="mobile-data-grid">
                  <div>
                    <span>UID</span>
                    <strong>{user.uid}</strong>
                  </div>
                  <div>
                    <span>Privilegio</span>
                    <strong>{user.privilege}</strong>
                  </div>
                  <div>
                    <span>Grupo</span>
                    <strong>{user.groupId}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Historial de sincronización</h3>
            <p>Corridas de lectura ejecutadas contra el dispositivo.</p>
          </div>

          <CheckCircle2 size={22} />
        </div>

        <div className="simple-table desktop-table">
          <table>
            <thead>
              <tr>
                <th>Sync Run</th>
                <th>Inicio</th>
                <th>Fin</th>
                <th>Estatus</th>
                <th>Usuarios</th>
                <th>Checadas</th>
                <th>Insertados</th>
                <th>Duplicados</th>
                <th>Mensaje</th>
              </tr>
            </thead>

            <tbody>
              {mockSyncLogs.map((log) => (
                <tr key={log.id}>
                  <td>
                    <strong>{log.syncRun}</strong>
                  </td>
                  <td>{log.startedAt}</td>
                  <td>{log.finishedAt}</td>
                  <td>
                    <span className={getStatusClass(log.status)}>
                      {log.status}
                    </span>
                  </td>
                  <td>{log.usersRead}</td>
                  <td>{log.punchesRead}</td>
                  <td>{log.insertedRecords}</td>
                  <td>{log.duplicatedRecords}</td>
                  <td>{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mobile-card-list">
          {mockSyncLogs.map((log) => (
            <article className="mobile-data-card" key={`${log.id}-mobile`}>
              <h4>{log.syncRun}</h4>
              <p>{log.message}</p>

              <div className="mobile-data-grid">
                <div>
                  <span>Estatus</span>
                  <strong>{log.status}</strong>
                </div>
                <div>
                  <span>Inicio</span>
                  <strong>{log.startedAt}</strong>
                </div>
                <div>
                  <span>Fin</span>
                  <strong>{log.finishedAt}</strong>
                </div>
                <div>
                  <span>Insertados</span>
                  <strong>{log.insertedRecords}</strong>
                </div>
                <div>
                  <span>Duplicados</span>
                  <strong>{log.duplicatedRecords}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default DeviceDetailPage;