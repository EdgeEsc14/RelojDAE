import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, KeyRound } from "lucide-react";

import { useAuth } from "../../context/AuthContext";

function ChangePasswordPage() {
  const navigate = useNavigate();

  const {
    user,
    isAuthenticated,
    loading: authLoading,
    changePassword,
    logout,
  } = useAuth();

  const [passwordActual, setPasswordActual] = useState("");
  const [passwordNueva, setPasswordNueva] = useState("");
  const [confirmarPassword, setConfirmarPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      navigate("/login", { replace: true });
      return;
    }

    // Si el usuario ya no requiere el cambio (p. ej. acceso directo
    // a la URL tras completarlo), no debe quedarse en esta pantalla.
    if (!user?.requiereCambioPassword) {
      navigate("/dashboard", { replace: true });
    }
  }, [authLoading, isAuthenticated, user, navigate]);

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");

    if (passwordNueva !== confirmarPassword) {
      setError("La confirmación no coincide con la nueva contraseña.");
      return;
    }

    if (passwordNueva.length < 8) {
      setError("La nueva contraseña debe tener al menos 8 caracteres.");
      return;
    }

    setSubmitting(true);

    try {
      await changePassword({ passwordActual, passwordNueva });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "No fue posible cambiar la contraseña.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-logo">
          <KeyRound size={34} />
        </div>

        <h1>Cambio de contraseña obligatorio</h1>
        <p>
          Por seguridad, debes establecer una nueva contraseña antes de
          continuar al sistema.
        </p>

        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Contraseña actual
            <input
              type="password"
              value={passwordActual}
              onChange={(event) => setPasswordActual(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          <label>
            Nueva contraseña
            <input
              type="password"
              value={passwordNueva}
              onChange={(event) => setPasswordNueva(event.target.value)}
              autoComplete="new-password"
              minLength={8}
              required
            />
          </label>

          <label>
            Confirmar nueva contraseña
            <input
              type="password"
              value={confirmarPassword}
              onChange={(event) => setConfirmarPassword(event.target.value)}
              autoComplete="new-password"
              minLength={8}
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
            {submitting ? "Guardando..." : "Cambiar contraseña"}
          </button>
        </form>

        <small>
          <button type="button" className="link-button" onClick={logout}>
            Cerrar sesión
          </button>
        </small>
      </section>
    </main>
  );
}

export default ChangePasswordPage;
