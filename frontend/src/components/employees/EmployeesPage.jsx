import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  Download,
  Eye,
  Plus,
  Search,
  SlidersHorizontal,
  UserRoundCheck,
  X,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";

import {
  ACCESS_LEVELS,
  MODULES,
} from "../../constants/permissions";

import { currentUser } from "../../data/currentUser";
import { mockEmployees } from "../../data/mockEmployees";
import { getModuleAccess } from "../../utils/permissions";

function getStatusClass(status) {
  if (status === "Activo") return "badge success";
  if (status === "Inactivo") return "badge danger";

  return "badge neutral";
}

function getAttendanceClass(status) {
  if (status === "Completo") return "badge success";
  if (status === "Retardo") return "badge warning";
  if (status === "Omisión de salida") return "badge danger";
  if (status === "Baja") return "badge neutral";

  return "badge neutral";
}

function normalizeText(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function EmployeesPage() {
  const [searchTerm, setSearchTerm] = useState("");

  const [showFilters, setShowFilters] = useState(false);

  const [selectedDepartment, setSelectedDepartment] =
    useState("todos");

  const [selectedStatus, setSelectedStatus] =
    useState("todos");

  const [selectedAttendanceStatus, setSelectedAttendanceStatus] =
    useState("todos");

  const employeeAccess = getModuleAccess(
    currentUser.role,
    MODULES.EMPLEADOS,
  );

  /*
   * Primer nivel:
   * limita los empleados según el alcance del rol.
   */
  const scopedEmployees = useMemo(() => {
    return mockEmployees.filter((employee) => {
      if (
        employeeAccess === ACCESS_LEVELS.TOTAL ||
        employeeAccess === ACCESS_LEVELS.LECTURA
      ) {
        return true;
      }

      if (employeeAccess === ACCESS_LEVELS.AREA) {
        return (
          Number(employee.departmentId) ===
          Number(currentUser.departmentId)
        );
      }

      if (employeeAccess === ACCESS_LEVELS.PROPIO) {
        return (
          Number(employee.id) ===
          Number(currentUser.employeeId)
        );
      }

      return false;
    });
  }, [employeeAccess]);

  /*
   * Opciones disponibles para el filtro de departamentos.
   *
   * Se generan con los departamentos que el usuario
   * tiene permitido consultar.
   */
  const departmentOptions = useMemo(() => {
    return [
      ...new Set(
        scopedEmployees
          .map((employee) => employee.department)
          .filter(Boolean),
      ),
    ].sort((a, b) => a.localeCompare(b, "es"));
  }, [scopedEmployees]);

  /*
   * Opciones disponibles para el filtro de asistencia.
   */
  const attendanceStatusOptions = useMemo(() => {
    return [
      ...new Set(
        scopedEmployees
          .map((employee) => employee.attendanceStatus)
          .filter(Boolean),
      ),
    ].sort((a, b) => a.localeCompare(b, "es"));
  }, [scopedEmployees]);

  /*
   * Segundo nivel:
   * aplica búsqueda y filtros sobre los empleados autorizados.
   */
  const visibleEmployees = useMemo(() => {
    const normalizedSearch = normalizeText(searchTerm);

    return scopedEmployees.filter((employee) => {
      const searchableValues = [
        employee.employeeCode,
        employee.fullName,
        employee.position,
        employee.department,
        employee.zkUserId,
        employee.schedule,
        employee.status,
        employee.attendanceStatus,
        employee.rfc,
        employee.supervisor,
      ];

      const matchesSearch =
        !normalizedSearch ||
        searchableValues.some((value) =>
          normalizeText(value).includes(normalizedSearch),
        );

      const matchesDepartment =
        selectedDepartment === "todos" ||
        employee.department === selectedDepartment;

      const matchesStatus =
        selectedStatus === "todos" ||
        employee.status === selectedStatus;

      const matchesAttendanceStatus =
        selectedAttendanceStatus === "todos" ||
        employee.attendanceStatus ===
          selectedAttendanceStatus;

      return (
        matchesSearch &&
        matchesDepartment &&
        matchesStatus &&
        matchesAttendanceStatus
      );
    });
  }, [
    scopedEmployees,
    searchTerm,
    selectedDepartment,
    selectedStatus,
    selectedAttendanceStatus,
  ]);

  /*
   * Las tarjetas muestran el total permitido por el rol.
   * No cambian con el buscador ni con los filtros visuales.
   */
  const activeEmployees = scopedEmployees.filter(
    (employee) => employee.status === "Activo",
  ).length;

  const inactiveEmployees = scopedEmployees.filter(
    (employee) => employee.status === "Inactivo",
  ).length;

  const departments = new Set(
    scopedEmployees.map((employee) => employee.department),
  );

  const canCreateEmployee =
    employeeAccess === ACCESS_LEVELS.TOTAL;

  const activeFilterCount = [
    selectedDepartment !== "todos",
    selectedStatus !== "todos",
    selectedAttendanceStatus !== "todos",
  ].filter(Boolean).length;

  const hasActiveFilters = activeFilterCount > 0;

  function clearFilters() {
    setSelectedDepartment("todos");
    setSelectedStatus("todos");
    setSelectedAttendanceStatus("todos");
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Empleados"
        description="Catálogo visual de empleados, usuarios ZKTeco, horarios y estatus de asistencia."
      >
        <div className="header-actions">
          <button
            className="secondary-button"
            type="button"
          >
            <Download size={17} />
            Exportar
          </button>

          {canCreateEmployee && (
            <Link
              className="primary-button link-button"
              to="/employees/new"
            >
              <Plus size={17} />
              Nuevo empleado
            </Link>
          )}
        </div>
      </PageHeader>

      <section className="metrics-grid three-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <UserRoundCheck size={22} />
          </div>

          <div>
            <p>Empleados activos</p>
            <strong>{activeEmployees}</strong>
            <span>Personal con asistencia vigente</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <UserRoundCheck size={22} />
          </div>

          <div>
            <p>Empleados inactivos</p>
            <strong>{inactiveEmployees}</strong>
            <span>Bajas lógicas del sistema</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <UserRoundCheck size={22} />
          </div>

          <div>
            <p>Departamentos</p>
            <strong>{departments.size}</strong>
            <span>Áreas registradas en catálogo</span>
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
              onChange={(event) =>
                setSearchTerm(event.target.value)
              }
              placeholder="Buscar por nombre, código, RFC, área o usuario ZKTeco..."
            />
          </div>

          <button
            className="secondary-button"
            type="button"
            aria-expanded={showFilters}
            onClick={() => setShowFilters((current) => !current)}
          >
            <SlidersHorizontal size={17} />

            {activeFilterCount > 0
              ? `Filtros (${activeFilterCount})`
              : "Filtros"}
          </button>
        </div>

        {showFilters && (
          <div className="advanced-filters">
            <div className="filter-field">
              <label htmlFor="department-filter">
                Departamento
              </label>

              <select
                id="department-filter"
                value={selectedDepartment}
                onChange={(event) =>
                  setSelectedDepartment(event.target.value)
                }
              >
                <option value="todos">
                  Todos los departamentos
                </option>

                {departmentOptions.map((department) => (
                  <option
                    key={department}
                    value={department}
                  >
                    {department}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-field">
              <label htmlFor="status-filter">
                Estatus
              </label>

              <select
                id="status-filter"
                value={selectedStatus}
                onChange={(event) =>
                  setSelectedStatus(event.target.value)
                }
              >
                <option value="todos">
                  Todos los estatus
                </option>

                <option value="Activo">
                  Activo
                </option>

                <option value="Inactivo">
                  Inactivo
                </option>
              </select>
            </div>

            <div className="filter-field">
              <label htmlFor="attendance-filter">
                Estado de asistencia
              </label>

              <select
                id="attendance-filter"
                value={selectedAttendanceStatus}
                onChange={(event) =>
                  setSelectedAttendanceStatus(
                    event.target.value,
                  )
                }
              >
                <option value="todos">
                  Todos los estados
                </option>

                {attendanceStatusOptions.map((status) => (
                  <option
                    key={status}
                    value={status}
                  >
                    {status}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={clearFilters}
                disabled={!hasActiveFilters}
              >
                <X size={17} />
                Limpiar filtros
              </button>
            </div>
          </div>
        )}

        <div className="filter-results-summary">
          <span>
            Mostrando{" "}
            <strong>{visibleEmployees.length}</strong>{" "}
            de{" "}
            <strong>{scopedEmployees.length}</strong>{" "}
            empleados
          </span>

          {(searchTerm || hasActiveFilters) && (
            <button
              className="text-button"
              type="button"
              onClick={() => {
                setSearchTerm("");
                clearFilters();
              }}
            >
              Limpiar búsqueda y filtros
            </button>
          )}
        </div>

        {visibleEmployees.length === 0 ? (
          <div className="empty-state">
            <h3>No se encontraron empleados</h3>

            <p>
              No existen empleados que coincidan con los
              criterios seleccionados.
            </p>

            <button
              className="secondary-button"
              type="button"
              onClick={() => {
                setSearchTerm("");
                clearFilters();
              }}
            >
              <X size={17} />
              Limpiar búsqueda y filtros
            </button>
          </div>
        ) : (
          <div className="simple-table">
            <table>
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Empleado</th>
                  <th>Usuario ZK</th>
                  <th>Área</th>
                  <th>Horario</th>
                  <th>Última checada</th>
                  <th>Asistencia</th>
                  <th>Estatus</th>
                  <th>Acciones</th>
                </tr>
              </thead>

              <tbody>
                {visibleEmployees.map((employee) => (
                  <tr key={employee.id}>
                    <td>
                      <strong>
                        {employee.employeeCode}
                      </strong>
                    </td>

                    <td>
                      <div className="employee-cell">
                        <div className="employee-avatar">
                          {employee.fullName.charAt(0)}
                        </div>

                        <div>
                          <strong>
                            {employee.fullName}
                          </strong>

                          <span>
                            {employee.position}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td>{employee.zkUserId}</td>
                    <td>{employee.department}</td>
                    <td>{employee.schedule}</td>
                    <td>{employee.lastPunch}</td>

                    <td>
                      <span
                        className={getAttendanceClass(
                          employee.attendanceStatus,
                        )}
                      >
                        {employee.attendanceStatus}
                      </span>
                    </td>

                    <td>
                      <span
                        className={getStatusClass(
                          employee.status,
                        )}
                      >
                        {employee.status}
                      </span>
                    </td>

                    <td>
                      <Link
                        className="table-action"
                        to={`/employees/${employee.id}`}
                      >
                        <Eye size={16} />
                        Ver
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default EmployeesPage;