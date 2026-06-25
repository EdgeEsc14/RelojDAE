import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  ChevronLeft,
  ChevronRight,
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
/* Esta cosa solamente era de prueba 
import { mockEmployees } from "../../data/mockEmployees";*/
import { empleadosApi } from "../../api/empleadosApi";
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

function getVisiblePageNumbers(currentPage, totalPages) {
  const maximumVisiblePages = 5;

  if (totalPages <= maximumVisiblePages) {
    return Array.from(
      { length: totalPages },
      (_, index) => index + 1,
    );
  }

  let startPage = Math.max(
    1,
    currentPage - Math.floor(maximumVisiblePages / 2),
  );

  let endPage = startPage + maximumVisiblePages - 1;

  if (endPage > totalPages) {
    endPage = totalPages;
    startPage = endPage - maximumVisiblePages + 1;
  }

  return Array.from(
    { length: endPage - startPage + 1 },
    (_, index) => startPage + index,
  );
}

function formatEmployeeStatus(status) {
  const normalizedStatus = normalizeText(status);

  if (normalizedStatus === "activo") return "Activo";
  if (normalizedStatus === "inactivo") return "Inactivo";
  if (normalizedStatus === "baja") return "Inactivo";

  return status || "Sin estatus";
}

function getEmployeesArrayFromApiResponse(response) {
  if (Array.isArray(response)) {
    return response;
  }

  if (Array.isArray(response?.items)) {
    return response.items;
  }

  if (Array.isArray(response?.data)) {
    return response.data;
  }

  if (Array.isArray(response?.empleados)) {
    return response.empleados;
  }

  if (Array.isArray(response?.results)) {
    return response.results;
  }

  return [];
}


/* Funcion de mapeo para conectar la API
protege el diseño aunque el backend todavía no regrese todos los campos */
function mapEmployeeFromApi(employee) {
  const fullName =
    employee.nombre_completo ??
    employee.fullName ??
    [
      employee.nombres,
      employee.apellido_paterno,
      employee.apellido_materno,
    ]
      .filter(Boolean)
      .join(" ");

  const scheduleText =
    employee.horario && employee.turno
      ? `${employee.horario} · ${employee.turno}`
      : employee.horario || employee.schedule || null;

  return {
    id: employee.id ?? employee.empleado_id ?? employee.codigo_empleado,

    employeeCode:
      employee.codigo_empleado ??
      employee.employeeCode ??
      "Sin código",

    fullName: fullName || "Sin nombre",

    email:
      employee.correo ??
      employee.email ??
      "",

    rfc:
      employee.rfc ??
      "",

    departmentId:
      employee.unidad_organizacional_id ??
      employee.departamento_id ??
      employee.departmentId ??
      null,

    areaId:
      employee.area_principal_id ??
      null,

    area:
      employee.area_principal ??
      employee.area ??
      employee.unidad_organizacional ??
      "Sin área",

    department:
      employee.unidad_organizacional ??
      employee.departamento_nombre ??
      employee.department ??
      "Sin departamento",

    departmentCode:
      employee.unidad_organizacional_codigo ??
      employee.departmentCode ??
      "",

    position:
      employee.puesto ??
      employee.puesto_nombre ??
      employee.position ??
      "Sin puesto",

    positionCode:
      employee.puesto_codigo ??
      "",

    supervisor:
      employee.supervisor?.trim() ||
      employee.supervisor_nombre?.trim() ||
      employee.supervisor_name?.trim() ||
      null,

    supervisorCode:
      employee.supervisor_codigo_empleado ??
      "",

    zkUserId:
      employee.zk_user_id ||
      employee.zk_uid ||
      employee.zkUserId ||
      null,

    zkUid:
      employee.zk_uid ??
      null,

    device:
      employee.dispositivo ||
      employee.dispositivo_codigo ||
      null,

    deviceCode:
      employee.dispositivo_codigo ??
      "",

    schedule:
      scheduleText,

    scheduleId:
      employee.horario_id ??
      null,

    shift:
      employee.turno ??
      "Sin turno",

    shiftCode:
      employee.turno_codigo ??
      "",

    scheduleStartDate:
      employee.horario_fecha_inicio ??
      null,

    scheduleEndDate:
      employee.horario_fecha_fin ??
      null,

    lastCheck:
      employee.ultima_checada ??
      employee.lastCheck ??
      "Sin checada",

    attendanceStatus:
      employee.estado_asistencia ??
      employee.attendanceStatus ??
      "Sin evaluar",

    status: formatEmployeeStatus(
      employee.estatus ?? employee.status,
    ),
  };
}


