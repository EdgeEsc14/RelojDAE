import { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Fingerprint,
  RefreshCw,
  Users,
  PlayCircle,
  CalendarDays,
} from "lucide-react";


import { dashboardApi } from "../../api/dashboardApi";
import { asistenciaApi } from "../../api/asistenciaApi";
import { getZkHealth, syncZkAttendanceToDb } from "../../api/zkApi";
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

function getPunchLabel(row) {
  return row.punch_label || row.status_label || `Punch ${row.punch ?? "N/D"}`;
}

const CATEGORIAS_HOY = [
  { estatus: "COMPLETO",       campo: "completos",         label: "Puntuales",    variant: "success" },
  { estatus: "TOLERANCIA",     campo: "tolerancias",       label: "Tolerancia",   variant: "teal"    },
  { estatus: "RETARDO_MENOR",  campo: "retardos_menores",  label: "Ret. menor",   variant: "warning" },
  { estatus: "RETARDO_MAYOR",  campo: "retardos_mayores",  label: "Ret. mayor",   variant: "orange"  },
  { estatus: "FALTA",          campo: "faltas",            label: "Faltas",       variant: "danger"  },
  { estatus: "OMISION_ENTRADA",campo: "omisiones_entrada", label: "Om. entrada",  variant: "muted"   },
  { estatus: "OMISION_SALIDA", campo: "omisiones_salida",  label: "Om. salida",   variant: "muted"   },
];

function DashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [error, setError] = useState("");
  const [procesamientoOmitido, setProcesamientoOmitido] = useState(false);

  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState(null);
  const [empleadosCategoria, setEmpleadosCategoria] = useState([]);
  const [loadingCategoria, setLoadingCategoria] = useState(false);

  async function toggleCategoria(estatus) {
    if (categoriaSeleccionada === estatus) {
      setCategoriaSeleccionada(null);
      setEmpleadosCategoria([]);
      return;
    }
    setCategoriaSeleccionada(estatus);
    setLoadingCategoria(true);
    try {
      const hoy = new Date().toISOString().split("T")[0];
      const result = await asistenciaApi.listarDiaria({ fecha: hoy, estatus, limit: 100 });
      setEmpleadosCategoria(result?.items ?? result ?? []);
    } catch {
      setEmpleadosCategoria([]);
    } finally {
      setLoadingCategoria(false);
    }
  }

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      // El motor solo genera FALTA definitiva para un empleado sin
      // marcaciones una vez que su jornada programada ya cerró
      // (Contrato §15: mientras datetime.now() < salida_programada la
      // fila ni siquiera se escribe). Sin procesar "hoy" antes de leer
      // el resumen, el Dashboard mostraba una foto incompleta: solo
      // los empleados cuya jornada ya se había (re)procesado después de
      // su cierre aparecían como falta/completo; el resto (jornada ya
      // cerrada pero nunca reprocesada desde entonces) simplemente no
      // tenía fila y desaparecía de los conteos.
      //
      // Requiere alcance TOTAL + editar sobre ASISTENCIA; si el usuario
      // no lo tiene (p. ej. Supervisor/Empleado viendo su Dashboard),
      // se omite en silencio y se avisa para no ocultar que los datos
      // pueden estar desactualizados.
      try {
        const hoy = new Date().toISOString().split("T")[0];
        await asistenciaApi.procesar({ fechaInicio: hoy, fechaFin: hoy });
        setProcesamientoOmitido(false);
      } catch {
        setProcesamientoOmitido(true);
      }

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
    let healthError = "";

    try {
      const health = await getZkHealth();
      if (health?.ok) {
        relojDisponible = true;
        setSyncStatus({ step: 2, message: `Reloj conectado (${health.total_users} usuarios). Sincronizando marcaciones...` });
      }
    } catch (err) {
      healthError = err.message || "sin respuesta";
      setSyncStatus({ step: 2, message: "Health check falló. Intentando sincronización directa..." });
    }

    try {
      const syncResult = await syncZkAttendanceToDb({ limit: 5000 });
      insertados = syncResult?.result?.insertados ?? syncResult?.result?.insertadas ?? 0;
      relojDisponible = true;
      setSyncStatus({ step: 3, message: `${insertados} marcaciones nuevas sincronizadas. Procesando asistencia...` });
    } catch (syncErr) {
      if (!relojDisponible) {
        setSyncStatus({ step: 3, message: `No se pudo conectar al reloj (${healthError || syncErr.message}). Procesando con datos existentes...` });
      } else {
        setSyncStatus({ step: 3, message: "Error al sincronizar: " + (syncErr.message || "desconocido") });
      }
    }

    try {
      const hoy = new Date();
      const hace7dias = new Date(hoy.getTime() - 7 * 24 * 60 * 60 * 1000);
      const fechaFin = hoy.toISOString().split("T")[0];
      const fechaInicio = hace7dias.toISOString().split("T")[0];
      const processResult = await asistenciaApi.procesar({ fechaInicio, fechaFin });
      procesados = processResult?.procesadas ?? 0;
      setSyncStatus({ step: 4, message: `Asistencia procesada (${procesados} registros, ${fechaInicio} a ${fechaFin}). Actualizando dashboard...` });
    } catch (procErr) {
      setSyncStatus({ step: 4, message: "Error al procesar: " + (procErr.message || "desconocido") });
    }

    try {
      await loadDashboard();
    } catch {
      // loadDashboard maneja su propio error
    }

    if (relojDisponible) {
      setSyncStatus({
        step: 5,
        message: `Sincronización completa: ${insertados} marcaciones nuevas, ${procesados} asistencias procesadas.`,
        completed: true,
      });
    } else {
      setSyncStatus({
        step: 5,
        message: `Reloj ZKTeco no respondió: ${healthError || "timeout o sin conexión de red"}. Se procesó asistencia con datos existentes en BD.${procesados > 0 ? ` (${procesados} procesados)` : ""}`,
        warning: true,
      });
    }

    setSyncing(false);
    setTimeout(() => setSyncStatus(null), 10000);
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const metrics = useMemo(() => {
    if (!dashboard) return [];
    const empleados = dashboard.empleados ?? {};
    const asistenciaHoy = dashboard.asistencia_hoy ?? {};
    const alertas = dashboard.alertas ?? {};
    const totalHoy = Number(asistenciaHoy.total ?? 0);
    const diasNoLaboralesHoy = Number(asistenciaHoy.dias_no_laborales ?? 0);
    const diasLaborablesHoy = totalHoy - diasNoLaboralesHoy;
    const completosHoy = Number(asistenciaHoy.completos ?? 0);
    const retardosHoy = Number(asistenciaHoy.retardos_menores ?? 0) + Number(asistenciaHoy.retardos_mayores ?? 0);
    const faltasHoy = Number(asistenciaHoy.faltas ?? 0);
    const pctPuntualidad = Number(asistenciaHoy.pct_puntualidad ?? 0);

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
        value: `${pctPuntualidad}%`,
        description: `${formatNumber(completosHoy)} puntuales de ${formatNumber(diasLaborablesHoy)} días laborables`,
        icon: CheckCircle2,
        color: "#10b981",
      },
      {
        title: "Faltas hoy",
        value: formatNumber(faltasHoy),
        description: `${formatNumber(retardosHoy)} retardos`,
        icon: AlertTriangle,
        color: "#ef4444",
      },
      {
        title: "Pendientes revisión",
        value: formatNumber(asistenciaHoy.requieren_revision),
        description: `${formatNumber(alertas.empleados_sin_horario)} sin horario asignado`,
        icon: Clock,
        color: "#f59e0b",
      },
    ];
  }, [dashboard]);

  const topFaltas = dashboard?.top_empleados_faltas ?? [];
  const departamentosIncidencias = dashboard?.departamentos_incidencias ?? [];
  const ultimasMarcaciones = dashboard?.ultimas_marcaciones ?? [];
  const alertas = dashboard?.alertas ?? {};

  const hayAlertas = Object.values(alertas).some((v) => Number(v) > 0);

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
          <div className={`sync-status ${syncStatus.error ? "error" : (syncStatus.completed || syncStatus.warning) ? "completed" : "in-progress"}`}>
            <div className="sync-status-header">
              {syncStatus.error || syncStatus.warning ? (
                <AlertTriangle size={20} />
              ) : syncStatus.completed ? (
                <CheckCircle2 size={20} />
              ) : (
                <RefreshCw size={20} className="spinning" />
              )}
              <h3>
                {syncStatus.error
                  ? "Error de sincronización"
                  : syncStatus.warning
                  ? "Sincronización completada con advertencias"
                  : syncStatus.completed
                  ? "Sincronización completada"
                  : "Sincronizando..."}
              </h3>
            </div>
            <p>{syncStatus.message}</p>
            {!syncStatus.completed && !syncStatus.warning && !syncStatus.error && (
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

      {!error && procesamientoOmitido && (
        <section className="warning-banner">
          <AlertTriangle size={22} />
          <div>
            <strong>Datos posiblemente desactualizados</strong>
            <p>
              Tu rol no tiene permiso para reprocesar la asistencia del día,
              así que estos números reflejan el último procesamiento
              disponible, no necesariamente el estado tras el cierre de la
              jornada de hoy. Pide a un administrador que ejecute
              &ldquo;Sincronizar ahora&rdquo; o procese asistencia.
            </p>
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
          {/* ZONA 1: Hoy — KPIs + Alertas RH */}
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

          {/* DESGLOSE HOY — clickeable por categoría */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Desglose de hoy</h3>
                <p>Haz clic en una categoría para ver los empleados.</p>
              </div>
              <CalendarDays size={22} />
            </div>

            {(() => {
              const hoy = dashboard.asistencia_hoy ?? {};
              const categorias = CATEGORIAS_HOY.filter(
                (cat) => Number(hoy[cat.campo] ?? 0) > 0
              );
              if (categorias.length === 0) {
                return (
                  <div className="empty-state">
                    <CalendarDays size={32} />
                    <p>Sin asistencia procesada hoy. Sincroniza y procesa para ver el desglose.</p>
                  </div>
                );
              }
              return (
                <>
                  <div className="hoy-categorias">
                    {categorias.map((cat) => (
                      <button
                        key={cat.estatus}
                        type="button"
                        className={`categoria-card categoria-card--${cat.variant}${categoriaSeleccionada === cat.estatus ? " categoria-card--active" : ""}`}
                        onClick={() => toggleCategoria(cat.estatus)}
                      >
                        <strong>{formatNumber(Number(hoy[cat.campo] ?? 0))}</strong>
                        <span>{cat.label}</span>
                      </button>
                    ))}
                  </div>

                  {categoriaSeleccionada && (
                    <div className="categoria-empleados">
                      {loadingCategoria ? (
                        <div className="empty-state">
                          <RefreshCw size={28} className="spinning" />
                          <p>Cargando empleados...</p>
                        </div>
                      ) : empleadosCategoria.length === 0 ? (
                        <div className="empty-state">
                          <CheckCircle2 size={28} />
                          <p>Sin empleados en esta categoría.</p>
                        </div>
                      ) : (
                        <div className="simple-table">
                          <table>
                            <thead>
                              <tr>
                                <th>Empleado</th>
                                <th>Departamento</th>
                                <th>Código</th>
                              </tr>
                            </thead>
                            <tbody>
                              {empleadosCategoria.map((row) => (
                                <tr key={row.asistencia_id ?? row.empleado_id}>
                                  <td>
                                    <div className="employee-cell">
                                      <div className="employee-avatar">
                                        {(row.nombre_completo || "?").charAt(0)}
                                      </div>
                                      <strong>{safeText(row.nombre_completo)}</strong>
                                    </div>
                                  </td>
                                  <td>{safeText(row.unidad_nombre, "—")}</td>
                                  <td>{safeText(row.codigo_empleado, "—")}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </>
              );
            })()}
          </section>

          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Alertas RH</h3>
                <p>Situaciones que requieren atención operativa.</p>
              </div>
              <AlertTriangle size={22} />
            </div>

            {hayAlertas ? (
              <div className="alert-list alert-list--horizontal">
                {Number(alertas.faltas_hoy) > 0 && (
                  <div className="alert-item danger">
                    <AlertTriangle size={18} />
                    <div>
                      <strong>{formatNumber(alertas.faltas_hoy)}</strong>
                      <span>Faltas hoy</span>
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
                      <span>Requieren revisión</span>
                    </div>
                  </div>
                )}
                {Number(alertas.marcaciones_sin_empleado_hoy) > 0 && (
                  <div className="alert-item danger">
                    <Fingerprint size={18} />
                    <div>
                      <strong>{formatNumber(alertas.marcaciones_sin_empleado_hoy)}</strong>
                      <span>Marcaciones sin empleado</span>
                    </div>
                  </div>
                )}
                {Number(alertas.empleados_sin_horario) > 0 && (
                  <div className="alert-item warning">
                    <Clock size={18} />
                    <div>
                      <strong>{formatNumber(alertas.empleados_sin_horario)}</strong>
                      <span>Sin horario vigente</span>
                    </div>
                  </div>
                )}
                {Number(alertas.empleados_sin_zk) > 0 && (
                  <div className="alert-item warning">
                    <Users size={18} />
                    <div>
                      <strong>{formatNumber(alertas.empleados_sin_zk)}</strong>
                      <span>Sin User ID ZKTeco</span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <CheckCircle2 size={32} />
                <p>Sin alertas activas. Todo en orden.</p>
              </div>
            )}
          </section>

          {/* Top faltas — 30 días */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Top faltas — 30 días</h3>
                <p>Empleados con más faltas.</p>
              </div>
              <AlertTriangle size={22} />
            </div>

            {topFaltas.length === 0 ? (
              <div className="empty-state">
                <CheckCircle2 size={28} />
                <p>Sin faltas en 30 días.</p>
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
          </section>

          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Departamentos con más incidencias — 30 días</h3>
                <p>Unidades con mayor concentración de faltas, retardos y omisiones.</p>
              </div>
              <Users size={22} />
            </div>

            {departamentosIncidencias.length === 0 ? (
              <div className="empty-state">
                <CheckCircle2 size={32} />
                <p>Sin incidencias por departamento en los últimos 30 días.</p>
              </div>
            ) : (
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
            )}
          </section>

          {/* ZONA 4: Actividad reciente */}
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
