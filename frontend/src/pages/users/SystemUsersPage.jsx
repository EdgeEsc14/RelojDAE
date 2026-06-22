import {
  Download,
  KeyRound,
  LockKeyhole,
  Plus,
  Search,
  Shield,
  ShieldCheck,
  SlidersHorizontal,
  UserCog,
  Users,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  mockPermissionMatrix,
  mockRoles,
  mockSystemUsers,
} from "../../data/mockSystemUsers";

function getStatusClass(status) {
  if (status === "Activo") return "badge success";
  if (status === "Bloqueado") return "badge danger";
  if (status === "Pendiente") return "badge warning";
  if (status === "No activo") return "badge neutral";
  return "badge neutral";
}

function getRoleClass(role) {
  if (role === "Super Admin") return "badge danger";
  if (role === "RH/Admin") return "badge warning";
  if (role === "Auditor") return "badge neutral";
  if (role === "Supervisor") return "badge success";
  return "badge neutral";
}

function renderPermission(value) {
  if (value === true) return <span className="permission-dot allow">Sí</span>;
  if (value === false) return <span className="permission-dot deny">No</span>;

  return <span className="permission-dot partial">{value}</span>;
}

function SystemUsersPage() {
  const activeUsers = mockSystemUsers.filter((user) => user.status === "Activo").length;
  const blockedUsers = mockSystemUsers.filter((user) => user.status === "Bloqueado").length;
  const criticalRoles = mockRoles.filter((role) => role.level === "Crítico").length;

  return (
    <div className="page-stack">
      <PageHeader
        title="Usuarios del sistema"
        description="Administración visual de accesos, roles, permisos y perfiles autorizados."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button">
            <Download size={17} />
            Exportar
          </button>

          <button className="primary-button" type="button">
            <Plus size={17} />
            Nuevo usuario
          </button>
        </div>
      </PageHeader>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Users size={22} />
          </div>
          <div>
            <p>Usuarios registrados</p>
            <strong>{mockSystemUsers.length}</strong>
            <span>Accesos web configurados</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <ShieldCheck size={22} />
          </div>
          <div>
            <p>Usuarios activos</p>
            <strong>{activeUsers}</strong>
            <span>Con acceso vigente</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <LockKeyhole size={22} />
          </div>
          <div>
            <p>Bloqueados</p>
            <strong>{blockedUsers}</strong>
            <span>Acceso suspendido</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Shield size={22} />
          </div>
          <div>
            <p>Roles críticos</p>
            <strong>{criticalRoles}</strong>
            <span>Acceso total o sensible</span>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Catálogo de usuarios</h3>
            <p>Usuarios autorizados para entrar al sistema web.</p>
          </div>
          <UserCog size={22} />
        </div>

        <div className="filters-row">
          <div className="filter-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por usuario, nombre, correo, rol o departamento..."
            />
          </div>

          <button className="secondary-button" type="button">
            <SlidersHorizontal size={17} />
            Filtros
          </button>
        </div>

        <div className="simple-table desktop-table">
          <table>
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Rol</th>
                <th>Departamento</th>
                <th>Estatus</th>
                <th>2FA</th>
                <th>Último acceso</th>
              </tr>
            </thead>

            <tbody>
              {mockSystemUsers.map((user) => (
                <tr key={user.id}>
                  <td>
                    <strong>{user.username}</strong>
                    <span className="table-subtext">{user.email}</span>
                  </td>

                  <td>
                    <div className="employee-cell">
                      <div className="employee-avatar">
                        {user.fullName.charAt(0)}
                      </div>
                      <div>
                        <strong>{user.fullName}</strong>
                        <span>{user.employeeCode}</span>
                      </div>
                    </div>
                  </td>

                  <td>
                    <span className={getRoleClass(user.role)}>{user.role}</span>
                  </td>

                  <td>{user.department}</td>

                  <td>
                    <span className={getStatusClass(user.status)}>
                      {user.status}
                    </span>
                  </td>

                  <td>
                    <span className={getStatusClass(user.twoFactor)}>
                      {user.twoFactor}
                    </span>
                  </td>

                  <td>{user.lastLogin}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mobile-card-list">
          {mockSystemUsers.map((user) => (
            <article className="mobile-data-card" key={`${user.id}-mobile`}>
              <h4>{user.fullName}</h4>
              <p>{user.email}</p>

              <div className="mobile-data-grid">
                <div>
                  <span>Usuario</span>
                  <strong>{user.username}</strong>
                </div>
                <div>
                  <span>Rol</span>
                  <strong>{user.role}</strong>
                </div>
                <div>
                  <span>Departamento</span>
                  <strong>{user.department}</strong>
                </div>
                <div>
                  <span>Estatus</span>
                  <strong>{user.status}</strong>
                </div>
                <div>
                  <span>2FA</span>
                  <strong>{user.twoFactor}</strong>
                </div>
                <div>
                  <span>Último acceso</span>
                  <strong>{user.lastLogin}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="users-grid">
        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Roles del sistema</h3>
              <p>Perfiles de autorización configurados para el sistema.</p>
            </div>
            <Shield size={22} />
          </div>

          <div className="role-list">
            {mockRoles.map((role) => (
              <article className="role-card" key={role.id}>
                <div>
                  <h4>{role.role}</h4>
                  <p>{role.description}</p>
                </div>

                <div className="role-card-footer">
                  <span className={getRoleClass(role.role)}>{role.level}</span>
                  <strong>{role.users} usuario(s)</strong>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Permisos sensibles</h3>
              <p>Resumen de operaciones restringidas al Super Admin.</p>
            </div>
            <KeyRound size={22} />
          </div>

          <div className="sensitive-permission-list">
            <div>
              <span>Configurar dispositivos ZKTeco</span>
              <strong>Solo Super Admin</strong>
            </div>

            <div>
              <span>Gestionar usuarios del sistema</span>
              <strong>Solo Super Admin</strong>
            </div>

            <div>
              <span>Ver bitácora de auditoría</span>
              <strong>Super Admin / Auditor</strong>
            </div>

            <div>
              <span>Editar reglas globales</span>
              <strong>Super Admin / RH autorizado</strong>
            </div>

            <div>
              <span>Eliminar registros crudos</span>
              <strong>No permitido</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Matriz de permisos</h3>
            <p>Visualización base de acceso por rol y módulo del sistema.</p>
          </div>
        </div>

        <div className="simple-table desktop-table">
          <table>
            <thead>
              <tr>
                <th>Módulo</th>
                <th>Super Admin</th>
                <th>RH/Admin</th>
                <th>Supervisor</th>
                <th>Empleado</th>
                <th>Auditor</th>
              </tr>
            </thead>

            <tbody>
              {mockPermissionMatrix.map((row) => (
                <tr key={row.module}>
                  <td>
                    <strong>{row.module}</strong>
                  </td>
                  <td>{renderPermission(row.superAdmin)}</td>
                  <td>{renderPermission(row.rhAdmin)}</td>
                  <td>{renderPermission(row.supervisor)}</td>
                  <td>{renderPermission(row.employee)}</td>
                  <td>{renderPermission(row.auditor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mobile-card-list">
          {mockPermissionMatrix.map((row) => (
            <article className="mobile-data-card" key={`${row.module}-mobile`}>
              <h4>{row.module}</h4>

              <div className="mobile-data-grid">
                <div>
                  <span>Super Admin</span>
                  <strong>{String(row.superAdmin)}</strong>
                </div>
                <div>
                  <span>RH/Admin</span>
                  <strong>{String(row.rhAdmin)}</strong>
                </div>
                <div>
                  <span>Supervisor</span>
                  <strong>{String(row.supervisor)}</strong>
                </div>
                <div>
                  <span>Empleado</span>
                  <strong>{String(row.employee)}</strong>
                </div>
                <div>
                  <span>Auditor</span>
                  <strong>{String(row.auditor)}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default SystemUsersPage;