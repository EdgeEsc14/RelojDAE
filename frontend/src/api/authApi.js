const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

const AUTH_TOKEN_KEY = "relojdae_access_token";

async function request(endpoint, options = {}) {
  const token = getStoredToken();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      data?.detail?.message ||
      data?.detail ||
      data?.message ||
      `Error HTTP ${response.status}`;

    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}

export function getStoredToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function storeToken(token) {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearStoredToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

export async function loginUser({ correo, password }) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      correo,
      password,
    }),
  });
}

export async function getCurrentUser() {
  return request("/auth/me");
}

export function logoutUser() {
  clearStoredToken();
}