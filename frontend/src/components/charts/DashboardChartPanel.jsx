import { useEffect, useMemo, useRef, useState } from "react";

import AttendanceByDayChart from "./AttendanceByDayChart";
import AuditEventsByModuleChart from "./AuditEventsByModuleChart";
import DelaysByEmployeeChart from "./DelaysByEmployeeChart";
import DeviceStatusChart from "./DeviceStatusChart";
import ExtraTimeByEmployeeChart from "./ExtraTimeByEmployeeChart";
import IncidentsByTypeChart from "./IncidentsByTypeChart";
import PunchesByHourChart from "./PunchesByHourChart";
import SyncByDeviceChart from "./SyncByDeviceChart";

const CHART_OPTIONS = [
  {
    value: "attendance",
    label: "Asistencia por día",
    description:
      "Muestra el comportamiento diario de asistencias completas, retardos y faltas en el periodo visible.",
  },
  {
    value: "incidents",
    label: "Incidencias por tipo",
    description:
      "Distribuye las incidencias registradas por categoría: tiempo extra, retardos, omisiones, faltas y permisos.",
  },
  {
    value: "punches",
    label: "Checadas por hora",
    description:
      "Permite identificar las horas con mayor concentración de entradas y salidas del personal.",
  },
  {
    value: "devices",
    label: "Estado de dispositivos",
    description:
      "Resume el estado operativo de los relojes ZKTeco registrados en el sistema.",
  },
  {
    value: "extra",
    label: "Top 10 tiempo extra por empleado",
    description:
      "Muestra los empleados con mayor tiempo extraordinario acumulado en el periodo visible.",
  },
  {
    value: "delays",
    label: "Top 10 retardos por empleado",
    description:
      "Muestra los empleados con mayor número de retardos acumulados en el periodo visible.",
  },
  {
    value: "audit",
    label: "Eventos de auditoría por módulo",
    description:
      "Muestra qué módulos concentran mayor actividad registrada en la bitácora.",
  },
  {
    value: "sync",
    label: "Sincronizaciones por dispositivo",
    description:
      "Compara registros insertados y duplicados durante sincronizaciones con relojes ZKTeco.",
  },
];

function useChartWidth() {
  const containerRef = useRef(null);
  const [width, setWidth] = useState(800);

  useEffect(() => {
    if (!containerRef.current) return;

    const updateWidth = () => {
      const nextWidth = containerRef.current?.clientWidth || 800;
      setWidth(Math.max(nextWidth, 320));
    };

    updateWidth();

    const observer = new ResizeObserver(updateWidth);
    observer.observe(containerRef.current);

    return () => observer.disconnect();
  }, []);

  return { containerRef, width };
}

function renderChart(chartType, width) {
  if (chartType === "attendance") return <AttendanceByDayChart width={width} />;
  if (chartType === "incidents") return <IncidentsByTypeChart width={width} />;
  if (chartType === "punches") return <PunchesByHourChart width={width} />;
  if (chartType === "devices") return <DeviceStatusChart width={width} />;
  if (chartType === "extra") return <ExtraTimeByEmployeeChart width={width} />;
  if (chartType === "delays") return <DelaysByEmployeeChart width={width} />;
  if (chartType === "audit") return <AuditEventsByModuleChart width={width} />;
  if (chartType === "sync") return <SyncByDeviceChart width={width} />;

  return <AttendanceByDayChart width={width} />;
}

function DashboardChartPanel() {
  const [selectedChart, setSelectedChart] = useState("attendance");
  const { containerRef, width } = useChartWidth();

  const activeOption = useMemo(
    () => CHART_OPTIONS.find((option) => option.value === selectedChart),
    [selectedChart]
  );

  return (
    <section className="panel-card chart-panel">
      <div className="chart-panel-header">
        <div>
          <h3>Análisis visual</h3>
          <p>
            Selecciona una gráfica para analizar asistencia, incidencias,
            dispositivos, sincronizaciones o auditoría.
          </p>
        </div>

        <label className="chart-selector">
          <span>Gráfica</span>
          <select
            value={selectedChart}
            onChange={(event) => setSelectedChart(event.target.value)}
          >
            {CHART_OPTIONS.map((option) => (
              <option value={option.value} key={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="chart-body">
        <div className="chart-render-area" ref={containerRef}>
          {renderChart(selectedChart, width)}
        </div>
      </div>

      <div className="chart-description">
        <strong>{activeOption?.label}</strong>
        <p>{activeOption?.description}</p>
      </div>
    </section>
  );
}

export default DashboardChartPanel;