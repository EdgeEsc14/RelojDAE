import { apiRequest } from "./client";

/**
 * API client para el módulo de Calendario Laboral.
 * Consume /api/v1/calendario
 */

export function getCalendarios() {
  return apiRequest("/calendario/calendarios");
}

export function getEventos({ anio, mes, tipoEvento, page = 1, pageSize = 100 } = {}) {
  const params = new URLSearchParams();
  if (anio) params.set("anio", String(anio));
  if (mes) params.set("mes", String(mes));
  if (tipoEvento) params.set("tipo_evento", tipoEvento);
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  return apiRequest(`/calendario/eventos?${params.toString()}`);
}

export function getEvento(eventoId) {
  return apiRequest(`/calendario/eventos/${eventoId}`);
}

export function crearEvento(data) {
  return apiRequest("/calendario/eventos", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function actualizarEvento(eventoId, data) {
  return apiRequest(`/calendario/eventos/${eventoId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function desactivarEvento(eventoId) {
  return apiRequest(`/calendario/eventos/${eventoId}`, {
    method: "DELETE",
  });
}

export function consultarDia(fecha, empleadoId) {
  let url = `/calendario/dia/${fecha}`;
  if (empleadoId) url += `?empleado_id=${empleadoId}`;
  return apiRequest(url);
}

export function getEventosRango(fechaInicio, fechaFin) {
  return apiRequest(`/calendario/rango?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`);
}
