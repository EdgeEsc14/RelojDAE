import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AlertCircle, Fingerprint } from "lucide-react";

import { useAuth } from "../../context/AuthContext";

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const { login, isAuthenticated, loading: authLoading } = useAuth();

  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const redirectTo = location.state?.from?.pathname || "/dashboard";

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [authLoading, isAuthenticated, navigate]);

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setSubmitting(true);

    try {
      await login({
        correo,
        password,
      });

      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || "No fue posible iniciar sesión.");
    } finally {
      setSubmitting(false);
    }
  }

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
            Correo
            <input
              type="email"
              placeholder="usuario@correo.com"
              value={correo}
              onChange={(event) => setCorreo(event.target.value)}
              autoComplete="email"
              required
            />
          </label>

          <label>
            Contraseña
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error && (
            <div className="form-error">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <button type="submit" disabled={submitting || authLoading}>
            {submitting ? "Entrando..." : "Entrar al sistema"}
          </button>
        </form>

        <small>Acceso con usuario real del sistema.</small>
      </section>
    </main>
  );
}

export default LoginPage;