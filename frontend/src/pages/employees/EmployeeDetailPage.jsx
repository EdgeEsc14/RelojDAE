import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  CalendarClock,
  Check,
  CheckCircle2,
  Clock,
  FileText,
  Fingerprint,
  Loader,
  Pencil,
  RefreshCcw,
  ShieldCheck,
  UserRound,
  Wifi,
  X,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { empleadosApi } from "../../api/empleadosApi";
import { asistenciaApi } from "../../api/asistenciaApi";
import { catalogosApi } from "../../api/catalogosApi";
import { horariosApi } from "../../api/horariosApi";

function formatDate(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
  } catch { return value; }
}

function formatDateTime(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
  } catch { return value; }
}

function formatTime(value) {
  if (!value) return "—";
  return String(value).slice(0, 5);
}

function getStatusClass(s) {
  const v = (s || "").toUpperCase();
  if (v === "ACTIVO" || v === "COMPLETO" || v === "SINCRONIZADO") return "badge success";
  if (v.includes("RETARDO")) return "badge warning";
  if (v === "FALTA" || v === "ERROR") return "badge danger";
  if (v === "PENDIENTE") return "badge warning";
  return "badge neutral";
}

function EmployeeDetailPage() {
  const { employeeId } = useParams();

  const [profile, setProfile] = useState(null);
  const [attendance, setAttendance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ZK verification
  const [zkResult, setZkResult] = useState(null);
  const [zkLoading, setZkLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  // Horario change
  const [showHorarioModal, setShowHorarioModal] = useState(false);
  const [horarios, setHorarios] = useState([]);
  const [selectedHorario, setSelectedHorario] = useState("");
  const [horarioLoading, setHorarioLoading] = useState(false);
  const [horarioError, setHorarioError] = useState("");

  useEffect(() => { loadData(); }, [employeeId]);

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [profileData, attendanceData] = await Promise.all([
        empleadosApi.obtenerPerfil(employeeId),
        asistenciaApi.obtenerResumenEmpleado(employeeId).catch(() => null),
      ]);
      setProfile(profileData);
      setAttendance(attendanceData);
    } catch (err) {
      setError(err.message || "Error al cargar datos.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerificarZk() {
    setZkLoading(true);
    setZkResult(null);
    try {
      const result = await empleadosApi.verificarZk(employeeId);
      setZkResult(result);
    } catch (err) {
      setZkResult({ ok: false, error: err.message });
    } finally {
      setZkLoading(false);
    }
  }

  async function handleReintentarSync() {
    setSyncLoading(true);
    setSyncResult(null);
    try {
      const dispositivo = profile?.dispositivo;
      const dispId = dispositivo?.dispositivo_id || dispositivo?.id || 1;
      const result = await empleadosApi.reintentarSincronizacion(employeeId, dispId);
      setSyncResult(result);
      loadData();
    } catch (err) {
      setSyncResult({ ok: false, error: err.message });
    } finally {
      setSyncLoading(false);
    }
  }

  async function openHorarioModal() {
    setShowHorarioModal(true);
    setHorarioError("");
    try {
      const data = await horariosApi.listar();
      setHorarios(data?.items || data || []);
    } catch (err) {
      setHorarioError("Error cargando horarios: " + err.message);
    }
  }

  async function handleCambiarHorario(e) {
    e.preventDefault();
    if (!selectedHorario) { setHorarioError("Selecciona un horario."); return; }
    setHorarioLoading(true);
    setHorarioError("");
    try {
      await empleadosApi.asignarHorario(employeeId, {
        horario_id: Number(selectedHorario),
        fecha_inicio: new Date().toISOString().split("T")[0],
        cerrar_asignaciones_activas: true,
      });
      setShowHorarioModal(false);
      loadData();
    } catch (err) {
      setHorarioError(err.message || "Error al cambiar horario.");
    } finally {
      setHorarioLoading(false);
    }
  }

  if (loading) return <div className="page-stack"><div className="panel-card"><div className="empty-state"><p>Cargando empleado...</p></div></div></div>;
  if (error) return <div className="page-stack"><div className="panel-card"><div className="empty-state"><p>{error}</p></div></div></div>;
  if (!profile) return null;

  const emp = profile.empleado || profile;
  const horario = profile.horario_actual;
  const dispositivo = profile.dispositivo;
  const puesto = profile.puesto;
  const supervisor = profile.supervisor;
  const unidad = profile.unidad_organizacional;

  const resumen = attendance?.resumen_periodo;
  const asistencias = attendance?.asistencias_recientes || [];
  const incidencias = attendance?.incidencias_recientes || [];

  const zkUserIdDisplay = dispositivo?.zk_user_id || emp?.zk_user_id || null;
  const syncEstado = dispositivo?.estado_sincronizacion || (zkUserIdDisplay ? "DESCONOCIDO" : null);

  return (
    <div className="page-stack">
      <PageHeader
        title={emp.nombre_completo || "Empleado"}
        description={`${emp.codigo_empleado} — ${puesto?.nombre || "Sin puesto"}`}
      >
        <div className="header-actions">
          <Link className="secondary-button link-button" to="/employees"><ArrowLeft size={17} /> Volver</Link>
          <Link className="secondary-button link-button" to={`/employees/${employeeId}/edit`}><Pencil size={17} /> Editar</Link>
        </div>
      </PageHeader>

      {/* Información */}
      <section className="panel-card">
        <div className="panel-header">
          <div><h3>Información del empleado</h3></div>
          <UserRound size={22} />
        </div>
        <div className="report-info-grid">
          <div><span>Código</span><strong>{emp.codigo_empleado}</strong></div>
          <div><span>Nombre</span><strong>{emp.nombre_completo}</strong></div>
          <div><span>RFC</span><strong>{emp.rfc || "—"}</strong></div>
          <div><span>Correo</span><strong>{emp.correo || emp.correo_personal || "—"}</strong></div>
          <div><span>Fecha ingreso</span><strong>{formatDate(emp.fecha_ingreso)}</strong></div>
          <div><span>Estatus</span><strong><span className={getStatusClass(emp.estatus)}>{emp.estatus}</span></strong></div>
          <div><span>Área</span><strong>{unidad?.nombre || "—"}</strong></div>
          <div><span>Puesto</span><strong>{puesto?.nombre || "—"}</strong></div>
          <div><span>Supervisor</span><strong>{supervisor?.nombre_completo || "Sin supervisor"}</strong></div>
        </div>
      </section>

      {/* ZKTeco */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>ZKTeco</h3>
            <p>{zkUserIdDisplay ? `User ID: ${zkUserIdDisplay}` : "Sin usuario ZK asignado"}</p>
          </div>
          <Fingerprint size={22} />
        </div>
        <div className="report-info-grid">
          <div><span>Dispositivo</span><strong>{dispositivo?.dispositivo_nombre || "Sin dispositivo"}</strong></div>
          <div><span>ZK User ID</span><strong>{zkUserIdDisplay || "—"}</strong></div>
          <div><span>Estado sincronización</span><strong><span className={getStatusClass(syncEstado)}>{syncEstado || "N/A"}</span></strong></div>
          <div><span>Nombre en reloj</span><strong>{dispositivo?.nombre_en_dispositivo || "—"}</strong></div>
          <div><span>Huella</span><strong>No verificable desde web</strong></div>
        </div>

        <div className="modal-footer" style={{ borderTop: "none", paddingTop: "12px" }}>
          <button className="secondary-button" type="button" onClick={handleVerificarZk} disabled={zkLoading}>
            {zkLoading ? <Loader size={17} /> : <Wifi size={17} />}
            {zkLoading ? "Verificando..." : "Verificar en reloj"}
          </button>
          {(syncEstado === "PENDIENTE" || syncEstado === "ERROR") && (
            <button className="primary-button" type="button" onClick={handleReintentarSync} disabled={syncLoading}>
              {syncLoading ? <Loader size={17} /> : <RefreshCcw size={17} />}
              {syncLoading ? "Sincronizando..." : "Reintentar registro"}
            </button>
          )}
        </div>

        {zkResult && (
          <div style={{ marginTop: "12px" }}>
            {zkResult.existe_en_reloj ? (
              <div className="form-error-message" style={{ background: "#f0fdf4", borderColor: "#86efac", color: "#166534" }}>
                Usuario {zkResult.zk_user_id} encontrado en reloj como "{zkResult.nombre_en_reloj}". Huella: {zkResult.huella === "NO_VERIFICABLE" ? "No verificable desde web" : zkResult.huella}.
              </div>
            ) : zkResult.ok ? (
              <div className="form-error-message" style={{ background: "#fffbeb", borderColor: "#fde68a", color: "#92400e" }}>
                {zkResult.mensaje}
              </div>
            ) : (
              <div className="form-error-message">
                Error: {zkResult.error || zkResult.mensaje}
              </div>
            )}
          </div>
        )}

        {syncResult && (
          <div style={{ marginTop: "8px" }}>
            {syncResult.exitosos > 0 ? (
              <div className="form-error-message" style={{ background: "#f0fdf4", borderColor: "#86efac", color: "#166534" }}>
                Sincronización exitosa. Usuario registrado en el reloj.
              </div>
            ) : (
              <div className="form-error-message">
                Error en sincronización: {syncResult.error || JSON.stringify(syncResult.resultados?.[0]?.error || "Desconocido")}
              </div>
            )}
          </div>
        )}
      </section>

      {/* Horario */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Horario</h3>
            <p>{horario ? horario.nombre : "Sin horario asignado"}</p>
          </div>
          <CalendarClock size={22} />
        </div>

        {horario ? (
          <div className="report-info-grid">
            <div><span>Nombre</span><strong>{horario.nombre}</strong></div>
            <div><span>Turno</span><strong>{horario.tipo_turno_nombre || "—"}</strong></div>
            <div><span>Entrada</span><strong>{formatTime(horario.hora_entrada)}</strong></div>
            <div><span>Salida</span><strong>{formatTime(horario.hora_salida)}</strong></div>
            <div><span>Tolerancia</span><strong>{horario.tolerancia_entrada_minutos || 0} min</strong></div>
            <div><span>Vigencia desde</span><strong>{formatDate(horario.fecha_inicio)}</strong></div>
          </div>
        ) : (
          <p style={{ color: "#6b7280", padding: "8px 0" }}>No hay horario activo asignado.</p>
        )}

        <div className="modal-footer" style={{ borderTop: "none", paddingTop: "12px" }}>
          <button className="secondary-button" type="button" onClick={openHorarioModal}>
            <CalendarClock size={17} />
            Cambiar horario
          </button>
        </div>
      </section>

      {/* Asistencia */}
      <section className="panel-card">
        <div className="panel-header">
          <div><h3>Asistencia</h3></div>
          <Clock size={22} />
        </div>

        {resumen ? (
          <div className="report-info-grid">
            <div><span>Días completos</span><strong>{resumen.dias_completos ?? 0}</strong></div>
            <div><span>Retardos menores</span><strong>{resumen.retardos_menores ?? 0}</strong></div>
            <div><span>Retardos mayores</span><strong>{resumen.retardos_mayores ?? 0}</strong></div>
            <div><span>Faltas</span><strong>{resumen.faltas ?? 0}</strong></div>
            <div><span>Puntos brutos</span><strong>{resumen.puntos_brutos ?? 0}</strong></div>
            <div><span>Horas ordinarias</span><strong>{resumen.minutos_ordinarios ? Math.round(resumen.minutos_ordinarios / 60) + "h" : "0h"}</strong></div>
          </div>
        ) : (
          <p style={{ color: "#6b7280", padding: "8px 0" }}>Sin datos de resumen de periodo.</p>
        )}

        {asistencias.length > 0 && (
          <div className="simple-table" style={{ marginTop: "16px" }}>
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Entrada</th>
                  <th>Salida</th>
                  <th>Retardo</th>
                  <th>Estatus</th>
                  <th>Puntos</th>
                </tr>
              </thead>
              <tbody>
                {asistencias.slice(0, 10).map((row) => (
                  <tr key={row.id || row.fecha}>
                    <td>{formatDate(row.fecha)}</td>
                    <td>{formatTime(row.primera_entrada)}</td>
                    <td>{formatTime(row.ultima_salida)}</td>
                    <td>{row.minutos_retardo || 0} min</td>
                    <td><span className={getStatusClass(row.estatus)}>{row.estatus}</span></td>
                    <td>{row.puntos_generados || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Incidencias */}
      {incidencias.length > 0 && (
        <section className="panel-card">
          <div className="panel-header">
            <div><h3>Incidencias recientes</h3></div>
            <FileText size={22} />
          </div>
          <div className="simple-table">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Estatus</th>
                  <th>Puntos</th>
                </tr>
              </thead>
              <tbody>
                {incidencias.slice(0, 10).map((row) => (
                  <tr key={row.id || row.fecha}>
                    <td>{formatDate(row.fecha)}</td>
                    <td>{row.tipo_nombre || row.tipo_codigo || "—"}</td>
                    <td><span className={getStatusClass(row.estatus)}>{row.estatus}</span></td>
                    <td>{row.puntos_efectivos || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Modal cambiar horario */}
      {showHorarioModal && (
        <div className="modal-overlay" onClick={() => setShowHorarioModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Cambiar horario</h3>
              <button className="modal-close" type="button" onClick={() => setShowHorarioModal(false)}><X size={20} /></button>
            </div>
            <form className="modal-body" onSubmit={handleCambiarHorario}>
              {horarioError && <div className="form-error-message">{horarioError}</div>}

              <div className="form-field">
                <label htmlFor="horario-select">Seleccionar horario</label>
                <select id="horario-select" value={selectedHorario} onChange={(e) => setSelectedHorario(e.target.value)}>
                  <option value="">Seleccionar...</option>
                  {horarios.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.nombre} — {h.hora_entrada ? `${String(h.hora_entrada).slice(0,5)}-${String(h.hora_salida).slice(0,5)}` : ""}
                    </option>
                  ))}
                </select>
              </div>

              {selectedHorario && (() => {
                const h = horarios.find((x) => String(x.id) === selectedHorario);
                if (!h) return null;
                return (
                  <div className="report-info-grid" style={{ marginTop: "8px" }}>
                    <div><span>Nombre</span><strong>{h.nombre}</strong></div>
                    <div><span>Entrada</span><strong>{formatTime(h.hora_entrada)}</strong></div>
                    <div><span>Salida</span><strong>{formatTime(h.hora_salida)}</strong></div>
                    <div><span>Tolerancia</span><strong>{h.tolerancia_entrada_minutos || 0} min</strong></div>
                  </div>
                );
              })()}

              <div className="modal-footer">
                <button className="secondary-button" type="button" onClick={() => setShowHorarioModal(false)}>Cancelar</button>
                <button className="primary-button" type="submit" disabled={horarioLoading}>
                  {horarioLoading ? "Guardando..." : <><Check size={17} /> Asignar horario</>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default EmployeeDetailPage;
