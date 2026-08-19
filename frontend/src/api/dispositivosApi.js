import { apiRequest } from "./client";

/**
 * API client para gestión de dispositivos ZKTeco.
 * Consume /api/v1/dispositivos
 */

export function getDispositivos({ activo, busqueda } = {}) {
  const params = new URLSearchParams();
  if (activo !== undefined && activo !== null) params.set("activo", String(activo));
  if (busqueda) params.set("busqueda", busqueda);
  const qs = params.toString();
  return apiRequest(`/dispositivos${qs ? `?${qs}` : ""}`);
}

export function getDispositivo(id) {
  return apiRequest(`/dispositivos/${id}`);
}

export function crearDispositivo(data) {
  return apiRequest("/dispositivos", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function actualizarDispositivo(id, data) {
  return apiRequest(`/dispositivos/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function probarConexion(id) {
  return apiRequest(`/dispositivos/${id}/probar-conexion`, {
    method: "POST",
  });
}

export function probarConexionLibre(data) {
  return apiRequest("/dispositivos/probar-conexion-libre", {
    method: "POST",
    body: JSON.stringify(data),
  });
}


export function consultarHora(id) {
  return apiRequest(`/dispositivos/${id}/hora`);
}

export function sincronizarHora(id, forzar = false) {
  const params = forzar ? "?forzar=true" : "";
  return apiRequest(`/dispositivos/${id}/sincronizar-hora${params}`, {
    method: "POST",
  });
}

export function sincronizarHoraTodos() {
  return apiRequest("/dispositivos/sincronizar-hora-todos", {
    method: "POST",
  });
}
