import { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Database,
  Fingerprint,
  RefreshCw,
  UserCheck,
  Users,
} from "lucide-react";

import { dashboardApi } from "../../api/dashboardApi";
import PageHeader from "../../components/layout/PageHeader";
import MetricCard from "../../components/ui/MetricCard";

function formatNumber(value) {
  return Number(value ?? 0).toLocaleString("es-MX");
}

function formatDateTime(value) {
  if (!value) return "Sin registros";

  try {
    return new Intl.DateTimeFormat("es-MX", {
      dateStyle: "medium",
      timeStyle: "medium",
    }).format(new Date(value));
  } catch {
    return String(value);
  }
}

function safeText(value, fallback = "No disponible") {
  const text = String(value ?? "").trim();

  return text || fallback;
}
function formatShortDate(value) {
  if (!value) return "";

  try {
    return new Intl.DateTimeFormat("es-MX", {
      weekday: "short",
      day: "2-digit",
      month: "short",
    }).format(new Date(`${value}T00:00:00`));
  } catch {
    return String(value);
  }
}

function getMaxChartValue(rows) {
  const maxValue = Math.max(
    ...rows.map((row) => Number(row.total ?? 0)),
    1
  );

  return maxValue;
}
function getMaxValueByField(rows, fieldName) {
  return Math.max(
    ...rows.map((row) => Number(row[fieldName] ?? 0)),
    1
  );
}
function getBarWidth(value, maxValue) {
  const safeValue = Number(value ?? 0);

  if (safeValue <= 0) return "0%";

  return `${Math.max((safeValue / maxValue) * 100, 8)}%`;
}
function getPercent(value, total) {
  const safeValue = Number(value ?? 0);
  const safeTotal = Number(total ?? 0);

  if (safeTotal <= 0) return 0;

  return Math.round((safeValue / safeTotal) * 100);
}
function getPunchLabel(row) {
  return (
    row.punch_label ||
    row.status_label ||
    `Punch ${row.punch ?? "N/D"}`
  );
}

function DashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const data = await dashboardApi.obtenerResumen();

      setDashboard(data);
    } catch (err) {
      setError(
        err.message ||
          "No fue posible cargar el dashboard real."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const metrics = useMemo(() => {
    const empleados = dashboard?.empleados ?? {};
    const marcaciones = dashboard?.marcaciones ?? {};
    const dispositivos = dashboard?.dispositivos ?? {};
    const asistenciaHoy = dashboard?.asistencia_hoy ?? {};
    const retardosHoy =
      Number(asistenciaHoy.retardos_menores ?? 0) +
      Number(asistenciaHoy.retardos_mayores ?? 0);

    return [
      {
        title: "Empleados activos",
        value: formatNumber(empleados.activos),
        description: `${formatNumber(empleados.total)} empleados registrados`,
        icon: Users,
      },
      {
        title: "Asistencia procesada hoy",
        value: formatNumber(asistenciaHoy.total),
        description: `${formatNumber(asistenciaHoy.completos)} asistencias completas`,
        icon: CheckCircle2,
      },
      {
        title: "Faltas hoy",
        value: formatNumber(asistenciaHoy.faltas),
        description: `${formatNumber(asistenciaHoy.requieren_revision)} requieren revisión`,
        icon: AlertTriangle,
      },
      {
        title: "Retardos hoy",
        value: formatNumber(retardosHoy),
        description: `${formatNumber(asistenciaHoy.retardos_menores)} menores · ${formatNumber(asistenciaHoy.retardos_mayores)} mayores`,
        icon: Clock,
      },
      {
        title: "Puntos generados hoy",
        value: formatNumber(asistenciaHoy.puntos_generados),
        description: "Puntos acumulados por retardos del día",
        icon: UserCheck,
      },
      {
        title: "Marcaciones de hoy",
        value: formatNumber(marcaciones.hoy),
        description: `${formatNumber(marcaciones.total)} marcaciones crudas totales`,
        icon: Fingerprint,
      },
    ];
  }, [dashboard]);

  const ultimasMarcaciones =
    dashboard?.ultimas_marcaciones ?? [];

  const asistenciaHoy = dashboard?.asistencia_hoy ?? {};
  const alertas = dashboard?.alertas ?? {};

  const asistenciaUltimosDias =
    dashboard?.asistencia_ultimos_dias ?? [];

  const maxAsistenciaUltimosDias = getMaxChartValue(
    asistenciaUltimosDias
  );
  const topEmpleadosFaltas =
    dashboard?.top_empleados_faltas ?? [];

  const topEmpleadosRetardos =
    dashboard?.top_empleados_retardos ?? [];

  const maxTopEmpleadosFaltas = getMaxValueByField(
    topEmpleadosFaltas,
    "faltas"
  );

  const maxTopEmpleadosRetardos = getMaxValueByField(
    topEmpleadosRetardos,
    "total_retardos"
  );
  const retardosAsistenciaHoy =
    Number(asistenciaHoy.retardos_menores ?? 0) +
    Number(asistenciaHoy.retardos_mayores ?? 0);

  const departamentosIncidencias =
    dashboard?.departamentos_incidencias ?? [];

  const maxDepartamentosIncidencias = getMaxValueByField(
    departamentosIncidencias,
    "total_incidencias"
  );

  const totalAsistenciaHoy = Number(asistenciaHoy.total ?? 0);

  return (
    <div className="page-stack">
      <PageHeader
        title="Dashboard Super Admin"
        description="Resumen de empleados, asistencia, dispositivos y marcaciones sincronizadas desde BD."
      >
        <button
          className="primary-button"
          type="button"
          disabled={loading}
          onClick={loadDashboard}
        >
          <RefreshCw size={17} />
          {loading ? "Actualizando..." : "Actualizar"}
        </button>
      </PageHeader>

      {error && (
        <section className="panel-card">
          <div className="empty-state">
            <AlertTriangle size={42} />
            <h3>Error al cargar dashboard</h3>
            <p>{error}</p>
          </div>
        </section>
      )}

      {loading && !dashboard && (
        <section className="panel-card">
          <div className="empty-state">
            <Database size={42} />
            <h3>Cargando dashboard real</h3>
            <p>Consultando información desde PostgreSQL.</p>
          </div>
        </section>
      )}

      {dashboard && (
        <>
          <section className="metrics-grid">
            {metrics.map((metric) => (
              <MetricCard
                key={metric.title}
                icon={metric.icon}
                title={metric.title}
                value={metric.value}
                description={metric.description}
              />
            ))}
          </section>

          <section className="dashboard-grid">
            <article className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Resumen de empleados</h3>
                  <p>Estado actual del catálogo de personal.</p>
                </div>
                <Users size={22} />
              </div>

              <div className="info-grid">
                <div>
                  <span>Total</span>
                  <strong>
                    {formatNumber(dashboard.empleados.total)}
                  </strong>
                </div>

                <div>
                  <span>Activos</span>
                  <strong>
                    {formatNumber(dashboard.empleados.activos)}
                  </strong>
                </div>

                <div>
                  <span>Inactivos</span>
                  <strong>
                    {formatNumber(dashboard.empleados.inactivos)}
                  </strong>
                </div>

                <div>
                  <span>Sin usuario ZKTeco</span>
                  <strong>
                    {formatNumber(dashboard.empleados.sin_zk)}
                  </strong>
                </div>
              </div>
            </article>

            <article className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Estado de datos recibidos</h3>
                  <p>Marcaciones crudas almacenadas en PostgreSQL.</p>
                </div>
                <CheckCircle2 size={22} />
              </div>

              <div className="info-grid">
                <div>
                  <span>Marcaciones totales</span>
                  <strong>
                    {formatNumber(dashboard.marcaciones.total)}
                  </strong>
                </div>

                <div>
                  <span>Marcaciones de hoy</span>
                  <strong>
                    {formatNumber(dashboard.marcaciones.hoy)}
                  </strong>
                </div>

                <div>
                  <span>Última marcación</span>
                  <strong>
                    {formatDateTime(
                      dashboard.marcaciones.ultima_fecha_hora
                    )}
                  </strong>
                </div>

                <div>
                  <span>Dispositivos activos</span>
                  <strong>
                    {formatNumber(dashboard.dispositivos.activos)}
                  </strong>
                </div>
              </div>
            </article>
          </section>
          
          
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Asistencia procesada de hoy</h3>
                <p>
                  Resultado del procesamiento diario de entradas, salidas,
                  retardos, faltas y puntos.
                </p>
              </div>

              <CheckCircle2 size={22} />
            </div>

            <div className="info-grid">
              <div>
                <span>Total procesadas</span>
                <strong>
                  {formatNumber(asistenciaHoy.total)}
                </strong>
              </div>

              <div>
                <span>Completas</span>
                <strong>
                  {formatNumber(asistenciaHoy.completos)}
                </strong>
              </div>

              <div>
                <span>Retardos menores</span>
                <strong>
                  {formatNumber(asistenciaHoy.retardos_menores)}
                </strong>
              </div>

              <div>
                <span>Retardos mayores</span>
                <strong>
                  {formatNumber(asistenciaHoy.retardos_mayores)}
                </strong>
              </div>

              <div>
                <span>Faltas</span>
                <strong>
                  {formatNumber(asistenciaHoy.faltas)}
                </strong>
              </div>

              <div>
                <span>Requieren revisión</span>
                <strong>
                  {formatNumber(asistenciaHoy.requieren_revision)}
                </strong>
              </div>

              <div>
                <span>Puntos generados</span>
                <strong>
                  {formatNumber(asistenciaHoy.puntos_generados)}
                </strong>
              </div>
            </div>
          </section>

          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Distribución de asistencia de hoy</h3>
                <p>
                  Proporción de asistencias completas, retardos, faltas y
                  registros que requieren revisión.
                </p>
              </div>

              <CheckCircle2 size={22} />
            </div>

            <div className="status-distribution-grid">
              <div className="status-distribution-card">
                <div className="status-distribution-header">
                  <span>Completas</span>
                  <strong>{formatNumber(asistenciaHoy.completos)}</strong>
                </div>

                <div className="status-distribution-track">
                  <div
                    className="status-distribution-bar complete"
                    style={{
                      width: `${getPercent(
                        asistenciaHoy.completos,
                        totalAsistenciaHoy
                      )}%`,
                    }}
                  />
                </div>

                <small>
                  {getPercent(asistenciaHoy.completos, totalAsistenciaHoy)}%
                  del total procesado
                </small>
              </div>

              <div className="status-distribution-card">
                <div className="status-distribution-header">
                  <span>Retardos</span>
                  <strong>{formatNumber(retardosAsistenciaHoy)}</strong>
                </div>

                <div className="status-distribution-track">
                  <div
                    className="status-distribution-bar delay"
                    style={{
                      width: `${getPercent(
                        retardosAsistenciaHoy,
                        totalAsistenciaHoy
                      )}%`,
                    }}
                  />
                </div>

                <small>
                  {getPercent(retardosAsistenciaHoy, totalAsistenciaHoy)}%
                  del total procesado
                </small>
              </div>

              <div className="status-distribution-card">
                <div className="status-distribution-header">
                  <span>Faltas</span>
                  <strong>{formatNumber(asistenciaHoy.faltas)}</strong>
                </div>

                <div className="status-distribution-track">
                  <div
                    className="status-distribution-bar absence"
                    style={{
                      width: `${getPercent(
                        asistenciaHoy.faltas,
                        totalAsistenciaHoy
                      )}%`,
                    }}
                  />
                </div>

                <small>
                  {getPercent(asistenciaHoy.faltas, totalAsistenciaHoy)}%
                  del total procesado
                </small>
              </div>

              <div className="status-distribution-card">
                <div className="status-distribution-header">
                  <span>Revisión RH</span>
                  <strong>{formatNumber(asistenciaHoy.requieren_revision)}</strong>
                </div>

                <div className="status-distribution-track">
                  <div
                    className="status-distribution-bar review"
                    style={{
                      width: `${getPercent(
                        asistenciaHoy.requieren_revision,
                        totalAsistenciaHoy
                      )}%`,
                    }}
                  />
                </div>

                <small>
                  {getPercent(
                    asistenciaHoy.requieren_revision,
                    totalAsistenciaHoy
                  )}
                  % del total procesado
                </small>
              </div>
            </div>
          </section>


          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Alertas RH</h3>
                <p>
                  Situaciones que requieren revisión operativa o administrativa.
                </p>
              </div>

              <AlertTriangle size={22} />
            </div>

            <div className="info-grid">
              <div>
                <span>Empleados sin User ID ZKTeco</span>
                <strong>
                  {formatNumber(alertas.empleados_sin_zk)}
                </strong>
              </div>

              <div>
                <span>Empleados sin horario vigente</span>
                <strong>
                  {formatNumber(alertas.empleados_sin_horario)}
                </strong>
              </div>

              <div>
                <span>Marcaciones sin empleado hoy</span>
                <strong>
                  {formatNumber(alertas.marcaciones_sin_empleado_hoy)}
                </strong>
              </div>

              <div>
                <span>Asistencias por revisar hoy</span>
                <strong>
                  {formatNumber(alertas.asistencias_revision_hoy)}
                </strong>
              </div>

              <div>
                <span>Faltas hoy</span>
                <strong>
                  {formatNumber(alertas.faltas_hoy)}
                </strong>
              </div>

              <div>
                <span>Retardos mayores hoy</span>
                <strong>
                  {formatNumber(alertas.retardos_mayores_hoy)}
                </strong>
              </div>
            </div>
          </section>

          
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Asistencia últimos 7 días</h3>
                <p>
                  Comparativo diario de asistencias completas, retardos,
                  faltas y registros que requieren revisión.
                </p>
              </div>

              <Clock size={22} />
            </div>

            {asistenciaUltimosDias.length === 0 ? (
              <div className="empty-state">
                <Clock size={42} />

                <h3>Sin datos procesados</h3>

                <p>
                  Procesa asistencia diaria para comenzar a visualizar la
                  tendencia.
                </p>
              </div>
            ) : (
              <div className="attendance-chart-list">
                {asistenciaUltimosDias.map((row) => (
                  <div className="attendance-chart-row" key={row.fecha}>
                    <div className="attendance-chart-date">
                      <strong>{formatShortDate(row.fecha)}</strong>
                      <span>{formatNumber(row.total)} total</span>
                    </div>

                    <div className="attendance-chart-bars">
                      <div className="attendance-chart-track">
                        <div
                          className="attendance-chart-bar complete"
                          style={{
                            width: getBarWidth(
                              row.completos,
                              maxAsistenciaUltimosDias
                            ),
                          }}
                          title={`Completas: ${formatNumber(row.completos)}`}
                        />
                      </div>

                      <div className="attendance-chart-track">
                        <div
                          className="attendance-chart-bar delay"
                          style={{
                            width: getBarWidth(
                              row.retardos,
                              maxAsistenciaUltimosDias
                            ),
                          }}
                          title={`Retardos: ${formatNumber(row.retardos)}`}
                        />
                      </div>

                      <div className="attendance-chart-track">
                        <div
                          className="attendance-chart-bar absence"
                          style={{
                            width: getBarWidth(
                              row.faltas,
                              maxAsistenciaUltimosDias
                            ),
                          }}
                          title={`Faltas: ${formatNumber(row.faltas)}`}
                        />
                      </div>

                      <div className="attendance-chart-track">
                        <div
                          className="attendance-chart-bar review"
                          style={{
                            width: getBarWidth(
                              row.requieren_revision,
                              maxAsistenciaUltimosDias
                            ),
                          }}
                          title={`Revisión: ${formatNumber(
                            row.requieren_revision
                          )}`}
                        />
                      </div>
                    </div>

                    <div className="attendance-chart-values">
                      <span>Completas: {formatNumber(row.completos)}</span>
                      <span>Retardos: {formatNumber(row.retardos)}</span>
                      <span>Faltas: {formatNumber(row.faltas)}</span>
                      <span>Revisión: {formatNumber(row.requieren_revision)}</span>
                    </div>
                  </div>
                ))}

                <div className="attendance-chart-legend">
                  <span>
                    <i className="complete" /> Completas
                  </span>
                  <span>
                    <i className="delay" /> Retardos
                  </span>
                  <span>
                    <i className="absence" /> Faltas
                  </span>
                  <span>
                    <i className="review" /> Revisión RH
                  </span>
                </div>
              </div>
            )}
          </section>
          
          <section className="dashboard-grid">
            <article className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Top empleados con más faltas</h3>
                  <p>
                    Empleados con más registros de falta en los últimos 30 días.
                  </p>
                </div>

                <AlertTriangle size={22} />
              </div>

              {topEmpleadosFaltas.length === 0 ? (
                <div className="empty-state">
                  <CheckCircle2 size={42} />

                  <h3>Sin faltas recientes</h3>

                  <p>
                    No hay empleados con faltas registradas en los últimos 30 días.
                  </p>
                </div>
              ) : (
                <div className="ranking-list">
                  {topEmpleadosFaltas.map((row, index) => (
                    <div className="ranking-row" key={row.empleado_id}>
                      <div className="ranking-position">
                        {index + 1}
                      </div>

                      <div className="ranking-content">
                        <div className="ranking-header">
                          <div>
                            <strong>
                              {safeText(row.empleado_nombre)}
                            </strong>
                            <span>
                              {safeText(row.codigo_empleado, "Sin código")}
                            </span>
                          </div>

                          <strong>
                            {formatNumber(row.faltas)}
                          </strong>
                        </div>

                        <div className="ranking-track">
                          <div
                            className="ranking-bar absence"
                            style={{
                              width: getBarWidth(
                                row.faltas,
                                maxTopEmpleadosFaltas
                              ),
                            }}
                          />
                        </div>

                        <div className="ranking-meta">
                          <span>
                            Revisión RH:{" "}
                            {formatNumber(row.requieren_revision)}
                          </span>
                          <span>
                            Días procesados:{" "}
                            {formatNumber(row.dias_procesados)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </article>

            <article className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Top empleados con más retardos</h3>
                  <p>
                    Empleados con más retardos menores o mayores en los últimos
                    30 días.
                  </p>
                </div>

                <Clock size={22} />
              </div>

              {topEmpleadosRetardos.length === 0 ? (
                <div className="empty-state">
                  <CheckCircle2 size={42} />

                  <h3>Sin retardos recientes</h3>

                  <p>
                    No hay empleados con retardos registrados en los últimos 30
                    días.
                  </p>
                </div>
              ) : (
                <div className="ranking-list">
                  {topEmpleadosRetardos.map((row, index) => (
                    <div className="ranking-row" key={row.empleado_id}>
                      <div className="ranking-position">
                        {index + 1}
                      </div>

                      <div className="ranking-content">
                        <div className="ranking-header">
                          <div>
                            <strong>
                              {safeText(row.empleado_nombre)}
                            </strong>
                            <span>
                              {safeText(row.codigo_empleado, "Sin código")}
                            </span>
                          </div>

                          <strong>
                            {formatNumber(row.total_retardos)}
                          </strong>
                        </div>

                        <div className="ranking-track">
                          <div
                            className="ranking-bar delay"
                            style={{
                              width: getBarWidth(
                                row.total_retardos,
                                maxTopEmpleadosRetardos
                              ),
                            }}
                          />
                        </div>

                        <div className="ranking-meta">
                          <span>
                            Menores:{" "}
                            {formatNumber(row.retardos_menores)}
                          </span>
                          <span>
                            Mayores:{" "}
                            {formatNumber(row.retardos_mayores)}
                          </span>
                          <span>
                            Puntos:{" "}
                            {formatNumber(row.puntos_generados)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </article>
          </section>
          
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Departamentos con más incidencias</h3>
                <p>
                  Unidades con mayor concentración de faltas, retardos,
                  omisiones y registros por revisar en los últimos 30 días.
                </p>
              </div>

              <AlertTriangle size={22} />
            </div>

            {departamentosIncidencias.length === 0 ? (
              <div className="empty-state">
                <CheckCircle2 size={42} />

                <h3>Sin incidencias por departamento</h3>

                <p>
                  No hay incidencias registradas por unidad organizacional en los
                  últimos 30 días.
                </p>
              </div>
            ) : (
              <div className="department-incidence-list">
                {departamentosIncidencias.map((row, index) => (
                  <div
                    className="department-incidence-row"
                    key={`${row.unidad_organizacional_id ?? "sin-unidad"}-${index}`}
                  >
                    <div className="ranking-position">
                      {index + 1}
                    </div>

                    <div className="department-incidence-content">
                      <div className="ranking-header">
                        <div>
                          <strong>
                            {safeText(
                              row.departamento_nombre,
                              "Sin departamento"
                            )}
                          </strong>

                          <span>
                            {formatNumber(row.empleados_involucrados)} empleados
                            involucrados
                          </span>
                        </div>

                        <strong>
                          {formatNumber(row.total_incidencias)}
                        </strong>
                      </div>

                      <div className="ranking-track">
                        <div
                          className="ranking-bar incidence"
                          style={{
                            width: getBarWidth(
                              row.total_incidencias,
                              maxDepartamentosIncidencias
                            ),
                          }}
                        />
                      </div>

                      <div className="department-incidence-metrics">
                        <span>
                          Faltas: {formatNumber(row.faltas)}
                        </span>

                        <span>
                          Retardos: {formatNumber(row.retardos)}
                        </span>

                        <span>
                          Retardos mayores:{" "}
                          {formatNumber(row.retardos_mayores)}
                        </span>

                        <span>
                          Omisiones: {formatNumber(row.omisiones)}
                        </span>

                        <span>
                          Revisión RH:{" "}
                          {formatNumber(row.requieren_revision)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Últimas checadas reales</h3>
                <p>
                  Eventos más recientes guardados en asistencia.marcaciones_crudas.
                </p>
              </div>
              <Fingerprint size={22} />
            </div>

            {ultimasMarcaciones.length === 0 ? (
              <div className="empty-state">
                <Clock size={42} />
                <h3>Sin marcaciones crudas</h3>
                <p>
                  Aún no hay checadas sincronizadas desde el reloj ZKTeco.
                </p>
              </div>
            ) : (
              <div className="simple-table">
                <table>
                  <thead>
                    <tr>
                      <th>Empleado</th>
                      <th>Código</th>
                      <th>User ID ZKTeco</th>
                      <th>Fecha y hora</th>
                      <th>Evento</th>
                      <th>Dispositivo</th>
                    </tr>
                  </thead>

                  <tbody>
                    {ultimasMarcaciones.map((row) => (
                      <tr key={row.id}>
                        <td>
                          <strong>
                            {safeText(row.empleado_nombre)}
                          </strong>
                        </td>
                        <td>{safeText(row.codigo_empleado, "Sin código")}</td>
                        <td>{safeText(row.zk_user_id, "Sin User ID")}</td>
                        <td>{formatDateTime(row.fecha_hora)}</td>
                        <td>
                          <span className="badge neutral">
                            {getPunchLabel(row)}
                          </span>
                        </td>
                        <td>
                          {safeText(
                            row.dispositivo_ip ||
                              row.dispositivo_origen
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

export default DashboardPage;