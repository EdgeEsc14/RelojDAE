import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  FileText,
  Printer,
  ShieldCheck,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { mockEmployeeReport } from "../../data/mockReports";

function getStatusClass(status) {
  if (status.includes("Completo")) return "badge success";
  if (status.includes("Pendiente")) return "badge warning";
  if (status.includes("Sin registro")) return "badge neutral";
  if (status.includes("Falta")) return "badge danger";
  return "badge neutral";
}

function EmployeeReportPage() {
  const report = mockEmployeeReport;

  return (
    <div className="page-stack">
      <PageHeader
        title="Reporte individual"
        description="Vista previa del reporte de asistencia e incidencias por empleado."
      >
        <div className="header-actions">
          <Link className="secondary-button link-button" to="/reports">
            <ArrowLeft size={17} />
            Volver
          </Link>

          <button className="secondary-button" type="button">
            <Printer size={17} />
            Imprimir
          </button>

          <button className="primary-button" type="button">
            <Download size={17} />
            Exportar PDF
          </button>
        </div>
      </PageHeader>

      <section className="report-paper">
        <div className="report-institutional-header">
          <div className="report-logo-box">
            <ShieldCheck size={34} />
          </div>

          <div>
            <p>Dirección de Administración Escolar</p>
            <h1>{report.title}</h1>
            <span>
              Periodo del {report.periodStart} al {report.periodEnd}
            </span>
          </div>

          <div className="report-folio">
            <span>Folio</span>
            <strong>{report.reportFolio}</strong>
          </div>
        </div>

        <div className="report-meta-grid">
          <div>
            <span>Fecha de generación</span>
            <strong>{report.generatedAt}</strong>
          </div>

          <div>
            <span>Generado por</span>
            <strong>{report.generatedBy}</strong>
          </div>

          <div>
            <span>Usuario ZKTeco</span>
            <strong>{report.employee.zkUserId}</strong>
          </div>

          <div>
            <span>Código empleado</span>
            <strong>{report.employee.employeeCode}</strong>
          </div>
        </div>

        <section className="report-section">
          <div className="report-section-title">
            <FileText size={18} />
            <h2>Datos del empleado</h2>
          </div>

          <div className="report-info-grid">
            <div>
              <span>RFC</span>
              <strong>{report.employee.rfc}</strong>
            </div>

            <div>
              <span>Nombre</span>
              <strong>{report.employee.fullName}</strong>
            </div>

            <div>
              <span>Área</span>
              <strong>{report.employee.department}</strong>
            </div>

            <div>
              <span>Puesto</span>
              <strong>{report.employee.position}</strong>
            </div>

            <div>
              <span>Supervisor</span>
              <strong>{report.employee.supervisor}</strong>
            </div>

            <div>
              <span>Horario asignado</span>
              <strong>{report.employee.schedule}</strong>
            </div>
          </div>
        </section>

        <section className="report-section">
          <div className="report-section-title">
            <FileText size={18} />
            <h2>Resumen del periodo</h2>
          </div>

          <div className="report-summary-grid">
            <div>
              <span>Días laborables</span>
              <strong>{report.summary.workDays}</strong>
            </div>

            <div>
              <span>Días trabajados</span>
              <strong>{report.summary.workedDays}</strong>
            </div>

            <div>
              <span>Faltas</span>
              <strong>{report.summary.absences}</strong>
            </div>

            <div>
              <span>Retardos</span>
              <strong>{report.summary.delays}</strong>
            </div>

            <div>
              <span>Incidencias pendientes</span>
              <strong>{report.summary.pendingIncidents}</strong>
            </div>

            <div>
              <span>Horas ordinarias</span>
              <strong>{report.summary.ordinaryTime}</strong>
            </div>

            <div>
              <span>Horas extra</span>
              <strong>{report.summary.extraTime}</strong>
            </div>

            <div>
              <span>Asistencia</span>
              <strong>{report.summary.attendancePercent}</strong>
            </div>
          </div>
        </section>

        <section className="report-section">
          <div className="report-section-title">
            <FileText size={18} />
            <h2>Detalle diario de asistencia</h2>
          </div>

          <div className="simple-table report-table">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Día</th>
                  <th>Horario</th>
                  <th>Entrada</th>
                  <th>Salida</th>
                  <th>Retardo</th>
                  <th>Ordinario</th>
                  <th>Extra inicio</th>
                  <th>Extra fin</th>
                  <th>Extra</th>
                  <th>Estado</th>
                  <th>Tratamiento</th>
                </tr>
              </thead>

              <tbody>
                {report.dailyRows.map((row) => (
                  <tr key={row.date}>
                    <td>{row.date}</td>
                    <td>{row.day}</td>
                    <td>{row.expectedSchedule}</td>
                    <td>{row.entryTime || "—"}</td>
                    <td>{row.exitTime || "—"}</td>
                    <td>{row.lateMinutes} min</td>
                    <td>{row.ordinaryTime}</td>
                    <td>{row.extraStart || "—"}</td>
                    <td>{row.extraEnd || "—"}</td>
                    <td>{row.extraTime}</td>
                    <td>
                      <span className={getStatusClass(row.status)}>
                        {row.status}
                      </span>
                    </td>
                    <td>{row.treatment}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="report-section">
          <div className="report-section-title">
            <FileText size={18} />
            <h2>Incidencias relacionadas</h2>
          </div>

          <div className="simple-table report-table">
            <table>
              <thead>
                <tr>
                  <th>Folio</th>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Estatus</th>
                  <th>Descripción</th>
                </tr>
              </thead>

              <tbody>
                {report.incidents.map((incident) => (
                  <tr key={incident.folio}>
                    <td>{incident.folio}</td>
                    <td>{incident.date}</td>
                    <td>{incident.type}</td>
                    <td>
                      <span className="badge warning">{incident.status}</span>
                    </td>
                    <td>{incident.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="report-signatures">
          <div>
            <span>Empleado</span>
            <strong>{report.employee.fullName}</strong>
          </div>

          <div>
            <span>Supervisor / RH</span>
            <strong>Nombre y firma</strong>
          </div>

          <div>
            <span>Super Admin</span>
            <strong>Nombre y firma</strong>
          </div>
        </section>
      </section>
    </div>
  );
}

export default EmployeeReportPage;