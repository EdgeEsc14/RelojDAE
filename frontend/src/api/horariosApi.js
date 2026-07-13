import { apiRequest } from "./client";

export const horariosApi = {
  listar: () => {
    return apiRequest("/horarios");
  },

  crear: (payload) => {
    return apiRequest("/horarios", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  cambiarEstatus: (horarioId, activo) => {
    return apiRequest(`/horarios/${horarioId}/estatus`, {
      method: "PATCH",
      body: JSON.stringify({
        activo,
      }),
    });
  },
};