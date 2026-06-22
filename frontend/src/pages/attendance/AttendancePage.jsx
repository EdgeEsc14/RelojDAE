import { useMemo, useState } from "react";

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
  ACCESS_LEVELS,
  MODULES,
} from "../../constants/permissions";

import { currentUser } from "../../data/currentUser";
import { mockAttendanceSummary } from "../../data/mockAttendance";
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

function AttendancePage() {
  const [searchTerm, setSearchTerm] = useState("");

  const attendanceAccess = getModuleAccess(
    currentUser.role,
    MODULES.ASISTENCIA,
  );

  /**
   * Primer filtro: seguridad y alcance del usuario.
   *
   * TOTAL   -> todos los registros.
   * LECTURA -> todos, pero sin acciones administrativas.
   * AREA    -> solamente su departamento.
   * PROPIO  -> solamente su employeeId.
   */
  const scopedAttendanceRecords = useMemo(() => {
    return mockAttendanceSummary.filter((row) => {
      if (
        attendanceAccess === ACCESS_LEVELS.TOTAL ||
        attendanceAccess === ACCESS_LEVELS.LECTURA
      ) {
        return true;
      }

      if (attendanceAccess === ACCESS_LEVELS.AREA) {
        return Number(row.departmentId) === Number(currentUser.departmentId);
      }

      if (attendanceAccess === ACCESS_LEVELS.PROPIO) {
        return Number(row.employeeId) === Number(currentUser.employeeId);
      }

      return false;
    });
  }, [attendanceAccess]);

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
    attendanceAccess === ACCESS_LEVELS.TOTAL;

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

      <section className="panel-card">
        <div className="filters-row">
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

        {visibleAttendanceRecords.length === 0 ? (
          <div className="empty-state">
            <h3>No se encontraron registros</h3>
            <p>
              No existen registros de asistencia disponibles para el usuario
              actual o para la búsqueda realizada.
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