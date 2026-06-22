import {
  CalendarClock,
  CheckCircle2,
  Clock,
  Download,
  Plus,
  Search,
  Settings2,
  SlidersHorizontal,
  Users,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  mockBusinessRules,
  mockScheduleAssignments,
  mockSchedules,
} from "../../data/mockSchedules";

function getStatusClass(status) {
  if (status === "Activo") return "badge success";
  if (status === "Activa") return "badge success";
  if (status === "Vigente") return "badge success";
  if (status === "Inactivo") return "badge neutral";
  return "badge neutral";
}

function SchedulesPage() {
  const activeSchedules = mockSchedules.filter(
    (schedule) => schedule.status === "Activo"
  ).length;

  const totalAssigned = mockSchedules.reduce(
    (sum, schedule) => sum + schedule.assignedEmployees,
    0
  );

  const averageTolerance =
    mockSchedules.reduce((sum, schedule) => sum + schedule.toleranceMinutes, 0) /
    mockSchedules.length;

  return (
    <div className="page-stack">
      <PageHeader
        title="Horarios y reglas"
        description="Administración visual de turnos, jornadas, tolerancias y reglas base para cálculo de asistencia."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button">
            <Download size={17} />
            Exportar
          </button>

          <button className="primary-button" type="button">
            <Plus size={17} />
            Nuevo horario
          </button>
        </div>
      </PageHeader>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <CalendarClock size={22} />
          </div>
          <div>
            <p>Horarios activos</p>
            <strong>{activeSchedules}</strong>
            <span>Turnos disponibles</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Users size={22} />
          </div>
          <div>
            <p>Asignaciones</p>
            <strong>{totalAssigned}</strong>
            <span>Empleados vinculados</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>
          <div>
            <p>Tolerancia promedio</p>
            <strong>{averageTolerance.toFixed(0)} min</strong>
            <span>Entrada posterior permitida</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Settings2 size={22} />
          </div>
          <div>
            <p>Reglas activas</p>
            <strong>{mockBusinessRules.length}</strong>
            <span>Cálculo automático</span>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Catálogo de horarios</h3>
            <p>Turnos utilizados para determinar jornada ordinaria, retardos y faltas.</p>
          </div>
        </div>

        <div className="filters-row">
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por nombre, código, tipo, días laborables o estatus..."
            />
          </div>

          <button className="secondary-button" type="button">
            <SlidersHorizontal size={17} />
            Filtros
          </button>
        </div>

        <div className="schedule-card-grid">
          {mockSchedules.map((schedule) => (
            <article className="schedule-card" key={schedule.id}>
              <div className="schedule-card-header">
                <div className="schedule-card-icon">
                  <CalendarClock size={24} />
                </div>

                <div>
                  <h4>{schedule.name}</h4>
                  <p>{schedule.code}</p>
                </div>

                <span className={getStatusClass(schedule.status)}>
                  {schedule.status}
                </span>
              </div>

              <p className="schedule-description">{schedule.description}</p>

              <div className="schedule-time-row">
                <div>
                  <span>Entrada</span>
                  <strong>{schedule.startTime}</strong>
                </div>

                <div>
                  <span>Salida</span>
                  <strong>{schedule.endTime}</strong>
                </div>

                <div>
                  <span>Tolerancia</span>
                  <strong>{schedule.toleranceMinutes} min</strong>
                </div>

                <div>
                  <span>Ordinario</span>
                  <strong>{schedule.ordinaryHours}</strong>
                </div>
              </div>

              <div className="workdays-row">
                {schedule.workDays.map((day) => (
                  <span key={`${schedule.id}-${day}`}>{day}</span>
                ))}
              </div>

              <div className="schedule-footer">
                <div>
                  <span>Empleados asignados</span>
                  <strong>{schedule.assignedEmployees}</strong>
                </div>

                <div>
                  <span>Regla extra</span>
                  <strong>{schedule.extraRule}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="schedules-grid">
        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Asignaciones vigentes</h3>
              <p>Relación visual entre empleado y horario asignado.</p>
            </div>
            <CheckCircle2 size={22} />
          </div>

          <div className="simple-table desktop-table">
            <table>
              <thead>
                <tr>
                  <th>Empleado</th>
                  <th>Departamento</th>
                  <th>Horario</th>
                  <th>Inicio vigencia</th>
                  <th>Fin vigencia</th>
                  <th>Estatus</th>
                </tr>
              </thead>

              <tbody>
                {mockScheduleAssignments.map((assignment) => (
                  <tr key={assignment.id}>
                    <td>
                      <div className="employee-cell">
                        <div className="employee-avatar">
                          {assignment.employeeName.charAt(0)}
                        </div>
                        <div>
                          <strong>{assignment.employeeName}</strong>
                          <span>{assignment.employeeCode}</span>
                        </div>
                      </div>
                    </td>
                    <td>{assignment.department}</td>
                    <td>{assignment.scheduleName}</td>
                    <td>{assignment.validFrom}</td>
                    <td>{assignment.validTo}</td>
                    <td>
                      <span className={getStatusClass(assignment.status)}>
                        {assignment.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mobile-card-list">
            {mockScheduleAssignments.map((assignment) => (
              <article
                className="mobile-data-card"
                key={`${assignment.id}-mobile`}
              >
                <h4>{assignment.employeeName}</h4>
                <p>{assignment.department}</p>

                <div className="mobile-data-grid">
                  <div>
                    <span>Código</span>
                    <strong>{assignment.employeeCode}</strong>
                  </div>
                  <div>
                    <span>Horario</span>
                    <strong>{assignment.scheduleName}</strong>
                  </div>
                  <div>
                    <span>Vigencia</span>
                    <strong>
                      {assignment.validFrom} - {assignment.validTo}
                    </strong>
                  </div>
                  <div>
                    <span>Estatus</span>
                    <strong>{assignment.status}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Reglas de cálculo</h3>
              <p>Condiciones que generan incidencias automáticamente.</p>
            </div>
            <Settings2 size={22} />
          </div>

          <div className="rule-list">
            {mockBusinessRules.map((rule) => (
              <div className="rule-card" key={rule.id}>
                <div>
                  <h4>{rule.rule}</h4>
                  <p>{rule.condition}</p>
                </div>

                <span className={getStatusClass(rule.status)}>
                  {rule.status}
                </span>

                <div className="rule-example">
                  <span>Ejemplo</span>
                  <strong>{rule.example}</strong>
                </div>

                <div className="rule-example">
                  <span>Acción</span>
                  <strong>{rule.action}</strong>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

export default SchedulesPage;