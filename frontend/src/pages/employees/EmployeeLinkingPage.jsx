import { useEffect, useState } from "react";

import {
  AlertTriangle,
  Check,
  Link2,
  Link2Off,
  RefreshCw,
  Search,
  UserCheck,
  Users,
  X,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { getZkEmployeeReconciliation, linkEmployeeWithZkUser, unlinkEmployeeFromZkUser } from "../../api/zkApi";

function safeText(value, fallback = "—") {
  return String(value ?? "").trim() || fallback;
}

function EmployeeLinkingPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState("all"); // all | linked | unlinked | conflicts

  // Modal para vincular
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [linkTarget, setLinkTarget] = useState(null);
  const [linkZkUserId, setLinkZkUserId] = useState("");
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkError, setLinkError] = useState("");

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const result = await getZkEmployeeReconciliation();
      setData(result);
    } catch (err) {
      // Si falla la conciliación (reloj no responde), intentar cargar al menos los empleados
      setError(
        (err.message || "Error al conectar con el reloj.") +
        " Verifica que el reloj esté encendido y conectado. Si el problema persiste, reinicia el backend."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleUnlink(codigoEmpleado) {
    if (!confirm(`¿Desvincular empleado ${codigoEmpleado} de su usuario ZKTeco?`)) return;
    try {
      await unlinkEmployeeFromZkUser(codigoEmpleado);
      await loadData();
    } catch (err) {
      alert("Error al desvincular: " + err.message);
    }
  }

  function openLinkModal(employee) {
    setLinkTarget(employee);
    setLinkZkUserId("");
    setLinkError("");
    setShowLinkModal(true);
  }

  async function handleLink(e) {
    e.preventDefault();
    if (!linkZkUserId.trim()) {
      setLinkError("Ingresa un User ID ZKTeco.");
      return;
    }
    setLinkLoading(true);
    setLinkError("");
    try {
      await linkEmployeeWithZkUser({
        codigoEmpleado: linkTarget.codigo_empleado,
        zkUserId: linkZkUserId.trim(),
      });
      setShowLinkModal(false);
      await loadData();
    } catch (err) {
      setLinkError(err.message || "Error al vincular.");
    } finally {
      setLinkLoading(false);
    }
  }

  // Filtrado
  const matched = data?.matched || [];
  const unlinked = data?.employees_without_zk_user || [];
  const zkWithoutEmployee = data?.zk_users_without_employee || [];
  const conflicts = data?.conflicts || [];
  const summary = data?.summary || {};

  const term = searchTerm.trim().toLowerCase();

  const filteredMatched = matched.filter((item) => {
    if (!term) return true;
    const emp = item.employee;
    const zk = item.zk_user;
    return (
      (emp.nombre_completo || "").toLowerCase().includes(term) ||
      (emp.codigo_empleado || "").toLowerCase().includes(term) ||
      (emp.zk_user_id || "").includes(term) ||
      (zk?.name || "").toLowerCase().includes(term) ||
      (zk?.user_id || "").includes(term)
    );
  });

  const filteredUnlinked = unlinked.filter((item) => {
    if (!term) return true;
    const emp = item.employee;
    return (
      (emp.nombre_completo || "").toLowerCase().includes(term) ||
      (emp.codigo_empleado || "").toLowerCase().includes(term)
    );
  });

  const filteredZkWithout = zkWithoutEmployee.filter((item) => {
    if (!term) return true;
    const zk = item.zk_user;
    return (
      (zk?.name || "").toLowerCase().includes(term) ||
      (zk?.user_id || "").includes(term)
    );
  });

  return (
    <div className="page-stack">
      <PageHeader
        title="Vinculación Reloj"
        description="Estado de vinculación entre empleados en base de datos y usuarios registrados en el reloj ZKTeco."
      >
        <button
          className="primary-button"
          type="button"
          onClick={loadData}
          disabled={loading}
        >
          <RefreshCw size={17} />
          {loading ? "Consultando..." : "Actualizar"}
        </button>
      </PageHeader>

      {/* Métricas */}
      {data && (
        <section className="metrics-grid four-columns">
          <article className="metric-card">
            <div className="metric-icon" style={{ color: "#10b981" }}><UserCheck size={22} /></div>
            <div>
              <p>Vinculados</p>
              <strong>{summary.matched || 0}</strong>
              <span>Empleado + Reloj OK</span>
            </div>
          </article>
          <article className="metric-card">
            <div className="metric-icon" style={{ color: "#ef4444" }}><Link2Off size={22} /></div>
            <div>
              <p>Sin vincular</p>
              <strong>{summary.employees_without_zk_user || 0}</strong>
              <span>Empleados sin reloj</span>
            </div>
          </article>
          <article className="metric-card">
            <div className="metric-icon" style={{ color: "#f59e0b" }}><AlertTriangle size={22} /></div>
            <div>
              <p>Huérfanos en reloj</p>
              <strong>{summary.zk_users_without_employee || 0}</strong>
              <span>En reloj sin empleado</span>
            </div>
          </article>
          <article className="metric-card">
            <div className="metric-icon" style={{ color: "#8b5cf6" }}><AlertTriangle size={22} /></div>
            <div>
              <p>Conflictos</p>
              <strong>{summary.conflicts || 0}</strong>
              <span>Duplicados o errores</span>
            </div>
          </article>
        </section>
      )}

      {error && (
        <section className="panel-card">
          <div className="empty-state">
            <AlertTriangle size={32} />
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        </section>
      )}

      {loading && !data && (
        <section className="panel-card">
          <div className="empty-state">
            <RefreshCw size={32} />
            <p>Consultando reloj y base de datos...</p>
          </div>
        </section>
      )}

      {data && (
        <section className="panel-card">
          {/* Filtros */}
          <div className="filters-row">
            <div className="filter-search">
              <Search size={18} />
              <input
                type="text"
                placeholder="Buscar por nombre, código o User ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{ minHeight: "42px", borderRadius: "12px", border: "1px solid var(--color-border)", padding: "0 12px", minWidth: "180px" }}
            >
              <option value="all">Todos</option>
              <option value="linked">Vinculados ({matched.length})</option>
              <option value="unlinked">Sin vincular ({unlinked.length})</option>
              <option value="orphan">Huérfanos reloj ({zkWithoutEmployee.length})</option>
              {conflicts.length > 0 && <option value="conflicts">Conflictos ({conflicts.length})</option>}
            </select>
          </div>

          {/* Tabla de vinculados */}
          {(filter === "all" || filter === "linked") && filteredMatched.length > 0 && (
            <>
              <div className="panel-header" style={{ marginTop: "16px" }}>
                <div>
                  <h3>Vinculados correctamente</h3>
                  <p>{filteredMatched.length} empleados con usuario en reloj</p>
                </div>
                <Check size={22} style={{ color: "#10b981" }} />
              </div>
              <div className="simple-table">
                <table>
                  <thead>
                    <tr>
                      <th>Empleado (BD)</th>
                      <th>Código</th>
                      <th>User ID ZK</th>
                      <th>Nombre en Reloj</th>
                      <th>Estado</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredMatched.map((item) => (
                      <tr key={item.employee.id}>
                        <td>
                          <div className="employee-cell">
                            <div className="employee-avatar" style={{ background: "#ecfdf3", color: "#10b981" }}>
                              {(item.employee.nombre_completo || "?").charAt(0)}
                            </div>
                            <div>
                              <strong>{safeText(item.employee.nombre_completo)}</strong>
                              <span>{safeText(item.employee.estatus)}</span>
                            </div>
                          </div>
                        </td>
                        <td>{safeText(item.employee.codigo_empleado)}</td>
                        <td><strong>{safeText(item.employee.zk_user_id)}</strong></td>
                        <td>{safeText(item.zk_user?.name)}</td>
                        <td>
                          {item.warnings && item.warnings.length > 0 ? (
                            <span className="badge warning" title={item.warnings.join(", ")}>Con advertencias</span>
                          ) : (
                            <span className="badge success">OK</span>
                          )}
                        </td>
                        <td>
                          <button
                            className="secondary-button"
                            type="button"
                            onClick={() => handleUnlink(item.employee.codigo_empleado)}
                            title="Desvincular"
                            style={{ padding: "6px 10px" }}
                          >
                            <Link2Off size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Tabla de no vinculados */}
          {(filter === "all" || filter === "unlinked") && filteredUnlinked.length > 0 && (
            <>
              <div className="panel-header" style={{ marginTop: "24px" }}>
                <div>
                  <h3>Sin vincular</h3>
                  <p>{filteredUnlinked.length} empleados sin usuario en reloj</p>
                </div>
                <Link2Off size={22} style={{ color: "#ef4444" }} />
              </div>
              <div className="simple-table">
                <table>
                  <thead>
                    <tr>
                      <th>Empleado (BD)</th>
                      <th>Código</th>
                      <th>Motivo</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUnlinked.map((item) => (
                      <tr key={item.employee.id}>
                        <td>
                          <div className="employee-cell">
                            <div className="employee-avatar" style={{ background: "#fef2f2", color: "#ef4444" }}>
                              {(item.employee.nombre_completo || "?").charAt(0)}
                            </div>
                            <div>
                              <strong>{safeText(item.employee.nombre_completo)}</strong>
                              <span>{safeText(item.employee.estatus)}</span>
                            </div>
                          </div>
                        </td>
                        <td>{safeText(item.employee.codigo_empleado)}</td>
                        <td><span style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>{item.reason}</span></td>
                        <td>
                          <button
                            className="primary-button"
                            type="button"
                            onClick={() => openLinkModal(item.employee)}
                            style={{ padding: "6px 12px" }}
                          >
                            <Link2 size={14} />
                            Vincular
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Tabla de huérfanos en reloj */}
          {(filter === "all" || filter === "orphan") && filteredZkWithout.length > 0 && (
            <>
              <div className="panel-header" style={{ marginTop: "24px" }}>
                <div>
                  <h3>Usuarios en reloj sin empleado</h3>
                  <p>{filteredZkWithout.length} usuarios en el reloj que no tienen empleado vinculado</p>
                </div>
                <AlertTriangle size={22} style={{ color: "#f59e0b" }} />
              </div>
              <div className="simple-table">
                <table>
                  <thead>
                    <tr>
                      <th>User ID ZK</th>
                      <th>Nombre en Reloj</th>
                      <th>UID</th>
                      <th>Privilegio</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredZkWithout.map((item) => (
                      <tr key={item.zk_user?.uid || item.zk_user?.user_id}>
                        <td><strong>{safeText(item.zk_user?.user_id)}</strong></td>
                        <td>{safeText(item.zk_user?.name)}</td>
                        <td>{safeText(item.zk_user?.uid)}</td>
                        <td><span className="badge neutral">{safeText(item.zk_user?.privilege)}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Conflictos */}
          {(filter === "all" || filter === "conflicts") && conflicts.length > 0 && (
            <>
              <div className="panel-header" style={{ marginTop: "24px" }}>
                <div>
                  <h3>Conflictos</h3>
                  <p>{conflicts.length} problemas de vinculación detectados</p>
                </div>
                <AlertTriangle size={22} style={{ color: "#8b5cf6" }} />
              </div>
              <div className="simple-table">
                <table>
                  <thead>
                    <tr>
                      <th>Tipo</th>
                      <th>ZK User ID</th>
                      <th>Detalle</th>
                      <th>Empleados afectados</th>
                    </tr>
                  </thead>
                  <tbody>
                    {conflicts.map((item, idx) => (
                      <tr key={idx}>
                        <td><span className="badge danger">{item.type}</span></td>
                        <td><strong>{safeText(item.zk_user_id)}</strong></td>
                        <td>{item.message}</td>
                        <td>
                          {(item.employees || []).map((e) => e.nombre_completo).join(", ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      )}

      {/* Modal vincular */}
      {showLinkModal && linkTarget && (
        <div className="modal-overlay" onClick={() => setShowLinkModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Vincular con reloj</h3>
              <button className="modal-close" type="button" onClick={() => setShowLinkModal(false)}><X size={20} /></button>
            </div>
            <form className="modal-body" onSubmit={handleLink}>
              <p style={{ marginBottom: "16px" }}>
                Vincular <strong>{linkTarget.nombre_completo}</strong> ({linkTarget.codigo_empleado}) con un User ID del reloj ZKTeco.
              </p>

              {linkError && <div className="form-error-message">{linkError}</div>}

              <div className="form-field">
                <label>User ID ZKTeco</label>
                <input
                  type="text"
                  placeholder="Ej: 5"
                  value={linkZkUserId}
                  onChange={(e) => setLinkZkUserId(e.target.value)}
                  autoFocus
                />
                <span style={{ fontSize: "12px", color: "var(--color-text-muted)", marginTop: "4px", display: "block" }}>
                  Ingresa el User ID que tiene este empleado en el reloj físico.
                </span>
              </div>

              {/* Mostrar usuarios disponibles en reloj */}
              {zkWithoutEmployee.length > 0 && (
                <div style={{ marginTop: "12px" }}>
                  <p style={{ fontSize: "12px", fontWeight: 700, marginBottom: "8px" }}>Usuarios disponibles en reloj (sin empleado):</p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {zkWithoutEmployee.map((item) => (
                      <button
                        key={item.zk_user?.user_id}
                        type="button"
                        className="secondary-button"
                        style={{ padding: "4px 10px", fontSize: "12px" }}
                        onClick={() => setLinkZkUserId(item.zk_user?.user_id || "")}
                      >
                        {item.zk_user?.user_id} — {item.zk_user?.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="modal-footer" style={{ marginTop: "20px" }}>
                <button className="secondary-button" type="button" onClick={() => setShowLinkModal(false)}>Cancelar</button>
                <button className="primary-button" type="submit" disabled={linkLoading}>
                  {linkLoading ? "Vinculando..." : <><Link2 size={17} /> Vincular</>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default EmployeeLinkingPage;
