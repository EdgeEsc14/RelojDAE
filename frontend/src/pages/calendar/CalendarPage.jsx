import { useEffect, useState } from "react";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Check,
  Plus,
  X,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import {
  getEventosRango,
  crearEvento,
  actualizarEvento,
  desactivarEvento,
} from "../../api/calendarioApi";

const TIPOS_EVENTO = [
  { value: "FESTIVO_OFICIAL", label: "Festivo oficial", color: "#dc2626" },
  { value: "DESCANSO_INSTITUCIONAL", label: "Descanso institucional", color: "#7c3aed" },
  { value: "DESCANSO_SINDICAL", label: "Descanso sindical", color: "#6366f1" },
  { value: "VACACIONES", label: "Vacaciones", color: "#0891b2" },
  { value: "INHABIL_ADMINISTRATIVO", label: "Inhábil administrativo", color: "#d97706" },
  { value: "SUSPENSION_LABORES", label: "Suspensión de labores", color: "#be185d" },
  { value: "LABORABLE_EXTRAORDINARIO", label: "Laborable extraordinario", color: "#16a34a" },
  { value: "OTRO", label: "Otro", color: "#6b7280" },
];

const TIPOS_RECURRENCIA = [
  { value: "FECHA_ESPECIFICA", label: "Fecha específica" },
  { value: "ANUAL_FIJA", label: "Anual fija (se repite cada año)" },
  { value: "PERIODO", label: "Periodo (rango de fechas)" },
];

function getEventColor(tipoEvento) {
  const tipo = TIPOS_EVENTO.find((t) => t.value === tipoEvento);
  return tipo ? tipo.color : "#6b7280";
}

function getEventLabel(tipoEvento) {
  const tipo = TIPOS_EVENTO.find((t) => t.value === tipoEvento);
  return tipo ? tipo.label : tipoEvento;
}

function getDaysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year, month) {
  const day = new Date(year, month, 1).getDay();
  return day === 0 ? 6 : day - 1; // Lunes = 0
}

const MONTH_NAMES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const DAY_NAMES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

