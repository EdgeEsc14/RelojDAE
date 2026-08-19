import { useEffect, useState } from "react";

import {
  Check,
  ChevronLeft,
  ChevronRight,
  Edit,
  KeyRound,
  LockKeyhole,
  Plus,
  Search,
  Shield,
  ShieldCheck,
  SlidersHorizontal,
  UserCog,
  Users,
  X,
  XCircle,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  getUsuarios,
  getRoles,
  crearUsuario,
  actualizarUsuario,
  desactivarUsuario,
} from "../../api/usuariosApi";


function getStatusClass(status) {
  const s = (status || "").toUpperCase();
  if (s === "ACTIVO") return "badge success";
  if (s === "BLOQUEADO") return "badge danger";
  if (s === "INACTIVO") return "badge neutral";
  if (s.startsWith("PENDIENTE")) return "badge warning";
  return "badge neutral";
}

function getStatusLabel(status) {
  const s = (status || "").toUpperCase();
  if (s === "ACTIVO") return "Activo";
  if (s === "BLOQUEADO") return "Bloqueado";
  if (s === "INACTIVO") return "Inactivo";
  if (s === "PENDIENTE_VERIFICACION") return "Pendiente verificación";
  if (s === "PENDIENTE_APROBACION") return "Pendiente aprobación";
  return status || "Desconocido";
}

function getRoleClass(rolCodigo) {
  const r = (rolCodigo || "").toUpperCase();
  if (r === "SUPER_ADMIN") return "badge danger";
  if (r === "RH_ADMIN") return "badge warning";
  if (r === "AUDITOR") return "badge neutral";
  if (r === "SUPERVISOR") return "badge success";
  return "badge neutral";
}


