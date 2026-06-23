import { apiRequest } from "./client";

/**
 * API de catálogos.
 *
 * Consume catálogos reales desde FastAPI.
 */
export const catalogosApi = {
  obtenerTodos: () => {
    return apiRequest("/catalogos/todos");
  },

  listarUnidadesOrganizacionales: () => {
    return apiRequest("/catalogos/unidades-organizacionales");
  },

  listarPuestos: () => {
    return apiRequest("/catalogos/puestos");
  },

  listarHorarios: () => {
    return apiRequest("/catalogos/horarios");
  },

  listarTiposTurno: () => {
    return apiRequest("/catalogos/tipos-turno");
  },

  listarDispositivos: () => {
    return apiRequest("/catalogos/dispositivos");
  },

  listarRoles: () => {
    return apiRequest("/catalogos/roles");
  },

  listarTiposMarcacion: () => {
    return apiRequest("/catalogos/tipos-marcacion");
  },

  listarTiposIncidencia: () => {
    return apiRequest("/catalogos/tipos-incidencia");
  },
};
