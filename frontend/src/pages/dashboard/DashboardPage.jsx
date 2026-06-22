import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Fingerprint,
  UserCheck,
  Users,
} from "lucide-react";
import PageHeader from "../../components/layout/PageHeader";
import MetricCard from "../../components/ui/MetricCard";
import DashboardChartPanel from "../../components/charts/DashboardChartPanel";
const metrics = [
  {
    title: "Empleados activos",
    value: "86",
    detail: "4 departamentos registrados",
    icon: Users,
  },
  {
    title: "Presentes hoy",
    value: "72",
    detail: "83.7% de asistencia",
    icon: UserCheck,
  },
  {
    title: "Retardos hoy",
    value: "6",
    detail: "2 pendientes de justificar",
    icon: Clock,
  },
  {
    title: "Incidencias pendientes",
    value: "9",
    detail: "Requieren revisión de RH",
    icon: AlertTriangle,
  },
];

const recentPunches = [
  {
    employee: "HIPOLITO BARRETO AYALA",
    area: "Departamento de Certificación",
    time: "07:58:00",
    type: "Entrada",
    device: "Reloj principal",
  },
  {
    employee: "MARÍA LÓPEZ RAMÍREZ",
    area: "Administración",
    time: "08:04:12",
    type: "Entrada",
    device: "Reloj principal",
  },
  {
    employee: "JOSÉ HERNÁNDEZ CRUZ",
    area: "Operaciones",
    time: "08:13:44",
    type: "Entrada con retardo",
    device: "Reloj acceso norte",
  },
  {
    employee: "ANA GARCÍA TORRES",
    area: "Recursos Humanos",
    time: "15:03:00",
    type: "Salida",
    device: "Reloj principal",
  },
];

const pendingIncidents = [
  {
    employee: "HIPOLITO BARRETO AYALA",
    date: "06/05/2026",
    type: "Tiempo extra",
    status: "Pendiente",
  },
  {
    employee: "JOSÉ HERNÁNDEZ CRUZ",
    date: "08/05/2026",
    type: "Retardo",
    status: "Pendiente",
  },
  {
    employee: "LAURA MARTÍNEZ DÍAZ",
    date: "09/05/2026",
    type: "Omisión de salida",
    status: "Pendiente",
  },
];

function DashboardPage() {
  return (
    <div className="page-stack">
      <PageHeader
        title="Dashboard Super Admin"
        description="Resumen general de asistencia, incidencias, dispositivos y sincronización."
      >
        <button className="primary-button" type="button">
          Sincronizar relojes
        </button>
      </PageHeader>

      <section className="metrics-grid">
        {metrics.map((metric) => {
          const Icon = metric.icon;

          return (
            <MetricCard
              icon={Users}
              title="Empleados activos"
              value="86"
              description="4 departamentos registrados"
            />
          );
        })}
      </section>
      <DashboardChartPanel />
      <section className="dashboard-grid">
        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Estado de dispositivos</h3>
              <p>Conexión actual de relojes ZKTeco</p>
            </div>
            <Fingerprint size={22} />
          </div>

          <div className="device-list">
            <div className="device-row">
              <div>
                <strong>Reloj principal</strong>
                <span>192.168.1.201:4370</span>
              </div>
              <span className="status-pill success">
                <CheckCircle2 size={14} />
                Conectado
              </span>
            </div>

            <div className="device-row">
              <div>
                <strong>Reloj acceso norte</strong>
                <span>192.168.1.202:4370</span>
              </div>
              <span className="status-pill warning">
                <AlertTriangle size={14} />
                Revisar
              </span>
            </div>
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Incidencias pendientes</h3>
              <p>Revisión administrativa requerida</p>
            </div>
          </div>

          <div className="simple-table">
            <table>
              <thead>
                <tr>
                  <th>Empleado</th>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Estatus</th>
                </tr>
              </thead>
              <tbody>
                {pendingIncidents.map((incident) => (
                  <tr key={`${incident.employee}-${incident.date}`}>
                    <td>{incident.employee}</td>
                    <td>{incident.date}</td>
                    <td>{incident.type}</td>
                    <td>
                      <span className="badge pending">{incident.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Últimas checadas</h3>
            <p>Eventos recientes recibidos desde los dispositivos</p>
          </div>
        </div>

        <div className="simple-table">
          <table>
            <thead>
              <tr>
                <th>Empleado</th>
                <th>Área</th>
                <th>Hora</th>
                <th>Evento</th>
                <th>Dispositivo</th>
              </tr>
            </thead>
            <tbody>
              {recentPunches.map((punch) => (
                <tr key={`${punch.employee}-${punch.time}`}>
                  <td>{punch.employee}</td>
                  <td>{punch.area}</td>
                  <td>{punch.time}</td>
                  <td>{punch.type}</td>
                  <td>{punch.device}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default DashboardPage;