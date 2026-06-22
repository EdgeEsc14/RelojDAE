import { Link } from "react-router-dom";
import { ShieldX } from "lucide-react";

function AccessDeniedPage() {
  return (
    <div className="page-stack">
      <section className="panel-card">
        <div className="empty-state">
          <ShieldX size={48} />

          <h2>Acceso no autorizado</h2>

          <p>
            NO TIENE PERMISO PARA ENTRAR AQUI
          </p>

          <Link
            className="primary-button"
            to="/attendance"
          >
            Ir a Asistencia
          </Link>
        </div>
      </section>
    </div>
  );
}

export default AccessDeniedPage;