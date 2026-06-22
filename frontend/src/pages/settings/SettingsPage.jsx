import {
  Building2,
  CalendarClock,
  DatabaseBackup,
  Download,
  FileText,
  Fingerprint,
  LockKeyhole,
  Save,
  Settings,
  ShieldCheck,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  mockGlobalRules,
  mockSettingsCards,
  mockSystemSettings,
} from "../../data/mockSettings";

function getStatusClass(status) {
  if (status === "Configurado") return "badge success";
  if (status === "Correcto") return "badge success";
  if (status === "Pendiente") return "badge warning";
  if (status === "Error") return "badge danger";
  return "badge neutral";
}

function SettingsPage() {
  const settings = mockSystemSettings;

  return (
    <div className="page-stack">
      <PageHeader
        title="Configuración"
        description="Parámetros generales del sistema, asistencia, seguridad, pyzk, reportes y respaldos."
      >
        <div className="header-actions">
          <button className="secondary-button" type="button">
            <Download size={17} />
            Exportar configuración
          </button>

          <button className="primary-button" type="button">
            <Save size={17} />
            Guardar cambios
          </button>
        </div>
      </PageHeader>

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <Building2 size={22} />
          </div>
          <div>
            <p>Institución</p>
            <strong className="metric-text">{settings.institution.shortName}</strong>
            <span>{settings.institution.parentInstitution}</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <CalendarClock size={22} />
          </div>
          <div>
            <p>Periodo activo</p>
            <strong className="metric-text">{settings.attendance.activePeriod}</strong>
            <span>
              {settings.attendance.periodStart} - {settings.attendance.periodEnd}
            </span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Fingerprint size={22} />
          </div>
          <div>
            <p>Puerto ZKTeco</p>
            <strong>{settings.pyzk.defaultPort}</strong>
            <span>Comunicación pyzk</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <DatabaseBackup size={22} />
          </div>
          <div>
            <p>Último respaldo</p>
            <strong className="metric-text">{settings.backup.lastBackup}</strong>
            <span>{settings.backup.status}</span>
          </div>
        </article>
      </section>

      <section className="settings-card-grid">
        {mockSettingsCards.map((card) => (
          <article className="settings-card" key={card.id}>
            <div className="settings-card-icon">
              <Settings size={24} />
            </div>

            <div>
              <span className={getStatusClass(card.status)}>{card.status}</span>
              <h3>{card.title}</h3>
              <p>{card.description}</p>
            </div>
          </article>
        ))}
      </section>

      <section className="settings-grid">
        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Datos institucionales</h3>
              <p>Información usada en encabezados, reportes y vistas generales.</p>
            </div>
            <Building2 size={22} />
          </div>

          <div className="form-grid">
            <label>
              Institución superior
              <input defaultValue={settings.institution.parentInstitution} />
            </label>

            <label>
              Nombre del área
              <input defaultValue={settings.institution.name} />
            </label>

            <label>
              Nombre corto
              <input defaultValue={settings.institution.shortName} />
            </label>

            <label>
              Modo de logo
              <select defaultValue={settings.institution.logoMode}>
                <option>Institucional</option>
                <option>Personalizado</option>
                <option>Sin logo</option>
              </select>
            </label>

            <label className="span-2">
              Pie de reporte
              <textarea rows="4" defaultValue={settings.institution.reportFooter} />
            </label>
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Asistencia y periodo</h3>
              <p>Reglas generales para procesar asistencia diaria.</p>
            </div>
            <CalendarClock size={22} />
          </div>

          <div className="form-grid">
            <label>
              Periodo activo
              <input defaultValue={settings.attendance.activePeriod} />
            </label>

            <label>
              Zona horaria
              <input defaultValue={settings.attendance.timezone} />
            </label>

            <label>
              Inicio periodo
              <input defaultValue={settings.attendance.periodStart} />
            </label>

            <label>
              Fin periodo
              <input defaultValue={settings.attendance.periodEnd} />
            </label>

            <label>
              Tolerancia predeterminada
              <input defaultValue={`${settings.attendance.defaultToleranceMinutes} minutos`} />
            </label>

            <label>
              Regla de falta
              <input defaultValue={settings.attendance.absenceRule} />
            </label>

            <label className="span-2">
              Regla de tiempo extra
              <input defaultValue={settings.attendance.extraTimeRule} />
            </label>
          </div>
        </article>
      </section>

      <section className="settings-grid">
        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>pyzk / ZKTeco</h3>
              <p>Parámetros técnicos para comunicación con relojes checadores.</p>
            </div>
            <Fingerprint size={22} />
          </div>

          <div className="form-grid">
            <label>
              Puerto predeterminado
              <input defaultValue={settings.pyzk.defaultPort} />
            </label>

            <label>
              Comm key predeterminada
              <input defaultValue={settings.pyzk.defaultCommKey} />
            </label>

            <label>
              Timeout conexión
              <input defaultValue={settings.pyzk.connectionTimeout} />
            </label>

            <label>
              Modo de sincronización
              <input defaultValue={settings.pyzk.syncMode} />
            </label>

            <label className="span-2">
              Política de duplicados
              <textarea rows="4" defaultValue={settings.pyzk.duplicatePolicy} />
            </label>

            <label className="span-2">
              Política de checadas crudas
              <textarea rows="4" defaultValue={settings.pyzk.rawPolicy} />
            </label>
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Seguridad</h3>
              <p>Configuración base para accesos, sesiones y bloqueo de usuarios.</p>
            </div>
            <LockKeyhole size={22} />
          </div>

          <div className="form-grid">
            <label>
              Política de contraseña
              <input defaultValue={settings.security.passwordPolicy} />
            </label>

            <label>
              2FA
              <select defaultValue={settings.security.twoFactorAuth}>
                <option>Obligatorio</option>
                <option>Opcional</option>
                <option>Desactivado</option>
              </select>
            </label>

            <label>
              Tiempo de sesión
              <input defaultValue={settings.security.sessionTimeout} />
            </label>

            <label>
              Intentos máximos
              <input defaultValue={settings.security.maxLoginAttempts} />
            </label>

            <label className="span-2">
              Política de bloqueo
              <textarea rows="4" defaultValue={settings.security.blockedUserPolicy} />
            </label>
          </div>
        </article>
      </section>

      <section className="settings-grid">
        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Exportaciones</h3>
              <p>Parámetros para reportes PDF, Excel, firmas y sello de auditoría.</p>
            </div>
            <FileText size={22} />
          </div>

          <div className="setting-toggle-list">
            <div>
              <span>Exportar PDF</span>
              <strong>{settings.exports.pdfEnabled ? "Activo" : "Inactivo"}</strong>
            </div>

            <div>
              <span>Exportar Excel</span>
              <strong>{settings.exports.excelEnabled ? "Activo" : "Inactivo"}</strong>
            </div>

            <div>
              <span>Incluir sello de auditoría</span>
              <strong>{settings.exports.includeAuditStamp ? "Activo" : "Inactivo"}</strong>
            </div>

            <div>
              <span>Incluir firmas</span>
              <strong>{settings.exports.includeSignatures ? "Activo" : "Inactivo"}</strong>
            </div>

            <div>
              <span>Formato predeterminado</span>
              <strong>{settings.exports.defaultReportFormat}</strong>
            </div>
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-header">
            <div>
              <h3>Respaldos</h3>
              <p>Configuración base de respaldo y retención de información.</p>
            </div>
            <DatabaseBackup size={22} />
          </div>

          <div className="setting-toggle-list">
            <div>
              <span>Frecuencia</span>
              <strong>{settings.backup.frequency}</strong>
            </div>

            <div>
              <span>Retención</span>
              <strong>{settings.backup.retention}</strong>
            </div>

            <div>
              <span>Último respaldo</span>
              <strong>{settings.backup.lastBackup}</strong>
            </div>

            <div>
              <span>Estatus</span>
              <strong>{settings.backup.status}</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Reglas globales</h3>
            <p>Parámetros operativos que afectan varios módulos del sistema.</p>
          </div>
          <ShieldCheck size={22} />
        </div>

        <div className="simple-table desktop-table">
          <table>
            <thead>
              <tr>
                <th>Parámetro</th>
                <th>Valor</th>
                <th>Módulo</th>
                <th>Descripción</th>
              </tr>
            </thead>

            <tbody>
              {mockGlobalRules.map((rule) => (
                <tr key={rule.id}>
                  <td>
                    <strong>{rule.parameter}</strong>
                  </td>
                  <td>{rule.value}</td>
                  <td>{rule.module}</td>
                  <td>{rule.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mobile-card-list">
          {mockGlobalRules.map((rule) => (
            <article className="mobile-data-card" key={`${rule.id}-mobile`}>
              <h4>{rule.parameter}</h4>
              <p>{rule.description}</p>

              <div className="mobile-data-grid">
                <div>
                  <span>Valor</span>
                  <strong>{rule.value}</strong>
                </div>
                <div>
                  <span>Módulo</span>
                  <strong>{rule.module}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default SettingsPage;