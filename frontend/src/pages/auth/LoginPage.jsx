import { useNavigate } from "react-router-dom";
import { Fingerprint } from "lucide-react";

function LoginPage() {
  const navigate = useNavigate();

  const handleSubmit = (event) => {
    event.preventDefault();
    navigate("/dashboard");
  };

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-logo">
          <Fingerprint size={34} />
        </div>

        <h1>Reloj DAE</h1>
        <p>Sistema de control de asistencia e incidencias</p>

        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Usuario
            <input type="text" placeholder="super.admin" defaultValue="super.admin" />
          </label>

          <label>
            Contraseña
            <input type="password" placeholder="••••••••" defaultValue="admin123" />
          </label>

          <button type="submit">Entrar al sistema</button>
        </form>

        <small>Vista demo visual.</small>
      </section>
    </main>
  );
}

export default LoginPage;