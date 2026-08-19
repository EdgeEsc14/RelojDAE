import { apiRequest } from "./client";

/**
 * API client para gestión de usuarios del sistema.
 * Consume /api/v1/usuarios
 */

export function getUsuarios({ page = 1, pageSize = 50, rolId, estatus, busqueda } = {}) {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  if (rolId) params.set("rol_id", String(rolId));
  if (estatus) params.set("estatus", estatus);
  if (busqueda) params.set("busqueda", busqueda);

  return apiRequest(`/usuarios?${params.toString()}`);
}

export function getUsuario(usuarioId) {
  return apiRequest(`/usuarios/${usuarioId}`);
}

export function getRoles() {
  return apiRequest("/usuarios/roles");
}

export function crearUsuario(data) {
  return apiRequest("/usuarios", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function actualizarUsuario(usuarioId, data) {
  return apiRequest(`/usuarios/${usuarioId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function desactivarUsuario(usuarioId) {
  return apiRequest(`/usuarios/${usuarioId}`, {
    method: "DELETE",
  });
}
