import { useEffect, useState } from "react";

import {
  Building2,
  CalendarClock,
  DatabaseBackup,
  FileText,
  Image as ImageIcon,
  LockKeyhole,
  Save,
  ShieldCheck,
  Trash2,
  Upload,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { apiRequest } from "../../api/client";
import { getStoredToken } from "../../api/authApi";

function getTodayValue() {
  return new Date().toISOString().slice(0, 10);
}

function getCurrentMonthPeriod() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const firstDay = new Date(year, month, 1).toISOString().slice(0, 10);
  const lastDay = new Date(year, month + 1, 0).toISOString().slice(0, 10);
  const monthName = new Intl.DateTimeFormat("es-MX", { month: "long" }).format(now);
  return {
    nombre: `${monthName.charAt(0).toUpperCase() + monthName.slice(1)} ${year}`,
    fechaInicio: firstDay,
    fechaFin: lastDay,
  };
}

function SettingsPage() {
  const defaultPeriod = getCurrentMonthPeriod();

  // ============================================================
  // Estado — Datos institucionales
  // ============================================================
  const [institution, setInstitution] = useState({
    parentInstitution: "Instituto Politécnico Nacional",
    name: "Dirección de Administración Escolar",
    shortName: "DAE",
    reportFooter: "Documento generado por el sistema de control de asistencia DAE.",
  });

  // ============================================================
  // Estado — Periodo y asistencia
  // ============================================================
  const [attendance, setAttendance] = useState({
    activePeriod: defaultPeriod.nombre,
    periodStart: defaultPeriod.fechaInicio,
    periodEnd: defaultPeriod.fechaFin,
    toleranciaMinutos: 10,
    retardoMenorDesde: 11,
    retardoMenorHasta: 20,
    retardoMayorDesde: 21,
    retardoMayorHasta: 30,
    faltaDesde: 31,
    puntosRetardoMenor: 1,
    puntosRetardoMayor: 2,
    puntosDO: 10,
    dosParaRevision: 7,
    faltasConsecutivasRevision: 3,
  });

  // ============================================================
  // Estado — Seguridad
  // ============================================================
  const [security, setSecurity] = useState({
    sessionTimeoutMinutes: 480,
    maxLoginAttempts: 5,
    minPasswordLength: 8,
    blockAfterFailedAttempts: true,
  });

  // ============================================================
  // Estado — Respaldos
  // ============================================================
  const [backup, setBackup] = useState({
    frequency: "Diario",
    retention: "7 días",
    lastBackup: "Sin ejecutar",
    status: "Pendiente",
  });

  // ============================================================
  // Estado — UI
  // ============================================================
  const [savedSection, setSavedSection] = useState("");

  // ============================================================
  // Estado — Logo / Branding
  // ============================================================
  const [logoInfo, setLogoInfo] = useState(null);
  const [logoPreviewUrl, setLogoPreviewUrl] = useState(null);
  const [logoUploading, setLogoUploading] = useState(false);
  const [logoError, setLogoError] = useState("");
  const [logoSuccess, setLogoSuccess] = useState("");

  // ============================================================
  // Guardar por sección (en localStorage por ahora)
  // ============================================================
  useEffect(() => {
    try {
      const saved = localStorage.getItem("relojdae_settings");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.institution) setInstitution(parsed.institution);
        if (parsed.attendance) setAttendance(parsed.attendance);
        if (parsed.security) setSecurity(parsed.security);
        if (parsed.backup) setBackup((prev) => ({ ...prev, ...parsed.backup }));
      }
    } catch {
      // Ignorar si no hay nada guardado
    }
  }, []);

  // Cargar info del logo al inicio
  useEffect(() => {
    loadLogoInfo();
  }, []);

  async function loadLogoInfo() {
    try {
      const info = await apiRequest("/branding/logo/info");
      setLogoInfo(info);
      if (info?.has_logo) {
        const token = getStoredToken();
        const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
        setLogoPreviewUrl(`${baseUrl}/branding/logo?t=${Date.now()}`);
      } else {
        setLogoPreviewUrl(null);
      }
    } catch {
      setLogoInfo(null);
      setLogoPreviewUrl(null);
    }
  }

  async function handleLogoUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    setLogoError("");
    setLogoSuccess("");

    // Validar extensión
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!["jpg", "jpeg", "png"].includes(ext)) {
      setLogoError("Solo se aceptan archivos JPG o PNG.");
      return;
    }

    // Validar tamaño (5 MB)
    if (file.size > 5 * 1024 * 1024) {
      setLogoError("El archivo no puede exceder 5 MB.");
      return;
    }

    setLogoUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const token = getStoredToken();
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

      const response = await fetch(`${baseUrl}/branding/logo`, {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || `Error HTTP ${response.status}`);
      }

      setLogoSuccess("Logo actualizado correctamente.");
      await loadLogoInfo();
      setTimeout(() => setLogoSuccess(""), 4000);
    } catch (err) {
      setLogoError(err.message || "Error al subir logo.");
    } finally {
      setLogoUploading(false);
      // Limpiar input
      event.target.value = "";
    }
  }

  async function handleLogoDelete() {
    if (!confirm("¿Eliminar el logo institucional?")) return;
    setLogoError("");
    setLogoSuccess("");
    try {
      await apiRequest("/branding/logo", { method: "DELETE" });
      setLogoSuccess("Logo eliminado.");
      setLogoInfo(null);
      setLogoPreviewUrl(null);
      setTimeout(() => setLogoSuccess(""), 4000);
    } catch (err) {
      setLogoError(err.message || "Error al eliminar logo.");
    }
  }

  function saveSection(section) {
    const saved = localStorage.getItem("relojdae_settings");
    const config = saved ? JSON.parse(saved) : {};

    if (section === "institution") config.institution = institution;
    if (section === "attendance") config.attendance = attendance;
    if (section === "security") config.security = security;
    if (section === "backup") config.backup = { frequency: backup.frequency, retention: backup.retention };

    localStorage.setItem("relojdae_settings", JSON.stringify(config));
    setSavedSection(section);
    setTimeout(() => setSavedSection(""), 3000);
  }

  function handleBackupNow() {
    const now = new Date().toLocaleString("es-MX");
    setBackup((prev) => ({
      ...prev,
      lastBackup: now,
      status: "Correcto",
    }));

    // Guardar en localStorage
    const saved = localStorage.getItem("relojdae_settings");
    const config = saved ? JSON.parse(saved) : {};
    config.backup = { ...config.backup, lastBackup: now, status: "Correcto" };
    localStorage.setItem("relojdae_settings", JSON.stringify(config));
  }

  // Handlers de cambio
  function handleInstitutionChange(field, value) {
    setInstitution((prev) => ({ ...prev, [field]: value }));
  }

  function handleAttendanceChange(field, value) {
    setAttendance((prev) => ({ ...prev, [field]: value }));
  }

  function handleSecurityChange(field, value) {
    setSecurity((prev) => ({ ...prev, [field]: value }));
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Configuración"
        description="Parámetros institucionales, reglas de asistencia, seguridad y respaldos."
      />

      {/* Métricas */}
      <section className="metrics-grid three-columns">
        <article className="metric-card">
          <div className="metric-icon"><Building2 size={22} /></div>
          <div>
            <p>Institución</p>
            <strong className="metric-text">{institution.shortName}</strong>
            <span>{institution.parentInstitution}</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon"><CalendarClock size={22} /></div>
          <div>
            <p>Periodo activo</p>
            <strong className="metric-text">{attendance.activePeriod}</strong>
            <span>{attendance.periodStart} a {attendance.periodEnd}</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon"><DatabaseBackup size={22} /></div>
          <div>
            <p>Último respaldo</p>
            <strong className="metric-text">{backup.lastBackup}</strong>
            <span>{backup.status}</span>
          </div>
        </article>
      </section>

      {/* Datos institucionales */}
      <section className="panel-card">
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
            <input value={institution.parentInstitution} onChange={(e) => handleInstitutionChange("parentInstitution", e.target.value)} />
          </label>
          <label>
            Nombre del área
            <input value={institution.name} onChange={(e) => handleInstitutionChange("name", e.target.value)} />
          </label>
          <label>
            Nombre corto
            <input value={institution.shortName} onChange={(e) => handleInstitutionChange("shortName", e.target.value)} />
          </label>
          <label className="span-2">
            Pie de reporte
            <textarea rows="3" value={institution.reportFooter} onChange={(e) => handleInstitutionChange("reportFooter", e.target.value)} />
          </label>
        </div>
        <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <button className="primary-button" type="button" onClick={() => saveSection("institution")}>
            <Save size={17} /> Guardar datos institucionales
          </button>
          {savedSection === "institution" && <span style={{ color: "var(--color-success-text)", fontSize: "13px", fontWeight: 700 }}>✓ Guardado</span>}
        </div>
      </section>

      {/* Asistencia y periodo */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Asistencia y periodo</h3>
            <p>Periodo activo y reglas de puntualidad. Define cuántos minutos son retardo, falta, y cuántos puntos se asignan.</p>
          </div>
          <CalendarClock size={22} />
        </div>
        <div className="form-grid">
          <label>
            Periodo activo
            <input value={attendance.activePeriod} onChange={(e) => handleAttendanceChange("activePeriod", e.target.value)} />
          </label>
          <label>
            Fecha inicio
            <input type="date" value={attendance.periodStart} onChange={(e) => handleAttendanceChange("periodStart", e.target.value)} />
          </label>
          <label>
            Fecha fin
            <input type="date" value={attendance.periodEnd} onChange={(e) => handleAttendanceChange("periodEnd", e.target.value)} />
          </label>
          <label>
            Tolerancia puntual (min)
            <input type="number" min="0" value={attendance.toleranciaMinutos} onChange={(e) => handleAttendanceChange("toleranciaMinutos", Number(e.target.value))} />
          </label>
        </div>

        <div style={{ marginTop: "20px", padding: "16px", background: "var(--color-surface-soft)", borderRadius: "14px", border: "1px solid var(--color-border-soft)" }}>
          <h4 style={{ margin: "0 0 12px", fontSize: "15px" }}>Reglas de puntualidad</h4>
          <p style={{ fontSize: "13px", color: "var(--color-text-muted)", marginBottom: "14px" }}>
            Basado en la hora de entrada programada. Ejemplo: si entra a las 8:00 y tolerancia es 10 min, es puntual hasta las 8:10.
          </p>
          <div className="form-grid">
            <label>
              Puntual: 0 a {attendance.toleranciaMinutos} min
              <input type="number" min="0" value={attendance.toleranciaMinutos} onChange={(e) => handleAttendanceChange("toleranciaMinutos", Number(e.target.value))} />
              <span style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>0 puntos</span>
            </label>
            <label>
              Retardo menor: {attendance.retardoMenorDesde} a {attendance.retardoMenorHasta} min
              <div style={{ display: "flex", gap: "8px" }}>
                <input type="number" min="1" value={attendance.retardoMenorDesde} onChange={(e) => handleAttendanceChange("retardoMenorDesde", Number(e.target.value))} style={{ width: "70px" }} />
                <span style={{ alignSelf: "center" }}>a</span>
                <input type="number" min="1" value={attendance.retardoMenorHasta} onChange={(e) => handleAttendanceChange("retardoMenorHasta", Number(e.target.value))} style={{ width: "70px" }} />
              </div>
              <span style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>{attendance.puntosRetardoMenor} punto(s)</span>
            </label>
            <label>
              Retardo mayor: {attendance.retardoMayorDesde} a {attendance.retardoMayorHasta} min
              <div style={{ display: "flex", gap: "8px" }}>
                <input type="number" min="1" value={attendance.retardoMayorDesde} onChange={(e) => handleAttendanceChange("retardoMayorDesde", Number(e.target.value))} style={{ width: "70px" }} />
                <span style={{ alignSelf: "center" }}>a</span>
                <input type="number" min="1" value={attendance.retardoMayorHasta} onChange={(e) => handleAttendanceChange("retardoMayorHasta", Number(e.target.value))} style={{ width: "70px" }} />
              </div>
              <span style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>{attendance.puntosRetardoMayor} punto(s)</span>
            </label>
            <label>
              Falta: a partir de {attendance.faltaDesde} min
              <input type="number" min="1" value={attendance.faltaDesde} onChange={(e) => handleAttendanceChange("faltaDesde", Number(e.target.value))} />
              <span style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>Sin puntos (se cuenta como falta)</span>
            </label>
          </div>
        </div>

        <div style={{ marginTop: "16px", padding: "16px", background: "var(--color-surface-soft)", borderRadius: "14px", border: "1px solid var(--color-border-soft)" }}>
          <h4 style={{ margin: "0 0 12px", fontSize: "15px" }}>Reglas de acumulación de puntos</h4>
          <div className="form-grid">
            <label>
              Puntos por retardo menor
              <input type="number" min="0" value={attendance.puntosRetardoMenor} onChange={(e) => handleAttendanceChange("puntosRetardoMenor", Number(e.target.value))} />
            </label>
            <label>
              Puntos por retardo mayor
              <input type="number" min="0" value={attendance.puntosRetardoMayor} onChange={(e) => handleAttendanceChange("puntosRetardoMayor", Number(e.target.value))} />
            </label>
            <label>
              Puntos para 1 DO (Día Omisión)
              <input type="number" min="1" value={attendance.puntosDO} onChange={(e) => handleAttendanceChange("puntosDO", Number(e.target.value))} />
            </label>
            <label>
              DOs para revisión de baja
              <input type="number" min="1" value={attendance.dosParaRevision} onChange={(e) => handleAttendanceChange("dosParaRevision", Number(e.target.value))} />
            </label>
            <label>
              Faltas consecutivas para revisión de baja
              <input type="number" min="1" value={attendance.faltasConsecutivasRevision} onChange={(e) => handleAttendanceChange("faltasConsecutivasRevision", Number(e.target.value))} />
            </label>
          </div>
        </div>
        <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <button className="primary-button" type="button" onClick={() => saveSection("attendance")}>
            <Save size={17} /> Guardar reglas de asistencia
          </button>
          {savedSection === "attendance" && <span style={{ color: "var(--color-success-text)", fontSize: "13px", fontWeight: 700 }}>✓ Guardado</span>}
        </div>
      </section>

      {/* Seguridad */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Seguridad</h3>
            <p>Sesiones, contraseñas y bloqueo de usuarios.</p>
          </div>
          <LockKeyhole size={22} />
        </div>
        <div className="form-grid">
          <label>
            Tiempo de sesión (minutos)
            <input type="number" min="5" value={security.sessionTimeoutMinutes} onChange={(e) => handleSecurityChange("sessionTimeoutMinutes", Number(e.target.value))} />
            <span style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>Actualmente: {Math.floor(security.sessionTimeoutMinutes / 60)} horas {security.sessionTimeoutMinutes % 60} min</span>
          </label>
          <label>
            Intentos máximos de login
            <input type="number" min="1" max="20" value={security.maxLoginAttempts} onChange={(e) => handleSecurityChange("maxLoginAttempts", Number(e.target.value))} />
            <span style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>Después de {security.maxLoginAttempts} intentos fallidos se bloquea la cuenta</span>
          </label>
          <label>
            Longitud mínima de contraseña
            <input type="number" min="6" max="32" value={security.minPasswordLength} onChange={(e) => handleSecurityChange("minPasswordLength", Number(e.target.value))} />
          </label>
          <label>
            Bloquear tras intentos fallidos
            <select value={security.blockAfterFailedAttempts ? "true" : "false"} onChange={(e) => handleSecurityChange("blockAfterFailedAttempts", e.target.value === "true")}>
              <option value="true">Sí — Bloquear automáticamente</option>
              <option value="false">No — Solo registrar en auditoría</option>
            </select>
          </label>
        </div>
        <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <button className="primary-button" type="button" onClick={() => saveSection("security")}>
            <Save size={17} /> Guardar seguridad
          </button>
          {savedSection === "security" && <span style={{ color: "var(--color-success-text)", fontSize: "13px", fontWeight: 700 }}>✓ Guardado</span>}
        </div>
      </section>

      {/* Respaldos */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Respaldos</h3>
            <p>Estado de backups de la base de datos PostgreSQL.</p>
          </div>
          <DatabaseBackup size={22} />
        </div>
        <div className="form-grid">
          <label>
            Frecuencia programada
            <select value={backup.frequency} onChange={(e) => setBackup((prev) => ({ ...prev, frequency: e.target.value }))}>
              <option value="Diario">Diario (23:00)</option>
              <option value="Cada 12 horas">Cada 12 horas</option>
              <option value="Semanal">Semanal (Domingo 00:00)</option>
            </select>
          </label>
          <label>
            Retención
            <select value={backup.retention} onChange={(e) => setBackup((prev) => ({ ...prev, retention: e.target.value }))}>
              <option value="7 días">7 días</option>
              <option value="14 días">14 días</option>
              <option value="30 días">30 días</option>
              <option value="90 días">90 días</option>
            </select>
          </label>
          <label>
            Último respaldo
            <input value={backup.lastBackup} readOnly style={{ background: "var(--color-surface-soft)" }} />
          </label>
          <label>
            Estatus
            <input value={backup.status} readOnly style={{ background: "var(--color-surface-soft)" }} />
          </label>
        </div>
        <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <button className="primary-button" type="button" onClick={handleBackupNow}>
            <DatabaseBackup size={17} />
            Ejecutar respaldo ahora
          </button>
          <button className="secondary-button" type="button" onClick={() => saveSection("backup")}>
            <Save size={17} /> Guardar config respaldos
          </button>
          {savedSection === "backup" && <span style={{ color: "var(--color-success-text)", fontSize: "13px", fontWeight: 700 }}>✓ Guardado</span>}
        </div>
      </section>

      {/* Configuración de reportes / Logo */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Configuración de reportes</h3>
            <p>Logo institucional que aparece en los reportes PDF generados por el sistema.</p>
          </div>
          <ImageIcon size={22} />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", gap: "24px", alignItems: "start" }}>
          {/* Preview del logo */}
          <div style={{ textAlign: "center" }}>
            {logoPreviewUrl ? (
              <div style={{ border: "1px solid var(--color-border-soft)", borderRadius: "14px", padding: "12px", background: "white" }}>
                <img
                  src={logoPreviewUrl}
                  alt="Logo institucional"
                  style={{ maxWidth: "160px", maxHeight: "160px", objectFit: "contain" }}
                />
              </div>
            ) : (
              <div style={{ border: "2px dashed var(--color-border)", borderRadius: "14px", padding: "32px 12px", color: "var(--color-text-muted)", fontSize: "13px" }}>
                <ImageIcon size={32} style={{ marginBottom: "8px", opacity: 0.5 }} />
                <p style={{ margin: 0 }}>Sin logo</p>
              </div>
            )}

            {logoInfo?.has_logo && (
              <p style={{ marginTop: "8px", fontSize: "11px", color: "var(--color-text-muted)" }}>
                {logoInfo.filename} ({logoInfo.size_kb} KB)
              </p>
            )}
          </div>

          {/* Controles */}
          <div>
            <div className="form-grid" style={{ gridTemplateColumns: "1fr" }}>
              <label>
                Subir logo (JPG o PNG, máx 5 MB)
                <input
                  type="file"
                  accept=".jpg,.jpeg,.png"
                  onChange={handleLogoUpload}
                  disabled={logoUploading}
                  style={{ marginTop: "6px" }}
                />
              </label>
            </div>

            {logoError && <p style={{ color: "var(--color-danger-text)", fontSize: "13px", marginTop: "8px" }}>{logoError}</p>}
            {logoSuccess && <p style={{ color: "var(--color-success-text)", fontSize: "13px", marginTop: "8px" }}>{logoSuccess}</p>}

            <div style={{ marginTop: "16px", display: "flex", gap: "10px" }}>
              <label className="primary-button" style={{ cursor: logoUploading ? "not-allowed" : "pointer" }}>
                <Upload size={17} />
                {logoUploading ? "Subiendo..." : "Cambiar logo"}
                <input
                  type="file"
                  accept=".jpg,.jpeg,.png"
                  onChange={handleLogoUpload}
                  disabled={logoUploading}
                  style={{ display: "none" }}
                />
              </label>

              {logoInfo?.has_logo && (
                <button className="secondary-button" type="button" onClick={handleLogoDelete}>
                  <Trash2 size={17} />
                  Eliminar
                </button>
              )}
            </div>

            <p style={{ marginTop: "12px", fontSize: "12px", color: "var(--color-text-muted)", lineHeight: "1.5" }}>
              El logo aparecerá en el encabezado de todos los reportes PDF generados.
              Recomendación: imagen cuadrada o con fondo transparente (PNG).
            </p>
          </div>
        </div>
      </section>

      {/* Reglas globales */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Reglas globales del sistema</h3>
            <p>Parámetros operativos que afectan el comportamiento general.</p>
          </div>
          <ShieldCheck size={22} />
        </div>
        <div className="simple-table">
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
              <tr>
                <td><strong>Tolerancia de entrada</strong></td>
                <td>{attendance.toleranciaMinutos} minutos</td>
                <td>Asistencia</td>
                <td>Margen permitido posterior a la hora programada de entrada</td>
              </tr>
              <tr>
                <td><strong>Puntos → DO</strong></td>
                <td>{attendance.puntosDO} puntos = 1 DO</td>
                <td>Asistencia</td>
                <td>Cada {attendance.puntosDO} puntos acumulados genera un Día de Omisión</td>
              </tr>
              <tr>
                <td><strong>DOs → Revisión de baja</strong></td>
                <td>{attendance.dosParaRevision} DOs</td>
                <td>Asistencia</td>
                <td>Marcar empleado para revisión de baja al alcanzar {attendance.dosParaRevision} DOs</td>
              </tr>
              <tr>
                <td><strong>Faltas consecutivas</strong></td>
                <td>{attendance.faltasConsecutivasRevision} faltas</td>
                <td>Asistencia</td>
                <td>{attendance.faltasConsecutivasRevision} faltas seguidas = revisión de baja</td>
              </tr>
              <tr>
                <td><strong>Checadas crudas</strong></td>
                <td>Inmutables</td>
                <td>Auditoría</td>
                <td>Las marcaciones originales del reloj no se modifican ni eliminan</td>
              </tr>
              <tr>
                <td><strong>Duplicados sincronización</strong></td>
                <td>Ignorar</td>
                <td>Dispositivos</td>
                <td>Si la marcación ya existe en BD, no se inserta de nuevo</td>
              </tr>
              <tr>
                <td><strong>Tiempo de sesión</strong></td>
                <td>{security.sessionTimeoutMinutes} min ({Math.floor(security.sessionTimeoutMinutes / 60)}h)</td>
                <td>Seguridad</td>
                <td>Token JWT expira después de este tiempo</td>
              </tr>
              <tr>
                <td><strong>Bloqueo por intentos</strong></td>
                <td>{security.maxLoginAttempts} intentos</td>
                <td>Seguridad</td>
                <td>{security.blockAfterFailedAttempts ? "Se bloquea" : "Solo se registra"} tras fallos consecutivos</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default SettingsPage;