function CalendarPage() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth());
  const [eventos, setEventos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDay, setSelectedDay] = useState(null);

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [formData, setFormData] = useState(getEmptyForm());
  const [formError, setFormError] = useState("");
  const [formLoading, setFormLoading] = useState(false);

  function getEmptyForm() {
    return {
      nombre: "",
      descripcion: "",
      tipo_evento: "FESTIVO_OFICIAL",
      tipo_recurrencia: "FECHA_ESPECIFICA",
      fecha_inicio: "",
      fecha_fin: "",
      mes: "",
      dia: "",
      afecta_asistencia: true,
      es_laborable: false,
      prioridad: 50,
    };
  }

  useEffect(() => {
    loadEventos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, month]);

  async function loadEventos() {
    setLoading(true);
    try {
      const fechaInicio = `${year}-${String(month + 1).padStart(2, "0")}-01`;
      const lastDay = getDaysInMonth(year, month);
      const fechaFin = `${year}-${String(month + 1).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;
      const data = await getEventosRango(fechaInicio, fechaFin);
      setEventos(data || []);
    } catch (err) {
      console.error("Error cargando eventos:", err.message);
      setEventos([]);
    } finally {
      setLoading(false);
    }
  }

  function prevMonth() {
    if (month === 0) {
      setMonth(11);
      setYear(year - 1);
    } else {
      setMonth(month - 1);
    }
    setSelectedDay(null);
  }

  function nextMonth() {
    if (month === 11) {
      setMonth(0);
      setYear(year + 1);
    } else {
      setMonth(month + 1);
    }
    setSelectedDay(null);
  }

  function getEventsForDay(dayNum) {
    return eventos.filter((ev) => {
      if (ev.tipo_recurrencia === "FECHA_ESPECIFICA" && ev.fecha_inicio) {
        const d = new Date(ev.fecha_inicio + "T00:00:00");
        return d.getFullYear() === year && d.getMonth() === month && d.getDate() === dayNum;
      }
      if (ev.tipo_recurrencia === "ANUAL_FIJA") {
        return ev.mes === month + 1 && ev.dia === dayNum;
      }
      if (ev.tipo_recurrencia === "PERIODO" && ev.fecha_inicio && ev.fecha_fin) {
        const checkDate = new Date(year, month, dayNum);
        const start = new Date(ev.fecha_inicio + "T00:00:00");
        const end = new Date(ev.fecha_fin + "T00:00:00");
        return checkDate >= start && checkDate <= end;
      }
      return false;
    });
  }

  function handleDayClick(dayNum) {
    setSelectedDay(dayNum === selectedDay ? null : dayNum);
  }

  function openCreateModal(dayNum) {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(dayNum).padStart(2, "0")}`;
    setEditingEvent(null);
    setFormData({
      ...getEmptyForm(),
      fecha_inicio: dateStr,
      mes: String(month + 1),
      dia: String(dayNum),
    });
    setFormError("");
    setShowModal(true);
  }

  function openEditModal(ev) {
    setEditingEvent(ev);
    setFormData({
      nombre: ev.nombre || "",
      descripcion: ev.descripcion || "",
      tipo_evento: ev.tipo_evento || "FESTIVO_OFICIAL",
      tipo_recurrencia: ev.tipo_recurrencia || "FECHA_ESPECIFICA",
      fecha_inicio: ev.fecha_inicio || "",
      fecha_fin: ev.fecha_fin || "",
      mes: ev.mes ? String(ev.mes) : "",
      dia: ev.dia ? String(ev.dia) : "",
      afecta_asistencia: ev.afecta_asistencia ?? true,
      es_laborable: ev.es_laborable ?? false,
      prioridad: ev.prioridad ?? 50,
    });
    setFormError("");
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setEditingEvent(null);
    setFormError("");
  }

  function handleChange(field, value) {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");
    setFormLoading(true);

    try {
      const payload = {
        nombre: formData.nombre,
        descripcion: formData.descripcion || null,
        tipo_evento: formData.tipo_evento,
        tipo_recurrencia: formData.tipo_recurrencia,
        afecta_asistencia: formData.afecta_asistencia,
        es_laborable: formData.es_laborable,
        prioridad: Number(formData.prioridad),
      };

      if (formData.tipo_recurrencia === "FECHA_ESPECIFICA") {
        if (!formData.fecha_inicio) { setFormError("La fecha es obligatoria."); setFormLoading(false); return; }
        payload.fecha_inicio = formData.fecha_inicio;
      } else if (formData.tipo_recurrencia === "ANUAL_FIJA") {
        if (!formData.mes || !formData.dia) { setFormError("Mes y día son obligatorios."); setFormLoading(false); return; }
        payload.mes = Number(formData.mes);
        payload.dia = Number(formData.dia);
      } else if (formData.tipo_recurrencia === "PERIODO") {
        if (!formData.fecha_inicio || !formData.fecha_fin) { setFormError("Fecha inicio y fin son obligatorias."); setFormLoading(false); return; }
        payload.fecha_inicio = formData.fecha_inicio;
        payload.fecha_fin = formData.fecha_fin;
      }

      if (!payload.nombre) { setFormError("El nombre es obligatorio."); setFormLoading(false); return; }

      if (editingEvent) {
        await actualizarEvento(editingEvent.id, payload);
      } else {
        await crearEvento(payload);
      }

      closeModal();
      loadEventos();
    } catch (err) {
      setFormError(err.message || "Error al guardar evento.");
    } finally {
      setFormLoading(false);
    }
  }

  async function handleDelete(ev) {
    if (!window.confirm(`¿Desactivar el evento "${ev.nombre}"?`)) return;
    try {
      await desactivarEvento(ev.id);
      loadEventos();
      setSelectedDay(null);
    } catch (err) {
      alert("Error: " + err.message);
    }
  }

  // Render calendar grid
  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);
  const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;
  const todayNum = today.getFullYear() === year && today.getMonth() === month ? today.getDate() : -1;

  const selectedDayEvents = selectedDay ? getEventsForDay(selectedDay) : [];

  return (
    <div className="page-stack">
      <PageHeader
        title="Calendario Laboral"
        description="Gestión de festivos, vacaciones, días inhábiles y excepciones laborales."
      >
        <div className="header-actions">
          <button className="primary-button" type="button" onClick={() => openCreateModal(todayNum > 0 ? todayNum : 1)}>
            <Plus size={17} />
            Nuevo evento
          </button>
        </div>
      </PageHeader>

      {/* Navegación de mes */}
      <section className="panel-card">
        <div className="calendar-nav">
          <button className="pagination-button" type="button" onClick={prevMonth}>
            <ChevronLeft size={20} />
          </button>

          <h2 className="calendar-month-title">
            {MONTH_NAMES[month]} {year}
          </h2>

          <button className="pagination-button" type="button" onClick={nextMonth}>
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Grid del calendario */}
        <div className="calendar-grid">
          {/* Header días */}
          {DAY_NAMES.map((name) => (
            <div className="calendar-day-header" key={name}>
              {name}
            </div>
          ))}

          {/* Celdas */}
          {Array.from({ length: totalCells }, (_, i) => {
            const dayNum = i - firstDay + 1;
            const isValidDay = dayNum >= 1 && dayNum <= daysInMonth;

            if (!isValidDay) {
              return <div className="calendar-cell empty" key={`empty-${i}`} />;
            }

            const dayEvents = getEventsForDay(dayNum);
            const isToday = dayNum === todayNum;
            const isSelected = dayNum === selectedDay;
            const isWeekend = (i % 7) >= 5;

            let cellClass = "calendar-cell";
            if (isToday) cellClass += " today";
            if (isSelected) cellClass += " selected";
            if (isWeekend) cellClass += " weekend";
            if (dayEvents.length > 0) cellClass += " has-events";

            return (
              <div
                className={cellClass}
                key={`day-${dayNum}`}
                onClick={() => handleDayClick(dayNum)}
              >
                <span className="calendar-day-number">{dayNum}</span>

                {dayEvents.length > 0 && (
                  <div className="calendar-event-dots">
                    {dayEvents.slice(0, 3).map((ev, idx) => (
                      <span
                        key={idx}
                        className="calendar-event-dot"
                        style={{ backgroundColor: getEventColor(ev.tipo_evento) }}
                        title={ev.nombre}
                      />
                    ))}
                    {dayEvents.length > 3 && (
                      <span className="calendar-event-more">+{dayEvents.length - 3}</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Leyenda */}
        <div className="calendar-legend">
          {TIPOS_EVENTO.map((tipo) => (
            <span key={tipo.value} className="calendar-legend-item">
              <i style={{ backgroundColor: tipo.color }} />
              {tipo.label}
            </span>
          ))}
        </div>
      </section>

      {/* Detalle del día seleccionado */}
      {selectedDay && (
        <section className="panel-card">
          <div className="panel-header">
            <div>
              <h3>{selectedDay} de {MONTH_NAMES[month]} {year}</h3>
              <p>{selectedDayEvents.length} evento(s) configurado(s)</p>
            </div>
            <button className="primary-button" type="button" onClick={() => openCreateModal(selectedDay)}>
              <Plus size={17} />
              Agregar evento
            </button>
          </div>

          {selectedDayEvents.length === 0 ? (
            <div className="empty-state">
              <Calendar size={32} />
              <p>Sin eventos para este día. Se considera laborable por defecto.</p>
            </div>
          ) : (
            <div className="calendar-event-list">
              {selectedDayEvents.map((ev) => (
                <div className="calendar-event-card" key={ev.id}>
                  <div
                    className="calendar-event-color-bar"
                    style={{ backgroundColor: getEventColor(ev.tipo_evento) }}
                  />
                  <div className="calendar-event-info">
                    <strong>{ev.nombre}</strong>
                    <div className="calendar-event-meta">
                      <span className="badge neutral">{getEventLabel(ev.tipo_evento)}</span>
                      <span className={ev.es_laborable ? "badge success" : "badge danger"}>
                        {ev.es_laborable ? "Laborable" : "No laborable"}
                      </span>
                      {ev.afecta_asistencia && (
                        <span className="badge warning">Afecta asistencia</span>
                      )}
                    </div>
                    {ev.descripcion && <p>{ev.descripcion}</p>}
                  </div>
                  <div className="calendar-event-actions">
                    <button className="table-action" type="button" onClick={() => openEditModal(ev)}>
                      Editar
                    </button>
                    <button className="table-action danger" type="button" onClick={() => handleDelete(ev)}>
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Modal crear/editar */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingEvent ? "Editar evento" : "Nuevo evento"}</h3>
              <button className="modal-close" type="button" onClick={closeModal}>
                <X size={20} />
              </button>
            </div>

            <form className="modal-body" onSubmit={handleSubmit}>
              {formError && <div className="form-error-message">{formError}</div>}

              <div className="form-field">
                <label htmlFor="ev-nombre">Nombre *</label>
                <input
                  id="ev-nombre"
                  type="text"
                  required
                  placeholder="Ej: Día de la Independencia"
                  value={formData.nombre}
                  onChange={(e) => handleChange("nombre", e.target.value)}
                />
              </div>

              <div className="form-field">
                <label htmlFor="ev-desc">Descripción</label>
                <input
                  id="ev-desc"
                  type="text"
                  placeholder="Descripción opcional"
                  value={formData.descripcion}
                  onChange={(e) => handleChange("descripcion", e.target.value)}
                />
              </div>

              <div className="form-field">
                <label htmlFor="ev-tipo">Tipo de evento *</label>
                <select
                  id="ev-tipo"
                  value={formData.tipo_evento}
                  onChange={(e) => handleChange("tipo_evento", e.target.value)}
                >
                  {TIPOS_EVENTO.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label htmlFor="ev-recurrencia">Recurrencia *</label>
                <select
                  id="ev-recurrencia"
                  value={formData.tipo_recurrencia}
                  onChange={(e) => handleChange("tipo_recurrencia", e.target.value)}
                >
                  {TIPOS_RECURRENCIA.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              {formData.tipo_recurrencia === "FECHA_ESPECIFICA" && (
                <div className="form-field">
                  <label htmlFor="ev-fecha">Fecha *</label>
                  <input
                    id="ev-fecha"
                    type="date"
                    required
                    value={formData.fecha_inicio}
                    onChange={(e) => handleChange("fecha_inicio", e.target.value)}
                  />
                </div>
              )}

              {formData.tipo_recurrencia === "ANUAL_FIJA" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div className="form-field">
                    <label htmlFor="ev-mes">Mes *</label>
                    <select
                      id="ev-mes"
                      required
                      value={formData.mes}
                      onChange={(e) => handleChange("mes", e.target.value)}
                    >
                      <option value="">Seleccionar...</option>
                      {MONTH_NAMES.map((name, idx) => (
                        <option key={idx} value={idx + 1}>{name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-field">
                    <label htmlFor="ev-dia">Día *</label>
                    <input
                      id="ev-dia"
                      type="number"
                      required
                      min={1}
                      max={31}
                      value={formData.dia}
                      onChange={(e) => handleChange("dia", e.target.value)}
                    />
                  </div>
                </div>
              )}

              {formData.tipo_recurrencia === "PERIODO" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div className="form-field">
                    <label htmlFor="ev-fi">Fecha inicio *</label>
                    <input
                      id="ev-fi"
                      type="date"
                      required
                      value={formData.fecha_inicio}
                      onChange={(e) => handleChange("fecha_inicio", e.target.value)}
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="ev-ff">Fecha fin *</label>
                    <input
                      id="ev-ff"
                      type="date"
                      required
                      value={formData.fecha_fin}
                      onChange={(e) => handleChange("fecha_fin", e.target.value)}
                    />
                  </div>
                </div>
              )}

              <div className="form-field">
                <label htmlFor="ev-prioridad">Prioridad (1=máxima, 100=mínima)</label>
                <input
                  id="ev-prioridad"
                  type="number"
                  min={1}
                  max={100}
                  value={formData.prioridad}
                  onChange={(e) => handleChange("prioridad", e.target.value)}
                />
              </div>

              <div className="form-field form-checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.afecta_asistencia}
                    onChange={(e) => handleChange("afecta_asistencia", e.target.checked)}
                  />
                  Afecta control de asistencia
                </label>
              </div>

              <div className="form-field form-checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.es_laborable}
                    onChange={(e) => handleChange("es_laborable", e.target.checked)}
                  />
                  Es día laborable (marcar para excepciones como LABORABLE_EXTRAORDINARIO)
                </label>
              </div>

              <div className="modal-footer">
                <button className="secondary-button" type="button" onClick={closeModal} disabled={formLoading}>
                  Cancelar
                </button>
                <button className="primary-button" type="submit" disabled={formLoading}>
                  {formLoading ? "Guardando..." : (
                    <>
                      <Check size={17} />
                      {editingEvent ? "Guardar cambios" : "Crear evento"}
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

export default CalendarPage;
