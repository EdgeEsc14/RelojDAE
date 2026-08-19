import { apiRequest } from "./client";

/**
 * API client para el módulo de incidencias.
 * Consume /api/v1/incidencias
 */

export function getIncidencias({
  page = 1,
  pageSize = 20,
  estatus,
  tipoIncidenciaId,
  empleadoId,
  fechaInicio,
  fechaFin,
  busqueda,
} = {}) {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  if (estatus) params.set("estatus", estatus);
  if (tipoIncidenciaId) params.set("tipo_incidencia_id", String(tipoIncidenciaId));
  if (empleadoId) params.set("empleado_id", String(empleadoId));
  if (fechaInicio) params.set("fecha_inicio", fechaInicio);
  if (fechaFin) params.set("fecha_fin", fechaFin);
  if (busqueda) params.set("busqueda", busqueda);

  return apiRequest(`/incidencias?${params.toString()}`);
}

export function getContadores() {
  return apiRequest("/incidencias/contadores");
}

export function getIncidencia(incidenciaId) {
  return apiRequest(`/incidencias/${incidenciaId}`);
}

export function crearIncidencia(data) {
  return apiRequest("/incidencias", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function revisarIncidencia(incidenciaId, data) {
  return apiRequest(`/incidencias/${incidenciaId}/revisar`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
