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