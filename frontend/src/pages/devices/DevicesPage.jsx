import { Link } from "react-router-dom";

import ZkUsersPanel from "../../components/devices/ZkUsersPanel";
import {
  Activity,
  Database,
  Eye,
  Fingerprint,
  Plus,
  RefreshCcw,
  Search,
  Server,
  SlidersHorizontal,
  Wifi,
  WifiOff,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { mockDevices } from "../../data/mockDevices";

function getDeviceStatusClass(status) {
  if (status === "Conectado") return "badge success";
  if (status === "Revisar") return "badge warning";
  if (status === "Desconectado") return "badge danger";
  return "badge neutral";
}

function DevicesPage() {
  const connected = mockDevices.filter(
    (device) => device.status === "Conectado"
  ).length;

  const warning = mockDevices.filter((device) => device.status === "Revisar").length;

  const disconnected = mockDevices.filter(
    (device) => device.status === "Desconectado"
  ).length;

  const totalPunches = mockDevices.reduce(
    (sum, device) => sum + device.punchesRead,
    0
  );

  return (
    <div className="page-stack">
      <PageHeader
        title="Dispositivos ZKTeco"
        description="Administración visual de relojes checadores, conexión pyzk, sincronización y estado operativo."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button">
            <RefreshCcw size={17} />
            Sincronizar todos
          </button>

          <button className="primary-button" type="button">
            <Plus size={17} />
            Nuevo dispositivo
          </button>
        </div>
      </PageHeader>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Server size={22} />
          </div>
          <div>
            <p>Dispositivos</p>
            <strong>{mockDevices.length}</strong>
            <span>Relojes registrados</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Wifi size={22} />
          </div>
          <div>
            <p>Conectados</p>
            <strong>{connected}</strong>
            <span>Responden correctamente</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <WifiOff size={22} />
          </div>
          <div>
            <p>Con alerta</p>
            <strong>{warning + disconnected}</strong>
            <span>Requieren revisión</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Database size={22} />
          </div>
          <div>
            <p>Checadas leídas</p>
            <strong>{totalPunches}</strong>
            <span>Histórico visible</span>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="filters-row">
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por nombre, IP, serie, ubicación o estatus..."
            />
          </div>

          <button className="secondary-button" type="button">
            <SlidersHorizontal size={17} />
            Filtros
          </button>
        </div>

        <div className="device-card-grid">
          {mockDevices.map((device) => (
            <article className="device-card" key={device.id}>
              <div className="device-card-header">
                <div className="device-card-icon">
                  <Fingerprint size={26} />
                </div>

                <div>
                  <h3>{device.name}</h3>
                  <p>{device.location}</p>
                </div>

                <span className={getDeviceStatusClass(device.status)}>
                  {device.status}
                </span>
              </div>

              <div className="device-info-grid">
                <div>
                  <span>IP</span>
                  <strong>{device.ipAddress}</strong>
                </div>

                <div>
                  <span>Puerto</span>
                  <strong>{device.port}</strong>
                </div>

                <div>
                  <span>Modelo</span>
                  <strong>{device.model}</strong>
                </div>

                <div>
                  <span>Modo</span>
                  <strong>{device.syncMode}</strong>
                </div>

                <div>
                  <span>Usuarios</span>
                  <strong>{device.usersRead}</strong>
                </div>

                <div>
                  <span>Checadas</span>
                  <strong>{device.punchesRead}</strong>
                </div>
              </div>

              <div className="device-card-footer">
                <div>
                  <span>Última sincronización</span>
                  <strong>{device.lastSyncAt}</strong>
                </div>

                <Link className="primary-button link-button" to={`/devices/${device.id}`}>
                  <Eye size={16} />
                  Ver detalle
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="warning-banner">
        <Activity size={22} />
        <div>
          <strong>Comunicación por pyzk</strong>
          <p>
            La vista está preparada para que el backend ejecute pruebas de conexión,
            lectura de usuarios y descarga de checadas mediante IP, puerto 4370 y
            clave de comunicación del dispositivo.
          </p>
        </div>
      </section>

      <ZkUsersPanel />
    </div>
  );
}

export default DevicesPage;