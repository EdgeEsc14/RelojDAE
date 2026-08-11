import { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock,
  Download,
  Search,
  SlidersHorizontal,
  TimerReset,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";

import {
  DATA_SCOPES,
  MODULES,
} from "../../constants/permissions";

import { useAuth } from "../../context/AuthContext";
import { asistenciaApi } from "../../api/asistenciaApi";
import { getModuleAccess } from "../../utils/permissions";

function getStatusClass(status) {
  if (status === "Completo") return "badge success";
  if (status === "Completo con tiempo extra") return "badge success";
  if (status === "Retardo") return "badge warning";
  if (status === "Omisión de salida") return "badge danger";
  if (status === "Falta") return "badge danger";

  return "badge neutral";
}

function getIncidentClass(status) {
  if (status === "Pendiente") return "badge warning";
  if (status === "Sin justificar") return "badge danger";
  if (status === "No aplica") return "badge neutral";
  if (status === "Aprobada") return "badge success";

  return "badge neutral";
}

function normalizeText(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}
function getTodayDateInputValue() {
  return new Date().toISOString().slice(0, 10);
}
function formatDate(value) {
  if (!value) return "";

  try {
    return new Intl.DateTimeFormat("es-MX", {
      dateStyle: "medium",
    }).format(new Date(`${value}T00:00:00`));
  } catch {
    return String(value);
  }
}

function getDayName(value) {
  if (!value) return "";

  try {
    return new Intl.DateTimeFormat("es-MX", {
      weekday: "long",
    }).format(new Date(`${value}T00:00:00`));
  } catch {
    return "";
  }
}

function formatTime(value) {
  if (!value) return "";

  return String(value).slice(11, 16) !== ""
    ? String(value).slice(11, 16)
    : String(value).slice(0, 5);
}

function formatMinutesAsDuration(minutes) {
  const safeMinutes = Number(minutes ?? 0);

  const hours = Math.floor(safeMinutes / 60);
  const remainingMinutes = safeMinutes % 60;

  if (hours === 0) {
    return `${remainingMinutes} min`;
  }

  if (remainingMinutes === 0) {
    return `${hours} h`;
  }

  return `${hours} h ${remainingMinutes} min`;
}

function formatAttendanceStatus(status) {
  const normalized = String(status ?? "")
    .trim()
    .toUpperCase();

  if (normalized === "COMPLETO") return "Completo";
  if (normalized === "RETARDO_MENOR") return "Retardo menor";
  if (normalized === "RETARDO_MAYOR") return "Retardo mayor";
  if (normalized === "FALTA") return "Falta";
  if (normalized === "OMISION_ENTRADA") return "Omisión de entrada";
  if (normalized === "OMISION_SALIDA") return "Omisión de salida";

  return status || "Sin procesar";
}

function getItemsFromApiResponse(response) {
  return (
    response?.items ??
    response?.data ??
    response?.resultados ??
    []
  );
}

function mapAttendanceRowFromApi(row) {
  return {
    id: row.id,

    employeeId: row.empleado_id,
    employeeCode: row.codigo_empleado,
    employeeName:
      row.nombre_completo ??
      row.empleado_nombre ??
      "Empleado sin nombre",

    departmentId: row.unidad_organizacional_id,
    department:
      row.unidad_organizacional_nombre ??
      row.unidad_nombre ??
      "Sin área",

    date: formatDate(row.fecha),
    rawDate: row.fecha,
    day: getDayName(row.fecha),

    expectedSchedule: `${formatTime(row.entrada_programada) || "—"} - ${
      formatTime(row.salida_programada) || "—"
    }`,

    entryTime: formatTime(row.primera_entrada),
    exitTime: formatTime(row.ultima_salida),

    lateMinutes: Number(row.minutos_retardo ?? 0),
    ordinaryTime: formatMinutesAsDuration(row.minutos_ordinarios),
    extraTime: formatMinutesAsDuration(row.minutos_extra),

    status: formatAttendanceStatus(row.estatus),

    incident: row.requiere_revision
      ? row.observaciones || "Requiere revisión"
      : "Sin incidencia",

    incidentStatus: row.requiere_revision
      ? "Pendiente"
      : "No aplica",

    source: "Procesada",
    points: Number(row.puntos_generados ?? 0),
    raw: row,
  };
}
function AttendancePage() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState("");
  const [attendanceDate, setAttendanceDate] = useState(
    getTodayDateInputValue(),
  );

  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [isLoadingAttendance, setIsLoadingAttendance] = useState(false);
  const [attendanceError, setAttendanceError] = useState("");
  const [reloadAttendanceToken, setReloadAttendanceToken] = useState(0);
  const [processStartDate, setProcessStartDate] = useState(
    getTodayDateInputValue(),
  );

  const [processEndDate, setProcessEndDate] = useState(
    getTodayDateInputValue(),
  );

  const [isProcessingAttendance, setIsProcessingAttendance] =
    useState(false);

  const [processResult, setProcessResult] = useState(null);
  const [processError, setProcessError] = useState("");
  const currentEmployeeId =
    user?.employeeId ??
    user?.empleadoId ??
    user?.raw?.empleado_id ??
    null;

  const currentDepartmentId =
    user?.departmentId ??
    user?.departamentoId ??
    user?.raw?.department_id ??
    user?.raw?.departamento_id ??
    null;

  useEffect(() => {
    let isMounted = true;

    async function loadAttendanceRecords() {
      try {
        setIsLoadingAttendance(true);
        setAttendanceError("");

        const response = await asistenciaApi.listarDiaria({
          fecha: attendanceDate,
          limit: 100,
          offset: 0,
        });

        if (!isMounted) return;

        const records = getItemsFromApiResponse(response).map(
          mapAttendanceRowFromApi,
        );

        setAttendanceRecords(records);
      } catch (error) {
        if (!isMounted) return;

        setAttendanceRecords([]);
        setAttendanceError(
          error.message ||
            "No fue posible cargar la asistencia procesada.",
        );
      } finally {
        if (isMounted) {
          setIsLoadingAttendance(false);
        }
      }
    }

    loadAttendanceRecords();

    return () => {
      isMounted = false;
    };
  }, [attendanceDate, reloadAttendanceToken]);




  const attendanceAccess = getModuleAccess(
    user?.role,
    MODULES.ASISTENCIA,
  );

  /**
   * Primer filtro: seguridad y alcance del usuario.
   *
   * TOTAL   -> todos los registros.
   * AREA    -> solamente su departamento.
   * PROPIO  -> solamente su employeeId.
   */
  const scopedAttendanceRecords = useMemo(() => {
    return attendanceRecords.filter((row) => {
      if (attendanceAccess === DATA_SCOPES.TOTAL) {
        return true;
      }

      if (attendanceAccess === DATA_SCOPES.AREA) {
        return Number(row.departmentId) === Number(currentDepartmentId);
      }

      if (attendanceAccess === DATA_SCOPES.PROPIO) {
        return Number(row.employeeId) === Number(currentEmployeeId);
      }

      return false;
    });
  }, [
    attendanceAccess,
    attendanceRecords,
    currentDepartmentId,
    currentEmployeeId,
  ]);

  /**
   * Segundo filtro: búsqueda del usuario.
   *
   * Se aplica después del filtro de seguridad para que un empleado
   * nunca pueda buscar datos de otros empleados.
   */
  const visibleAttendanceRecords = useMemo(() => {
    const normalizedSearch = normalizeText(searchTerm);

    if (!normalizedSearch) {
      return scopedAttendanceRecords;
    }

    return scopedAttendanceRecords.filter((row) => {
      const searchableValues = [
        row.employeeName,
        row.department,
        row.date,
        row.day,
        row.expectedSchedule,
        row.status,
        row.incident,
        row.incidentStatus,
        row.source,
      ];

      return searchableValues.some((value) =>
        normalizeText(value).includes(normalizedSearch),
      );
    });
  }, [scopedAttendanceRecords, searchTerm]);

  /**
   * Las métricas se calculan únicamente con los registros permitidos
   * y actualmente visibles después de la búsqueda.
   */
  const totalRecords = visibleAttendanceRecords.length;

  const completeDays = visibleAttendanceRecords.filter((row) =>
    row.status?.includes("Completo"),
  ).length;

  const lateDays = visibleAttendanceRecords.filter(
    (row) => row.status === "Retardo",
  ).length;

  const incidentDays = visibleAttendanceRecords.filter(
    (row) => row.incident !== "No",
  ).length;

  /**
   * Solo los roles con acceso TOTAL pueden reprocesar.
   *
   * Esto incluye actualmente a:
   * - Super Admin
   * - RH/Admin
   */
  const canReprocessPeriod =
    attendanceAccess === DATA_SCOPES.TOTAL;
  async function handleProcessAttendance(event) {
    event.preventDefault();

    if (!processStartDate || !processEndDate) {
      setProcessError("Selecciona fecha inicio y fecha fin.");
      setProcessResult(null);
      return;
    }

    if (processStartDate > processEndDate) {
      setProcessError(
        "La fecha inicio no puede ser mayor que la fecha fin.",
      );
      setProcessResult(null);
      return;
    }

    try {
      setIsProcessingAttendance(true);
      setProcessError("");
      setProcessResult(null);

      const response = await asistenciaApi.procesar({
        fechaInicio: processStartDate,
        fechaFin: processEndDate,
      });

      setProcessResult(response);
      setAttendanceDate(processEndDate);
      setReloadAttendanceToken((currentValue) => currentValue + 1);
    } catch (error) {
      setProcessError(
        error.message ||
          "No fue posible procesar la asistencia.",
      );
      setProcessResult(null);
    } finally {
      setIsProcessingAttendance(false);
    }
  }
  return (
    <div className="page-stack">
      <PageHeader
        title="Asistencia procesada"
        description="Vista operativa de entradas, salidas, retardos, faltas, tiempo ordinario y tiempo extra."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button">
            <Download size={17} />
            Exportar
          </button>

          {canReprocessPeriod && (
            <button className="primary-button" type="button">
              <TimerReset size={17} />
              Reprocesar periodo
            </button>
          )}
        </div>
      </PageHeader>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <CalendarDays size={22} />
          </div>

          <div>
            <p>Registros procesados</p>
            <strong>{totalRecords}</strong>
            <span>Periodo visible en pantalla</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <CheckCircle2 size={22} />
          </div>

          <div>
            <p>Días completos</p>
            <strong>{completeDays}</strong>
            <span>Con entrada y salida válida</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>

          <div>
            <p>Retardos</p>
            <strong>{lateDays}</strong>
            <span>Fuera de tolerancia</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <AlertTriangle size={22} />
          </div>

          <div>
            <p>Incidencias</p>
            <strong>{incidentDays}</strong>
            <span>Con revisión administrativa</span>
          </div>
        </article>
      </section>
      {canReprocessPeriod && (
        <section className="panel-card form-card">
          <div className="form-section-header">
            <div>
              <h3>Procesar asistencia</h3>
              <p>
                Genera asistencias diarias a partir de las marcaciones
                crudas sincronizadas del reloj.
              </p>
            </div>
          </div>

          <form onSubmit={handleProcessAttendance} noValidate>
            <div className="form-grid two-columns">
              <div className="form-field">
                <label htmlFor="processStartDate">
                  Fecha inicio
                </label>

                <input
                  id="processStartDate"
                  type="date"
                  value={processStartDate}
                  onChange={(event) =>
                    setProcessStartDate(event.target.value)
                  }
                />
              </div>

              <div className="form-field">
                <label htmlFor="processEndDate">
                  Fecha fin
                </label>

                <input
                  id="processEndDate"
                  type="date"
                  value={processEndDate}
                  onChange={(event) =>
                    setProcessEndDate(event.target.value)
                  }
                />
              </div>
            </div>

            {processError && (
              <div className="form-alert error" role="alert">
                <AlertTriangle size={22} />

                <div>
                  <strong>No se pudo procesar</strong>
                  <p>{processError}</p>
                </div>
              </div>
            )}

            {processResult && (
              <div className="form-alert success" role="status">
                <CheckCircle2 size={22} />

                <div>
                  <strong>Asistencia procesada</strong>
                  <p>
                    Registros encontrados:{" "}
                    {processResult.registros_encontrados} ·
                    Procesadas: {processResult.procesadas} ·
                    Errores: {processResult.errores?.length ?? 0}
                  </p>
                </div>
              </div>
            )}

            <div className="form-actions">
              <button
                className="primary-button"
                type="submit"
                disabled={isProcessingAttendance}
              >
                <TimerReset size={17} />
                {isProcessingAttendance
                  ? "Procesando..."
                  : "Procesar asistencia"}
              </button>
            </div>
          </form>
        </section>
      )}
      <section className="panel-card">
        <div className="filters-row">
          <div className="form-field compact-field">
            <label htmlFor="attendanceDate">Fecha</label>

            <input
              id="attendanceDate"
              type="date"
              value={attendanceDate}
              onChange={(event) =>
                setAttendanceDate(event.target.value)
              }
            />
          </div>
          <div className="filter-search">
            <Search size={18} />

            <input
              type="text"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Buscar por empleado, área, fecha, estatus o incidencia..."
            />
          </div>

          <button className="secondary-button" type="button">
            <SlidersHorizontal size={17} />
            Filtros
          </button>
        </div>

        {attendanceError ? (
          <div className="empty-state">
            <AlertTriangle size={42} />

            <h3>No se pudo cargar la asistencia</h3>

            <p>{attendanceError}</p>
          </div>
        ) : isLoadingAttendance ? (
          <div className="empty-state">
            <Clock size={42} />

            <h3>Cargando asistencia</h3>

            <p>Consultando registros procesados del backend.</p>
          </div>
        ) : visibleAttendanceRecords.length === 0 ? (
          <div className="empty-state">
            <CalendarDays size={42} />

            <h3>Sin registros de asistencia</h3>

            <p>
              No hay asistencia procesada para la fecha seleccionada.
            </p>
          </div>
        ) : (
          <>
            <div className="simple-table desktop-table">
              <table>
                <thead>
                  <tr>
                    <th>Empleado</th>
                    <th>Fecha</th>
                    <th>Horario esperado</th>
                    <th>Entrada</th>
                    <th>Salida</th>
                    <th>Retardo</th>
                    <th>Ordinario</th>
                    <th>Extra</th>
                    <th>Estado</th>
                    <th>Incidencia</th>
                    <th>Fuente</th>
                  </tr>
                </thead>

                <tbody>
                  {visibleAttendanceRecords.map((row) => (
                    <tr key={row.id}>
                      <td>
                        <div className="employee-cell">
                          <div className="employee-avatar">
                            {row.employeeName.charAt(0)}
                          </div>

                          <div>
                            <strong>{row.employeeName}</strong>
                            <span>{row.department}</span>
                          </div>
                        </div>
                      </td>

                      <td>
                        <strong>{row.date}</strong>
                        <span className="table-subtext">{row.day}</span>
                      </td>

                      <td>{row.expectedSchedule}</td>
                      <td>{row.entryTime || "—"}</td>
                      <td>{row.exitTime || "—"}</td>
                      <td>{row.lateMinutes} min</td>
                      <td>{row.ordinaryTime}</td>
                      <td>{row.extraTime}</td>

                      <td>
                        <span className={getStatusClass(row.status)}>
                          {row.status}
                        </span>
                      </td>

                      <td>
                        <span
                          className={getIncidentClass(row.incidentStatus)}
                        >
                          {row.incident}
                        </span>
                      </td>

                      <td>{row.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mobile-card-list">
              {visibleAttendanceRecords.map((row) => (
                <article
                  className="mobile-data-card"
                  key={`${row.id}-mobile`}
                >
                  <h4>{row.employeeName}</h4>
                  <p>{row.department}</p>

                  <div className="mobile-data-grid">
                    <div>
                      <span>Fecha</span>
                      <strong>
                        {row.date} / {row.day}
                      </strong>
                    </div>

                    <div>
                      <span>Horario</span>
                      <strong>{row.expectedSchedule}</strong>
                    </div>

                    <div>
                      <span>Entrada</span>
                      <strong>{row.entryTime || "—"}</strong>
                    </div>

                    <div>
                      <span>Salida</span>
                      <strong>{row.exitTime || "—"}</strong>
                    </div>

                    <div>
                      <span>Retardo</span>
                      <strong>{row.lateMinutes} min</strong>
                    </div>

                    <div>
                      <span>Ordinario</span>
                      <strong>{row.ordinaryTime}</strong>
                    </div>

                    <div>
                      <span>Extra</span>
                      <strong>{row.extraTime}</strong>
                    </div>

                    <div>
                      <span>Estado</span>
                      <strong>{row.status}</strong>
                    </div>

                    <div>
                      <span>Incidencia</span>
                      <strong>{row.incident}</strong>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}

export default AttendancePage;