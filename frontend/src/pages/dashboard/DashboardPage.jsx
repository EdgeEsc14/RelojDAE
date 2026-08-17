import { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Fingerprint,
  RefreshCw,
  TrendingUp,
  UserCheck,
  Users,
  Download,
  PlayCircle,
} from "lucide-react";

import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

import { dashboardApi } from "../../api/dashboardApi";
import { asistenciaApi } from "../../api/asistenciaApi";
import { getZkHealth, syncZkAttendanceToDb, syncZkTime } from "../../api/zkApi";
import PageHeader from "../../components/layout/PageHeader";

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
  return String(value ?? "").trim() || fallback;
}

function formatShortDate(value) {
  if (!value) return "";
  try {
    return new Intl.DateTimeFormat("es-MX", {
      day: "2-digit",
      month: "short",
    }).format(new Date(`${value}T00:00:00`));
  } catch {
    return String(value);
  }
}

function getPunchLabel(row) {
  return row.punch_label || row.status_label || `Punch ${row.punch ?? "N/D"}`;
}

function getPercent(value, total) {
  const safeValue = Number(value ?? 0);
  const safeTotal = Number(total ?? 0);
  if (safeTotal <= 0) return 0;
  return Math.round((safeValue / safeTotal) * 100);
}

// Colores para gráficas
const COLORS = {
  completos: "#10b981",
  retardos: "#f59e0b",
  faltas: "#ef4444",
  revision: "#8b5cf6",
  omisiones: "#f97316",
  puntualidad: "#3b82f6",
  asistencia: "#10b981",
};

const PIE_COLORS = ["#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#f97316", "#6366f1"];

const INCIDENCIA_COLORS = {
  RETARDO: "#f59e0b",
  FALTA: "#ef4444",
  OMISION: "#f97316",
  TIEMPO_EXTRA: "#3b82f6",
  SANCION: "#dc2626",
  REVISION: "#8b5cf6",
  ADMINISTRATIVA: "#6b7280",
};

function DashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");
      const data = await dashboardApi.obtenerResumen();
      setDashboard(data);
    } catch (err) {
      setError(err.message || "No fue posible cargar el dashboard.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSyncNow() {
    setSyncing(true);
    setSyncStatus({ step: 1, message: "Verificando conexión con reloj ZKTeco..." });

    let relojDisponible = false;
    let insertados = 0;
    let procesados = 0;

    // 1. Health check: verificar si el reloj responde antes de intentar cualquier cosa
    try {
      const health = await getZkHealth();
      if (health?.ok) {
        relojDisponible = true;
        setSyncStatus({ step: 2, message: `Reloj conectado (${health.total_users} usuarios). Sincronizando marcaciones...` });
      }
    } catch {
      relojDisponible = false;
      setSyncStatus({ step: 2, message: "Reloj no disponible. Procesando con datos existentes en BD..." });
    }

    // 2. Si el reloj está disponible, sincronizar marcaciones
    if (relojDisponible) {
      try {
        const syncResult = await syncZkAttendanceToDb({ limit: 5000 });
        insertados = syncResult?.result?.insertados ?? syncResult?.result?.insertadas ?? 0;
        setSyncStatus({ step: 3, message: `${insertados} marcaciones nuevas sincronizadas. Procesando asistencia...` });
      } catch (syncErr) {
        setSyncStatus({ step: 3, message: "Error al leer marcaciones. Procesando con datos existentes..." });
      }
    }

    // 3. Procesar asistencia de hoy (funciona siempre, usa datos ya en BD)
    try {
      const hoy = new Date().toISOString().split("T")[0];
      const processResult = await asistenciaApi.procesar({
        fechaInicio: hoy,
        fechaFin: hoy,
      });
      procesados = processResult?.procesados || processResult?.total_procesados || 0;
      setSyncStatus({ step: 4, message: `Asistencia procesada (${procesados} registros). Actualizando dashboard...` });
    } catch (procErr) {
      setSyncStatus({ step: 4, message: "Error al procesar asistencia: " + (procErr.message || "desconocido") });
    }

    // 4. Recargar dashboard
    try {
      await loadDashboard();
    } catch {
      // loadDashboard maneja su propio error
    }

    // 5. Resultado final
    if (relojDisponible && insertados >= 0) {
      setSyncStatus({
        step: 5,
        message: `Sincronización completa: ${insertados} marcaciones nuevas, ${procesados} asistencias procesadas.`,
        completed: true,
      });
    } else if (!relojDisponible) {
      setSyncStatus({
        step: 5,
        message: `Reloj ZKTeco no disponible (sin red o apagado). Se procesó asistencia con datos ya existentes en la BD.${procesados > 0 ? ` (${procesados} procesados)` : ""} Conecta el reloj e intenta de nuevo.`,
        warning: true,
      });
    }

    setSyncing(false);

    setTimeout(() => {
      setSyncStatus(null);
    }, 10000);
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  // Métricas principales
  const metrics = useMemo(() => {
    if (!dashboard) return [];
    const empleados = dashboard.empleados ?? {};
    const asistenciaHoy = dashboard.asistencia_hoy ?? {};
    const alertas = dashboard.alertas ?? {};
    const totalHoy = Number(asistenciaHoy.total ?? 0);
    const completosHoy = Number(asistenciaHoy.completos ?? 0);
    const pctAsistencia = totalHoy > 0 ? Math.round((completosHoy / totalHoy) * 100) : 0;

    return [
      {
        title: "Empleados activos",
        value: formatNumber(empleados.activos),
        description: `${formatNumber(empleados.total)} registrados`,
        icon: Users,
        color: "#3b82f6",
      },
      {
        title: "Puntualidad hoy",
        value: `${pctAsistencia}%`,
        description: `${formatNumber(completosHoy)} de ${formatNumber(totalHoy)} completas`,
        icon: CheckCircle2,
        color: "#10b981",
      },
      {
        title: "Faltas hoy",
        value: formatNumber(asistenciaHoy.faltas),
        description: `${formatNumber(asistenciaHoy.requieren_revision)} requieren revisión`,
        icon: AlertTriangle,
        color: "#ef4444",
      },
      {
        title: "Incidencias pendientes",
        value: formatNumber(alertas.asistencias_revision_hoy),
        description: `${formatNumber(alertas.empleados_sin_horario)} sin horario`,
        icon: Clock,
        color: "#f59e0b",
      },
    ];
  }, [dashboard]);

  // Datos para BarChart 7 días
  const barChartData = useMemo(() => {
    if (!dashboard) return [];
    return (dashboard.asistencia_ultimos_dias ?? []).map((row) => ({
      fecha: formatShortDate(row.fecha),
      Completas: Number(row.completos ?? 0),
      Retardos: Number(row.retardos ?? 0),
      Faltas: Number(row.faltas ?? 0),
    }));
  }, [dashboard]);

  // Datos para PieChart distribución de hoy
  const pieChartData = useMemo(() => {
    if (!dashboard) return [];
    const hoy = dashboard.asistencia_hoy ?? {};
    const data = [];
    if (Number(hoy.completos) > 0) data.push({ name: "Completas", value: Number(hoy.completos) });
    const retardos = Number(hoy.retardos_menores ?? 0) + Number(hoy.retardos_mayores ?? 0);
    if (retardos > 0) data.push({ name: "Retardos", value: retardos });
    if (Number(hoy.faltas) > 0) data.push({ name: "Faltas", value: Number(hoy.faltas) });
    if (Number(hoy.requieren_revision) > 0) data.push({ name: "Revisión", value: Number(hoy.requieren_revision) });
    return data;
  }, [dashboard]);

  // Datos para AreaChart tendencia 30 días
  const tendenciaData = useMemo(() => {
    if (!dashboard) return [];
    return (dashboard.tendencia_puntualidad ?? []).map((row) => ({
      fecha: formatShortDate(row.fecha),
      Puntualidad: Number(row.pct_puntualidad ?? 0),
      Asistencia: Number(row.pct_asistencia ?? 0),
    }));
  }, [dashboard]);

  // Datos para PieChart incidencias por categoría
  const incidenciasCatData = useMemo(() => {
    if (!dashboard) return [];
    return (dashboard.incidencias_por_categoria ?? []).map((row) => ({
      name: row.tipo_nombre || row.categoria,
      value: Number(row.cantidad ?? 0),
      categoria: row.categoria,
    }));
  }, [dashboard]);

  // Rankings
  const topFaltas = dashboard?.top_empleados_faltas ?? [];
  const topRetardos = dashboard?.top_empleados_retardos ?? [];
  const departamentosIncidencias = dashboard?.departamentos_incidencias ?? [];
  const ultimasMarcaciones = dashboard?.ultimas_marcaciones ?? [];
  const alertas = dashboard?.alertas ?? {};

  return (
    <div className="page-stack">
      <PageHeader
        title="Dashboard"
        description="Resumen ejecutivo de asistencia, puntualidad e incidencias."
      >
        <div className="header-actions">
          <button
            className="secondary-button"
            type="button"
            disabled={syncing}
            onClick={handleSyncNow}
            title="Sincronizar reloj y procesar asistencia"
          >
            {syncing ? <RefreshCw size={17} className="spinning" /> : <PlayCircle size={17} />}
            {syncing ? "Sincronizando..." : "Sincronizar ahora"}
          </button>
          <button
            className="primary-button"
            type="button"
            disabled={loading}
            onClick={loadDashboard}
          >
            <RefreshCw size={17} />
            {loading ? "Actualizando..." : "Actualizar"}
          </button>
        </div>
      </PageHeader>

      {syncStatus && (
        <section className="panel-card">
          <div className={`sync-status ${syncStatus.error ? 'error' : syncStatus.completed ? 'completed' : 'in-progress'}`}>
            <div className="sync-status-header">
              {syncStatus.error ? (
                <AlertTriangle size={20} />
              ) : syncStatus.completed ? (
                <CheckCircle2 size={20} />
              ) : (
                <RefreshCw size={20} className="spinning" />
              )}
              <h3>
                {syncStatus.error ? 'Error de sincronización' : 
                 syncStatus.completed ? 'Sincronización completada' : 
                 'Sincronizando...'}
              </h3>
            </div>
            <p>{syncStatus.message}</p>
            {!syncStatus.completed && !syncStatus.error && (
              <div className="sync-progress">
                <div 
                  className="sync-progress-bar" 
                  style={{ width: `${(syncStatus.step / 5) * 100}%` }}
                />
              </div>
            )}
          </div>
        </section>
      )}

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
            <RefreshCw size={42} />
            <h3>Cargando dashboard</h3>
            <p>Consultando información desde PostgreSQL.</p>
          </div>
        </section>
      )}

      {dashboard && (
        <>
          {/* Métricas KPI */}
          <section className="metrics-grid four-columns">
            {metrics.map((m) => {
              const Icon = m.icon;
              return (
                <article className="metric-card" key={m.title}>
                  <div className="metric-icon" style={{ color: m.color }}>
                    <Icon size={22} />
                  </div>
                  <div>
                    <p>{m.title}</p>
                    <strong>{m.value}</strong>
                    <span>{m.description}</span>
                  </div>
                </article>
              );
            })}
          </section>

          {/* Gráficas principales: BarChart + PieChart */}
          <section className="dashboard-grid">
            {/* BarChart: Asistencia últimos 7 días */}
            <article className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Asistencia últimos 7 días</h3>
                  <p>Distribución diaria de completas, retardos y faltas.</p>
                </div>
                <UserCheck size={22} />
              </div>

              {barChartData.length > 0 ? (
                <div className="chart-container">
                  <BarChart width={500} height={270} data={barChartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ fontWeight: 600 }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="Completas" stackId="a" fill={COLORS.completos} radius={[0, 0, 0, 0]} />
                    <Bar dataKey="Retardos" stackId="a" fill={COLORS.retardos} />
                    <Bar dataKey="Faltas" stackId="a" fill={COLORS.faltas} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </div>
              ) : (
                <div className="empty-state">
                  <p>Sin datos de asistencia procesada en los últimos 7 días.</p>
                </div>
              )}
            </article>

            {/* PieChart: Distribución de hoy */}
            <article className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Distribución de hoy</h3>
                  <p>Proporción de asistencias por estatus del día actual.</p>
                </div>
                <CheckCircle2 size={22} />
              </div>

              {pieChartData.length > 0 ? (
                <div className="chart-container">
                  <PieChart width={400} height={270}>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={95}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {pieChartData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatNumber(value)} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </div>
              ) : (
                <div className="empty-state">
                  <p>No hay asistencia procesada hoy.</p>
                </div>
              )}
            </article>
          </section>

          {/* AreaChart: Tendencia de puntualidad 30 días */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Tendencia de puntualidad — 30 días</h3>
                <p>Porcentaje diario de asistencias completas (puntualidad) vs asistencia total (con retardos).</p>
              </div>
              <TrendingUp size={22} />
            </div>

            {tendenciaData.length > 0 ? (
              <div className="chart-container chart-wide">
                  <AreaChart width={900} height={250} data={tendenciaData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="gradPuntualidad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={COLORS.puntualidad} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={COLORS.puntualidad} stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gradAsistencia" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={COLORS.asistencia} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={COLORS.asistencia} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="fecha"
                      tick={{ fontSize: 10 }}
                      interval={Math.floor(tendenciaData.length / 8)}
                    />
                    <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
                    <Tooltip
                      contentStyle={{ borderRadius: 8, fontSize: 12 }}
                      formatter={(value) => `${value}%`}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Area
                      type="monotone"
                      dataKey="Puntualidad"
                      stroke={COLORS.puntualidad}
                      fill="url(#gradPuntualidad)"
                      strokeWidth={2}
                    />
                    <Area
                      type="monotone"
                      dataKey="Asistencia"
                      stroke={COLORS.asistencia}
                      fill="url(#gradAsistencia)"
                      strokeWidth={2}
                    />
                  </AreaChart>
              </div>
            ) : (
              <div className="empty-state">
                <p>Sin datos suficientes para mostrar tendencia.</p>
              </div>
            )}
          </section>

          {/* Incidencias por categoría + Alertas RH */}
          <section className="dashboard-grid">
            {/* PieChart incidencias por categoría */}
            <article className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Incidencias por tipo — 30 días</h3>
                  <p>Distribución de incidencias registradas por categoría.</p>
                </div>
                <AlertTriangle size={22} />
              </div>

              {incidenciasCatData.length > 0 ? (
                <div className="chart-container">
                  <PieChart width={400} height={250}>
                    <Pie
                      data={incidenciasCatData}
                      cx="50%"
                      cy="50%"
                      outerRadius={85}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                      labelLine={true}
                    >
                      {incidenciasCatData.map((entry, index) => (
                        <Cell
                          key={`cat-${index}`}
                          fill={INCIDENCIA_COLORS[entry.categoria] || PIE_COLORS[index % PIE_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatNumber(value)} />
                  </PieChart>
                </div>
              ) : (
                <div className="empty-state">
                  <p>Sin incidencias registradas en los últimos 30 días.</p>
                </div>
              )}
            </article>

            {/* Alertas RH */}
            <article className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Alertas RH</h3>
                  <p>Situaciones que requieren atención operativa.</p>
                </div>
                <AlertTriangle size={22} />
              </div>

              <div className="alert-list">
                {Number(alertas.empleados_sin_zk) > 0 && (
                  <div className="alert-item warning">
                    <Users size={18} />
                    <div>
                      <strong>{formatNumber(alertas.empleados_sin_zk)}</strong>
                      <span>Empleados sin User ID ZKTeco</span>
                    </div>
                  </div>
                )}

                {Number(alertas.empleados_sin_horario) > 0 && (
                  <div className="alert-item warning">
                    <Clock size={18} />
                    <div>
                      <strong>{formatNumber(alertas.empleados_sin_horario)}</strong>
                      <span>Empleados sin horario vigente</span>
                    </div>
                  </div>
                )}

                {Number(alertas.marcaciones_sin_empleado_hoy) > 0 && (
                  <div className="alert-item danger">
                    <Fingerprint size={18} />
                    <div>
                      <strong>{formatNumber(alertas.marcaciones_sin_empleado_hoy)}</strong>
                      <span>Marcaciones sin empleado hoy</span>
                    </div>
                  </div>
                )}

                {Number(alertas.faltas_hoy) > 0 && (
                  <div className="alert-item danger">
                    <AlertTriangle size={18} />
                    <div>
                      <strong>{formatNumber(alertas.faltas_hoy)}</strong>
                      <span>Faltas registradas hoy</span>
                    </div>
                  </div>
                )}

                {Number(alertas.retardos_mayores_hoy) > 0 && (
                  <div className="alert-item warning">
                    <Clock size={18} />
                    <div>
                      <strong>{formatNumber(alertas.retardos_mayores_hoy)}</strong>
                      <span>Retardos mayores hoy</span>
                    </div>
                  </div>
                )}

                {Number(alertas.asistencias_revision_hoy) > 0 && (
                  <div className="alert-item info">
                    <CheckCircle2 size={18} />
                    <div>
                      <strong>{formatNumber(alertas.asistencias_revision_hoy)}</strong>
                      <span>Asistencias requieren revisión</span>
                    </div>
                  </div>
                )}

                {Object.values(alertas).every((v) => Number(v) === 0) && (
                  <div className="empty-state">
                    <CheckCircle2 size={32} />
                    <p>Sin alertas activas. Todo en orden.</p>
                  </div>
                )}
              </div>
            </article>
          </section>

          {/* Rankings: Top faltas + Top retardos */}
          <section className="dashboard-grid">
            <article className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Top faltas — 30 días</h3>
                  <p>Empleados con más faltas registradas.</p>
                </div>
                <AlertTriangle size={22} />
              </div>

              {topFaltas.length === 0 ? (
                <div className="empty-state">
                  <CheckCircle2 size={32} />
                  <p>Sin faltas en los últimos 30 días.</p>
                </div>
              ) : (
                <div className="ranking-list">
                  {topFaltas.map((row, index) => (
                    <div className="ranking-row" key={row.empleado_id}>
                      <div className="ranking-position">{index + 1}</div>
                      <div className="ranking-content">
                        <div className="ranking-header">
                          <div>
                            <strong>{safeText(row.empleado_nombre)}</strong>
                            <span>{safeText(row.codigo_empleado)}</span>
                          </div>
                          <strong className="ranking-value danger">{row.faltas}</strong>
                        </div>
                        <div className="ranking-track">
                          <div
                            className="ranking-bar absence"
                            style={{ width: `${Math.max((row.faltas / (topFaltas[0]?.faltas || 1)) * 100, 8)}%` }}
                          />
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
                  <h3>Top retardos — 30 días</h3>
                  <p>Empleados con más retardos y puntos acumulados.</p>
                </div>
                <Clock size={22} />
              </div>

              {topRetardos.length === 0 ? (
                <div className="empty-state">
                  <CheckCircle2 size={32} />
                  <p>Sin retardos en los últimos 30 días.</p>
                </div>
              ) : (
                <div className="ranking-list">
                  {topRetardos.map((row, index) => (
                    <div className="ranking-row" key={row.empleado_id}>
                      <div className="ranking-position">{index + 1}</div>
                      <div className="ranking-content">
                        <div className="ranking-header">
                          <div>
                            <strong>{safeText(row.empleado_nombre)}</strong>
                            <span>{safeText(row.codigo_empleado)}</span>
                          </div>
                          <strong className="ranking-value warning">{row.total_retardos}</strong>
                        </div>
                        <div className="ranking-track">
                          <div
                            className="ranking-bar delay"
                            style={{ width: `${Math.max((row.total_retardos / (topRetardos[0]?.total_retardos || 1)) * 100, 8)}%` }}
                          />
                        </div>
                        <div className="ranking-meta">
                          <span>Menores: {row.retardos_menores}</span>
                          <span>Mayores: {row.retardos_mayores}</span>
                          <span>Puntos: {row.puntos_generados}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </article>
          </section>

          {/* Departamentos con incidencias */}
          {departamentosIncidencias.length > 0 && (
            <section className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Departamentos con más incidencias — 30 días</h3>
                  <p>Unidades con mayor concentración de faltas, retardos y omisiones.</p>
                </div>
                <Users size={22} />
              </div>

              <div className="department-incidence-list">
                {departamentosIncidencias.map((row, index) => (
                  <div
                    className="department-incidence-row"
                    key={`${row.unidad_organizacional_id ?? "sin"}-${index}`}
                  >
                    <div className="ranking-position">{index + 1}</div>
                    <div className="department-incidence-content">
                      <div className="ranking-header">
                        <div>
                          <strong>{safeText(row.departamento_nombre, "Sin departamento")}</strong>
                          <span>{formatNumber(row.empleados_involucrados)} empleados</span>
                        </div>
                        <strong>{formatNumber(row.total_incidencias)}</strong>
                      </div>
                      <div className="ranking-track">
                        <div
                          className="ranking-bar incidence"
                          style={{
                            width: `${Math.max(
                              (row.total_incidencias / (departamentosIncidencias[0]?.total_incidencias || 1)) * 100,
                              8
                            )}%`,
                          }}
                        />
                      </div>
                      <div className="department-incidence-metrics">
                        <span>Faltas: {row.faltas}</span>
                        <span>Retardos: {row.retardos}</span>
                        <span>Omisiones: {row.omisiones}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Últimas marcaciones */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Últimas checadas</h3>
                <p>Marcaciones más recientes sincronizadas desde ZKTeco.</p>
              </div>
              <Fingerprint size={22} />
            </div>

            {ultimasMarcaciones.length === 0 ? (
              <div className="empty-state">
                <Fingerprint size={32} />
                <p>Sin marcaciones sincronizadas.</p>
              </div>
            ) : (
              <div className="simple-table">
                <table>
                  <thead>
                    <tr>
                      <th>Empleado</th>
                      <th>User ID ZK</th>
                      <th>Fecha y hora</th>
                      <th>Evento</th>
                      <th>Dispositivo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ultimasMarcaciones.map((row) => (
                      <tr key={row.id}>
                        <td>
                          <div className="employee-cell">
                            <div className="employee-avatar">
                              {(row.empleado_nombre || "?").charAt(0)}
                            </div>
                            <div>
                              <strong>{safeText(row.empleado_nombre)}</strong>
                              <span>{safeText(row.codigo_empleado, "Sin código")}</span>
                            </div>
                          </div>
                        </td>
                        <td>{safeText(row.zk_user_id, "—")}</td>
                        <td>{formatDateTime(row.fecha_hora)}</td>
                        <td>
                          <span className="badge neutral">{getPunchLabel(row)}</span>
                        </td>
                        <td>{safeText(row.dispositivo_ip || row.dispositivo_origen)}</td>
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