function EmployeesPage() {
  const [employees, setEmployees] = useState([]);
  const [isLoadingEmployees, setIsLoadingEmployees] =
    useState(false);
  const [employeesError, setEmployeesError] = useState("");

  const [searchTerm, setSearchTerm] = useState("");

  const [showFilters, setShowFilters] = useState(false);

  const [selectedDepartment, setSelectedDepartment] =
    useState("todos");

  const [selectedStatus, setSelectedStatus] =
    useState("todos");

  const [selectedAttendanceStatus, setSelectedAttendanceStatus] =
    useState("todos");

  // Paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  const employeeAccess = getModuleAccess(
    currentUser.role,
    MODULES.EMPLEADOS,
  );
  useEffect(() => {
    let isMounted = true;

    async function loadEmployees() {
      try {
        setIsLoadingEmployees(true);
        setEmployeesError("");

        const data = await empleadosApi.listar();
        /*Esta cosa es temporal solo para saber como esta
        console.log("Respuesta empleados API:", data);*/
        
        if (!isMounted) return;

        const employeesFromApi =
          getEmployeesArrayFromApiResponse(data);

        const mappedEmployees =
          employeesFromApi.map(mapEmployeeFromApi);

        setEmployees(mappedEmployees);
      } catch (error) {
        if (!isMounted) return;

        setEmployees([]);
        setEmployeesError(
          error.message ||
            "No fue posible cargar los empleados desde el backend.",
        );
      } finally {
        if (isMounted) {
          setIsLoadingEmployees(false);
        }
      }
    }

    loadEmployees();

    return () => {
      isMounted = false;
    };
  }, []);

  /*
   * Primer nivel:
   * limita los empleados según el alcance del rol.
   */
  const scopedEmployees = useMemo(() => {
    return employees.filter((employee) => {
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
  }, [employeeAccess, employees]);

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
        employee.area,
        employee.department,
        employee.zkUserId,
        employee.zkUid,
        employee.device,
        employee.schedule,
        employee.shift,
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
        employee.area === selectedDepartment;

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
  // =========================================
  // PAGINACIÓN
  // =========================================

  const totalVisibleEmployees = visibleEmployees.length;

  const totalPages = Math.max(
    1,
    Math.ceil(totalVisibleEmployees / rowsPerPage),
  );

  const firstEmployeeIndex =
    (currentPage - 1) * rowsPerPage;

  const lastEmployeeIndex =
    firstEmployeeIndex + rowsPerPage;

  const paginatedEmployees = visibleEmployees.slice(
    firstEmployeeIndex,
    lastEmployeeIndex,
  );

  const firstVisibleRecord =
    totalVisibleEmployees === 0
      ? 0
      : firstEmployeeIndex + 1;

  const lastVisibleRecord = Math.min(
    lastEmployeeIndex,
    totalVisibleEmployees,
  );

  const visiblePageNumbers = getVisiblePageNumbers(
    currentPage,
    totalPages,
  );

  /*
   * Regresa a la página 1 cuando cambia la búsqueda,
   * algún filtro o la cantidad de filas.
   */
  useEffect(() => {
    setCurrentPage(1);
  }, [
    searchTerm,
    selectedDepartment,
    selectedStatus,
    selectedAttendanceStatus,
    rowsPerPage,
  ]);

  /*
   * Evita permanecer en una página que ya no existe.
   */
  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);
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
    scopedEmployees.map((employee) => employee.area),
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

        {employeesError && (
          <div className="empty-state">
            <h3>Error al cargar empleados</h3>

            <p>{employeesError}</p>
          </div>
        )}

        {isLoadingEmployees && (
          <div className="empty-state">
            <h3>Cargando empleados</h3>

            <p>
              Consultando la información desde el backend de
              RelojChecador.
            </p>
          </div>
        )}


        {(searchTerm || hasActiveFilters) && (
        <div className="filter-results-summary">
          <span>
            <strong>{visibleEmployees.length}</strong>{" "}
            resultados encontrados
          </span>

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
        </div>
      )}

        {!isLoadingEmployees && visibleEmployees.length === 0 ? (
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
          <>
            <div className="simple-table">
            <table>
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Empleado</th>
                  <th>Usuario ZK</th>
                  <th>División / Departamento</th>
                  <th>Horario</th>
                  <th>Última checada</th>
                  <th>Asistencia</th>
                  <th>Estatus</th>
                  <th>Acciones</th>
                </tr>
              </thead>

              <tbody>
                {paginatedEmployees.map((employee) => (
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

                          <span>
                            {employee.supervisor
                              ? `Supervisor: ${employee.supervisor}`
                              : "Sin supervisor asignado"}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td>
                      {employee.zkUserId ? (
                        <div className="table-stacked-cell">
                          <strong>{employee.zkUserId}</strong>

                          {employee.device && (
                            <span>{employee.device}</span>
                          )}
                        </div>
                      ) : (
                        <span className="muted-table-text">
                          Sin usuario ZK
                        </span>
                      )}
                    </td>

                    <td>
                      <div className="table-stacked-cell table-organization-cell">
                        <strong>{employee.area}</strong>

                        {employee.department &&
                          employee.department !== employee.area && (
                            <span>{employee.department}</span>
                          )}
                      </div>
                    </td>

                    <td>
                      {employee.schedule ? (
                        <div className="table-stacked-cell">
                          <strong>{employee.schedule}</strong>

                          {employee.scheduleStartDate && (
                            <span>
                              Desde {employee.scheduleStartDate}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="muted-table-text">
                          Sin horario
                        </span>
                      )}
                    </td>

                    <td>{employee.lastCheck}</td>
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
                        to={`/employees/${employee.employeeCode}`}
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

          <div className="pagination-bar">
            <div className="pagination-summary">
              Mostrando{" "}
              <strong>{firstVisibleRecord}</strong>
              {" – "}
              <strong>{lastVisibleRecord}</strong>
              {" de "}
              <strong>{totalVisibleEmployees}</strong>
              {" empleados"}
            </div>

            <div className="pagination-size">
              <label htmlFor="employees-per-page">
                Filas por página
              </label>

              <select
                id="employees-per-page"
                value={rowsPerPage}
                onChange={(event) =>
                  setRowsPerPage(Number(event.target.value))
                }
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>

            <div
              className="pagination-controls"
              aria-label="Paginación de empleados"
            >
              <button
                className="pagination-button"
                type="button"
                disabled={currentPage === 1}
                onClick={() =>
                  setCurrentPage((page) =>
                    Math.max(1, page - 1),
                  )
                }
                aria-label="Página anterior"
              >
                <ChevronLeft size={17} />
              </button>

              {visiblePageNumbers.map((pageNumber) => (
                <button
                  key={pageNumber}
                  className={
                    pageNumber === currentPage
                      ? "pagination-button active"
                      : "pagination-button"
                  }
                  type="button"
                  onClick={() => setCurrentPage(pageNumber)}
                  aria-current={
                    pageNumber === currentPage
                      ? "page"
                      : undefined
                  }
                >
                  {pageNumber}
                </button>
              ))}

              <button
                className="pagination-button"
                type="button"
                disabled={currentPage === totalPages}
                onClick={() =>
                  setCurrentPage((page) =>
                    Math.min(totalPages, page + 1),
                  )
                }
                aria-label="Página siguiente"
              >
                <ChevronRight size={17} />
              </button>
            </div>
          </div>
        </>
        )}
      </section>
    </div>
  );
}

export default EmployeesPage;