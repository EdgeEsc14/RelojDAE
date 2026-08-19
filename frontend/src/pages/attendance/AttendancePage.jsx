import React, { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Download,
  FileWarning,
  Fingerprint,
  Search,
  SlidersHorizontal,
  TimerReset,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { DATA_SCOPES, MODULES } from "../../constants/permissions";
import { useAuth } from "../../context/AuthContext";
import { asistenciaApi } from "../../api/asistenciaApi";
import { catalogosApi } from "../../api/catalogosApi";
import { crearIncidencia } from "../../api/incidenciasApi";
import { getZkAttendanceFromDb } from "../../api/zkApi";
import { getModuleAccess } from "../../utils/permissions";

// ============================================================
// Utilidades
// ============================================================

function getTodayDateInputValue() {
  return new Date().toISOString().slice(0, 10);
}

function formatDate(value) {
  if (!value) return "";
  try {
    return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
  } catch { return String(value); }
}

function getDayName(value) {
  if (!value) return "";
  try {
    return new Intl.DateTimeFormat("es-MX", { weekday: "long" }).format(new Date(`${value}T00:00:00`));
  } catch { return ""; }
}

function formatTime(value) {
  if (!value) return "";
  return String(value).slice(11, 16) || String(value).slice(0, 5);
}

function formatMinutes(minutes) {
  const m = Number(minutes ?? 0);
  if (m === 0) return "0 min";
  const h = Math.floor(m / 60);
  const r = m % 60;
  if (h === 0) return `${r} min`;
  if (r === 0) return `${h} h`;
  return `${h} h ${r} min`;
}

function normalizeText(value) {
  return String(value ?? "").trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function formatAttendanceStatus(status) {
  const s = String(status ?? "").trim().toUpperCase();
  if (s === "COMPLETO") return "Completo";
  if (s === "RETARDO_MENOR") return "Retardo menor";
  if (s === "RETARDO_MAYOR") return "Retardo mayor";
  if (s === "FALTA") return "Falta";
  if (s === "OMISION_ENTRADA") return "Omisión entrada";
  if (s === "OMISION_SALIDA") return "Omisión salida";
  if (s === "EN_CURSO") return "En curso";
  if (s === "DIA_NO_LABORAL") return "No laboral";
  return status || "Sin procesar";
}

function getStatusClass(status) {
  if (status?.includes("Completo")) return "badge success";
  if (status?.includes("Retardo")) return "badge warning";
  if (status === "Falta" || status?.includes("Omisión")) return "badge danger";
  if (status === "En curso") return "badge neutral";
  if (status === "No laboral") return "badge neutral";
  return "badge neutral";
}

function mapRow(row) {
  return {
    id: row.asistencia_id || row.id,
    employeeId: row.empleado_id,
    employeeCode: row.codigo_empleado,
    employeeName: row.nombre_completo ?? row.empleado_nombre ?? "Sin nombre",
    department: row.unidad_organizacional_nombre ?? row.unidad_nombre ?? "Sin área",
    departmentId: row.unidad_organizacional_id,
    rawDate: row.fecha,
    date: formatDate(row.fecha),
    day: getDayName(row.fecha),
    expectedSchedule: `${formatTime(row.entrada_programada) || "—"} - ${formatTime(row.salida_programada) || "—"}`,
    entryTime: formatTime(row.primera_entrada),
    exitTime: formatTime(row.ultima_salida),
    lateMinutes: Number(row.minutos_retardo ?? 0),
    ordinaryTime: formatMinutes(row.minutos_ordinarios),
    extraTime: formatMinutes(row.minutos_extra),
    status: formatAttendanceStatus(row.estatus),
    rawStatus: row.estatus,
    points: Number(row.puntos_generados ?? 0),
    requiresReview: row.requiere_revision,
    observations: row.observaciones,
    raw: row,
  };
}

// ============================================================
// Componente principal
// ============================================================

function AttendancePage() {
  const { user } = useAuth();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [attendanceDate, setAttendanceDate] = useState(getTodayDateInputValue());
  const [reloadToken, setReloadToken] = useState(0);

  // Procesar
  const [processStartDate, setProcessStartDate] = useState(getTodayDateInputValue());
  const [processEndDate, setProcessEndDate] = useState(getTodayDateInputValue());
  const [isProcessing, setIsProcessing] = useState(false);
  const [processResult, setProcessResult] = useState(null);
  const [processError, setProcessError] = useState("");

  // Modal incidencia
  const [showIncidentModal, setShowIncidentModal] = useState(false);
  const [incidentRow, setIncidentRow] = useState(null);
  const [incidentTypeId, setIncidentTypeId] = useState("");
  const [incidentDescription, setIncidentDescription] = useState("");
  const [incidentLoading, setIncidentLoading] = useState(false);
  const [incidentError, setIncidentError] = useState("");
  const [incidentSuccess, setIncidentSuccess] = useState("");
  const [tiposIncidencia, setTiposIncidencia] = useState([]);

  // Expandir marcaciones crudas
  const [expandedRow, setExpandedRow] = useState(null);
  const [rawPunches, setRawPunches] = useState([]);
  const [rawLoading, setRawLoading] = useState(false);

  const attendanceAccess = getModuleAccess(user?.role, MODULES.ASISTENCIA);
  const canProcess = attendanceAccess === DATA_SCOPES.TOTAL;
  const canCreateIncident = [DATA_SCOPES.TOTAL, DATA_SCOPES.AREA].includes(attendanceAccess);

  const currentEmployeeId = user?.employeeId ?? user?.empleadoId ?? user?.raw?.empleado_id ?? null;
  const currentDepartmentId = user?.departmentId ?? user?.departamentoId ?? user?.raw?.department_id ?? null;

  // Cargar tipos de incidencia
  useEffect(() => {
    catalogosApi.listarTiposIncidencia().then((data) => {
      const items = Array.isArray(data) ? data : (data?.items || []);
      setTiposIncidencia(items.filter((t) => t.activo));
    }).catch(() => {});
  }, []);

  // Cargar asistencia
  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const response = await asistenciaApi.listarDiaria({ fecha: attendanceDate, limit: 100, offset: 0 });
        if (!mounted) return;
        const items = response?.items ?? response?.data ?? response?.resultados ?? [];
        setRecords(items.map(mapRow));
      } catch (err) {
        if (!mounted) return;
        setRecords([]);
        setError(err.message || "Error al cargar asistencia.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, [attendanceDate, reloadToken]);

  // Filtro por alcance
  const scopedRecords = useMemo(() => {
    return records.filter((row) => {
      if (attendanceAccess === DATA_SCOPES.TOTAL) return true;
      if (attendanceAccess === DATA_SCOPES.AREA) return Number(row.departmentId) === Number(currentDepartmentId);
      if (attendanceAccess === DATA_SCOPES.PROPIO) return Number(row.employeeId) === Number(currentEmployeeId);
      return false;
    });
  }, [records, attendanceAccess, currentDepartmentId, currentEmployeeId]);

  // Filtro por búsqueda
  const visibleRecords = useMemo(() => {
    const term = normalizeText(searchTerm);
    if (!term) return scopedRecords;
    return scopedRecords.filter((row) =>
      [row.employeeName, row.department, row.date, row.day, row.status].some((v) => normalizeText(v).includes(term))
    );
  }, [scopedRecords, searchTerm]);

  // Métricas
  const totalRecords = visibleRecords.length;
  const completeDays = visibleRecords.filter((r) => r.status?.includes("Completo")).length;
  const lateDays = visibleRecords.filter((r) => r.status?.includes("Retardo")).length;
  const faltaDays = visibleRecords.filter((r) => r.status === "Falta" || r.status?.includes("Omisión")).length;

  // Procesar asistencia
  async function handleProcess(e) {
    e.preventDefault();
    if (!processStartDate || !processEndDate) { setProcessError("Selecciona ambas fechas."); return; }
    if (processStartDate > processEndDate) { setProcessError("Fecha inicio mayor que fin."); return; }
    setIsProcessing(true); setProcessError(""); setProcessResult(null);
    try {
      const res = await asistenciaApi.procesar({ fechaInicio: processStartDate, fechaFin: processEndDate });
      setProcessResult(res);
      setAttendanceDate(processEndDate);
      setReloadToken((t) => t + 1);
    } catch (err) { setProcessError(err.message || "Error al procesar."); }
    finally { setIsProcessing(false); }
  }

  // Expandir marcaciones crudas
  async function toggleRawPunches(row) {
    if (expandedRow === row.id) {
      setExpandedRow(null);
      setRawPunches([]);
      return;
    }
    setExpandedRow(row.id);
    setRawPunches([]);
    setRawLoading(true);
    try {
      const zkUserId = row.raw?.zk_user_id || "";
      if (!zkUserId) {
        setRawPunches([]);
        setRawLoading(false);
        return;
      }
      const result = await getZkAttendanceFromDb({
        limit: 50,
        userId: zkUserId,
        dateFrom: row.rawDate,
        dateTo: row.rawDate,
      });
      setRawPunches(result.records || []);
    } catch {
      setRawPunches([]);
    } finally {
      setRawLoading(false);
    }
  }

  // Modal incidencia
  function openIncidentModal(row) {
    setIncidentRow(row);
    setIncidentTypeId("");
    setIncidentDescription("");
    setIncidentError("");
    setIncidentSuccess("");
    setShowIncidentModal(true);
  }

  async function handleCreateIncident(e) {
    e.preventDefault();
    if (!incidentTypeId) { setIncidentError("Selecciona un tipo de incidencia."); return; }
    setIncidentLoading(true); setIncidentError("");
    try {
      await crearIncidencia({
        empleado_id: incidentRow.employeeId,
        tipo_incidencia_id: Number(incidentTypeId),
        fecha: incidentRow.rawDate,
        descripcion: incidentDescription.trim() || null,
        puntos_originales: incidentRow.points,
      });
      setIncidentSuccess("Incidencia registrada correctamente.");
      setTimeout(() => { setShowIncidentModal(false); setReloadToken((t) => t + 1); }, 1500);
    } catch (err) {
      setIncidentError(err.message || "Error al crear incidencia.");
    } finally { setIncidentLoading(false); }
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Asistencia"
        description="Entradas, salidas, retardos y faltas procesadas. Crea justificantes o revisa marcaciones originales."
      >
        <div className="header-actions">
          {canProcess && (
            <button className="primary-button" type="button" onClick={() => document.getElementById("processSection")?.scrollIntoView({ behavior: "smooth" })}>
              <TimerReset size={17} />
              Procesar periodo
            </button>
          )}
        </div>
      </PageHeader>

      {/* Métricas */}
      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon"><CalendarDays size={22} /></div>
          <div><p>Registros</p><strong>{totalRecords}</strong><span>Del día seleccionado</span></div>
        </article>
        <article className="metric-card">
          <div className="metric-icon" style={{ color: "#10b981" }}><CheckCircle2 size={22} /></div>
          <div><p>Completos</p><strong>{completeDays}</strong><span>Entrada y salida OK</span></div>
        </article>
        <article className="metric-card">
          <div className="metric-icon" style={{ color: "#f59e0b" }}><Clock size={22} /></div>
          <div><p>Retardos</p><strong>{lateDays}</strong><span>Fuera de tolerancia</span></div>
        </article>
        <article className="metric-card">
          <div className="metric-icon" style={{ color: "#ef4444" }}><AlertTriangle size={22} /></div>
          <div><p>Faltas / Omisiones</p><strong>{faltaDays}</strong><span>Requieren atención</span></div>
        </article>
      </section>

      {/* Procesamiento (solo admins) */}
      {canProcess && (
        <section className="panel-card" id="processSection">
          <div className="panel-header">
            <div><h3>Procesar asistencia</h3><p>Genera registros de asistencia a partir de marcaciones sincronizadas.</p></div>
            <TimerReset size={22} />
          </div>
          <form onSubmit={handleProcess} style={{ display: "flex", gap: "12px", alignItems: "flex-end", flexWrap: "wrap" }}>
            <div className="form-field" style={{ minWidth: "140px" }}>
              <label htmlFor="pStart">Desde</label>
              <input id="pStart" type="date" value={processStartDate} onChange={(e) => setProcessStartDate(e.target.value)} />
            </div>
            <div className="form-field" style={{ minWidth: "140px" }}>
              <label htmlFor="pEnd">Hasta</label>
              <input id="pEnd" type="date" value={processEndDate} onChange={(e) => setProcessEndDate(e.target.value)} />
            </div>
            <button className="primary-button" type="submit" disabled={isProcessing}>
              <TimerReset size={17} /> {isProcessing ? "Procesando..." : "Procesar"}
            </button>
          </form>
          {processError && <p style={{ color: "var(--color-danger-text)", marginTop: "8px" }}>{processError}</p>}
          {processResult && <p style={{ color: "var(--color-success-text)", marginTop: "8px" }}>Procesado: {processResult.registros_encontrados ?? processResult.procesados ?? 0} registros.</p>}
        </section>
      )}

      {/* Tabla de asistencia */}
      <section className="panel-card">
        <div className="filters-row">
          <div className="form-field compact-field">
            <label htmlFor="attDate">Fecha</label>
            <input id="attDate" type="date" value={attendanceDate} onChange={(e) => setAttendanceDate(e.target.value)} />
          </div>
          <div className="filter-search">
            <Search size={18} />
            <input type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Buscar empleado, área, estado..." />
          </div>
        </div>

        {error && <div className="empty-state"><AlertTriangle size={32} /><p>{error}</p></div>}
        {loading && <div className="empty-state"><Clock size={32} /><p>Cargando asistencia...</p></div>}
        {!loading && !error && visibleRecords.length === 0 && (
          <div className="empty-state"><CalendarDays size={32} /><h3>Sin registros</h3><p>No hay asistencia procesada para esta fecha.</p></div>
        )}

        {!loading && visibleRecords.length > 0 && (
          <div className="simple-table">
            <table>
              <thead>
                <tr>
                  <th>Empleado</th>
                  <th>Horario</th>
                  <th>Entrada</th>
                  <th>Salida</th>
                  <th>Retardo</th>
                  <th>Ordinario</th>
                  <th>Extra</th>
                  <th>Estado</th>
                  <th>Puntos</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {visibleRecords.map((row) => (
                  <React.Fragment key={row.id}>
                    <tr>
                      <td>
                        <div className="employee-cell">
                          <div className="employee-avatar">{row.employeeName.charAt(0)}</div>
                          <div><strong>{row.employeeName}</strong><span>{row.department}</span></div>
                        </div>
                      </td>
                      <td>{row.expectedSchedule}</td>
                      <td>{row.entryTime || "—"}</td>
                      <td>{row.exitTime || "—"}</td>
                      <td>{row.lateMinutes > 0 ? `${row.lateMinutes} min` : "—"}</td>
                      <td>{row.ordinaryTime}</td>
                      <td>{row.extraTime}</td>
                      <td><span className={getStatusClass(row.status)}>{row.status}</span></td>
                      <td>{row.points > 0 ? <strong style={{ color: "#ef4444" }}>{row.points}</strong> : "0"}</td>
                      <td>
                        <div className="table-actions-group">
                          {canCreateIncident && (
                            <button
                              className="secondary-button"
                              type="button"
                              onClick={() => openIncidentModal(row)}
                              title="Crear justificante / incidencia"
                              style={{ padding: "6px 10px" }}
                            >
                              <FileWarning size={14} />
                            </button>
                          )}
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={() => toggleRawPunches(row)}
                            title="Ver marcaciones crudas"
                            style={{ padding: "6px 10px" }}
                          >
                            {expandedRow === row.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          </button>
                        </div>
                      </td>
                    </tr>

                    {/* Fila expandible: marcaciones crudas */}
                    {expandedRow === row.id && (
                      <tr>
                        <td colSpan={10} style={{ background: "var(--color-surface-soft)", padding: "12px 16px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                            <Fingerprint size={16} />
                            <strong style={{ fontSize: "13px" }}>Marcaciones crudas del {row.date}</strong>
                          </div>
                          {rawLoading ? (
                            <p style={{ fontSize: "13px", color: "var(--color-text-muted)" }}>Cargando...</p>
                          ) : rawPunches.length === 0 ? (
                            <p style={{ fontSize: "13px", color: "var(--color-text-muted)" }}>Sin marcaciones sincronizadas para este empleado en esta fecha.</p>
                          ) : (
                            <table style={{ width: "100%", fontSize: "12px", borderCollapse: "collapse" }}>
                              <thead>
                                <tr style={{ borderBottom: "1px solid var(--color-border-soft)" }}>
                                  <th style={{ padding: "6px 8px", textAlign: "left" }}>Hora</th>
                                  <th style={{ padding: "6px 8px", textAlign: "left" }}>Evento</th>
                                  <th style={{ padding: "6px 8px", textAlign: "left" }}>Verificación</th>
                                  <th style={{ padding: "6px 8px", textAlign: "left" }}>Dispositivo</th>
                                </tr>
                              </thead>
                              <tbody>
                                {rawPunches.map((p, i) => (
                                  <tr key={i} style={{ borderBottom: "1px solid var(--color-border-soft)" }}>
                                    <td style={{ padding: "6px 8px" }}><strong>{(p.fecha_hora || "").slice(11, 19) || (p.hora || "—")}</strong></td>
                                    <td style={{ padding: "6px 8px" }}><span className={Number(p.punch) === 0 ? "badge success" : "badge warning"}>{p.punch_label || `Punch ${p.punch}`}</span></td>
                                    <td style={{ padding: "6px 8px" }}>{p.status_label || `Status ${p.status}`}</td>
                                    <td style={{ padding: "6px 8px" }}>{p.dispositivo_ip || p.dispositivo_origen || "—"}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Modal de incidencia */}
      {showIncidentModal && incidentRow && (
        <div className="modal-overlay" onClick={() => setShowIncidentModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Registrar justificante</h3>
              <button className="modal-close" type="button" onClick={() => setShowIncidentModal(false)}>
                <AlertTriangle size={0} /><span style={{ fontSize: "20px" }}>&times;</span>
              </button>
            </div>
            <form className="modal-body" onSubmit={handleCreateIncident}>
              <div style={{ marginBottom: "16px", padding: "12px", background: "var(--color-surface-soft)", borderRadius: "12px" }}>
                <strong>{incidentRow.employeeName}</strong>
                <p style={{ margin: "4px 0 0", color: "var(--color-text-muted)", fontSize: "13px" }}>
                  {incidentRow.date} — Estado: <span className={getStatusClass(incidentRow.status)}>{incidentRow.status}</span>
                  {incidentRow.points > 0 && ` — ${incidentRow.points} punto(s)`}
                </p>
              </div>

              {incidentError && <div className="form-error-message">{incidentError}</div>}
              {incidentSuccess && <div className="form-error-message" style={{ background: "#f0fdf4", borderColor: "#86efac", color: "#166534" }}>{incidentSuccess}</div>}

              <div className="form-field">
                <label>Tipo de incidencia</label>
                <select value={incidentTypeId} onChange={(e) => setIncidentTypeId(e.target.value)}>
                  <option value="">Selecciona tipo...</option>
                  {tiposIncidencia.map((t) => (
                    <option key={t.id} value={t.id}>{t.nombre} ({t.categoria})</option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label>Descripción / Justificación</label>
                <textarea
                  rows={3}
                  value={incidentDescription}
                  onChange={(e) => setIncidentDescription(e.target.value)}
                  placeholder="Motivo del justificante (ej: cita médica, comisión, permiso autorizado...)"
                  style={{ width: "100%", borderRadius: "12px", border: "1px solid var(--color-border)", padding: "12px" }}
                />
              </div>

              <div className="modal-footer">
                <button className="secondary-button" type="button" onClick={() => setShowIncidentModal(false)}>Cancelar</button>
                <button className="primary-button" type="submit" disabled={incidentLoading}>
                  {incidentLoading ? "Registrando..." : "Registrar justificante"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AttendancePage;
