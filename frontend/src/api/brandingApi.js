import { apiRequest } from "./client";

export const brandingApi = {
  obtenerConfig: () => {
    return apiRequest("/branding/config");
  },

  actualizarConfig: (payload) => {
    return apiRequest("/branding/config", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
};