function SystemUsersPage() {
  // Data state
  const [usuarios, setUsuarios] = useState([]);
  const [roles, setRoles] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Filters
  const [busqueda, setBusqueda] = useState("");
  const [filtroRolId, setFiltroRolId] = useState("");
  const [filtroEstatus, setFiltroEstatus] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    correo_electronico: "",
    password: "",
    rol_id: "",
    nombre_usuario: "",
    empleado_id: "",
    requiere_cambio_password: true,
  });
  const [formError, setFormError] = useState("");
  const [formLoading, setFormLoading] = useState(false);

  // Load roles on mount
  useEffect(() => {
    async function loadRoles() {
      try {
        const data = await getRoles();
        setRoles(data);
      } catch (err) {
        console.error("Error cargando roles:", err.message);
      }
    }
    loadRoles();
  }, []);

  // Load users when filters/page change
  useEffect(() => {
    loadUsuarios();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, filtroRolId, filtroEstatus]);

  async function loadUsuarios() {
    try {
      setLoading(true);
      setError("");

      const data = await getUsuarios({
        page,
        pageSize,
        rolId: filtroRolId || undefined,
        estatus: filtroEstatus || undefined,
        busqueda: busqueda.trim() || undefined,
      });

      setUsuarios(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message || "Error al cargar usuarios.");
      setUsuarios([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e) {
    e.preventDefault();
    setPage(1);
    loadUsuarios();
  }

  function clearFilters() {
    setBusqueda("");
    setFiltroRolId("");
    setFiltroEstatus("");
    setPage(1);
  }

  // Modal handlers
  function openCreateModal() {
    setEditingUser(null);
    setFormData({
      correo_electronico: "",
      password: "",
      rol_id: roles.length > 0 ? String(roles[0].id) : "",
      nombre_usuario: "",
      empleado_id: "",
      requiere_cambio_password: true,
    });
    setFormError("");
    setShowModal(true);
  }

  function openEditModal(usuario) {
    setEditingUser(usuario);
    setFormData({
      correo_electronico: usuario.correo_electronico || "",
      password: "",
      rol_id: String(usuario.rol_id || ""),
      nombre_usuario: usuario.nombre_usuario || "",
      empleado_id: usuario.empleado_id ? String(usuario.empleado_id) : "",
      requiere_cambio_password: usuario.requiere_cambio_password || false,
      estatus: usuario.estatus || "ACTIVO",
    });
    setFormError("");
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setEditingUser(null);
    setFormError("");
  }

  function handleFormChange(field, value) {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    setFormError("");
    setFormLoading(true);

    try {
      if (editingUser) {
        // Update
        const updatePayload = {};

        if (formData.correo_electronico !== editingUser.correo_electronico) {
          updatePayload.correo_electronico = formData.correo_electronico;
        }
        if (String(formData.rol_id) !== String(editingUser.rol_id)) {
          updatePayload.rol_id = Number(formData.rol_id);
        }
        if (formData.nombre_usuario !== (editingUser.nombre_usuario || "")) {
          updatePayload.nombre_usuario = formData.nombre_usuario || null;
        }
        if (formData.estatus !== editingUser.estatus) {
          updatePayload.estatus = formData.estatus;
        }
        if (formData.requiere_cambio_password !== editingUser.requiere_cambio_password) {
          updatePayload.requiere_cambio_password = formData.requiere_cambio_password;
        }
        if (formData.password) {
          updatePayload.nueva_password = formData.password;
        }

        if (Object.keys(updatePayload).length === 0) {
          setFormError("No hay cambios para guardar.");
          setFormLoading(false);
          return;
        }

        await actualizarUsuario(editingUser.id, updatePayload);
      } else {
        // Create
        if (!formData.correo_electronico) {
          setFormError("El correo electrónico es obligatorio.");
          setFormLoading(false);
          return;
        }
        if (!formData.password || formData.password.length < 8) {
          setFormError("La contraseña debe tener al menos 8 caracteres.");
          setFormLoading(false);
          return;
        }
        if (!formData.rol_id) {
          setFormError("Debes seleccionar un rol.");
          setFormLoading(false);
          return;
        }

        const createPayload = {
          correo_electronico: formData.correo_electronico,
          password: formData.password,
          rol_id: Number(formData.rol_id),
          requiere_cambio_password: formData.requiere_cambio_password,
        };

        if (formData.nombre_usuario) {
          createPayload.nombre_usuario = formData.nombre_usuario;
        }
        if (formData.empleado_id) {
          createPayload.empleado_id = Number(formData.empleado_id);
        }

        await crearUsuario(createPayload);
      }

      closeModal();
      loadUsuarios();
    } catch (err) {
      setFormError(err.message || "Error al guardar usuario.");
    } finally {
      setFormLoading(false);
    }
  }

  async function handleDeactivate(usuario) {
    if (!window.confirm(`¿Desactivar al usuario "${usuario.nombre_usuario || usuario.correo_electronico}"?`)) {
      return;
    }

    try {
      await desactivarUsuario(usuario.id);
      loadUsuarios();
    } catch (err) {
      alert("Error al desactivar: " + err.message);
    }
  }

  // Pagination calculations
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const firstRecord = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastRecord = Math.min(page * pageSize, total);

  // Metrics
  const activeCount = usuarios.filter((u) => u.estatus === "ACTIVO").length;
  const blockedCount = usuarios.filter((u) => u.estatus === "BLOQUEADO").length;

  return (
    <div className="page-stack">
      <PageHeader
        title="Usuarios del sistema"
        description="Gestión de cuentas de acceso, roles y permisos del sistema web."
      >
        <div className="header-actions">
          <button className="primary-button" type="button" onClick={openCreateModal}>
            <Plus size={17} />
            Nuevo usuario
          </button>
        </div>
      </PageHeader>

      {/* Metrics */}
      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Users size={22} />
          </div>
          <div>
            <p>Total usuarios</p>
            <strong>{total}</strong>
            <span>Registrados en el sistema</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <ShieldCheck size={22} />
          </div>
          <div>
            <p>Activos</p>
            <strong>{activeCount}</strong>
            <span>Con acceso vigente</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <LockKeyhole size={22} />
          </div>
          <div>
            <p>Bloqueados</p>
            <strong>{blockedCount}</strong>
            <span>Acceso suspendido</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Shield size={22} />
          </div>
          <div>
            <p>Roles disponibles</p>
            <strong>{roles.length}</strong>
            <span>Perfiles de autorización</span>
          </div>
        </article>
      </section>

      {/* Table */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Catálogo de usuarios</h3>
            <p>Usuarios autorizados para acceder al sistema web.</p>
          </div>
          <UserCog size={22} />
        </div>

        {/* Search + Filters */}
        <form className="filters-row" onSubmit={handleSearch}>
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por correo, nombre de usuario o empleado..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </div>

          <button className="secondary-button" type="submit">
            <Search size={17} />
            Buscar
          </button>

          <button
            className="secondary-button"
            type="button"
            onClick={() => setShowFilters((v) => !v)}
          >
            <SlidersHorizontal size={17} />
            Filtros
          </button>
        </form>

        {showFilters && (
          <div className="advanced-filters">
            <div className="filter-field">
              <label htmlFor="filter-rol">Rol</label>
              <select
                id="filter-rol"
                value={filtroRolId}
                onChange={(e) => {
                  setFiltroRolId(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Todos los roles</option>
                {roles.map((rol) => (
                  <option key={rol.id} value={rol.id}>
                    {rol.nombre}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-field">
              <label htmlFor="filter-estatus">Estatus</label>
              <select
                id="filter-estatus"
                value={filtroEstatus}
                onChange={(e) => {
                  setFiltroEstatus(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Todos</option>
                <option value="ACTIVO">Activo</option>
                <option value="INACTIVO">Inactivo</option>
                <option value="BLOQUEADO">Bloqueado</option>
              </select>
            </div>

            <div className="filter-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={clearFilters}
              >
                <X size={17} />
                Limpiar
              </button>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="empty-state">
            <h3>Error al cargar usuarios</h3>
            <p>{error}</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="empty-state">
            <h3>Cargando usuarios...</h3>
            <p>Consultando información del sistema.</p>
          </div>
        )}

        {/* Empty */}
        {!loading && !error && usuarios.length === 0 && (
          <div className="empty-state">
            <h3>No se encontraron usuarios</h3>
            <p>No existen usuarios que coincidan con los criterios.</p>
          </div>
        )}

        {/* Table */}
        {!loading && usuarios.length > 0 && (
          <>
            <div className="simple-table">
              <table>
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>Empleado</th>
                    <th>Rol</th>
                    <th>Estatus</th>
                    <th>Último login</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {usuarios.map((usuario) => (
                    <tr key={usuario.id}>
                      <td>
                        <div className="employee-cell">
                          <div className="employee-avatar">
                            {(usuario.nombre_usuario || usuario.correo_electronico || "U").charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <strong>{usuario.nombre_usuario || "Sin nombre de usuario"}</strong>
                            <span>{usuario.correo_electronico}</span>
                          </div>
                        </div>
                      </td>

                      <td>
                        {usuario.nombre_empleado ? (
                          <div>
                            <strong>{usuario.nombre_empleado}</strong>
                            <span className="table-subtext">{usuario.codigo_empleado}</span>
                          </div>
                        ) : (
                          <span className="muted-table-text">Sin empleado vinculado</span>
                        )}
                      </td>

                      <td>
                        <span className={getRoleClass(usuario.rol_codigo)}>
                          {usuario.rol_nombre}
                        </span>
                      </td>

                      <td>
                        <span className={getStatusClass(usuario.estatus)}>
                          {getStatusLabel(usuario.estatus)}
                        </span>
                      </td>

                      <td>
                        {usuario.ultimo_login
                          ? new Date(usuario.ultimo_login).toLocaleString("es-MX", {
                              day: "2-digit",
                              month: "short",
                              year: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "Nunca"}
                      </td>

                      <td>
                        <div className="table-actions-group">
                          <button
                            className="table-action"
                            type="button"
                            onClick={() => openEditModal(usuario)}
                            title="Editar usuario"
                          >
                            <Edit size={16} />
                          </button>

                          {usuario.estatus === "ACTIVO" && (
                            <button
                              className="table-action danger"
                              type="button"
                              onClick={() => handleDeactivate(usuario)}
                              title="Desactivar usuario"
                            >
                              <XCircle size={16} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination-bar">
              <div className="pagination-summary">
                Mostrando <strong>{firstRecord}</strong> – <strong>{lastRecord}</strong> de{" "}
                <strong>{total}</strong> usuarios
              </div>

              <div className="pagination-size">
                <label htmlFor="users-per-page">Filas por página</label>
                <select
                  id="users-per-page"
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>

              <div className="pagination-controls" aria-label="Paginación de usuarios">
                <button
                  className="pagination-button"
                  type="button"
                  disabled={page === 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  aria-label="Página anterior"
                >
                  <ChevronLeft size={17} />
                </button>

                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let startPage = Math.max(1, page - 2);
                  if (startPage + 4 > totalPages) startPage = Math.max(1, totalPages - 4);
                  const pageNum = startPage + i;
                  if (pageNum > totalPages) return null;
                  return (
                    <button
                      key={pageNum}
                      className={pageNum === page ? "pagination-button active" : "pagination-button"}
                      type="button"
                      onClick={() => setPage(pageNum)}
                    >
                      {pageNum}
                    </button>
                  );
                })}

                <button
                  className="pagination-button"
                  type="button"
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  aria-label="Página siguiente"
                >
                  <ChevronRight size={17} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {/* Roles panel */}
      {roles.length > 0 && (
        <section className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Roles del sistema</h3>
              <p>Perfiles de autorización configurados.</p>
            </div>
            <KeyRound size={22} />
          </div>

          <div className="role-list">
            {roles.map((rol) => (
              <article className="role-card" key={rol.id}>
                <div>
                  <h4>{rol.nombre}</h4>
                  <p>{rol.descripcion || "Sin descripción"}</p>
                </div>
                <div className="role-card-footer">
                  <span className={getRoleClass(rol.codigo)}>{rol.codigo}</span>
                  {rol.es_sistema && <span className="badge neutral">Sistema</span>}
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingUser ? "Editar usuario" : "Nuevo usuario"}</h3>
              <button className="modal-close" type="button" onClick={closeModal}>
                <X size={20} />
              </button>
            </div>

            <form className="modal-body" onSubmit={handleFormSubmit}>
              {formError && (
                <div className="form-error-message">
                  {formError}
                </div>
              )}

              <div className="form-field">
                <label htmlFor="user-email">Correo electrónico *</label>
                <input
                  id="user-email"
                  type="email"
                  required
                  placeholder="usuario@dominio.com"
                  value={formData.correo_electronico}
                  onChange={(e) => handleFormChange("correo_electronico", e.target.value)}
                />
              </div>

              <div className="form-field">
                <label htmlFor="user-password">
                  {editingUser ? "Nueva contraseña (dejar vacío para no cambiar)" : "Contraseña *"}
                </label>
                <input
                  id="user-password"
                  type="password"
                  placeholder={editingUser ? "Sin cambios" : "Mínimo 8 caracteres"}
                  required={!editingUser}
                  minLength={editingUser ? 0 : 8}
                  value={formData.password}
                  onChange={(e) => handleFormChange("password", e.target.value)}
                />
              </div>

              <div className="form-field">
                <label htmlFor="user-role">Rol *</label>
                <select
                  id="user-role"
                  required
                  value={formData.rol_id}
                  onChange={(e) => handleFormChange("rol_id", e.target.value)}
                >
                  <option value="">Seleccionar rol...</option>
                  {roles.map((rol) => (
                    <option key={rol.id} value={rol.id}>
                      {rol.nombre} ({rol.codigo})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label htmlFor="user-username">Nombre de usuario</label>
                <input
                  id="user-username"
                  type="text"
                  placeholder="Se genera del correo si se deja vacío"
                  value={formData.nombre_usuario}
                  onChange={(e) => handleFormChange("nombre_usuario", e.target.value)}
                />
              </div>

              {!editingUser && (
                <div className="form-field">
                  <label htmlFor="user-empleado">ID de empleado (opcional)</label>
                  <input
                    id="user-empleado"
                    type="number"
                    placeholder="Vincular a empleado existente"
                    value={formData.empleado_id}
                    onChange={(e) => handleFormChange("empleado_id", e.target.value)}
                  />
                </div>
              )}

              {editingUser && (
                <div className="form-field">
                  <label htmlFor="user-estatus">Estatus</label>
                  <select
                    id="user-estatus"
                    value={formData.estatus}
                    onChange={(e) => handleFormChange("estatus", e.target.value)}
                  >
                    <option value="ACTIVO">Activo</option>
                    <option value="INACTIVO">Inactivo</option>
                    <option value="BLOQUEADO">Bloqueado</option>
                  </select>
                </div>
              )}

              <div className="form-field form-checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.requiere_cambio_password}
                    onChange={(e) => handleFormChange("requiere_cambio_password", e.target.checked)}
                  />
                  Requerir cambio de contraseña al primer login
                </label>
              </div>

              <div className="modal-footer">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={closeModal}
                  disabled={formLoading}
                >
                  Cancelar
                </button>

                <button
                  className="primary-button"
                  type="submit"
                  disabled={formLoading}
                >
                  {formLoading ? (
                    "Guardando..."
                  ) : (
                    <>
                      <Check size={17} />
                      {editingUser ? "Guardar cambios" : "Crear usuario"}
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default SystemUsersPage;
