const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

/**
 * Cliente HTTP base para consumir FastAPI desde React.
 *
 * Centralizamos aquí:
 * - URL base del backend
 * - headers JSON
 * - parseo de respuestas
 * - manejo de errores HTTP
 */
export async function apiRequest(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;

  const config = {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  };

  const response = await fetch(url, config);

  let data = null;

  const contentType = response.headers.get("content-type");

  if (contentType && contentType.includes("application/json")) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = text || null;
  }

  if (!response.ok) {
    const message =
      data?.detail ??
      data?.message ??
      `Error HTTP ${response.status} al consumir ${path}`;

    throw new Error(
      typeof message === "string" ? message : JSON.stringify(message)
    );
  }

  return data;
}
export const apiClient = apiRequest;