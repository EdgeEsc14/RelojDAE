import { Fragment, useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileSearch,
  Loader,
  LockKeyhole,
  Search,
  ShieldAlert,
  XCircle,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { auditoriaApi } from "../../api/auditoriaApi";

const OPERACIONES = ["INSERT", "UPDATE", "DELETE"];
const RESULTADOS_LOGIN = [
  "EXITOSO",
  "FALLIDO",
  "BLOQUEADO",
  "PENDIENTE_VERIFICACION",
  "PENDIENTE_APROBACION",
  "USUARIO_INACTIVO",
  "ERROR",
];
const LIMITE_PAGINA = 20;

function getDefaultDates() {
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  return {
    inicio: firstDay.toISOString().split("T")[0],
    fin: today.toISOString().split("T")[0],
  };
}

function formatDateTime(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("es-MX", {
      dateStyle: "short",
      timeStyle: "medium",
    }).format(new Date(value));
  } catch {
    return String(value);
  }
}

function getOperacionClass(operacion) {
  if (operacion === "INSERT") return "badge success";
  if (operacion === "UPDATE") return "badge warning";
  if (operacion === "DELETE") return "badge danger";
  return "badge neutral";
}

function getResultadoClass(resultado) {
  if (resultado === "EXITOSO") return "badge success";
  if (resultado === "FALLIDO" || resultado === "ERROR") return "badge danger";
  if (resultado === "BLOQUEADO") return "badge danger";
  return "badge warning";
}

