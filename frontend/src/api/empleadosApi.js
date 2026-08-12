import { apiRequest } from "./client";

function buildQuery(params = {}) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (
      value === undefined ||
      value === null ||
      value === ""
    ) {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach((item) => {
        searchParams.append(key, String(item));
      });

      return;
    }

    searchParams.set(key, String(value));
  });

  const query = searchParams.toString();

  return query ? `?${query}` : "";
}

function encodeEmployeeCode(codigoEmpleado) {
  return encodeURIComponent(
    String(codigoEmpleado ?? "").trim(),
  );
}

/**
 * API real del módulo de empleados.
 */
export const empleadosApi = {
  listar: (params = {}) => {
    return apiRequest(
      `/empleados${buildQuery(params)}`,
    );
  },

  obtenerPorCodigo: (codigoEmpleado) => {
    const codigo = encodeEmployeeCode(
      codigoEmpleado,
    );

    return apiRequest(`/empleados/${codigo}`);
  },

  obtenerPerfil: (codigoEmpleado) => {
    const codigo = encodeEmployeeCode(
      codigoEmpleado,
    );

    return apiRequest(
      `/empleados/${codigo}/perfil`,
    );
  },

  obtenerSiguienteCodigo: (prefijo = "DAE") => {
    return apiRequest(
      `/empleados/siguiente-codigo${buildQuery({
        prefijo,
      })}`,
    );
  },

  obtenerSiguienteZkUserId: () => {
    return apiRequest("/empleados/siguiente-zk-user-id");
  },

  verificarZk: (codigoEmpleado) => {
    const codigo = encodeEmployeeCode(codigoEmpleado);
    return apiRequest(`/empleados/${codigo}/verificar-zk`);
  },

  reintentarSincronizacion: (codigoEmpleado, dispositivoId) => {
    const codigo = encodeEmployeeCode(codigoEmpleado);
    return apiRequest(
      `/empleados/${codigo}/dispositivos/${dispositivoId}/reintentar`,
      { method: "POST" },
    );
  },

  /**
   * Endpoint anterior.
   *
   * Se conserva temporalmente para edición y compatibilidad.
   * Las nuevas altas deben usar crearAltaIntegral().
   */
  crear: (payload) => {
    return apiRequest("/empleados", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  crearAltaIntegral: (payload) => {
    return apiRequest(
      "/empleados/alta-integral",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },

  actualizar: (
    codigoEmpleado,
    payload,
  ) => {
    const codigo = encodeEmployeeCode(
      codigoEmpleado,
    );

    return apiRequest(`/empleados/${codigo}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  actualizarEstatus: (
    codigoEmpleado,
    payload,
  ) => {
    const codigo = encodeEmployeeCode(
      codigoEmpleado,
    );

    return apiRequest(
      `/empleados/${codigo}/estatus`,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      },
    );
  },

  asignarHorario: (
    codigoEmpleado,
    payload,
  ) => {
    const codigo = encodeEmployeeCode(
      codigoEmpleado,
    );

    return apiRequest(
      `/empleados/${codigo}/horarios/asignar`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },

  asignarDispositivo: (
    codigoEmpleado,
    payload,
  ) => {
    const codigo = encodeEmployeeCode(
      codigoEmpleado,
    );

    return apiRequest(
      `/empleados/${codigo}/dispositivos/asignar`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },

  crearUsuarioSistema: (
    codigoEmpleado,
    payload,
  ) => {
    const codigo = encodeEmployeeCode(
      codigoEmpleado,
    );

    return apiRequest(
      `/empleados/${codigo}/usuario-sistema`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },

  sincronizarRelojes: (
    codigoEmpleado,
    dispositivoIds = [],
  ) => {
    const codigo = encodeEmployeeCode(
      codigoEmpleado,
    );

    return apiRequest(
      `/empleados/${codigo}/sincronizar-relojes`,
      {
        method: "POST",
        body: JSON.stringify({
          dispositivo_ids: dispositivoIds,
        }),
      },
    );
  },

  reintentarSincronizacion: (
    codigoEmpleado,
    dispositivoId,
  ) => {
    const codigo = encodeEmployeeCode(
      codigoEmpleado,
    );

    return apiRequest(
      `/empleados/${codigo}/dispositivos/${Number(
        dispositivoId,
      )}/reintentar`,
      {
        method: "POST",
      },
    );
  },
};


empleadosApi.exportarCSV = async () => {
  const { getStoredToken } = await import("./authApi");
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
  const token = getStoredToken();

  const response = await fetch(`${API_BASE_URL}/empleados/exportar-csv`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error(`Error HTTP ${response.status}`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "empleados.csv";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
