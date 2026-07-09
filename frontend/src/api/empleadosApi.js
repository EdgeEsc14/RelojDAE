import { apiRequest } from "./client";

/**
 * API de empleados.
 *
 * Estos métodos consumen los endpoints reales de FastAPI.
 */
export const empleadosApi = {
  listar: () => {
    return apiRequest("/empleados");
  },

  obtenerPorCodigo: (codigoEmpleado) => {
    return apiRequest(`/empleados/${codigoEmpleado}`);
  },

  obtenerPerfil: (codigoEmpleado) => {
    return apiRequest(`/empleados/${codigoEmpleado}/perfil`);
  },

  obtenerSiguienteCodigo: () => {
    return apiRequest("/empleados/siguiente-codigo");
  },

  crear: (payload) => {
    return apiRequest("/empleados", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  actualizar: (codigoEmpleado, payload) => {
    return apiRequest(`/empleados/${codigoEmpleado}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  actualizarEstatus: (codigoEmpleado, payload) => {
    return apiRequest(`/empleados/${codigoEmpleado}/estatus`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  asignarHorario: (codigoEmpleado, payload) => {
    return apiRequest(`/empleados/${codigoEmpleado}/horarios/asignar`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  asignarDispositivo: (codigoEmpleado, payload) => {
    return apiRequest(`/empleados/${codigoEmpleado}/dispositivos/asignar`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  crearUsuarioSistema: (codigoEmpleado, payload) => {
    return apiRequest(`/empleados/${codigoEmpleado}/usuario-sistema`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};