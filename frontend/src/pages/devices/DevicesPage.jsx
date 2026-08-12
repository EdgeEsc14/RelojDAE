import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import ZkUsersPanel from "../../components/devices/ZkUsersPanel";
import ZkReconciliationPanel from "../../components/devices/ZkReconciliationPanel";

import {
  Check,
  Clock,
  Eye,
  Fingerprint,
  Loader,
  Plus,
  RefreshCcw,
  Search,
  Server,
  Wifi,
  WifiOff,
  X,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  getDispositivos,
  crearDispositivo,
  probarConexion,
  probarConexionLibre,
  sincronizarHora,
} from "../../api/dispositivosApi";

function getStatusClass(estado) {
  if (estado === "CONECTADO") return "badge success";
  if (estado === "ERROR") return "badge danger";
  if (estado === "DESHABILITADO") return "badge neutral";
  return "badge warning";
}

function getStatusLabel(estado) {
  const labels = {
    CONECTADO: "Conectado",
    DESCONECTADO: "Desconectado",
    ERROR: "Error",
    DESHABILITADO: "Deshabilitado",
  };
  return labels[estado] || estado || "Desconocido";
}

function formatDateTime(value) {
  if (!value) return "Nunca";
  try {
    return new Date(value).toLocaleString("es-MX", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch { return value; }
}

function DevicesPage() {
  const [dispositivos, setDispositivos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [probando, setProbando] = useState(null);

  // Modal crear
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ nombre: "", ip: "", puerto: 4370, password_comunicacion: 0, ubicacion: "", codigo: "" });
  const [formError, setFormError] = useState("");
  const [formLoading, setFormLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => { loadDispositivos(); }, []);

  async function loadDispositivos() {
    setLoading(true);
    setError("");
    try {
      const data = await getDispositivos();
      setDispositivos(data || []);
    } catch (err) {
      setError(err.message || "Error al cargar dispositivos.");
    } finally {
      setLoading(false);
    }
  }

  async function handleProbarConexion(id) {
    setProbando(id);
    try {
      await probarConexion(id);
      loadDispositivos();
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setProbando(null);
    }
  }

  async function handleSyncHora(id) {
    try {
      await sincronizarHora(id, true);
      loadDispositivos();
    } catch (err) {
      alert("Error sync hora: " + err.message);
    }
  }

  async function handleTestBeforeSave() {
    setTestResult(null);
    try {
      const result = await probarConexionLibre({
        ip: formData.ip,
        puerto: Number(formData.puerto),
        password_comunicacion: Number(formData.password_comunicacion),
      });
      setTestResult(result);
    } catch (err) {
      setTestResult({ ok: false, error: err.message });
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    setFormError("");
    setFormLoading(true);
    try {
      if (!formData.nombre) { setFormError("Nombre obligatorio."); setFormLoading(false); return; }
      if (!formData.ip) { setFormError("IP obligatoria."); setFormLoading(false); return; }
      await crearDispositivo({
        ...formData,
        puerto: Number(formData.puerto),
        password_comunicacion: Number(formData.password_comunicacion),
      });
      setShowModal(false);
      setTestResult(null);
      loadDispositivos();
    } catch (err) {
      setFormError(err.message || "Error al crear.");
    } finally {
      setFormLoading(false);
    }
  }

  const connected = dispositivos.filter((d) => d.estado_conexion === "CONECTADO").length;
  const withIssues = dispositivos.filter((d) => d.estado_conexion === "ERROR" || d.estado_conexion === "DESCONECTADO").length;

  return (
    <div className="page-stack">
      <PageHeader
        title="Dispositivos ZKTeco"
        description="Administración de relojes checadores, conexión, sincronización y estado operativo."
      >
        <div className="header-actions">
          <button className="primary-button" type="button" onClick={() => setShowModal(true)}>
            <Plus size={17} />
            Agregar dispositivo
          </button>
        </div>
      </PageHeader>

      {/* Métricas */}
      <section className="metrics-grid three-columns">
        <article className="metric-card">
          <div className="metric-icon"><Server size={22} /></div>
          <div>
            <p>Dispositivos</p>
            <strong>{dispositivos.length}</strong>
            <span>Registrados</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon"><Wifi size={22} /></div>
          <div>
            <p>Conectados</p>
            <strong>{connected}</strong>
            <span>Responden correctamente</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon"><WifiOff size={22} /></div>
          <div>
            <p>Con problema</p>
            <strong>{withIssues}</strong>
            <span>Requieren revisión</span>
          </div>
        </article>
      </section>

      {error && <div className="panel-card"><div className="empty-state"><p>{error}</p></div></div>}
      {loading && <div className="panel-card"><div className="empty-state"><p>Cargando dispositivos...</p></div></div>}

      {/* Tarjetas de dispositivos */}
      {!loading && dispositivos.length > 0 && (
        <section className="panel-card">
          <div className="device-card-grid">
            {dispositivos.map((device) => (
              <article className="device-card" key={device.id}>
                <div className="device-card-header">
                  <div className="device-card-icon"><Fingerprint size={26} /></div>
                  <div>
                    <h3>{device.nombre}</h3>
                    <p>{device.ubicacion || "Sin ubicación"}</p>
                  </div>
                  <span className={getStatusClass(device.estado_conexion)}>
                    {getStatusLabel(device.estado_conexion)}
                  </span>
                </div>

                <div className="device-info-grid">
                  <div><span>IP</span><strong>{device.ip}</strong></div>
                  <div><span>Puerto</span><strong>{device.puerto}</strong></div>
                  <div><span>Modelo</span><strong>{device.modelo || "—"}</strong></div>
                  <div><span>Firmware</span><strong>{device.firmware || "—"}</strong></div>
                  <div><span>Serie</span><strong>{device.numero_serie || "—"}</strong></div>
                  <div><span>Activo</span><strong>{device.activo ? "Sí" : "No"}</strong></div>
                </div>

                <div className="device-card-footer">
                  <div>
                    <span>Última conexión</span>
                    <strong>{formatDateTime(device.ultima_conexion)}</strong>
                  </div>
                  <div>
                    <span>Hora</span>
                    <strong>{
                      device.ultimo_resultado_hora === "HORA_OK" || device.ultimo_resultado_hora === "SINCRONIZADA"
                        ? "Sincronizada"
                        : device.ultimo_desfase_segundos != null
                          ? `Desfase ${device.ultimo_desfase_segundos > 0 ? "+" : ""}${device.ultimo_desfase_segundos}s`
                          : "Sin verificar"
                    }</strong>
                  </div>
                  <div className="table-actions-group">
                    <button
                      className="secondary-button"
                      type="button"
                      disabled={probando === device.id}
                      onClick={() => handleProbarConexion(device.id)}
                    >
                      {probando === device.id ? <Loader size={14} /> : <Wifi size={14} />}
                    </button>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => handleSyncHora(device.id)}
                      title="Sincronizar hora"
                    >
                      <Clock size={14} />
                    </button>
                    <Link className="primary-button link-button" to={`/devices/${device.id}`}>
                      <Eye size={14} /> Detalle
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {!loading && dispositivos.length === 0 && !error && (
        <div className="panel-card"><div className="empty-state"><p>No hay dispositivos registrados.</p></div></div>
      )}

      {/* Paneles funcionales existentes */}
      <ZkUsersPanel />
      <ZkReconciliationPanel />

      {/* Modal crear dispositivo */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Agregar dispositivo</h3>
              <button className="modal-close" type="button" onClick={() => setShowModal(false)}><X size={20} /></button>
            </div>
            <form className="modal-body" onSubmit={handleCreate}>
              {formError && <div className="form-error-message">{formError}</div>}

              <div className="form-field">
                <label>Nombre *</label>
                <input type="text" required placeholder="Ej: Reloj acceso principal" value={formData.nombre} onChange={(e) => setFormData({...formData, nombre: e.target.value})} />
              </div>
              <div className="form-field">
                <label>IP *</label>
                <input type="text" required placeholder="10.254.26.251" value={formData.ip} onChange={(e) => setFormData({...formData, ip: e.target.value})} />
              </div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"12px"}}>
                <div className="form-field">
                  <label>Puerto</label>
                  <input type="number" value={formData.puerto} onChange={(e) => setFormData({...formData, puerto: e.target.value})} />
                </div>
                <div className="form-field">
                  <label>Comm Key</label>
                  <input type="number" value={formData.password_comunicacion} onChange={(e) => setFormData({...formData, password_comunicacion: e.target.value})} />
                </div>
              </div>
              <div className="form-field">
                <label>Ubicación</label>
                <input type="text" placeholder="Ej: Entrada principal" value={formData.ubicacion} onChange={(e) => setFormData({...formData, ubicacion: e.target.value})} />
              </div>
              <div className="form-field">
                <label>Código (opcional)</label>
                <input type="text" placeholder="Se genera automáticamente" value={formData.codigo} onChange={(e) => setFormData({...formData, codigo: e.target.value})} />
              </div>

              <button className="secondary-button" type="button" onClick={handleTestBeforeSave} style={{width:"100%"}}>
                <Wifi size={17} /> Probar conexión antes de guardar
              </button>

              {testResult && (
                <div className={testResult.ok ? "form-error-message" : "form-error-message"} style={testResult.ok ? {background:"#f0fdf4",borderColor:"#86efac",color:"#166534"} : {}}>
                  {testResult.ok
                    ? `Conexión exitosa — Firmware: ${testResult.firmware || "N/D"}, Usuarios: ${testResult.total_usuarios}, Serie: ${testResult.numero_serie || "N/D"}`
                    : `Error: ${testResult.error}`
                  }
                </div>
              )}

              <div className="modal-footer">
                <button className="secondary-button" type="button" onClick={() => setShowModal(false)}>Cancelar</button>
                <button className="primary-button" type="submit" disabled={formLoading}>
                  {formLoading ? "Guardando..." : <><Check size={17} /> Guardar dispositivo</>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default DevicesPage;
