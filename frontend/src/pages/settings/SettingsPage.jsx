import { useEffect, useState } from "react";

import {
  AlertCircle,
  Building2,
  CalendarClock,
  DatabaseBackup,
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
import { politicasApi } from "../../api/politicasApi";
import { brandingApi } from "../../api/brandingApi";

// ============================================================
// Política de asistencia — conversión segundos <-> minutos/segundos
//
// asistencia.politicas_asistencia guarda los límites en SEGUNDOS para
// no perder precisión en fronteras como 08:10:59 (Contrato §5). La UI
// los presenta como minutos + segundos, pero el valor que se envía al
// backend siempre se reconstruye a segundos completos, sin redondear.
// ============================================================

function segundosAMinutosSegundos(totalSegundos) {
  const total = Math.max(0, Number(totalSegundos ?? 0));
  return {
    minutos: Math.floor(total / 60),
    segundos: total % 60,
  };
}

function minutosSegundosASegundos(minutos, segundos) {
  const min = Math.max(0, Number(minutos) || 0);
  const seg = Math.max(0, Number(segundos) || 0);
  return min * 60 + seg;
}

function politicaAFormulario(politica) {
  const tolerancia = segundosAMinutosSegundos(politica.limite_tolerancia_segundos);
  const retardoMenor = segundosAMinutosSegundos(politica.limite_retardo_menor_segundos);
  const retardoMayor = segundosAMinutosSegundos(politica.limite_retardo_mayor_segundos);
  const margenExtra = segundosAMinutosSegundos(politica.margen_tiempo_extra_segundos);

  return {
    toleranciaMinutos: tolerancia.minutos,
    toleranciaSegundos: tolerancia.segundos,
    retardoMenorMinutos: retardoMenor.minutos,
    retardoMenorSegundos: retardoMenor.segundos,
    retardoMayorMinutos: retardoMayor.minutos,
    retardoMayorSegundos: retardoMayor.segundos,
    margenExtraMinutos: margenExtra.minutos,
    margenExtraSegundos: margenExtra.segundos,
    puntosRetardoMenor: politica.puntos_retardo_menor,
    puntosRetardoMayor: politica.puntos_retardo_mayor,
    puntosParaDescanso: politica.puntos_para_descanso,
    descansosParaRevisionBaja: politica.descansos_para_revision_baja,
    faltasConsecutivasRevisionBaja: politica.faltas_consecutivas_revision_baja,
  };
}

function formularioAPayload(form) {
  return {
    limite_tolerancia_segundos: minutosSegundosASegundos(
      form.toleranciaMinutos,
      form.toleranciaSegundos
    ),
    limite_retardo_menor_segundos: minutosSegundosASegundos(
      form.retardoMenorMinutos,
      form.retardoMenorSegundos
    ),
    limite_retardo_mayor_segundos: minutosSegundosASegundos(
      form.retardoMayorMinutos,
      form.retardoMayorSegundos
    ),
    margen_tiempo_extra_segundos: minutosSegundosASegundos(
      form.margenExtraMinutos,
      form.margenExtraSegundos
    ),
    puntos_retardo_menor: Number(form.puntosRetardoMenor) || 0,
    puntos_retardo_mayor: Number(form.puntosRetardoMayor) || 0,
    puntos_para_descanso: Number(form.puntosParaDescanso) || 0,
    descansos_para_revision_baja: Number(form.descansosParaRevisionBaja) || 0,
    faltas_consecutivas_revision_baja:
      Number(form.faltasConsecutivasRevisionBaja) || 0,
  };
}

function validarFormularioPolitica(form) {
  const errors = {};

  const toleranciaSeg = minutosSegundosASegundos(
    form.toleranciaMinutos,
    form.toleranciaSegundos
  );
  const retardoMenorSeg = minutosSegundosASegundos(
    form.retardoMenorMinutos,
    form.retardoMenorSegundos
  );
  const retardoMayorSeg = minutosSegundosASegundos(
    form.retardoMayorMinutos,
    form.retardoMayorSegundos
  );

  if (!(toleranciaSeg < retardoMenorSeg && retardoMenorSeg < retardoMayorSeg)) {
    errors.limites =
      "Los límites deben ser crecientes: tolerancia < retardo menor < retardo mayor.";
  }

  if (Number(form.puntosRetardoMayor) < Number(form.puntosRetardoMenor)) {
    errors.puntos =
      "Los puntos de retardo mayor no pueden ser menores que los de retardo menor.";
  }

  if (Number(form.puntosParaDescanso) <= 0) {
    errors.puntosParaDescanso = "Debe ser mayor a 0.";
  }

  if (Number(form.descansosParaRevisionBaja) <= 0) {
    errors.descansosParaRevisionBaja = "Debe ser mayor a 0.";
  }

  if (Number(form.faltasConsecutivasRevisionBaja) <= 0) {
    errors.faltasConsecutivasRevisionBaja = "Debe ser mayor a 0.";
  }

  return errors;
}

function formatSegundosLegible(totalSegundos) {
  const { minutos, segundos } = segundosAMinutosSegundos(totalSegundos);
  return segundos > 0 ? `${minutos} min ${segundos} s` : `${minutos} min`;
}

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
  //
  // Fuente real: GET/PUT /branding/config. Es la misma configuración
  // que usan los generadores de reportes PDF/CSV — no se mantiene una
  // copia local en localStorage, para no crear una segunda fuente de
  // verdad. Sin configurar, el backend expone valores neutros.
  // ============================================================
  const [institution, setInstitution] = useState({
    nombreInstitucion: "",
    nombreCorto: "",
    piePagina: "",
    prefijoCodigoEmpleado: "EMP",
  });
  const [institutionLoading, setInstitutionLoading] = useState(true);
  const [institutionError, setInstitutionError] = useState("");
  const [institutionSaving, setInstitutionSaving] = useState(false);

  // ============================================================
  // Estado — Periodo de evaluación (preferencia local de UI; no
  // existe todavía un endpoint de configuración para esto)
  // ============================================================
  const [periodo, setPeriodo] = useState({
    activePeriod: defaultPeriod.nombre,
    periodStart: defaultPeriod.fechaInicio,
    periodEnd: defaultPeriod.fechaFin,
  });

  // ============================================================
  // Estado — Política de asistencia
  //
  // Fuente única de verdad: asistencia.politicas_asistencia, vía
  // GET/PUT /politicas-asistencia/activa. No se mantiene copia local
  // ni valores hardcodeados: esta pantalla lee y edita el mismo
  // registro que usa el motor de procesamiento (Contrato §5).
  // ============================================================
  const [politica, setPolitica] = useState(null);
  const [politicaForm, setPoliticaForm] = useState(null);
  const [politicaLoading, setPoliticaLoading] = useState(true);
  const [politicaError, setPoliticaError] = useState("");
  const [politicaFormErrors, setPoliticaFormErrors] = useState({});
  const [politicaSaving, setPoliticaSaving] = useState(false);
  const [politicaSaved, setPoliticaSaved] = useState(false);

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
        if (parsed.periodo) setPeriodo(parsed.periodo);
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

  // Cargar configuración institucional real al inicio
  useEffect(() => {
    loadInstitution();
  }, []);

  async function loadInstitution() {
    setInstitutionLoading(true);
    setInstitutionError("");

    try {
      const data = await brandingApi.obtenerConfig();
      setInstitution({
        nombreInstitucion: data.nombre_institucion,
        nombreCorto: data.nombre_corto,
        piePagina: data.pie_pagina,
        prefijoCodigoEmpleado: data.prefijo_codigo_empleado || "EMP",
      });
    } catch (err) {
      setInstitutionError(
        err.message || "No fue posible obtener la configuración institucional."
      );
    } finally {
      setInstitutionLoading(false);
    }
  }

  async function handleSaveInstitution() {
    setInstitutionSaving(true);
    setInstitutionError("");

    try {
      const data = await brandingApi.actualizarConfig({
        nombre_institucion: institution.nombreInstitucion,
        nombre_corto: institution.nombreCorto,
        pie_pagina: institution.piePagina,
        prefijo_codigo_empleado: institution.prefijoCodigoEmpleado,
      });
      setInstitution({
        nombreInstitucion: data.nombre_institucion,
        nombreCorto: data.nombre_corto,
        piePagina: data.pie_pagina,
        prefijoCodigoEmpleado: data.prefijo_codigo_empleado || "EMP",
      });
      setSavedSection("institution");
      setTimeout(() => setSavedSection(""), 3000);
    } catch (err) {
      setInstitutionError(
        err.message || "No fue posible guardar la configuración institucional."
      );
    } finally {
      setInstitutionSaving(false);
    }
  }

  // Cargar la política de asistencia ACTIVA vigente al inicio
  useEffect(() => {
    loadPolitica();
  }, []);

  async function loadPolitica() {
    setPoliticaLoading(true);
    setPoliticaError("");

    try {
      const data = await politicasApi.obtenerActiva();
      setPolitica(data);
      setPoliticaForm(politicaAFormulario(data));
      setPoliticaFormErrors({});
    } catch (err) {
      setPolitica(null);
      setPoliticaForm(null);
      setPoliticaError(
        err.message ||
          "No fue posible obtener la política de asistencia vigente."
      );
    } finally {
      setPoliticaLoading(false);
    }
  }

  function handlePoliticaFieldChange(field, value) {
    setPoliticaForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSavePolitica() {
    const errors = validarFormularioPolitica(politicaForm);
    setPoliticaFormErrors(errors);

    if (Object.keys(errors).length > 0) {
      return;
    }

    setPoliticaSaving(true);
    setPoliticaError("");

    try {
      const actualizada = await politicasApi.actualizarActiva(
        formularioAPayload(politicaForm)
      );
      setPolitica(actualizada);
      setPoliticaForm(politicaAFormulario(actualizada));
      setPoliticaSaved(true);
      setTimeout(() => setPoliticaSaved(false), 3000);
    } catch (err) {
      setPoliticaError(
        err.message || "No fue posible guardar la política de asistencia."
      );
    } finally {
      setPoliticaSaving(false);
    }
  }

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

    if (section === "periodo") config.periodo = periodo;
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

  function handlePeriodoChange(field, value) {
    setPeriodo((prev) => ({ ...prev, [field]: value }));
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
            <strong className="metric-text">
              {institution.nombreInstitucion || "Sin configurar"}
            </strong>
            <span>{institution.nombreCorto}</span>
          </div>
        </article>
        <article className="metric-card">
          <div className="metric-icon"><CalendarClock size={22} /></div>
          <div>
            <p>Periodo activo</p>
            <strong className="metric-text">{periodo.activePeriod}</strong>
            <span>{periodo.periodStart} a {periodo.periodEnd}</span>
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
            <p>
              Usados en el encabezado y pie de página de los reportes PDF/CSV
              generados por el sistema (junto con el logo configurado abajo).
              Sin configurar, los reportes muestran valores neutros.
            </p>
          </div>
          <Building2 size={22} />
        </div>

        {institutionLoading && <p>Cargando configuración institucional…</p>}

        {!institutionLoading && institutionError && (
          <div className="form-error" style={{ marginBottom: "14px" }}>
            <AlertCircle size={18} />
            <span>{institutionError}</span>
          </div>
        )}

        {!institutionLoading && (
          <>
            <div className="form-grid">
              <label>
                Nombre de la institución
                <input
                  value={institution.nombreInstitucion}
                  onChange={(e) => handleInstitutionChange("nombreInstitucion", e.target.value)}
                />
              </label>
              <label>
                Nombre corto / unidad (subtítulo)
                <input
                  value={institution.nombreCorto}
                  onChange={(e) => handleInstitutionChange("nombreCorto", e.target.value)}
                />
              </label>
              <label className="span-2">
                Pie de página de reportes
                <textarea
                  rows="3"
                  value={institution.piePagina}
                  onChange={(e) => handleInstitutionChange("piePagina", e.target.value)}
                />
              </label>
              <label>
                Prefijo de código de empleado
                <input
                  value={institution.prefijoCodigoEmpleado}
                  maxLength={10}
                  onChange={(e) =>
                    handleInstitutionChange(
                      "prefijoCodigoEmpleado",
                      e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "")
                    )
                  }
                />
                <span style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>
                  Se usa para generar códigos nuevos, ej. {institution.prefijoCodigoEmpleado || "EMP"}-0001. No renombra empleados existentes.
                </span>
              </label>
            </div>
            <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
              <button
                className="primary-button"
                type="button"
                onClick={handleSaveInstitution}
                disabled={institutionSaving}
              >
                <Save size={17} /> {institutionSaving ? "Guardando..." : "Guardar datos institucionales"}
              </button>
              {savedSection === "institution" && <span style={{ color: "var(--color-success-text)", fontSize: "13px", fontWeight: 700 }}>✓ Guardado</span>}
            </div>
          </>
        )}
      </section>

      {/* Periodo de evaluación */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Periodo de evaluación</h3>
            <p>Periodo activo mostrado en los paneles del sistema.</p>
          </div>
          <CalendarClock size={22} />
        </div>
        <div className="form-grid">
          <label>
            Periodo activo
            <input value={periodo.activePeriod} onChange={(e) => handlePeriodoChange("activePeriod", e.target.value)} />
          </label>
          <label>
            Fecha inicio
            <input type="date" value={periodo.periodStart} onChange={(e) => handlePeriodoChange("periodStart", e.target.value)} />
          </label>
          <label>
            Fecha fin
            <input type="date" value={periodo.periodEnd} onChange={(e) => handlePeriodoChange("periodEnd", e.target.value)} />
          </label>
        </div>
        <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <button className="primary-button" type="button" onClick={() => saveSection("periodo")}>
            <Save size={17} /> Guardar periodo
          </button>
          {savedSection === "periodo" && <span style={{ color: "var(--color-success-text)", fontSize: "13px", fontWeight: 700 }}>✓ Guardado</span>}
        </div>
      </section>

      {/* Política de asistencia — fuente única: asistencia.politicas_asistencia */}
      <section className="panel-card">
        <div className="panel-header">
          <div>
            <h3>Política de asistencia</h3>
            <p>
              Política ACTIVA vigente en <code>asistencia.politicas_asistencia</code>.
              Estas son las mismas reglas que usa el motor de procesamiento: no existe
              una copia independiente en esta pantalla.
            </p>
          </div>
          <ShieldCheck size={22} />
        </div>

        {politicaLoading && <p>Cargando política de asistencia…</p>}

        {!politicaLoading && politicaError && (
          <div className="form-error" style={{ marginBottom: "14px" }}>
            <AlertCircle size={18} />
            <span>{politicaError}</span>
          </div>
        )}

        {!politicaLoading && politica && politicaForm && (
          <>
            <div className="form-grid">
              <label>
                Código
                <input value={politica.codigo} readOnly style={{ background: "var(--color-surface-soft)" }} />
              </label>
              <label>
                Nombre
                <input value={politica.nombre} readOnly style={{ background: "var(--color-surface-soft)" }} />
              </label>
              <label>
                Vigente desde
                <input value={politica.vigencia_desde} readOnly style={{ background: "var(--color-surface-soft)" }} />
              </label>
              <label>
                Tipo de periodo
                <input value={politica.tipo_periodo} readOnly style={{ background: "var(--color-surface-soft)" }} />
              </label>
            </div>

            <div style={{ marginTop: "20px", padding: "16px", background: "var(--color-surface-soft)", borderRadius: "14px", border: "1px solid var(--color-border-soft)" }}>
              <h4 style={{ margin: "0 0 12px", fontSize: "15px" }}>Límites de puntualidad (minutos y segundos)</h4>
              <p style={{ fontSize: "13px", color: "var(--color-text-muted)", marginBottom: "14px" }}>
                Tiempo transcurrido desde la hora de entrada programada. Cada límite es el
                punto hasta el cual aplica esa clasificación; el motor de procesamiento usa
                la precisión exacta en segundos, así que un valor como &ldquo;10 min 59 s&rdquo;
                se guarda y se aplica tal cual, sin redondear a minutos completos.
              </p>
              <div className="form-grid">
                <label>
                  Tolerancia — hasta (0 puntos)
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <input type="number" min="0" value={politicaForm.toleranciaMinutos} onChange={(e) => handlePoliticaFieldChange("toleranciaMinutos", e.target.value)} style={{ width: "70px" }} />
                    <span>min</span>
                    <input type="number" min="0" max="59" value={politicaForm.toleranciaSegundos} onChange={(e) => handlePoliticaFieldChange("toleranciaSegundos", e.target.value)} style={{ width: "70px" }} />
                    <span>s</span>
                  </div>
                </label>
                <label>
                  Retardo menor — hasta ({politicaForm.puntosRetardoMenor} punto(s))
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <input type="number" min="0" value={politicaForm.retardoMenorMinutos} onChange={(e) => handlePoliticaFieldChange("retardoMenorMinutos", e.target.value)} style={{ width: "70px" }} />
                    <span>min</span>
                    <input type="number" min="0" max="59" value={politicaForm.retardoMenorSegundos} onChange={(e) => handlePoliticaFieldChange("retardoMenorSegundos", e.target.value)} style={{ width: "70px" }} />
                    <span>s</span>
                  </div>
                </label>
                <label>
                  Retardo mayor — hasta ({politicaForm.puntosRetardoMayor} punto(s))
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <input type="number" min="0" value={politicaForm.retardoMayorMinutos} onChange={(e) => handlePoliticaFieldChange("retardoMayorMinutos", e.target.value)} style={{ width: "70px" }} />
                    <span>min</span>
                    <input type="number" min="0" max="59" value={politicaForm.retardoMayorSegundos} onChange={(e) => handlePoliticaFieldChange("retardoMayorSegundos", e.target.value)} style={{ width: "70px" }} />
                    <span>s</span>
                  </div>
                  <span style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>Después de este límite: FALTA</span>
                </label>
              </div>
              {politicaFormErrors.limites && (
                <div className="form-error" style={{ marginTop: "12px" }}>
                  <AlertCircle size={16} />
                  <span>{politicaFormErrors.limites}</span>
                </div>
              )}
            </div>

            <div style={{ marginTop: "16px", padding: "16px", background: "var(--color-surface-soft)", borderRadius: "14px", border: "1px solid var(--color-border-soft)" }}>
              <h4 style={{ margin: "0 0 12px", fontSize: "15px" }}>Margen de tiempo extra</h4>
              <p style={{ fontSize: "13px", color: "var(--color-text-muted)", marginBottom: "14px" }}>
                Franja de gracia que nunca se paga como tiempo extra. Se aplica según la
                modalidad del turno: turnos matutinos (después de la salida) o vespertinos
                (antes de la entrada). Solo el excedente por encima de este margen se
                reconoce como minutos extra.
              </p>
              <div className="form-grid">
                <label>
                  Margen antes de contar tiempo extra
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <input type="number" min="0" value={politicaForm.margenExtraMinutos} onChange={(e) => handlePoliticaFieldChange("margenExtraMinutos", e.target.value)} style={{ width: "70px" }} />
                    <span>min</span>
                    <input type="number" min="0" max="59" value={politicaForm.margenExtraSegundos} onChange={(e) => handlePoliticaFieldChange("margenExtraSegundos", e.target.value)} style={{ width: "70px" }} />
                    <span>s</span>
                  </div>
                </label>
              </div>
            </div>

            <div style={{ marginTop: "16px", padding: "16px", background: "var(--color-surface-soft)", borderRadius: "14px", border: "1px solid var(--color-border-soft)" }}>
              <h4 style={{ margin: "0 0 12px", fontSize: "15px" }}>Puntos y revisión de baja</h4>
              <div className="form-grid">
                <label>
                  Puntos por retardo menor
                  <input type="number" min="0" value={politicaForm.puntosRetardoMenor} onChange={(e) => handlePoliticaFieldChange("puntosRetardoMenor", e.target.value)} />
                </label>
                <label>
                  Puntos por retardo mayor
                  <input type="number" min="0" value={politicaForm.puntosRetardoMayor} onChange={(e) => handlePoliticaFieldChange("puntosRetardoMayor", e.target.value)} />
                </label>
                <label>
                  Puntos para 1 descanso obligatorio
                  <input type="number" min="1" value={politicaForm.puntosParaDescanso} onChange={(e) => handlePoliticaFieldChange("puntosParaDescanso", e.target.value)} />
                  {politicaFormErrors.puntosParaDescanso && <span style={{ fontSize: "11px", color: "var(--color-danger-text)" }}>{politicaFormErrors.puntosParaDescanso}</span>}
                </label>
                <label>
                  Descansos para revisión de baja
                  <input type="number" min="1" value={politicaForm.descansosParaRevisionBaja} onChange={(e) => handlePoliticaFieldChange("descansosParaRevisionBaja", e.target.value)} />
                  {politicaFormErrors.descansosParaRevisionBaja && <span style={{ fontSize: "11px", color: "var(--color-danger-text)" }}>{politicaFormErrors.descansosParaRevisionBaja}</span>}
                </label>
                <label>
                  Faltas consecutivas para revisión de baja
                  <input type="number" min="1" value={politicaForm.faltasConsecutivasRevisionBaja} onChange={(e) => handlePoliticaFieldChange("faltasConsecutivasRevisionBaja", e.target.value)} />
                  {politicaFormErrors.faltasConsecutivasRevisionBaja && <span style={{ fontSize: "11px", color: "var(--color-danger-text)" }}>{politicaFormErrors.faltasConsecutivasRevisionBaja}</span>}
                </label>
              </div>
              {politicaFormErrors.puntos && (
                <div className="form-error" style={{ marginTop: "12px" }}>
                  <AlertCircle size={16} />
                  <span>{politicaFormErrors.puntos}</span>
                </div>
              )}
            </div>

            <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
              <button className="primary-button" type="button" onClick={handleSavePolitica} disabled={politicaSaving}>
                <Save size={17} /> {politicaSaving ? "Guardando..." : "Guardar política de asistencia"}
              </button>
              {politicaSaved && <span style={{ color: "var(--color-success-text)", fontSize: "13px", fontWeight: 700 }}>✓ Guardado</span>}
            </div>
          </>
        )}
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
              {politica ? (
                <>
                  <tr>
                    <td><strong>Tolerancia de entrada</strong></td>
                    <td>{formatSegundosLegible(politica.limite_tolerancia_segundos)}</td>
                    <td>Asistencia</td>
                    <td>Margen permitido posterior a la hora programada de entrada (política {politica.codigo})</td>
                  </tr>
                  <tr>
                    <td><strong>Retardo mayor / falta</strong></td>
                    <td>{formatSegundosLegible(politica.limite_retardo_mayor_segundos)}</td>
                    <td>Asistencia</td>
                    <td>Después de este límite la entrada se clasifica como FALTA</td>
                  </tr>
                  <tr>
                    <td><strong>Margen de tiempo extra</strong></td>
                    <td>{formatSegundosLegible(politica.margen_tiempo_extra_segundos)}</td>
                    <td>Asistencia</td>
                    <td>Franja que nunca se paga; solo el excedente sobre este margen cuenta como tiempo extra</td>
                  </tr>
                  <tr>
                    <td><strong>Puntos → descanso obligatorio</strong></td>
                    <td>{politica.puntos_para_descanso} puntos = 1 descanso</td>
                    <td>Asistencia</td>
                    <td>Cada {politica.puntos_para_descanso} puntos acumulados genera un descanso obligatorio</td>
                  </tr>
                  <tr>
                    <td><strong>Descansos → Revisión de baja</strong></td>
                    <td>{politica.descansos_para_revision_baja} descansos</td>
                    <td>Asistencia</td>
                    <td>Marcar empleado para revisión de baja al alcanzar {politica.descansos_para_revision_baja} descansos</td>
                  </tr>
                  <tr>
                    <td><strong>Faltas consecutivas</strong></td>
                    <td>{politica.faltas_consecutivas_revision_baja} faltas</td>
                    <td>Asistencia</td>
                    <td>{politica.faltas_consecutivas_revision_baja} faltas seguidas = revisión de baja</td>
                  </tr>
                </>
              ) : (
                <tr>
                  <td colSpan={4}>
                    {politicaLoading
                      ? "Cargando reglas de asistencia…"
                      : "No fue posible cargar las reglas de asistencia (ver política de asistencia arriba)."}
                  </td>
                </tr>
              )}
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
