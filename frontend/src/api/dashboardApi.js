import { apiRequest } from "./client";

export const dashboardApi = {
  obtenerResumen: () => {
    return apiRequest("/dashboard/resumen");
  },
};