function AuditPage() {
  const defaults = getDefaultDates();

  const [fechaInicio, setFechaInicio] = useState(defaults.inicio);
  const [fechaFin, setFechaFin] = useState(defaults.fin);

  const [resumen, setResumen] = useState(null);
  const [resumenError, setResumenError] = useState("");

  const [filtrosDisponibles, setFiltrosDisponibles] = useState({ esquemas: [], tablas: [] });

  const [bitacoraEsquema, setBitacoraEsquema] = useState("");
  const [bitacoraTabla, setBitacoraTabla] = useState("");
  const [bitacoraOperacion, setBitacoraOperacion] = useState("");
  const [bitacoraQ, setBitacoraQ] = useState("");
  const [bitacoraOffset, setBitacoraOffset] = useState(0);
  const [bitacora, setBitacora] = useState({ total: 0, items: [] });
  const [bitacoraLoading, setBitacoraLoading] = useState(false);
  const [bitacoraError, setBitacoraError] = useState("");
  const [exportandoBitacora, setExportandoBitacora] = useState(false);

  const [loginResultado, setLoginResultado] = useState("");
  const [loginQ, setLoginQ] = useState("");
  const [loginOffset, setLoginOffset] = useState(0);
  const [login, setLogin] = useState({ total: 0, items: [] });
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [exportandoLogin, setExportandoLogin] = useState(false);

  const [detalleAbiertoId, setDetalleAbiertoId] = useState(null);
  const [detalle, setDetalle] = useState(null);
  const [detalleLoading, setDetalleLoading] = useState(false);

  async function loadResumen() {
    setResumenError("");
    try {
      const data = await auditoriaApi.obtenerResumen({ fecha_inicio: fechaInicio, fecha_fin: fechaFin });
      setResumen(data);
    } catch (err) {
      setResumenError(err.message || "No fue posible cargar el resumen de auditoría.");
    }
  }

  async function loadBitacora() {
    setBitacoraLoading(true);
    setBitacoraError("");
    try {
      const data = await auditoriaApi.listarBitacora({
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        esquema: bitacoraEsquema,
        tabla: bitacoraTabla,
        operacion: bitacoraOperacion,
        q: bitacoraQ,
        limit: LIMITE_PAGINA,
        offset: bitacoraOffset,
      });
      setBitacora(data);
    } catch (err) {
      setBitacoraError(err.message || "No fue posible cargar la bitácora.");
      setBitacora({ total: 0, items: [] });
    } finally {
      setBitacoraLoading(false);
    }
  }

  async function loadLogin() {
    setLoginLoading(true);
    setLoginError("");
    try {
      const data = await auditoriaApi.listarLogin({
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        resultado: loginResultado,
        q: loginQ,
        limit: LIMITE_PAGINA,
        offset: loginOffset,
      });
      setLogin(data);
    } catch (err) {
      setLoginError(err.message || "No fue posible cargar los accesos.");
      setLogin({ total: 0, items: [] });
    } finally {
      setLoginLoading(false);
    }
  }

  useEffect(() => {
    auditoriaApi
      .obtenerFiltrosBitacora()
      .then(setFiltrosDisponibles)
      .catch(() => setFiltrosDisponibles({ esquemas: [], tablas: [] }));
  }, []);

  useEffect(() => {
    loadResumen();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fechaInicio, fechaFin]);

  useEffect(() => {
    loadBitacora();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fechaInicio, fechaFin, bitacoraEsquema, bitacoraTabla, bitacoraOperacion, bitacoraOffset]);

  useEffect(() => {
    loadLogin();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fechaInicio, fechaFin, loginResultado, loginOffset]);

  function handleBuscarBitacora(event) {
    event.preventDefault();
    setBitacoraOffset(0);
    loadBitacora();
  }

  function handleBuscarLogin(event) {
    event.preventDefault();
    setLoginOffset(0);
    loadLogin();
  }

  async function handleVerDetalle(id) {
    if (detalleAbiertoId === id) {
      setDetalleAbiertoId(null);
      setDetalle(null);
      return;
    }

    setDetalleAbiertoId(id);
    setDetalle(null);
    setDetalleLoading(true);
    try {
      const data = await auditoriaApi.obtenerDetalleBitacora(id);
      setDetalle(data);
    } catch (err) {
      setDetalle({ error: err.message || "No fue posible cargar el detalle." });
    } finally {
      setDetalleLoading(false);
    }
  }

  async function handleExportBitacora() {
    setExportandoBitacora(true);
    try {
      await auditoriaApi.descargarBitacoraCSV({
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        esquema: bitacoraEsquema,
        tabla: bitacoraTabla,
        operacion: bitacoraOperacion,
        q: bitacoraQ,
      });
    } catch (err) {
      alert("Error al exportar bitácora: " + err.message);
    } finally {
      setExportandoBitacora(false);
    }
  }

  async function handleExportLogin() {
    setExportandoLogin(true);
    try {
      await auditoriaApi.descargarLoginCSV({
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        resultado: loginResultado,
        q: loginQ,
      });
    } catch (err) {
      alert("Error al exportar accesos: " + err.message);
    } finally {
      setExportandoLogin(false);
    }
  }

  const bitacoraPaginaActual = Math.floor(bitacoraOffset / LIMITE_PAGINA) + 1;
  const bitacoraTotalPaginas = Math.max(1, Math.ceil(bitacora.total / LIMITE_PAGINA));
  const loginPaginaActual = Math.floor(loginOffset / LIMITE_PAGINA) + 1;
  const loginTotalPaginas = Math.max(1, Math.ceil(login.total / LIMITE_PAGINA));

  return (
    <div className="page-stack">
      <PageHeader
        title="Auditoría"
        description="Bitácora real de cambios (auditoria.bitacora) y accesos (seguridad.login_auditoria)."
      >
        <div className="header-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={handleExportBitacora}
            disabled={exportandoBitacora}
          >
            <Download size={17} />
            {exportandoBitacora ? "Exportando..." : "Exportar bitácora CSV"}
          </button>

          <button
            className="secondary-button"
            type="button"
            onClick={handleExportLogin}
            disabled={exportandoLogin}
          >
            <Download size={17} />
            {exportandoLogin ? "Exportando..." : "Exportar accesos CSV"}
          </button>
        </div>
      </PageHeader>

      {/* Rango de fechas (aplica a resumen, bitácora y accesos) */}
      <section className="panel-card">
        <div className="filters-row">
          <div className="filter-field">
            <label htmlFor="aud-fecha-inicio">Desde</label>
            <input
              id="aud-fecha-inicio"
              type="date"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
            />
          </div>
          <div className="filter-field">
            <label htmlFor="aud-fecha-fin">Hasta</label>
            <input
              id="aud-fecha-fin"
              type="date"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
            />
          </div>
        </div>
      </section>

      {resumenError && (
        <section className="panel-card">
          <div className="empty-state">
            <AlertTriangle size={32} />
            <p>{resumenError}</p>
          </div>
        </section>
      )}

      {resumen && (
        <section className="metrics-grid four-columns">
          <article className="metric-card">
            <div className="metric-icon"><ShieldAlert size={22} /></div>
            <div>
              <p>Cambios en bitácora</p>
              <strong>{resumen.bitacora.total}</strong>
              <span>{resumen.bitacora.inserts} altas, {resumen.bitacora.updates} modif., {resumen.bitacora.deletes} bajas</span>
            </div>
          </article>
          <article className="metric-card">
            <div className="metric-icon"><LockKeyhole size={22} /></div>
            <div>
              <p>Cambios en seguridad</p>
              <strong>{resumen.bitacora.cambios_seguridad}</strong>
              <span>Usuarios, roles y permisos</span>
            </div>
          </article>
          <article className="metric-card">
            <div className="metric-icon"><CheckCircle2 size={22} /></div>
            <div>
              <p>Accesos exitosos</p>
              <strong>{resumen.login.exitosos}</strong>
              <span>de {resumen.login.total} intentos</span>
            </div>
          </article>
          <article className="metric-card">
            <div className="metric-icon"><XCircle size={22} /></div>
            <div>
              <p>Accesos fallidos/bloqueados</p>
              <strong>{resumen.login.fallidos + resumen.login.bloqueados}</strong>
              <span>{resumen.login.bloqueados} bloqueados</span>
            </div>
          </article>
        </section>
      )}

      <section className="warning-banner">
        <LockKeyhole size={22} />
        <div>
          <strong>Registro de auditoría no editable</strong>
          <p>
            auditoria.bitacora se llena únicamente por triggers de PostgreSQL sobre
            INSERT/UPDATE/DELETE; no existe ningún endpoint que permita crear, editar
            o eliminar eventos desde esta pantalla.
          </p>
        </div>
      </section>

      {/* Bitácora de cambios */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Bitácora de cambios</h3>
            <p>Cada fila es un INSERT/UPDATE/DELETE real capturado automáticamente.</p>
          </div>
        </div>

        <form className="filters-row" onSubmit={handleBuscarBitacora}>
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por usuario, tabla, registro, módulo..."
              value={bitacoraQ}
              onChange={(e) => setBitacoraQ(e.target.value)}
            />
          </div>

          <select value={bitacoraEsquema} onChange={(e) => { setBitacoraEsquema(e.target.value); setBitacoraOffset(0); }}>
            <option value="">Todos los esquemas</option>
            {filtrosDisponibles.esquemas.map((esq) => (
              <option key={esq} value={esq}>{esq}</option>
            ))}
          </select>

          <select value={bitacoraTabla} onChange={(e) => { setBitacoraTabla(e.target.value); setBitacoraOffset(0); }}>
            <option value="">Todas las tablas</option>
            {filtrosDisponibles.tablas.map((tbl) => (
              <option key={tbl} value={tbl}>{tbl}</option>
            ))}
          </select>

          <select value={bitacoraOperacion} onChange={(e) => { setBitacoraOperacion(e.target.value); setBitacoraOffset(0); }}>
            <option value="">Todas las operaciones</option>
            {OPERACIONES.map((op) => (
              <option key={op} value={op}>{op}</option>
            ))}
          </select>

          <button className="secondary-button" type="submit">
            {bitacoraLoading ? <Loader size={17} /> : <Search size={17} />}
            Buscar
          </button>
        </form>

        {bitacoraError && (
          <div className="empty-state">
            <AlertTriangle size={32} />
            <p>{bitacoraError}</p>
          </div>
        )}

        {!bitacoraError && bitacora.items.length === 0 && !bitacoraLoading && (
          <div className="empty-state">
            <p>Sin eventos de bitácora para los filtros seleccionados.</p>
          </div>
        )}

        {bitacora.items.length > 0 && (
          <div className="simple-table desktop-table">
            <table>
              <thead>
                <tr>
                  <th>Fecha/hora</th>
                  <th>Objeto</th>
                  <th>Operación</th>
                  <th>Registro</th>
                  <th>Usuario</th>
                  <th>Cambios</th>
                  <th>Detalle</th>
                </tr>
              </thead>
              <tbody>
                {bitacora.items.map((evento) => (
                  <Fragment key={evento.id}>
                    <tr>
                      <td>{formatDateTime(evento.fecha_evento)}</td>
                      <td><strong>{evento.objeto}</strong></td>
                      <td><span className={getOperacionClass(evento.operacion)}>{evento.operacion}</span></td>
                      <td>{evento.registro_id || "—"}</td>
                      <td>{evento.usuario_app_correo || "Sistema"}</td>
                      <td>{evento.cambios ? Object.keys(evento.cambios).length : "—"}</td>
                      <td>
                        <button className="secondary-button" type="button" onClick={() => handleVerDetalle(evento.id)}>
                          <FileSearch size={15} />
                          {detalleAbiertoId === evento.id ? "Ocultar" : "Ver"}
                        </button>
                      </td>
                    </tr>
                    {detalleAbiertoId === evento.id && (
                      <tr>
                        <td colSpan={7}>
                          {detalleLoading && <p>Cargando detalle…</p>}
                          {!detalleLoading && detalle?.error && <p>{detalle.error}</p>}
                          {!detalleLoading && detalle && !detalle.error && (
                            <div style={{ display: "grid", gap: "8px", fontSize: "12px" }}>
                              <div><strong>IP origen:</strong> {detalle.ip_origen || "No disponible"}</div>
                              <div><strong>Módulo:</strong> {detalle.modulo || "No disponible"}</div>
                              <div><strong>Acción:</strong> {detalle.accion_app || "No disponible"}</div>
                              <div>
                                <strong>Datos anteriores:</strong>
                                <pre style={{ whiteSpace: "pre-wrap", background: "var(--color-surface-soft)", padding: "8px", borderRadius: "8px" }}>
                                  {JSON.stringify(detalle.datos_anteriores, null, 2) || "—"}
                                </pre>
                              </div>
                              <div>
                                <strong>Datos nuevos:</strong>
                                <pre style={{ whiteSpace: "pre-wrap", background: "var(--color-surface-soft)", padding: "8px", borderRadius: "8px" }}>
                                  {JSON.stringify(detalle.datos_nuevos, null, 2) || "—"}
                                </pre>
                              </div>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {bitacora.total > LIMITE_PAGINA && (
          <div className="filters-row" style={{ marginTop: "12px", justifyContent: "flex-end" }}>
            <button
              className="secondary-button"
              type="button"
              disabled={bitacoraOffset === 0}
              onClick={() => setBitacoraOffset((prev) => Math.max(0, prev - LIMITE_PAGINA))}
            >
              Anterior
            </button>
            <span>Página {bitacoraPaginaActual} de {bitacoraTotalPaginas}</span>
            <button
              className="secondary-button"
              type="button"
              disabled={bitacoraOffset + LIMITE_PAGINA >= bitacora.total}
              onClick={() => setBitacoraOffset((prev) => prev + LIMITE_PAGINA)}
            >
              Siguiente
            </button>
          </div>
        )}
      </section>

      {/* Accesos (login) */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Accesos al sistema</h3>
            <p>Intentos de inicio de sesión (seguridad.login_auditoria).</p>
          </div>
        </div>

        <form className="filters-row" onSubmit={handleBuscarLogin}>
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por correo, IP o motivo..."
              value={loginQ}
              onChange={(e) => setLoginQ(e.target.value)}
            />
          </div>

          <select value={loginResultado} onChange={(e) => { setLoginResultado(e.target.value); setLoginOffset(0); }}>
            <option value="">Todos los resultados</option>
            {RESULTADOS_LOGIN.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>

          <button className="secondary-button" type="submit">
            {loginLoading ? <Loader size={17} /> : <Search size={17} />}
            Buscar
          </button>
        </form>

        {loginError && (
          <div className="empty-state">
            <AlertTriangle size={32} />
            <p>{loginError}</p>
          </div>
        )}

        {!loginError && login.items.length === 0 && !loginLoading && (
          <div className="empty-state">
            <p>Sin intentos de acceso para los filtros seleccionados.</p>
          </div>
        )}

        {login.items.length > 0 && (
          <div className="simple-table desktop-table">
            <table>
              <thead>
                <tr>
                  <th>Fecha/hora</th>
                  <th>Correo intentado</th>
                  <th>Usuario</th>
                  <th>Rol</th>
                  <th>Resultado</th>
                  <th>Motivo</th>
                  <th>IP</th>
                </tr>
              </thead>
              <tbody>
                {login.items.map((evento) => (
                  <tr key={evento.id}>
                    <td>{formatDateTime(evento.fecha_evento)}</td>
                    <td>{evento.correo_intentado || "—"}</td>
                    <td>{evento.usuario_correo || "—"}</td>
                    <td>{evento.usuario_rol || "—"}</td>
                    <td><span className={getResultadoClass(evento.resultado)}>{evento.resultado}</span></td>
                    <td>{evento.motivo || "—"}</td>
                    <td>{evento.ip_origen_raw || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {login.total > LIMITE_PAGINA && (
          <div className="filters-row" style={{ marginTop: "12px", justifyContent: "flex-end" }}>
            <button
              className="secondary-button"
              type="button"
              disabled={loginOffset === 0}
              onClick={() => setLoginOffset((prev) => Math.max(0, prev - LIMITE_PAGINA))}
            >
              Anterior
            </button>
            <span>Página {loginPaginaActual} de {loginTotalPaginas}</span>
            <button
              className="secondary-button"
              type="button"
              disabled={loginOffset + LIMITE_PAGINA >= login.total}
              onClick={() => setLoginOffset((prev) => prev + LIMITE_PAGINA)}
            >
              Siguiente
            </button>
          </div>
        )}
      </section>

      {/* Controles recomendados (referencia de diseño, no datos en vivo) */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Controles recomendados</h3>
            <p>Reglas mínimas de trazabilidad ya implementadas en el sistema.</p>
          </div>
          <LockKeyhole size={22} />
        </div>

        <div className="audit-control-list">
          <div>
            <span>Checadas crudas</span>
            <strong>Solo lectura; no edición directa</strong>
          </div>
          <div>
            <span>Incidencias</span>
            <strong>Aprobación/rechazo con usuario y fecha</strong>
          </div>
          <div>
            <span>Cambios administrativos</span>
            <strong>Capturados automáticamente en auditoria.bitacora</strong>
          </div>
          <div>
            <span>Accesos</span>
            <strong>Registrados en seguridad.login_auditoria por cada intento</strong>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AuditPage;
