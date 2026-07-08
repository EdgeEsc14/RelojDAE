import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  TimerReset,
} from "lucide-react";

import { syncZkTime } from "../../api/zkApi";

function getStatusLabel(status) {
  const labels = {
    TIME_OK: "Hora correcta",
    TIME_CORRECTED: "Hora corregida",
    MIN_INTERVAL_NOT_REACHED: "Revisión no necesaria todavía",
    MAX_DAILY_CHECKS_REACHED: "Límite diario alcanzado",
    AUTO_SYNC_DISABLED: "Sincronización automática desactivada",
    DRIFT_DETECTED_WRITE_DISABLED: "Diferencia detectada, escritura desactivada",
    ERROR: "Error",
  };

  return labels[status] || status || "Sin revisión";
}

function getStatusClass(status) {
  if (status === "TIME_OK") return "badge success";
  if (status === "TIME_CORRECTED") return "badge success";
  if (status === "MIN_INTERVAL_NOT_REACHED") return "badge neutral";
  if (status === "MAX_DAILY_CHECKS_REACHED") return "badge warning";
  if (status === "DRIFT_DETECTED_WRITE_DISABLED") return "badge warning";
  if (status === "ERROR") return "badge danger";

  return "badge neutral";
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "No disponible";
  }

  return String(value);
}

function ZkTimeSyncPanel() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSync(force = false) {
    try {
      setLoading(true);
      setError("");

      const response = await syncZkTime({ force });

      setResult(response);
    } catch (err) {
      setError(
        err.message ||
          "No fue posible revisar la hora del reloj."
      );
    } finally {
      setLoading(false);
    }
  }

  const status = result?.status;
  const checked = Boolean(result?.checked);
  const corrected = Boolean(result?.corrected);

  return (
    <section className="panel-card">
      <div className="panel-header">
        <div>
          <h3>Sincronización de hora</h3>
          <p>
            Revisa la hora del reloj ZKTeco y la corrige si existe una
            diferencia mayor a la tolerancia configurada.
          </p>
        </div>

        <Clock size={22} />
      </div>

      <div className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            {corrected ? (
              <TimerReset size={22} />
            ) : (
              <CheckCircle2 size={22} />
            )}
          </div>

          <div>
            <p>Estado</p>
            <strong>
              <span className={getStatusClass(status)}>
                {getStatusLabel(status)}
              </span>
            </strong>
            <span>
              {result?.status === "MIN_INTERVAL_NOT_REACHED"
                ? "Aún no toca revisar por intervalo mínimo"
                : checked
                  ? "Última respuesta recibida"
                  : "Aún sin revisión en pantalla"}
            </span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>

          <div>
            <p>Hora del reloj</p>
            <strong>
              {formatValue(result?.device_time_after || result?.device_time_before)}
            </strong>
            <span>ZKTeco</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>

          <div>
            <p>Hora del servidor</p>
            <strong>{formatValue(result?.server_time)}</strong>
            <span>PC donde corre FastAPI</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <AlertTriangle size={22} />
          </div>

          <div>
            <p>Diferencia</p>
            <strong>
              {result?.drift_seconds !== undefined
                ? `${result.drift_seconds} s`
                : "No disponible"}
            </strong>
            <span>
              Revisiones: {result?.check_count ?? 0} /{" "}
              {result?.max_checks_per_day ?? 5}
            </span>
          </div>
        </article>
      </div>

      {error && (
        <div className="empty-state">
          <h3>Error al revisar hora</h3>
          <p>{error}</p>
        </div>
      )}

      <div className="header-actions">
        <button
          className="secondary-button"
          type="button"
          disabled={loading}
          onClick={() => handleSync(false)}
        >
          <RefreshCw size={17} />
          {loading ? "Revisando..." : "Revisar si corresponde"}
        </button>

        <button
          className="primary-button"
          type="button"
          disabled={loading}
          onClick={() => handleSync(true)}
        >
          <TimerReset size={17} />
          Forzar sincronización
        </button>
      </div>

      <p className="table-subtext">
        La revisión normal respeta el límite de 5 veces al día. La opción
        forzada ignora ese límite y debe usarse solo cuando sepas que el reloj
        perdió la hora.
      </p>
    </section>
  );
}

export default ZkTimeSyncPanel;