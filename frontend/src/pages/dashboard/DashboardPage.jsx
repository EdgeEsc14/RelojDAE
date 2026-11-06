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
import { useAuth } from "../../context/AuthContext";
import { ROLES } from "../../constants/roles";

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

function formatTime(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("es-MX", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return "—";
  }
}

function formatDate(value) {
  if (!value) return "";
  try {
    const d = new Date(value + "T00:00:00");
    return d.toLocaleDateString("es-MX", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return value;
  }
}

function minutosAHoras(min) {
  if (!min) return "00:00";
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function safeText(value, fallback = "No disponible") {
  return String(value ?? "").trim() || fallback;
}

function getLocalDateISO() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function getPunchLabel(row) {
  return row.punch_label || row.status_label || `Punch ${row.punch ?? "N/D"}`;
}

function getStatusClass(estatus) {
  if (estatus === "COMPLETO") return "badge success";
  if (estatus === "TOLERANCIA") return "badge neutral";
  if (estatus === "RETARDO_MENOR") return "badge warning";
  if (estatus === "RETARDO_MAYOR") return "badge warning";
  if (estatus === "FALTA") return "badge danger";
  if (estatus === "OMISION_ENTRADA") return "badge neutral";
  if (estatus === "OMISION_SALIDA") return "badge neutral";
  if (estatus === "DIA_NO_LABORAL") return "badge neutral";
  return "badge neutral";
}

function getStatusLabel(estatus) {
  const labels = {
    COMPLETO: "Completo",
    TOLERANCIA: "Tolerancia",
    RETARDO_MENOR: "Retardo menor",
    RETARDO_MAYOR: "Retardo mayor",
    FALTA: "Falta",
    OMISION_ENTRADA: "Om. entrada",
    OMISION_SALIDA: "Om. salida",
    DIA_NO_LABORAL: "No laboral",
    EN_CURSO: "En curso",
  };
  return labels[estatus] || estatus || "—";
}

const CATEGORIAS_HOY = [
  { estatus: "COMPLETO",        campo: "completos",         label: "Puntuales",    variant: "success" },
  { estatus: "TOLERANCIA",      campo: "tolerancias",       label: "Tolerancia",   variant: "teal"    },
  { estatus: "RETARDO_MENOR",   campo: "retardos_menores",  label: "Ret. menor",   variant: "warning" },
  { estatus: "RETARDO_MAYOR",   campo: "retardos_mayores",  label: "Ret. mayor",   variant: "orange"  },
  { estatus: "FALTA",           campo: "faltas",            label: "Faltas",       variant: "danger"  },
  { estatus: "OMISION_ENTRADA", campo: "omisiones_entrada", label: "Om. entrada",  variant: "muted"   },
  { estatus: "OMISION_SALIDA",  campo: "omisiones_salida",  label: "Om. salida",   variant: "muted"   },
];

// ─── Vista empleado ──────────────────────────────────────────────────────────

function EmployeeDashboard({ codigoEmpleado }) {
  const [resumen, setResumen] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadResumen() {
    if (!codigoEmpleado) {
      setError("Tu cuenta no está vinculada a un empleado. Pide al administrador que complete la configuración.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await asistenciaApi.obtenerResumenEmpleado(codigoEmpleado, 15);
      setResumen(data);
    } catch (err) {
      setError(err.message || "No fue posible cargar tu información.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadResumen();
  }, [codigoEmpleado]);

  const hoy = getLocalDateISO();
  const registroHoy = resumen?.asistencias_recientes?.find((d) => d.fecha === hoy);
  const periodo = resumen?.resumen_periodo;
  const empleado = resumen?.empleado;

  return (
    <div className="page-stack">
      <PageHeader
        title="Mi asistencia"
        description="Resumen de tu asistencia y puntualidad."
      >
        <div className="header-actions">
          <button
            className="secondary-button"
            type="button"
            disabled={loading}
            onClick={loadResumen}
          >
            <RefreshCw size={17} className={loading ? "spinning" : ""} />
            {loading ? "Actualizando..." : "Actualizar"}
          </button>
        </div>
      </PageHeader>

      {error && (
        <section className="panel-card">
          <div className="empty-state">
            <AlertTriangle size={42} />
            <h3>Error al cargar</h3>
            <p>{error}</p>
          </div>
        </section>
      )}

      {loading && !resumen && (
        <section className="panel-card">
          <div className="empty-state">
            <RefreshCw size={42} className="spinning" />
            <h3>Cargando...</h3>
            <p>Consultando tu información de asistencia.</p>
          </div>
        </section>
      )}

      {resumen && (
        <>
          {/* Hoy */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Hoy</h3>
                <p>{formatDate(hoy)}</p>
              </div>
              <CalendarDays size={22} />
            </div>

            {registroHoy ? (
              <div className="report-info-grid">
                <div>
                  <span>Estatus</span>
                  <strong>
                    <span className={getStatusClass(registroHoy.estatus)}>
                      {getStatusLabel(registroHoy.estatus)}
                    </span>
                  </strong>
                </div>
                <div>
                  <span>Entrada</span>
                  <strong>{formatTime(registroHoy.primera_entrada)}</strong>
                </div>
                <div>
                  <span>Salida</span>
                  <strong>{formatTime(registroHoy.ultima_salida)}</strong>
                </div>
                {registroHoy.minutos_retardo > 0 && (
                  <div>
                    <span>Retardo</span>
                    <strong>{registroHoy.minutos_retardo} min</strong>
                  </div>
                )}
                <div>
                  <span>Horas ordinarias</span>
                  <strong>{minutosAHoras(registroHoy.minutos_ordinarios)}</strong>
                </div>
                {registroHoy.minutos_extra > 0 && (
                  <div>
                    <span>Horas extra</span>
                    <strong>{minutosAHoras(registroHoy.minutos_extra)}</strong>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <Clock size={32} />
                <p>Sin registro procesado para hoy.</p>
              </div>
            )}
          </section>

          {/* Resumen del periodo */}
          {periodo && (
            <section className="metrics-grid four-columns">
              <article className="metric-card">
                <div className="metric-icon" style={{ color: "#10b981" }}>
                  <CheckCircle2 size={22} />
                </div>
                <div>
                  <p>Días completos</p>
                  <strong>{periodo.dias_completos}</strong>
                  <span>de {periodo.dias_laborales} laborales</span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-icon" style={{ color: "#ef4444" }}>
                  <AlertTriangle size={22} />
                </div>
                <div>
                  <p>Faltas</p>
                  <strong>{periodo.faltas}</strong>
                  <span>
                    {periodo.retardos_menores + periodo.retardos_mayores} retardos
                  </span>
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-icon" style={{ color: "#3b82f6" }}>
                  <Clock size={22} />
                </div>
                <div>
                  <p>Horas ordinarias</p>
                  <strong>{minutosAHoras(periodo.minutos_ordinarios)}</strong>
                  {periodo.minutos_extra > 0 && (
                    <span>+{minutosAHoras(periodo.minutos_extra)} extra</span>
                  )}
                </div>
              </article>

              <article className="metric-card">
                <div className="metric-icon" style={{ color: "#f59e0b" }}>
                  <CalendarDays size={22} />
                </div>
                <div>
                  <p>Puntos acumulados</p>
                  <strong>{periodo.puntos_efectivos ?? periodo.puntos_brutos ?? 0}</strong>
                  <span>en el periodo actual</span>
                </div>
              </article>
            </section>
          )}

          {/* Últimas asistencias */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Últimos registros</h3>
                <p>
                  {empleado?.nombre_completo} · {empleado?.codigo_empleado}
                </p>
              </div>
            </div>

            {(resumen.asistencias_recientes ?? []).length === 0 ? (
              <div className="empty-state">
                <CalendarDays size={32} />
                <p>Sin registros de asistencia.</p>
              </div>
            ) : (
              <div className="simple-table">
                <table>
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Entrada</th>
                      <th>Salida</th>
                      <th>Retardo</th>
                      <th>Horas</th>
                      <th>Estatus</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resumen.asistencias_recientes.map((dia) => (
                      <tr key={dia.id}>
                        <td>{formatDate(dia.fecha)}</td>
                        <td>{formatTime(dia.primera_entrada)}</td>
                        <td>{formatTime(dia.ultima_salida)}</td>
                        <td>{dia.minutos_retardo > 0 ? `${dia.minutos_retardo} min` : "—"}</td>
                        <td>{minutosAHoras(dia.minutos_ordinarios)}</td>
                        <td>
                          <span className={getStatusClass(dia.estatus)}>
                            {getStatusLabel(dia.estatus)}
                          </span>
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

// ─── Vista admin/supervisor ──────────────────────────────────────────────────

function AdminDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [error, setError] = useState("");

  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState(null);
  const [empleadosCategoria, setEmpleadosCategoria] = useState([]);
  const [loadingCategoria, setLoadingCategoria] = useState(false);
  const [errorCategoria, setErrorCategoria] = useState("");

  async function toggleCategoria(estatus) {
    if (categoriaSeleccionada === estatus) {
      setCategoriaSeleccionada(null);
      setEmpleadosCategoria([]);
      return;
    }
    setCategoriaSeleccionada(estatus);
    setErrorCategoria("");
    setLoadingCategoria(true);
    try {
      const hoy = getLocalDateISO();
      const result = await asistenciaApi.listarDiaria({ fecha: hoy, estatus, limit: 100 });
      console.log("listarDiaria response:", { hoy, estatus, total: result?.total, itemsLen: result?.items?.length, fechaResp: result?.fecha });
      setEmpleadosCategoria(result?.items ?? result ?? []);
    } catch (err) {
      console.error("toggleCategoria error:", err);
      setErrorCategoria(err.message || "Error al cargar empleados.");
      setEmpleadosCategoria([]);
    } finally {
      setLoadingCategoria(false);
    }
  }

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");
      try {
        const hoy = getLocalDateISO();
        await asistenciaApi.procesar({ fechaInicio: hoy, fechaFin: hoy });
      } catch {
        // sin permiso para procesar — se ignora en silencio
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
      const fechaFin = getLocalDateISO();
      const hace7dias = new Date();
      hace7dias.setDate(hace7dias.getDate() - 7);
      const y = hace7dias.getFullYear();
      const mo = String(hace7dias.getMonth() + 1).padStart(2, "0");
      const da = String(hace7dias.getDate()).padStart(2, "0");
      const fechaInicio = `${y}-${mo}-${da}`;
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
                      ) : errorCategoria ? (
                        <div className="empty-state">
                          <AlertTriangle size={28} />
                          <p style={{ color: "var(--color-danger)" }}>{errorCategoria}</p>
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

// ─── Enrutador de dashboard por rol ─────────────────────────────────────────

function DashboardPage() {
  const { user } = useAuth();

  if (user?.role === ROLES.EMPLEADO) {
    return <EmployeeDashboard codigoEmpleado={user.codigoEmpleado} />;
  }

  return <AdminDashboard />;
}

export default DashboardPage;
