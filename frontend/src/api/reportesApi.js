import { getStoredToken } from "./authApi";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

/**
 * API client para el módulo de reportes.
 * Soporta descarga de archivos CSV y PDF.
 */

export function getReporteEmpleadoJSON(codigoEmpleado, fechaInicio, fechaFin) {
  return fetchReporte(
    `/reportes/empleado/${codigoEmpleado}?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&formato=json`
  );
}

export function getReporteDepartamentalJSON(fechaInicio, fechaFin, unidadId) {
  let url = `/reportes/departamental?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&formato=json`;
  if (unidadId) url += `&unidad_organizacional_id=${unidadId}`;
  return fetchReporte(url);
}

export function descargarReporteEmpleadoCSV(codigoEmpleado, fechaInicio, fechaFin) {
  const url = `/reportes/empleado/${codigoEmpleado}?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&formato=csv`;
  return descargarArchivo(url, `reporte_empleado_${codigoEmpleado}_${fechaInicio}_${fechaFin}.csv`);
}

export function descargarReporteEmpleadoPDF(codigoEmpleado, fechaInicio, fechaFin) {
  const url = `/reportes/empleado/${codigoEmpleado}?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&formato=pdf`;
  return descargarArchivo(url, `reporte_empleado_${codigoEmpleado}_${fechaInicio}_${fechaFin}.pdf`);
}

export function descargarReporteDepartamentalCSV(fechaInicio, fechaFin, unidadId) {
  let url = `/reportes/departamental?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&formato=csv`;
  if (unidadId) url += `&unidad_organizacional_id=${unidadId}`;
  return descargarArchivo(url, `reporte_departamental_${fechaInicio}_${fechaFin}.csv`);
}

export function descargarReporteDepartamentalPDF(fechaInicio, fechaFin, unidadId) {
  let url = `/reportes/departamental?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&formato=pdf`;
  if (unidadId) url += `&unidad_organizacional_id=${unidadId}`;
  return descargarArchivo(url, `reporte_departamental_${fechaInicio}_${fechaFin}.pdf`);
}

// ============================================================
// Helpers
// ============================================================

async function fetchReporte(path) {
  const url = `${API_BASE_URL}${path}`;
  const token = getStoredToken();

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const message = data?.detail || `Error HTTP ${response.status}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return response.json();
}

async function descargarArchivo(path, filename) {
  const url = `${API_BASE_URL}${path}`;
  const token = getStoredToken();

  const response = await fetch(url, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    let message = `Error HTTP ${response.status}`;
    try {
      const data = await response.json();
      message = data?.detail || message;
    } catch {
      // ignore parse error
    }
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(blobUrl);
}
