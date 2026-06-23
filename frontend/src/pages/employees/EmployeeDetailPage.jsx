import {
  useEffect,
  useState,
} from "react";

import { Link, useParams } from "react-router-dom";

import {
  AlertTriangle,
  ArrowLeft,
  CalendarClock,
  CheckCircle2,
  Clock,
  FileText,
  Fingerprint,
  Pencil,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { empleadosApi } from "../../api/empleadosApi";
import { catalogosApi } from "../../api/catalogosApi";
import {
  ACCESS_LEVELS,
  MODULES,
} from "../../constants/permissions";

import { currentUser } from "../../data/currentUser";
import { mockAttendanceSummary } from "../../data/mockAttendance";
import { getModuleAccess } from "../../utils/permissions";

/**
 * Convierte duraciones como:
 *
 * "07:05"
 * "04:17:01"
 *
 * a segundos.
 */
function durationToSeconds(value) {
  if (!value || typeof value !== "string") {
    return 0;
  }

  const parts = value.split(":").map(Number);

  if (parts.some(Number.isNaN)) {
    return 0;
  }

  if (parts.length === 2) {
    const [hours, minutes] = parts;

    return hours * 3600 + minutes * 60;
  }

  if (parts.length === 3) {
    const [hours, minutes, seconds] = parts;

    return hours * 3600 + minutes * 60 + seconds;
  }

  return 0;
}

/**
 * Convierte segundos acumulados a HH:MM:SS.
 */
function formatDuration(totalSeconds) {
  const safeSeconds = Math.max(0, totalSeconds);

  const hours = Math.floor(safeSeconds / 3600);

  const minutes = Math.floor(
    (safeSeconds % 3600) / 60,
  );

  const seconds = safeSeconds % 60;

  return [
    String(hours).padStart(2, "0"),
    String(minutes).padStart(2, "0"),
    String(seconds).padStart(2, "0"),
  ].join(":");
}

function getStatusClass(status) {
  if (status === "Completo") {
    return "badge success";
  }

  if (status === "Completo con tiempo extra") {
    return "badge success";
  }

  if (status === "Retardo") {
    return "badge warning";
  }

  if (status === "Omisión de salida") {
    return "badge danger";
  }

  if (status === "Falta") {
    return "badge danger";
  }

  return "badge neutral";
}

function getIncidentClass(status) {
  if (status === "Pendiente") {
    return "badge warning";
  }

  if (status === "Sin justificar") {
    return "badge danger";
  }

  if (status === "Aprobada") {
    return "badge success";
  }

  return "badge neutral";
}


function getCatalogArrayFromApiResponse(response) {
  if (Array.isArray(response)) {
    return response;
  }

  if (Array.isArray(response?.value)) {
    return response.value;
  }

  if (Array.isArray(response?.items)) {
    return response.items;
  }

  if (Array.isArray(response?.data)) {
    return response.data;
  }

  return [];
}

function getOrganizationInfo(unit, organizationalUnits) {
  if (!unit) {
    return {
      mainArea: "Sin área principal",
      department: "Sin departamento",
      finalUnitName: "Sin área",
    };
  }

  const catalogUnit =
    organizationalUnits.find(
      (item) => Number(item.id) === Number(unit.id),
    ) ?? unit;

  const parentUnit = organizationalUnits.find(
    (item) =>
      Number(item.id) ===
      Number(catalogUnit.unidad_padre_id),
  );

  const isDepartment =
    catalogUnit.tipo_unidad_codigo === "DEPARTAMENTO";

  const isDivision =
    catalogUnit.tipo_unidad_codigo === "DIVISION";

  if (isDepartment && parentUnit) {
    const parentIsDivision =
      parentUnit.tipo_unidad_codigo === "DIVISION";

    if (parentIsDivision) {
      return {
        mainArea: parentUnit.nombre,
        department: catalogUnit.nombre,
        finalUnitName: catalogUnit.nombre,
      };
    }

    return {
      mainArea: catalogUnit.nombre,
      department: "No aplica",
      finalUnitName: catalogUnit.nombre,
    };
  }

  if (isDivision) {
    return {
      mainArea: catalogUnit.nombre,
      department: "No aplica",
      finalUnitName: catalogUnit.nombre,
    };
  }

  return {
    mainArea: catalogUnit.nombre ?? "Sin área principal",
    department: "No aplica",
    finalUnitName: catalogUnit.nombre ?? "Sin área",
  };
}
function formatEmployeeStatus(status) {
  const normalizedStatus = String(status ?? "")
    .trim()
    .toUpperCase();

  if (normalizedStatus === "ACTIVO") return "Activo";
  if (normalizedStatus === "INACTIVO") return "Inactivo";
  if (normalizedStatus === "BAJA") return "Inactivo";

  return status || "Sin estatus";
}

function mapEmployeeDetailFromApi(
  apiResponse,
  organizationalUnits = [],
) {
  const employeeData =
    apiResponse?.empleado ??
    apiResponse?.item ??
    apiResponse?.data ??
    apiResponse;

  const unidadOrganizacional =
    apiResponse?.unidad_organizacional ??
    employeeData?.unidad_organizacional ??
    null;

  const puesto =
    apiResponse?.puesto ??
    employeeData?.puesto ??
    null;

  const supervisor =
    apiResponse?.supervisor ??
    employeeData?.supervisor ??
    null;

  const horarioActual =
    apiResponse?.horario_actual ??
    employeeData?.horario_actual ??
    null;

  const dispositivo =
    apiResponse?.dispositivo ??
    employeeData?.dispositivo ??
    null;

  const organizationInfo = getOrganizationInfo(
    unidadOrganizacional,
    organizationalUnits,
  );

  const fullName =
    employeeData?.nombre_completo ??
    [
      employeeData?.nombres,
      employeeData?.apellido_paterno,
      employeeData?.apellido_materno,
    ]
      .filter(Boolean)
      .join(" ") ??
    "Empleado sin nombre";

  return {
    id: employeeData?.id ?? null,

    employeeCode:
      employeeData?.codigo_empleado ?? "",

    fullName,

    email:
      employeeData?.correo ?? "",

    rfc:
      employeeData?.rfc ?? "Sin RFC",

    mainArea:
      organizationInfo.mainArea,

    department:
      organizationInfo.department,

    finalUnitName:
      organizationInfo.finalUnitName,

    position:
      puesto?.nombre ?? "Sin puesto",

    supervisorId:
      supervisor?.id ?? null,

    supervisor:
      supervisor?.nombre_completo ??
      "Sin supervisor asignado",

    scheduleId:
      horarioActual?.horario_id ?? null,

    schedule:
      horarioActual?.nombre ?? "Sin horario",

    scheduleTurn:
      horarioActual?.tipo_turno_nombre ?? "",

    scheduleStartDate:
      horarioActual?.fecha_inicio ?? null,

    zkUserId:
      dispositivo?.zk_user_id ?? "Sin usuario ZK",

    status: formatEmployeeStatus(
      employeeData?.estatus,
    ),

    attendanceStatus: "Sin evaluar",

    lastPunch: "Sin registros",
  };
}
function EmployeeDetailPage() {
  const { employeeId } = useParams();

  const [employee, setEmployee] = useState(null);
  const [isLoadingEmployee, setIsLoadingEmployee] =
    useState(false);  
  const [employeeError, setEmployeeError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadEmployee() {
      try {
        setIsLoadingEmployee(true);
        setEmployeeError("");

        const [
          employeeProfile,
          organizationalUnitsResponse,
        ] = await Promise.all([
          empleadosApi.obtenerPerfil(employeeId),
          catalogosApi.listarUnidadesOrganizacionales(),
        ]);

        if (!isMounted) return;

        const organizationalUnits =
          getCatalogArrayFromApiResponse(
            organizationalUnitsResponse,
          );

        setEmployee(
          mapEmployeeDetailFromApi(
            employeeProfile,
            organizationalUnits,
          ),
        );
      } catch (error) {
        if (!isMounted) return;

        setEmployee(null);
        setEmployeeError(
          error.message ||
            "No fue posible cargar el empleado desde el backend.",
        );
      } finally {
        if (isMounted) {
          setIsLoadingEmployee(false);
        }
      }
    }

    if (employeeId) {
      loadEmployee();
    }

    return () => {
      isMounted = false;
    };
  }, [employeeId]);

  const employeeAccess = getModuleAccess(
    currentUser.role,
    MODULES.EMPLEADOS,
  );

  if (isLoadingEmployee) {
  return (
    <div className="page-stack">
      <PageHeader
        title="Cargando empleado"
        description="Consultando la información del empleado en el backend."
      />

      <section className="panel-card">
        <div className="empty-state">
          <UserRound size={48} />

          <h3>Cargando información</h3>

          <p>
            Espera un momento mientras se recupera el
            expediente del empleado.
          </p>
        </div>
      </section>
    </div>
  );
}

  if (!employee) {
    return (
      <div className="page-stack">
        <PageHeader
          title="Empleado no encontrado"
          description="No existe un empleado con el identificador solicitado."
        />

        <section className="panel-card">
          <div className="empty-state">
            <UserRound size={48} />

            <h3>Empleado no encontrado</h3>

            <p>
              {employeeError ||
                "Verifica que el identificador del empleado sea correcto."}
            </p>

            <Link
              className="secondary-button link-button"
              to="/employees"
            >
              <ArrowLeft size={17} />
              Volver a empleados
            </Link>
          </div>
        </section>
      </div>
    );
  }

  /**
   * Seguridad adicional dentro de la página.
   *
   * Aunque la ruta pertenezca al módulo Empleados,
   * el Supervisor solo puede consultar empleados
   * de su propio departamento.
   */
  const canViewEmployee =
    employeeAccess === ACCESS_LEVELS.TOTAL ||
    employeeAccess === ACCESS_LEVELS.LECTURA ||
    (
      employeeAccess === ACCESS_LEVELS.AREA &&
      Number(employee.departmentId) ===
        Number(currentUser.departmentId)
    ) ||
    (
      employeeAccess === ACCESS_LEVELS.PROPIO &&
      Number(employee.id) ===
        Number(currentUser.employeeId)
    );

  if (!canViewEmployee) {
    return (
      <div className="page-stack">
        <PageHeader
          title="Acceso no autorizado"
          description="No tienes permisos para consultar la información de este empleado."
        />

        <section className="panel-card">
          <div className="empty-state">
            <ShieldCheck size={48} />

            <h3>Empleado fuera de tu alcance</h3>

            <p>
              Solo puedes consultar empleados pertenecientes
              al área asignada a tu usuario.
            </p>

            <Link
              className="secondary-button link-button"
              to="/employees"
            >
              <ArrowLeft size={17} />
              Volver a empleados
            </Link>
          </div>
        </section>
      </div>
    );
  }

  /**
   * Filtra la asistencia usando la llave interna employeeId.
   */
  const employeeAttendance = mockAttendanceSummary.filter(
    (row) =>
      Number(row.employeeId) === Number(employee.id),
  );

  /**
   * Una incidencia es cualquier registro distinto de "No".
   */
  const employeeIncidents = employeeAttendance.filter(
    (row) =>
      row.incident &&
      row.incident !== "No",
  );

  const completeDays = employeeAttendance.filter(
    (row) => row.status.includes("Completo"),
  ).length;

  const lateDays = employeeAttendance.filter(
    (row) => row.status === "Retardo",
  ).length;

  const absenceDays = employeeAttendance.filter(
    (row) => row.status === "Falta",
  ).length;

  const ordinarySeconds = employeeAttendance.reduce(
    (total, row) =>
      total + durationToSeconds(row.ordinaryTime),
    0,
  );

  const extraSeconds = employeeAttendance.reduce(
    (total, row) =>
      total + durationToSeconds(row.extraTime),
    0,
  );

  const totalOrdinaryTime =
    formatDuration(ordinarySeconds);

  const totalExtraTime =
    formatDuration(extraSeconds);

  /**
   * Solo los usuarios con acceso total podrán modificar
   * empleados cuando implementemos la pantalla de edición.
   */
  const canManageEmployee =
    employeeAccess === ACCESS_LEVELS.TOTAL;

  return (
    <div className="page-stack">
      <PageHeader
        title={employee.fullName}
        description={`${employee.employeeCode} · ${employee.position} · ${employee.mainArea}`}
      >
        <div className="header-actions">
          <Link
            className="secondary-button link-button"
            to="/employees"
          >
            <ArrowLeft size={17} />
            Volver
          </Link>
          {canManageEmployee && (
            <Link
              className="secondary-button link-button"
              to={`/employees/${employee.employeeCode}/edit`}
            >
              <Pencil size={17} />
              Editar empleado
            </Link>
          )}
          <Link
            className="primary-button link-button"
            to={`/reports/employee/${employee.id}`}
          >
            <FileText size={17} />
            Ver reporte
          </Link>
        </div>
      </PageHeader>

      <section className="profile-grid">
        <article className="panel-card employee-profile-card">
          <div className="large-avatar">
            <UserRound size={42} />
          </div>

          <h3>{employee.fullName}</h3>

          <p>{employee.position}</p>

          <div className="profile-badges">
            <span
              className={
                employee.status === "Activo"
                  ? "badge success"
                  : "badge danger"
              }
            >
              {employee.status}
            </span>

            <span className="badge neutral">
              Código {employee.employeeCode}
            </span>

            <span
              className={getStatusClass(
                employee.attendanceStatus,
              )}
            >
              {employee.attendanceStatus}
            </span>
          </div>

          {canManageEmployee && (
            <span className="table-subtext">
              Usuario con permisos administrativos
              para modificar este empleado.
            </span>
          )}
        </article>

        <article className="panel-card profile-info-card">
          <div className="panel-header">
            <div>
              <h3>Información general</h3>

              <p>
                Datos administrativos y laborales del empleado.
              </p>
            </div>

            <UserRound size={22} />
          </div>

          <div className="info-grid">
            <div>
              <span>RFC</span>
              <strong>{employee.rfc}</strong>
            </div>

            <div>
              <span>Área principal</span>
              <strong>{employee.mainArea}</strong>
            </div>

            <div>
              <span>Departamento específico</span>
              <strong>{employee.department}</strong>
            </div>

            <div>
              <span>Puesto</span>
              <strong>{employee.position}</strong>
            </div>

            <div>
              <span>Supervisor</span>
              <strong>{employee.supervisor}</strong>
            </div>

            <div>
              <span>Horario asignado</span>
              <strong>
                {employee.scheduleTurn
                  ? `${employee.schedule} · ${employee.scheduleTurn}`
                  : employee.schedule}
              </strong>
            </div>

            <div>
              <span>Inicio de horario</span>
              <strong>
                {employee.scheduleStartDate ?? "Sin fecha"}
              </strong>
            </div>

            <div>
              <span>Última checada</span>
              <strong>{employee.lastPunch}</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Relación con reloj checador</h3>

            <p>
              Identificadores utilizados para sincronizar
              empleados y checadas.
            </p>
          </div>

          <Fingerprint size={22} />
        </div>

        <div className="info-grid">
          <div>
            <span>Código de empleado</span>
            <strong>{employee.employeeCode}</strong>
          </div>

          <div>
            <span>Usuario ZKTeco</span>
            <strong>{employee.zkUserId}</strong>
          </div>

          <div>
            <span>Estado del empleado</span>
            <strong>{employee.status}</strong>
          </div>

          <div>
            <span>Última marcación recibida</span>
            <strong>{employee.lastPunch}</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <CheckCircle2 size={22} />
          </div>

          <div>
            <p>Días completos</p>
            <strong>{completeDays}</strong>
            <span>Entradas y salidas válidas</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>

          <div>
            <p>Horas ordinarias</p>
            <strong>{totalOrdinaryTime}</strong>
            <span>Acumulado del periodo visible</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <CalendarClock size={22} />
          </div>

          <div>
            <p>Horas extra</p>
            <strong>{totalExtraTime}</strong>
            <span>Tiempo extraordinario acumulado</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <AlertTriangle size={22} />
          </div>

          <div>
            <p>Incidencias</p>
            <strong>{employeeIncidents.length}</strong>
            <span>
              {lateDays} retardos · {absenceDays} faltas
            </span>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Detalle de asistencia</h3>

            <p>
              Registros procesados asociados al empleado.
            </p>
          </div>

          <ShieldCheck size={22} />
        </div>

        {employeeAttendance.length === 0 ? (
          <div className="empty-state">
            <Clock size={42} />

            <h3>Sin registros de asistencia</h3>

            <p>
              Este empleado todavía no tiene asistencias
              procesadas en el periodo disponible.
            </p>
          </div>
        ) : (
          <div className="simple-table">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Día</th>
                  <th>Horario esperado</th>
                  <th>Entrada</th>
                  <th>Salida</th>
                  <th>Retardo</th>
                  <th>Ordinario</th>
                  <th>Extra</th>
                  <th>Estado</th>
                </tr>
              </thead>

              <tbody>
                {employeeAttendance.map((row) => (
                  <tr key={row.id}>
                    <td>{row.date}</td>
                    <td>{row.day}</td>
                    <td>{row.expectedSchedule}</td>
                    <td>{row.entryTime || "—"}</td>
                    <td>{row.exitTime || "—"}</td>
                    <td>{row.lateMinutes} min</td>
                    <td>{row.ordinaryTime}</td>
                    <td>{row.extraTime}</td>

                    <td>
                      <span
                        className={getStatusClass(row.status)}
                      >
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Incidencias del periodo</h3>

            <p>
              Registros relacionados con retardos, faltas,
              omisiones o tiempo extraordinario.
            </p>
          </div>

          <AlertTriangle size={22} />
        </div>

        {employeeIncidents.length === 0 ? (
          <div className="empty-state">
            <CheckCircle2 size={42} />

            <h3>Sin incidencias</h3>

            <p>
              No existen incidencias registradas para este
              empleado en el periodo disponible.
            </p>
          </div>
        ) : (
          <div className="simple-table">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Descripción</th>
                  <th>Estatus</th>
                </tr>
              </thead>

              <tbody>
                {employeeIncidents.map((incident) => (
                  <tr key={`incident-${incident.id}`}>
                    <td>{incident.date}</td>

                    <td>{incident.incident}</td>

                    <td>
                      Incidencia generada a partir del estado
                      de asistencia: {incident.status}.
                    </td>

                    <td>
                      <span
                        className={getIncidentClass(
                          incident.incidentStatus,
                        )}
                      >
                        {incident.incidentStatus}
                      </span>
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

export default EmployeeDetailPage;