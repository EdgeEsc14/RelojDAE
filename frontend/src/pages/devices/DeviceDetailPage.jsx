import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Check,
  Clock,
  Edit,
  Fingerprint,
  Loader,
  RefreshCcw,
  Server,
  Wifi,
  X,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  getDispositivo,
  probarConexion,
  actualizarDispositivo,
  consultarHora,
  sincronizarHora,
} from "../../api/dispositivosApi";
import { syncZkAttendanceToDb } from "../../api/zkApi";

function getStatusClass(estado) {
  if (estado === "CONECTADO") return "badge success";
  if (estado === "ERROR") return "badge danger";
  if (estado === "DESHABILITADO") return "badge neutral";
  return "badge warning";
}

function getStatusLabel(estado) {
  const labels = { CONECTADO: "Conectado", DESCONECTADO: "Desconectado", ERROR: "Error", DESHABILITADO: "Deshabilitado" };
  return labels[estado] || estado || "Desconocido";
}

function formatDateTime(value) {
  if (!value) return "Nunca";
  try {
    return new Date(value).toLocaleString("es-MX", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch { return value; }
}

function DeviceDetailPage() {
  const { deviceId } = useParams();
  const [device, setDevice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [probando, setProbando] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [horaResult, setHoraResult] = useState(null);
  const [horaLoading, setHoraLoading] = useState(false);
  const [horaSyncing, setHoraSyncing] = useState(false);

  // Editar
  const [showEdit, setShowEdit] = useState(false);
  const [editData, setEditData] = useState({});
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState("");

  useEffect(() => { loadDevice(); }, [deviceId]);

  async function loadDevice() {
    setLoading(true);
    setError("");
    try {
      const data = await getDispositivo(deviceId);
      setDevice(data);
    } catch (err) {
      setError(err.message || "Error al cargar dispositivo.");
    } finally {
      setLoading(false);
    }
  }

  async function handleProbar() {
    setProbando(true);
    setTestResult(null);
    try {
      const result = await probarConexion(deviceId);
      setTestResult(result);
      loadDevice();
    } catch (err) {
      setTestResult({ ok: false, error: err.message });
    } finally {
      setProbando(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    setSyncResult(null);
    try {
      const result = await syncZkAttendanceToDb({ limit: 5000 });
      setSyncResult(result);
      loadDevice();
    } catch (err) {
      setSyncResult({ ok: false, error: err.message });
    } finally {
      setSyncing(false);
    }
  }

  async function handleConsultarHora() {
    setHoraLoading(true);
    setHoraResult(null);
    try {
      const result = await consultarHora(deviceId);
      setHoraResult(result);
    } catch (err) {
      setHoraResult({ ok: false, error: err.message });
    } finally {
      setHoraLoading(false);
    }
  }

  async function handleSincronizarHora(forzar = false) {
    setHoraSyncing(true);
    setHoraResult(null);
    try {
      const result = await sincronizarHora(deviceId, forzar);
      setHoraResult(result);
      loadDevice();
    } catch (err) {
      setHoraResult({ ok: false, error: err.message });
    } finally {
      setHoraSyncing(false);
    }
  }

  function openEdit() {
    setEditData({
      nombre: device.nombre || "",
      ubicacion: device.ubicacion || "",
      descripcion: device.descripcion || "",
      activo: device.activo,
    });
    setEditError("");
    setShowEdit(true);
  }

  async function handleSaveEdit(e) {
    e.preventDefault();
    setEditLoading(true);
    setEditError("");
    try {
      await actualizarDispositivo(deviceId, editData);
      setShowEdit(false);
      loadDevice();
    } catch (err) {
      setEditError(err.message);
    } finally {
      setEditLoading(false);
    }
  }

  if (loading) return <div className="page-stack"><div className="panel-card"><div className="empty-state"><p>Cargando...</p></div></div></div>;
  if (error) return <div className="page-stack"><div className="panel-card"><div className="empty-state"><p>{error}</p></div></div></div>;
  if (!device) return null;

  return (
    <div className="page-stack">
      <PageHeader title={device.nombre} description={`${device.ip}:${device.puerto} — ${device.ubicacion || "Sin ubicación"}`}>
        <div className="header-actions">
          <Link className="secondary-button link-button" to="/devices"><ArrowLeft size={17} /> Volver</Link>
          <button className="secondary-button" type="button" onClick={openEdit}><Edit size={17} /> Editar</button>
          <button className="secondary-button" type="button" onClick={handleProbar} disabled={probando}>
            {probando ? <Loader size={17} /> : <Wifi size={17} />}
            {probando ? "Probando..." : "Probar conexión"}
          </button>
          <button className="primary-button" type="button" onClick={handleSync} disabled={syncing}>
            {syncing ? <Loader size={17} /> : <RefreshCcw size={17} />}
            {syncing ? "Sincronizando..." : "Sincronizar"}
          </button>
        </div>
      </PageHeader>

      {/* Resumen */}
      <section className="panel-card">
        <div className="panel-header">
          <div><h3>Estado del dispositivo</h3></div>
          <span className={getStatusClass(device.estado_conexion)}>{getStatusLabel(device.estado_conexion)}</span>
        </div>
        <div className="report-info-grid">
          <div><span>Código</span><strong>{device.codigo}</strong></div>
          <div><span>IP</span><strong>{device.ip}</strong></div>
          <div><span>Puerto</span><strong>{device.puerto}</strong></div>
          <div><span>Activo</span><strong>{device.activo ? "Sí" : "No"}</strong></div>
          <div><span>Modelo</span><strong>{device.modelo || "—"}</strong></div>
          <div><span>Firmware</span><strong>{device.firmware || "—"}</strong></div>
          <div><span>Número de serie</span><strong>{device.numero_serie || "—"}</strong></div>
          <div><span>Ubicación</span><strong>{device.ubicacion || "—"}</strong></div>
          <div><span>Última conexión</span><strong>{formatDateTime(device.ultima_conexion)}</strong></div>
          <div><span>Última comprobación</span><strong>{formatDateTime(device.ultima_comprobacion)}</strong></div>
          <div><span>Última sincronización</span><strong>{formatDateTime(device.ultima_sincronizacion)}</strong></div>
          <div><span>Último error</span><strong>{device.ultimo_error || "Ninguno"}</strong></div>
        </div>
      </section>

      {/* Resultado prueba de conexión */}
      {testResult && (
        <section className="panel-card">
          <div className="panel-header">
            <div><h3>Resultado de prueba de conexión</h3></div>
            <Wifi size={22} />
          </div>
          {testResult.ok ? (
            <div className="report-info-grid">
              <div><span>Estado</span><strong className="badge success">Conectado</strong></div>
              <div><span>Firmware</span><strong>{testResult.firmware || "—"}</strong></div>
              <div><span>Nº serie</span><strong>{testResult.numero_serie || "—"}</strong></div>
              <div><span>Plataforma</span><strong>{testResult.plataforma || "—"}</strong></div>
              <div><span>Usuarios en reloj</span><strong>{testResult.total_usuarios}</strong></div>
              <div><span>Hora dispositivo</span><strong>{testResult.hora_dispositivo || "—"}</strong></div>
              <div><span>Desfase</span><strong>{testResult.desfase_segundos != null ? `${testResult.desfase_segundos}s` : "—"}</strong></div>
              <div><span>Latencia</span><strong>{testResult.duracion_ms}ms</strong></div>
            </div>
          ) : (
            <div className="form-error-message">
              Error de conexión: {testResult.error}
            </div>
          )}
        </section>
      )}

      {/* Resultado sincronización */}
      {syncResult && (
        <section className="panel-card">
          <div className="panel-header">
            <div><h3>Resultado de sincronización</h3></div>
            <RefreshCcw size={22} />
          </div>
          {syncResult.ok ? (
            <div className="report-info-grid">
              <div><span>Estado</span><strong className="badge success">Exitosa</strong></div>
              <div><span>Sync Run</span><strong>{syncResult.sync_run_id}</strong></div>
              <div><span>Total leídas</span><strong>{syncResult.result?.total_leidas ?? "—"}</strong></div>
              <div><span>Nuevas</span><strong>{syncResult.result?.insertadas ?? "—"}</strong></div>
              <div><span>Duplicadas</span><strong>{syncResult.result?.duplicadas ?? "—"}</strong></div>
            </div>
          ) : (
            <div className="form-error-message">
              Error: {syncResult.error || "Error desconocido"}
            </div>
          )}
        </section>
      )}

      {/* Sección de hora del dispositivo */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Hora del dispositivo</h3>
                <p>
                  {device.ultimo_resultado_hora === "HORA_OK" || device.ultimo_resultado_hora === "SINCRONIZADA"
                    ? "Hora sincronizada correctamente."
                    : device.ultimo_desfase_segundos != null
                      ? `Desfase detectado: ${device.ultimo_desfase_segundos > 0 ? "+" : ""}${device.ultimo_desfase_segundos} segundos`
                      : "Sin verificar."
                  }
                </p>
              </div>
              <Clock size={22} />
            </div>

            <div className="report-info-grid">
              <div><span>Última sincronización hora</span><strong>{formatDateTime(device.ultima_sincronizacion_hora)}</strong></div>
              <div><span>Último desfase</span><strong>{device.ultimo_desfase_segundos != null ? `${device.ultimo_desfase_segundos}s` : "—"}</strong></div>
              <div><span>Estado</span><strong>{device.ultimo_resultado_hora || "Sin verificar"}</strong></div>
              {device.ultimo_error_hora && <div><span>Último error</span><strong>{device.ultimo_error_hora}</strong></div>}
            </div>

            <div className="modal-footer" style={{ borderTop: "none", paddingTop: "12px" }}>
              <button className="secondary-button" type="button" onClick={handleConsultarHora} disabled={horaLoading}>
                {horaLoading ? <Loader size={17} /> : <Clock size={17} />}
                {horaLoading ? "Revisando..." : "Revisar hora"}
              </button>
              <button className="primary-button" type="button" onClick={() => handleSincronizarHora(true)} disabled={horaSyncing}>
                {horaSyncing ? <Loader size={17} /> : <RefreshCcw size={17} />}
                {horaSyncing ? "Sincronizando..." : "Sincronizar ahora"}
              </button>
            </div>

            {horaResult && (
              <div style={{ marginTop: "12px" }}>
                {horaResult.ok ? (
                  <div className="report-info-grid">
                    {horaResult.hora_dispositivo && <div><span>Hora dispositivo</span><strong>{horaResult.hora_dispositivo}</strong></div>}
                    {horaResult.hora_servidor && <div><span>Hora servidor</span><strong>{horaResult.hora_servidor}</strong></div>}
                    {horaResult.desfase_antes_segundos != null && <div><span>Desfase antes</span><strong>{horaResult.desfase_antes_segundos}s</strong></div>}
                    {horaResult.desfase_despues_segundos != null && <div><span>Desfase después</span><strong>{horaResult.desfase_despues_segundos}s</strong></div>}
                    {horaResult.desfase_segundos != null && <div><span>Desfase</span><strong>{horaResult.desfase_segundos}s</strong></div>}
                    {horaResult.sincronizada != null && <div><span>Sincronizada</span><strong>{horaResult.sincronizada ? "Sí" : "No (dentro de tolerancia)"}</strong></div>}
                    {horaResult.motivo && <div><span>Motivo</span><strong>{horaResult.motivo}</strong></div>}
                  </div>
                ) : (
                  <div className="form-error-message">Error: {horaResult.error}</div>
                )}
              </div>
            )}
          </section>

      {/* Modal editar */}
      {showEdit && (
        <div className="modal-overlay" onClick={() => setShowEdit(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Editar dispositivo</h3>
              <button className="modal-close" type="button" onClick={() => setShowEdit(false)}><X size={20} /></button>
            </div>
            <form className="modal-body" onSubmit={handleSaveEdit}>
              {editError && <div className="form-error-message">{editError}</div>}
              <div className="form-field">
                <label>Nombre</label>
                <input type="text" value={editData.nombre} onChange={(e) => setEditData({...editData, nombre: e.target.value})} />
              </div>
              <div className="form-field">
                <label>Ubicación</label>
                <input type="text" value={editData.ubicacion} onChange={(e) => setEditData({...editData, ubicacion: e.target.value})} />
              </div>
              <div className="form-field">
                <label>Descripción</label>
                <input type="text" value={editData.descripcion} onChange={(e) => setEditData({...editData, descripcion: e.target.value})} />
              </div>
              <div className="form-field form-checkbox">
                <label>
                  <input type="checkbox" checked={editData.activo} onChange={(e) => setEditData({...editData, activo: e.target.checked})} />
                  Dispositivo activo
                </label>
              </div>
              <div className="modal-footer">
                <button className="secondary-button" type="button" onClick={() => setShowEdit(false)}>Cancelar</button>
                <button className="primary-button" type="submit" disabled={editLoading}>
                  {editLoading ? "Guardando..." : <><Check size={17} /> Guardar</>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default DeviceDetailPage;
