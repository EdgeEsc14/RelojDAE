import {
  Database,
  Download,
  LockKeyhole,
} from "lucide-react";

import ZkAttendanceRawPanel from "../../components/devices/ZkAttendanceRawPanel";
import PageHeader from "../../components/layout/PageHeader";

function AttendanceRawPage() {
  return (
    <div className="page-stack">
      <PageHeader
        title="Checadas crudas"
        description="Registros originales leídos directamente desde el reloj ZKTeco. Estos datos representan la evidencia base antes del procesamiento de asistencia."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button" disabled>
            <Download size={17} />
            Exportar raw
          </button>

          <button className="primary-button" type="button" disabled>
            <Database size={17} />
            Sincronizar a BD
          </button>
        </div>
      </PageHeader>

      <section className="warning-banner">
        <LockKeyhole size={22} />
        <div>
          <strong>Registro original del reloj</strong>
          <p>
            Esta vista consulta las marcaciones crudas directamente desde el reloj.
            Por ahora no guarda, no edita y no elimina registros. La sincronización
            hacia PostgreSQL se agregará en el siguiente paso.
          </p>
        </div>
      </section>

      <ZkAttendanceRawPanel />
    </div>
  );
}

export default AttendanceRawPage;