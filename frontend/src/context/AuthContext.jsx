import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  clearStoredToken,
  getCurrentUser,
  getStoredToken,
  loginUser,
  storeToken,
} from "../api/authApi";

const AuthContext = createContext(null);

function normalizeUser(user) {
  if (!user) return null;

  return {
    id: user.id,
    correo: user.correo,
    nombreUsuario: user.nombre_usuario,
    fullName: user.nombre_empleado || user.nombre_usuario || user.correo,
    role: user.rol,
    roleLabel: user.rol_nombre || user.rol,
    rolId: user.rol_id,
    estatus: user.estatus,
    empleadoId: user.empleado_id,
    codigoEmpleado: user.codigo_empleado,
    correoVerificado: user.correo_verificado,
    raw: user,
  };
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => getStoredToken());
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  async function loadSession() {
    const storedToken = getStoredToken();

    if (!storedToken) {
      setUser(null);
      setToken(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setAuthError("");

    try {
      const response = await getCurrentUser();

      setUser(normalizeUser(response));
      setToken(storedToken);
    } catch (err) {
      clearStoredToken();
      setUser(null);
      setToken(null);
      setAuthError(err.message || "Sesión inválida.");
    } finally {
      setLoading(false);
    }
  }

  async function login({ correo, password }) {
    setAuthError("");

    const response = await loginUser({
      correo,
      password,
    });

    storeToken(response.access_token);
    setToken(response.access_token);
    setUser(normalizeUser(response.user));

    return response;
  }

  function logout() {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }

  useEffect(() => {
    loadSession();
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      authError,
      isAuthenticated: Boolean(user && token),
      login,
      logout,
      reloadSession: loadSession,
    }),
    [user, token, loading, authError]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider.");
  }

  return context;
}