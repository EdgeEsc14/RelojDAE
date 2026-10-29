import { apiRequest } from "./client";
import { getStoredToken } from "./authApi";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

function buildQuery(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, value);
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

async function descargarArchivo(path, filename) {
  const url = `${API_BASE_URL}${path}`;
  const token = getStoredToken();

  const response = await fetch(url, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    let message = `Error HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data?.detail || message;
    } catch {
      // ignore parse error
    }
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(blobUrl);
}

export const auditoriaApi = {
  obtenerResumen: (filtros) => {
    return apiRequest(`/auditoria/resumen${buildQuery(filtros)}`);
  },

  obtenerFiltrosBitacora: () => {
    return apiRequest("/auditoria/bitacora/filtros");
  },

  listarBitacora: (filtros) => {
    return apiRequest(`/auditoria/bitacora${buildQuery(filtros)}`);
  },

  obtenerDetalleBitacora: (id) => {
    return apiRequest(`/auditoria/bitacora/${id}`);
  },

  descargarBitacoraCSV: (filtros) => {
    return descargarArchivo(
      `/auditoria/bitacora/export${buildQuery(filtros)}`,
      `auditoria_bitacora_${new Date().toISOString().slice(0, 10)}.csv`
    );
  },

  listarLogin: (filtros) => {
    return apiRequest(`/auditoria/login${buildQuery(filtros)}`);
  },

  descargarLoginCSV: (filtros) => {
    return descargarArchivo(
      `/auditoria/login/export${buildQuery(filtros)}`,
      `auditoria_login_${new Date().toISOString().slice(0, 10)}.csv`
    );
  },
};
