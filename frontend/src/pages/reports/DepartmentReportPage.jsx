import { Link } from "react-router-dom";
import { ArrowLeft, Download, Printer, Users } from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { mockDepartmentReport } from "../../data/mockReports";

function DepartmentReportPage() {
  const totalEmployees = mockDepartmentReport.reduce(
    (sum, row) => sum + row.employees,
    0
  );

  const totalIncidents = mockDepartmentReport.reduce(
    (sum, row) => sum + row.incidents,
    0
  );

  const totalDelays = mockDepartmentReport.reduce(
    (sum, row) => sum + row.delays,
    0
  );

  return (
    <div className="page-stack">
      <PageHeader
        title="Reporte por departamento"
        description="Concentrado de asistencia, incidencias y tiempo extra por área."
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
            Exportar
          </button>
        </div>
      </PageHeader>

      <section className="metrics-grid three-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Users size={22} />
          </div>
          <div>
            <p>Empleados</p>
            <strong>{totalEmployees}</strong>
            <span>Total en áreas visibles</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Users size={22} />
          </div>
          <div>
            <p>Incidencias</p>
            <strong>{totalIncidents}</strong>
            <span>Generadas en el periodo</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Users size={22} />
          </div>
          <div>
            <p>Retardos</p>
            <strong>{totalDelays}</strong>
            <span>Fuera de tolerancia</span>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Concentrado por departamento</h3>
            <p>Periodo 01/05/2026 - 15/05/2026.</p>
          </div>
        </div>

        <div className="simple-table desktop-table">
          <table>
            <thead>
              <tr>
                <th>Departamento</th>
                <th>Empleados</th>
                <th>Días trabajados</th>
                <th>Faltas</th>
                <th>Retardos</th>
                <th>Incidencias</th>
                <th>Horas ordinarias</th>
                <th>Horas extra</th>
              </tr>
            </thead>

            <tbody>
              {mockDepartmentReport.map((row) => (
                <tr key={row.department}>
                  <td>
                    <strong>{row.department}</strong>
                  </td>
                  <td>{row.employees}</td>
                  <td>{row.workedDays}</td>
                  <td>{row.absences}</td>
                  <td>{row.delays}</td>
                  <td>{row.incidents}</td>
                  <td>{row.ordinaryTime}</td>
                  <td>{row.extraTime}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mobile-card-list">
          {mockDepartmentReport.map((row) => (
            <article className="mobile-data-card" key={`${row.department}-mobile`}>
              <h4>{row.department}</h4>
              <p>Concentrado del periodo</p>

              <div className="mobile-data-grid">
                <div>
                  <span>Empleados</span>
                  <strong>{row.employees}</strong>
                </div>
                <div>
                  <span>Días trabajados</span>
                  <strong>{row.workedDays}</strong>
                </div>
                <div>
                  <span>Faltas</span>
                  <strong>{row.absences}</strong>
                </div>
                <div>
                  <span>Retardos</span>
                  <strong>{row.delays}</strong>
                </div>
                <div>
                  <span>Incidencias</span>
                  <strong>{row.incidents}</strong>
                </div>
                <div>
                  <span>Ordinario</span>
                  <strong>{row.ordinaryTime}</strong>
                </div>
                <div>
                  <span>Extra</span>
                  <strong>{row.extraTime}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default DepartmentReportPage;