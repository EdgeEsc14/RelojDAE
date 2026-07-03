import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Link2,
  RefreshCcw,
  UserCheck,
  UserX,
  Users,
} from "lucide-react";

import {
  getZkEmployeeReconciliation,
  linkEmployeeWithZkUser,
  unlinkEmployeeFromZkUser,
} from "../../api/zkApi";

function safeText(value, fallback = "-") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  return String(value);
}

function MetricItem({ icon: Icon, title, value, description, status = "neutral" }) {
  const badgeClass =
    status === "success"
      ? "badge success"
      : status === "warning"
      ? "badge warning"
      : status === "danger"
      ? "badge danger"
      : "badge neutral";

  return (
    <article className="metric-card">
      <div className="metric-icon">
        <Icon size={22} />
      </div>

      <div>
        <p>{title}</p>
        <strong>{value}</strong>
        <span>{description}</span>
      </div>

      <span className={badgeClass}>{status}</span>
    </article>
  );
}

function EmptyState({ title, description }) {
  return (
    <article className="device-card">
      <div className="device-card-header">
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>

        <span className="badge success">OK</span>
      </div>
    </article>
  );
}

export default function ZkReconciliationPanel() {
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState("employeesWithoutZk");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedEmployeeCode, setSelectedEmployeeCode] = useState("");
  const [selectedZkUserId, setSelectedZkUserId] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState("");

  async function loadReconciliation() {
    setLoading(true);
    setError("");

    try {
      const response = await getZkEmployeeReconciliation();
      setData(response);
    } catch (err) {
      setError(err.message || "No se pudo consultar la conciliación.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }
  async function handleLinkEmployee() {
  setError("");
  setActionMessage("");

  if (!selectedEmployeeCode) {
    setError("Selecciona un empleado para vincular.");
    return;
  }

  if (!selectedZkUserId) {
    setError("Selecciona un usuario ZKTeco para vincular.");
    return;
  }

  setActionLoading(true);

  try {
    const response = await linkEmployeeWithZkUser({
      codigoEmpleado: selectedEmployeeCode,
      zkUserId: selectedZkUserId,
    });

    setActionMessage(response.message || "Empleado vinculado correctamente.");
    setSelectedEmployeeCode("");
    setSelectedZkUserId("");

    await loadReconciliation();
  } catch (err) {
    setError(err.message || "No se pudo vincular el empleado.");
  } finally {
    setActionLoading(false);
  }
}

async function handleUnlinkEmployee(codigoEmpleado) {
  setError("");
  setActionMessage("");

  const confirmed = window.confirm(
    `¿Seguro que quieres desvincular el empleado ${codigoEmpleado} del usuario ZKTeco?`
  );

  if (!confirmed) {
    return;
  }

  setActionLoading(true);

  try {
    const response = await unlinkEmployeeFromZkUser(codigoEmpleado);

    setActionMessage(response.message || "Empleado desvinculado correctamente.");

    await loadReconciliation();
  } catch (err) {
    setError(err.message || "No se pudo desvincular el empleado.");
  } finally {
    setActionLoading(false);
  }
}
  useEffect(() => {
    loadReconciliation();
  }, []);

  const summary = data?.summary || {
    zk_users_total: 0,
    zk_users_operational: 0,
    employees_total: 0,
    matched: 0,
    employees_without_zk_user: 0,
    zk_users_without_employee: 0,
    conflicts: 0,
  };

  const matched = data?.matched || [];
  const employeesWithoutZkUser = data?.employees_without_zk_user || [];
  const zkUsersWithoutEmployee = data?.zk_users_without_employee || [];
  const conflicts = data?.conflicts || [];

  const filteredEmployeesWithoutZk = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    if (!term) return employeesWithoutZkUser;

    return employeesWithoutZkUser.filter((item) => {
      const employee = item.employee || {};

      return (
        safeText(employee.codigo_empleado).toLowerCase().includes(term) ||
        safeText(employee.nombre_completo).toLowerCase().includes(term) ||
        safeText(employee.correo).toLowerCase().includes(term) ||
        safeText(employee.zk_user_id).toLowerCase().includes(term) ||
        safeText(item.reason).toLowerCase().includes(term)
      );
    });
  }, [employeesWithoutZkUser, searchTerm]);

  const filteredZkUsersWithoutEmployee = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    if (!term) return zkUsersWithoutEmployee;

    return zkUsersWithoutEmployee.filter((item) => {
      const zkUser = item.zk_user || {};

      return (
        safeText(zkUser.uid).toLowerCase().includes(term) ||
        safeText(zkUser.user_id).toLowerCase().includes(term) ||
        safeText(zkUser.name).toLowerCase().includes(term) ||
        safeText(zkUser.privilege).toLowerCase().includes(term) ||
        safeText(item.reason).toLowerCase().includes(term)
      );
    });
  }, [zkUsersWithoutEmployee, searchTerm]);

  const filteredMatched = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    if (!term) return matched;

    return matched.filter((item) => {
      const employee = item.employee || {};
      const zkUser = item.zk_user || {};

      return (
        safeText(employee.codigo_empleado).toLowerCase().includes(term) ||
        safeText(employee.nombre_completo).toLowerCase().includes(term) ||
        safeText(employee.zk_user_id).toLowerCase().includes(term) ||
        safeText(zkUser.user_id).toLowerCase().includes(term) ||
        safeText(zkUser.name).toLowerCase().includes(term)
      );
    });
  }, [matched, searchTerm]);

  return (
    <section className="panel-card">
      <div className="section-header">
        <div>
          <h2>BD & Reloj</h2>
          <p>
            Comparación entre empleados registrados en PostgreSQL y usuarios reales
            detectados en el reloj ZKTeco.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={loadReconciliation}
          disabled={loading}
        >
          <RefreshCcw size={17} />
          {loading ? "Actualizando..." : "Actualizar conciliación"}
        </button>
      </div>

      <section className="metrics-grid four-columns">
        <MetricItem
          icon={Users}
          title="Empleados"
          value={summary.employees_total}
          description="Registros en BD"
          status="neutral"
        />

        <MetricItem
          icon={UserCheck}
          title="Vinculados"
          value={summary.matched}
          description="Empleado con usuario ZKTeco"
          status="success"
        />

        <MetricItem
          icon={UserX}
          title="Empleados sin usuario"
          value={summary.employees_without_zk_user}
          description="Sin vínculo válido"
          status={summary.employees_without_zk_user > 0 ? "warning" : "success"}
        />

        <MetricItem
          icon={AlertTriangle}
          title="Conflictos"
          value={summary.conflicts}
          description="Duplicados o inconsistencias"
          status={summary.conflicts > 0 ? "danger" : "success"}
        />
      </section>

      <section className="metrics-grid four-columns">
        <MetricItem
          icon={Link2}
          title="Usuarios reloj"
          value={summary.zk_users_total}
          description="Incluye admin/protegidos"
          status="neutral"
        />

        <MetricItem
          icon={Users}
          title="Usuarios operativos"
          value={summary.zk_users_operational}
          description="Disponibles para empleados"
          status="neutral"
        />

        <MetricItem
          icon={UserX}
          title="Usuarios sin empleado"
          value={summary.zk_users_without_employee}
          description="Existen en reloj, no en BD"
          status={summary.zk_users_without_employee > 0 ? "warning" : "success"}
        />

        <MetricItem
          icon={CheckCircle2}
          title="Estado"
          value={data?.ok ? "OK" : "Pendiente"}
          description="Resultado de conciliación"
          status={data?.ok ? "success" : "warning"}
        />
      </section>

      <div className="filters-row">
        <div className="filter-search">
          <input
            type="text"
            placeholder="Buscar por empleado, correo, User ID, nombre del reloj..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </div>
      </div>

        <section className="panel-card">
            <div className="section-header">
                <div>
                <h2>Vincular empleado con usuario ZKTeco</h2>
                <p>
                    Selecciona un empleado pendiente y un usuario operativo del reloj. Esta acción
                    solo actualiza la columna zk_user_id en PostgreSQL.
                </p>
                </div>
            </div>

            <div className="filters-row">
                <select
                value={selectedEmployeeCode}
                onChange={(event) => setSelectedEmployeeCode(event.target.value)}
                disabled={actionLoading}
                style={{
                    minHeight: "42px",
                    borderRadius: "12px",
                    border: "1px solid #ddd",
                    padding: "0 12px",
                    minWidth: "320px",
                }}
                >
                <option value="">Selecciona empleado pendiente...</option>

                {employeesWithoutZkUser.map((item) => {
                    const employee = item.employee || {};

                    return (
                    <option
                        key={employee.codigo_empleado}
                        value={employee.codigo_empleado}
                    >
                        {safeText(employee.codigo_empleado)} ·{" "}
                        {safeText(employee.nombre_completo, "Empleado sin nombre")}
                    </option>
                    );
                })}
                </select>

                <select
                value={selectedZkUserId}
                onChange={(event) => setSelectedZkUserId(event.target.value)}
                disabled={actionLoading}
                style={{
                    minHeight: "42px",
                    borderRadius: "12px",
                    border: "1px solid #ddd",
                    padding: "0 12px",
                    minWidth: "300px",
                }}
                >
                <option value="">Selecciona usuario del reloj...</option>

                {zkUsersWithoutEmployee.map((item) => {
                    const zkUser = item.zk_user || {};

                    return (
                    <option key={zkUser.user_id} value={zkUser.user_id}>
                        User ID {safeText(zkUser.user_id)} ·{" "}
                        {safeText(zkUser.name, "Usuario sin nombre")}
                    </option>
                    );
                })}
                </select>

                <button
                className="primary-button"
                type="button"
                onClick={handleLinkEmployee}
                disabled={actionLoading}
                >
                {actionLoading ? "Procesando..." : "Vincular"}
                </button>
            </div>

            {actionMessage && (
                <section className="warning-banner">
                <CheckCircle2 size={22} />
                <div>
                    <strong>Acción completada</strong>
                    <p>{actionMessage}</p>
                </div>
                </section>
            )}
            </section>

      <div className="filters-row">
        <button
          type="button"
          className={
            activeTab === "employeesWithoutZk"
              ? "secondary-button active"
              : "secondary-button"
          }
          onClick={() => setActiveTab("employeesWithoutZk")}
        >
          Empleados sin usuario ({summary.employees_without_zk_user})
        </button>

        <button
          type="button"
          className={
            activeTab === "zkWithoutEmployee"
              ? "secondary-button active"
              : "secondary-button"
          }
          onClick={() => setActiveTab("zkWithoutEmployee")}
        >
          Usuarios sin empleado ({summary.zk_users_without_employee})
        </button>

        <button
          type="button"
          className={
            activeTab === "matched" ? "secondary-button active" : "secondary-button"
          }
          onClick={() => setActiveTab("matched")}
        >
          Vinculados ({summary.matched})
        </button>

        <button
          type="button"
          className={
            activeTab === "conflicts" ? "secondary-button active" : "secondary-button"
          }
          onClick={() => setActiveTab("conflicts")}
        >
          Conflictos ({summary.conflicts})
        </button>
      </div>

      {error && (
        <section className="warning-banner">
          <AlertTriangle size={22} />
          <div>
            <strong>Error de conciliación</strong>
            <p>{error}</p>
          </div>
        </section>
      )}

      {activeTab === "employeesWithoutZk" && (
        <div className="device-card-grid">
          {filteredEmployeesWithoutZk.map((item, index) => {
            const employee = item.employee || {};

            return (
              <article className="device-card" key={`employee-without-zk-${index}`}>
                <div className="device-card-header">
                  <div>
                    <h3>{safeText(employee.nombre_completo, "Empleado sin nombre")}</h3>
                    <p>{safeText(item.reason)}</p>
                  </div>

                  <span className="badge warning">Pendiente</span>
                </div>

                <div className="device-info-grid">
                  <div>
                    <span>Código</span>
                    <strong>{safeText(employee.codigo_empleado)}</strong>
                  </div>

                  <div>
                    <span>ZK User ID</span>
                    <strong>{safeText(employee.zk_user_id, "No asignado")}</strong>
                  </div>

                  <div>
                    <span>Correo</span>
                    <strong>{safeText(employee.correo)}</strong>
                  </div>

                  <div>
                    <span>Estatus</span>
                    <strong>{safeText(employee.estatus)}</strong>
                  </div>
                </div>
              </article>
            );
          })}

          {!loading && filteredEmployeesWithoutZk.length === 0 && (
            <EmptyState
              title="Sin empleados pendientes"
              description="No hay empleados sin usuario ZKTeco en esta categoría."
            />
          )}
        </div>
      )}

      {activeTab === "zkWithoutEmployee" && (
        <div className="device-card-grid">
          {filteredZkUsersWithoutEmployee.map((item, index) => {
            const zkUser = item.zk_user || {};

            return (
              <article className="device-card" key={`zk-without-employee-${index}`}>
                <div className="device-card-header">
                  <div>
                    <h3>{safeText(zkUser.name, "Usuario sin nombre")}</h3>
                    <p>{safeText(item.reason)}</p>
                  </div>

                  <span className="badge warning">Sin vínculo</span>
                </div>

                <div className="device-info-grid">
                  <div>
                    <span>User ID</span>
                    <strong>{safeText(zkUser.user_id)}</strong>
                  </div>

                  <div>
                    <span>UID interno</span>
                    <strong>{safeText(zkUser.uid)}</strong>
                  </div>

                  <div>
                    <span>Privilegio</span>
                    <strong>{safeText(zkUser.privilege)}</strong>
                  </div>

                  <div>
                    <span>PIN</span>
                    <strong>{zkUser.has_pin ? "Sí" : "No"}</strong>
                  </div>
                </div>
              </article>
            );
          })}

          {!loading && filteredZkUsersWithoutEmployee.length === 0 && (
            <EmptyState
              title="Sin usuarios sueltos"
              description="Todos los usuarios ZKTeco operativos están vinculados a empleados."
            />
          )}
        </div>
      )}

      {activeTab === "matched" && (
        <div className="device-card-grid">
          {filteredMatched.map((item, index) => {
            const employee = item.employee || {};
            const zkUser = item.zk_user || {};
            const warnings = item.warnings || [];

            return (
              <article className="device-card" key={`matched-${index}`}>
                <div className="device-card-header">
                  <div>
                    <h3>{safeText(employee.nombre_completo, "Empleado sin nombre")}</h3>
                    <p>
                      Vinculado con {safeText(zkUser.name)} / User ID{" "}
                      {safeText(zkUser.user_id)}
                    </p>
                  </div>

                  <span className={warnings.length > 0 ? "badge warning" : "badge success"}>
                    {warnings.length > 0 ? "Revisar" : "OK"}
                  </span>
                </div>

                <div className="device-info-grid">
                  <div>
                    <span>Código empleado</span>
                    <strong>{safeText(employee.codigo_empleado)}</strong>
                  </div>

                  <div>
                    <span>ZK User ID BD</span>
                    <strong>{safeText(employee.zk_user_id)}</strong>
                  </div>

                  <div>
                    <span>Nombre reloj</span>
                    <strong>{safeText(zkUser.name)}</strong>
                  </div>

                  <div>
                    <span>UID reloj</span>
                    <strong>{safeText(zkUser.uid)}</strong>
                  </div>
                </div>
                <div className="device-card-footer">
                    <div>
                        <span>Acción sobre vínculo</span>
                        <strong>Solo modifica PostgreSQL</strong>
                    </div>

                    <button
                        className="secondary-button"
                        type="button"
                        onClick={() => handleUnlinkEmployee(employee.codigo_empleado)}
                        disabled={actionLoading}
                    >
                        Desvincular
                    </button>
                    </div>
                {warnings.length > 0 && (
                  <section className="warning-banner">
                    <AlertTriangle size={18} />
                    <div>
                      <strong>Advertencias</strong>
                      {warnings.map((warning, warningIndex) => (
                        <p key={`warning-${warningIndex}`}>{warning}</p>
                      ))}
                    </div>
                  </section>
                )}
              </article>
            );
          })}

          {!loading && filteredMatched.length === 0 && (
            <EmptyState
              title="Sin vinculaciones"
              description="Todavía no hay empleados vinculados con usuarios del reloj."
            />
          )}
        </div>
      )}

      {activeTab === "conflicts" && (
        <div className="device-card-grid">
          {conflicts.map((conflict, index) => (
            <article className="device-card" key={`conflict-${index}`}>
              <div className="device-card-header">
                <div>
                  <h3>{safeText(conflict.type, "Conflicto")}</h3>
                  <p>{safeText(conflict.message)}</p>
                </div>

                <span className="badge danger">Conflicto</span>
              </div>

              <div className="device-info-grid">
                <div>
                  <span>ZK User ID</span>
                  <strong>{safeText(conflict.zk_user_id)}</strong>
                </div>

                <div>
                  <span>Empleados afectados</span>
                  <strong>{conflict.employees?.length || 0}</strong>
                </div>
              </div>
            </article>
          ))}

          {!loading && conflicts.length === 0 && (
            <EmptyState
              title="Sin conflictos"
              description="No se detectaron duplicados o inconsistencias fuertes."
            />
          )}
        </div>
      )}
    </section>
  );
}