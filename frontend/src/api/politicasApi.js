import { apiRequest } from "./client";

export const politicasApi = {
  obtenerActiva: () => {
    return apiRequest("/politicas-asistencia/activa");
  },

  actualizarActiva: (payload) => {
    return apiRequest("/politicas-asistencia/activa", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
};
