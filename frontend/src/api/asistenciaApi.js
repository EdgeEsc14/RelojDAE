import { apiRequest } from "./client";

export const asistenciaApi = {
  listarDiaria: ({
    fecha,
    q = "",
    estatus = "",
    unidadOrganizacionalId = "",
    limit = 100,
    offset = 0,
  }) => {
    const params = new URLSearchParams();

    params.set("fecha", fecha);

    if (q) params.set("q", q);
    if (estatus) params.set("estatus", estatus);
    if (unidadOrganizacionalId) {
      params.set("unidad_organizacional_id", unidadOrganizacionalId);
    }

    params.set("limit", String(limit));
    params.set("offset", String(offset));

    return apiRequest(`/asistencia/diaria?${params.toString()}`);
  },

  obtenerResumenEmpleado: (codigoEmpleado, limite = 10) => {
    return apiRequest(
      `/asistencia/empleados/${codigoEmpleado}/resumen?limite=${limite}`,
    );
  },

  procesar: ({ fechaInicio, fechaFin }) => {
    return apiRequest("/asistencia/procesar", {
      method: "POST",
      body: JSON.stringify({
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
      }),
    });
  },
};