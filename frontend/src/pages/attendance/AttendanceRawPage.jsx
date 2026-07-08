import { LockKeyhole } from "lucide-react";

import ZkAttendanceRawPanel from "../../components/devices/ZkAttendanceRawPanel";
import PageHeader from "../../components/layout/PageHeader";

function AttendanceRawPage() {
  return (
    <div className="page-stack">
      <PageHeader
        title="Checadas crudas"
        description="Registros originales leídos directamente desde el reloj ZKTeco o consultados desde PostgreSQL después de sincronizar."
      />

      <section className="warning-banner">
        <LockKeyhole size={22} />
        <div>
          <strong>Registro original del reloj</strong>
          <p>
            Esta vista permite consultar marcaciones crudas desde el reloj y
            sincronizarlas a PostgreSQL como evidencia base. Las marcaciones no
            deben editarse manualmente; cualquier corrección debe realizarse
            mediante incidencias o reprocesamiento.
          </p>
        </div>
      </section>

      <ZkAttendanceRawPanel />
    </div>
  );
}

export default AttendanceRawPage;