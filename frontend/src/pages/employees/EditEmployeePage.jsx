import { Link, useParams } from "react-router-dom";
import { ArrowLeft, UserRoundX } from "lucide-react";

import EmployeeForm from "../../components/employees/EmployeeForm";
import PageHeader from "../../components/layout/PageHeader";
import { mockEmployees } from "../../data/mockEmployees";

function EditEmployeePage() {
  const { employeeId } = useParams();

  const employee = mockEmployees.find(
    (item) => item.id === Number(employeeId),
  );

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
              Verifica el identificador o vuelve al catálogo
              de empleados.
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