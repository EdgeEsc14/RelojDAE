import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, UserRoundX } from "lucide-react";

import { empleadosApi } from "../../api/empleadosApi";
import EmployeeForm from "../../components/employees/EmployeeForm";
import PageHeader from "../../components/layout/PageHeader";

function formatEmployeeStatus(status) {
  const normalizedStatus = String(status ?? "")
    .trim()
    .toUpperCase();

  if (normalizedStatus === "ACTIVO") return "Activo";
  if (normalizedStatus === "INACTIVO") return "Inactivo";
  if (normalizedStatus === "BAJA") return "Inactivo";

  return status || "Activo";
}

function mapEmployeeProfileToForm(apiResponse) {
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

  const fullName =
    employeeData?.nombre_completo ??
    [
      employeeData?.nombres,
      employeeData?.apellido_paterno,
      employeeData?.apellido_materno,
    ]
      .filter(Boolean)
      .join(" ");

  return {
    id: employeeData?.id ?? null,

    employeeCode: employeeData?.codigo_empleado ?? "",
    codigo_empleado: employeeData?.codigo_empleado ?? "",

    fullName: fullName || "Empleado sin nombre",

    nombres: employeeData?.nombres ?? "",
    apellido_paterno: employeeData?.apellido_paterno ?? "",
    apellido_materno: employeeData?.apellido_materno ?? "",

    rfc: employeeData?.rfc ?? "",
    email: employeeData?.correo ?? "",
    correo: employeeData?.correo ?? "",

    fechaIngreso:
      employeeData?.fecha_ingreso ??
      employeeData?.fechaIngreso ??
      null,

    status: formatEmployeeStatus(employeeData?.estatus),

    mainUnitId:
      unidadOrganizacional?.unidad_padre_id ??
      employeeData?.mainUnitId ??
      "",

    departmentId:
      unidadOrganizacional?.id ??
      employeeData?.unidad_organizacional_id ??
      employeeData?.departmentId ??
      "",

    positionId:
      puesto?.id ??
      employeeData?.puesto_id ??
      "",

    position:
      puesto?.nombre ??
      employeeData?.puesto ??
      "",

    supervisorId:
      supervisor?.id ??
      employeeData?.supervisor_id ??
      null,

    scheduleId:
      horarioActual?.horario_id ??
      employeeData?.horario_id ??
      "",

    schedule:
      horarioActual?.nombre ??
      horarioActual?.horario_nombre ??
      "Sin horario",

    scheduleStartDate:
      horarioActual?.fecha_inicio ??
      null,

    zkUserId:
      dispositivo?.zk_user_id ??
      employeeData?.zk_user_id ??
      "",
  };
}

function EditEmployeePage() {
  const { employeeId } = useParams();

  const [employee, setEmployee] = useState(null);
  const [isLoadingEmployee, setIsLoadingEmployee] = useState(false);
  const [employeeError, setEmployeeError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadEmployee() {
      try {
        setIsLoadingEmployee(true);
        setEmployeeError("");

        const employeeProfile = await empleadosApi.obtenerPerfil(employeeId);

        if (!isMounted) return;

        setEmployee(mapEmployeeProfileToForm(employeeProfile));
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

  if (isLoadingEmployee) {
    return (
      <div className="page-stack">
        <PageHeader
          title="Cargando empleado"
          description="Consultando la información real del empleado."
        />

        <section className="panel-card">
          <div className="empty-state">
            <UserRoundX size={48} />

            <h3>Cargando información</h3>

            <p>Espera un momento mientras se recupera el expediente.</p>
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
            <UserRoundX size={48} />

            <h3>No se encontró el empleado</h3>

            <p>
              {employeeError ||
                "Verifica el identificador o vuelve al catálogo de empleados."}
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

  return (
    <EmployeeForm
      mode="edit"
      initialEmployee={employee}
    />
  );
}

export default EditEmployeePage;