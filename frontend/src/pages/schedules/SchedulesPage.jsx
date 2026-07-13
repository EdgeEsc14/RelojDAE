import { useEffect, useMemo, useState } from "react";
import {
  CalendarClock,
  CheckCircle2,
  Clock,
  Plus,
  Search,
  Settings2,
  Users,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { horariosApi } from "../../api/horariosApi";

const TURNOS_DISPONIBLES = [
  {
    id: 1,
    codigo: "MATUTINO",
    nombre: "Turno matutino",
    descripcion: "Jornada de 7 horas.",
  },
  {
    id: 2,
    codigo: "VESPERTINO",
    nombre: "Turno vespertino",
    descripcion: "Jornada de 6 horas.",
  },
];

const INITIAL_FORM = {
  codigo: "",
  nombre: "",
  descripcion: "",
  tipo_turno_id: "1",
  hora_entrada: "09:00",
  hora_salida: "16:00",
  tolerancia_entrada_minutos: 10,
  descanso_minutos: 0,
  permite_tiempo_extra: true,
  activo: true,
};

function getStatusClass(activo) {
  return activo ? "badge success" : "badge neutral";
}

function formatBoolean(value) {
  return value ? "Sí" : "No";
}

function formatMinutes(minutes) {
  const safeMinutes = Number(minutes ?? 0);

  if (safeMinutes < 60) {
    return `${safeMinutes} min`;
  }

  const hours = Math.floor(safeMinutes / 60);
  const remainingMinutes = safeMinutes % 60;

  if (remainingMinutes === 0) {
    return `${hours} h`;
  }

  return `${hours} h ${remainingMinutes} min`;
}

function formatTime(value) {
  if (!value) return "—";

  return String(value).slice(0, 5);
}

function normalizeCode(value) {
  return String(value ?? "")
    .trim()
    .toUpperCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^A-Z0-9]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_|_$/g, "");
}

function validateForm(form) {
  const errors = {};

  if (!String(form.codigo).trim()) {
    errors.codigo = "Captura un código.";
  }

  if (!String(form.nombre).trim()) {
    errors.nombre = "Captura el nombre del horario.";
  }

  if (!form.tipo_turno_id) {
    errors.tipo_turno_id = "Selecciona un tipo de turno.";
  }

  if (Number(form.tolerancia_entrada_minutos) < 0) {
    errors.tolerancia_entrada_minutos =
      "La tolerancia no puede ser negativa.";
  }

  if (Number(form.descanso_minutos) < 0) {
    errors.descanso_minutos =
      "El descanso no puede ser negativo.";
  }
  if (!form.hora_entrada) {
  errors.hora_entrada = "Captura la hora de entrada.";
}

  if (!form.hora_salida) {
    errors.hora_salida = "Captura la hora de salida.";
  }

  if (
    form.hora_entrada &&
    form.hora_salida &&
    form.hora_entrada === form.hora_salida
  ) {
    errors.hora_salida =
      "La hora de salida debe ser diferente a la entrada.";
  }
  return errors;
}

function mapHorarioPayload(form) {
  return {
    codigo: normalizeCode(form.codigo),
    nombre: String(form.nombre).trim(),
    descripcion:
      String(form.descripcion ?? "").trim() || null,
    tipo_turno_id: Number(form.tipo_turno_id),

    hora_entrada:
      form.hora_entrada.length === 5
        ? `${form.hora_entrada}:00`
        : form.hora_entrada,

    hora_salida:
      form.hora_salida.length === 5
        ? `${form.hora_salida}:00`
        : form.hora_salida,

    tolerancia_entrada_minutos: Number(
      form.tolerancia_entrada_minutos,
    ),
    descanso_minutos: Number(form.descanso_minutos),
    permite_tiempo_extra: Boolean(form.permite_tiempo_extra),
    activo: Boolean(form.activo),
  };
}

function getTurnoDescription(horario) {
  const entradaDesde = formatTime(horario.hora_entrada_desde);
  const entradaHasta = formatTime(horario.hora_entrada_hasta);

  if (horario.tipo_turno_codigo === "MATUTINO") {
    return `Matutino · ${formatMinutes(
      horario.duracion_jornada_minutos,
    )} · salida máxima ${entradaHasta}`;
  }

  if (horario.tipo_turno_codigo === "VESPERTINO") {
    return `Vespertino · ${formatMinutes(
      horario.duracion_jornada_minutos,
    )} · entrada desde ${entradaDesde}`;
  }

  return `${horario.tipo_turno_nombre} · ${formatMinutes(
    horario.duracion_jornada_minutos,
  )}`;
}

function SchedulesPage() {
  const [horarios, setHorarios] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const [searchTerm, setSearchTerm] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [form, setForm] = useState(INITIAL_FORM);
  const [formErrors, setFormErrors] = useState({});

  async function loadHorarios() {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const response = await horariosApi.listar();

      setHorarios(response?.items ?? []);
    } catch (error) {
      setErrorMessage(
        error.message ||
          "No fue posible cargar los horarios desde el backend.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadHorarios();
  }, []);

  const filteredHorarios = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    if (!query) return horarios;

    return horarios.filter((horario) => {
      return [
        horario.codigo,
        horario.nombre,
        horario.descripcion,
        horario.tipo_turno_nombre,
        horario.tipo_turno_codigo,
      ]
        .filter(Boolean)
        .some((value) =>
          String(value).toLowerCase().includes(query),
        );
    });
  }, [horarios, searchTerm]);

  const activeSchedules = horarios.filter(
    (horario) => horario.activo,
  ).length;

  const totalAssigned = horarios.reduce(
    (sum, horario) =>
      sum + Number(horario.empleados_asignados ?? 0),
    0,
  );

  const averageTolerance =
    horarios.length === 0
      ? 0
      : horarios.reduce(
          (sum, horario) =>
            sum +
            Number(
              horario.tolerancia_entrada_minutos ?? 0,
            ),
          0,
        ) / horarios.length;

  function handleChange(event) {
    const { name, value, type, checked } = event.target;

    setForm((currentForm) => ({
      ...currentForm,
      [name]: type === "checkbox" ? checked : value,
    }));

    setFormErrors((currentErrors) => ({
      ...currentErrors,
      [name]: undefined,
    }));
  }

  function handleNameBlur() {
    if (form.codigo.trim()) return;

    setForm((currentForm) => ({
      ...currentForm,
      codigo: normalizeCode(currentForm.nombre),
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const validationErrors = validateForm(form);

    if (Object.keys(validationErrors).length > 0) {
      setFormErrors(validationErrors);
      return;
    }

    try {
      setIsSaving(true);
      setErrorMessage("");
      setSuccessMessage("");

      await horariosApi.crear(mapHorarioPayload(form));

      setSuccessMessage("Horario creado correctamente.");
      setForm(INITIAL_FORM);
      setFormErrors({});
      setShowCreateForm(false);

      await loadHorarios();
    } catch (error) {
      setErrorMessage(
        error.message ||
          "No fue posible crear el horario.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleToggleStatus(horario) {
    try {
      setErrorMessage("");
      setSuccessMessage("");

      await horariosApi.cambiarEstatus(
        horario.id,
        !horario.activo,
      );

      setSuccessMessage(
        horario.activo
          ? "Horario desactivado correctamente."
          : "Horario activado correctamente.",
      );

      await loadHorarios();
    } catch (error) {
      setErrorMessage(
        error.message ||
          "No fue posible cambiar el estatus del horario.",
      );
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Horarios y reglas"
        description="Administración real de horarios disponibles para asignación de empleados."
      >
        <div className="header-actions">
          <button
            className="primary-button"
            type="button"
            onClick={() =>
              setShowCreateForm((currentValue) => !currentValue)
            }
          >
            <Plus size={17} />
            Nuevo horario
          </button>
        </div>
      </PageHeader>

      {errorMessage && (
        <section className="form-alert error" role="alert">
          <Settings2 size={22} />

          <div>
            <strong>Error</strong>
            <p>{errorMessage}</p>
          </div>
        </section>
      )}

      {successMessage && (
        <section className="form-alert success" role="status">
          <CheckCircle2 size={22} />

          <div>
            <strong>Operación correcta</strong>
            <p>{successMessage}</p>
          </div>
        </section>
      )}

      <section className="metrics-grid four-columns">
        <article className="metric-card">
          <div className="metric-icon">
            <CalendarClock size={22} />
          </div>

          <div>
            <span className="metric-label">Horarios activos</span>
            <strong className="metric-value">
              {activeSchedules}
            </strong>
            <p className="metric-helper">
              {horarios.length} registrados
            </p>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Users size={22} />
          </div>

          <div>
            <span className="metric-label">Asignaciones activas</span>
            <strong className="metric-value">
              {totalAssigned}
            </strong>
            <p className="metric-helper">
              Empleados con horario vigente
            </p>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Clock size={22} />
          </div>

          <div>
            <span className="metric-label">Tolerancia promedio</span>
            <strong className="metric-value">
              {Math.round(averageTolerance)} min
            </strong>
            <p className="metric-helper">
              Entrada permitida antes de retardo
            </p>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-icon">
            <Settings2 size={22} />
          </div>

          <div>
            <span className="metric-label">Tipos de turno</span>
            <strong className="metric-value">
              {TURNOS_DISPONIBLES.length}
            </strong>
            <p className="metric-helper">
              Matutino y vespertino
            </p>
          </div>
        </article>
      </section>

      {showCreateForm && (
        <section className="panel-card form-card">
          <div className="form-section-header">
            <div>
              <h3>Nuevo horario</h3>
              <p>
                Crea un horario para después asignarlo desde el
                expediente del empleado.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <div className="form-grid two-columns">
              <div className="form-field">
                <label htmlFor="nombre">Nombre</label>

                <input
                  id="nombre"
                  className={
                    formErrors.nombre ? "input-error" : ""
                  }
                  type="text"
                  name="nombre"
                  value={form.nombre}
                  onChange={handleChange}
                  onBlur={handleNameBlur}
                  placeholder="Horario administrativo vespertino"
                />

                {formErrors.nombre && (
                  <span className="field-error">
                    {formErrors.nombre}
                  </span>
                )}
              </div>

              <div className="form-field">
                <label htmlFor="codigo">Código</label>

                <input
                  id="codigo"
                  className={
                    formErrors.codigo ? "input-error" : ""
                  }
                  type="text"
                  name="codigo"
                  value={form.codigo}
                  onChange={handleChange}
                  onBlur={() =>
                    setForm((currentForm) => ({
                      ...currentForm,
                      codigo: normalizeCode(
                        currentForm.codigo,
                      ),
                    }))
                  }
                  placeholder="ADMIN_VESPERTINO"
                />

                {formErrors.codigo && (
                  <span className="field-error">
                    {formErrors.codigo}
                  </span>
                )}
              </div>

              <div className="form-field">
                <label htmlFor="tipo_turno_id">
                  Tipo de turno
                </label>

                <select
                  id="tipo_turno_id"
                  className={
                    formErrors.tipo_turno_id
                      ? "input-error"
                      : ""
                  }
                  name="tipo_turno_id"
                  value={form.tipo_turno_id}
                  onChange={handleChange}
                >
                  {TURNOS_DISPONIBLES.map((turno) => (
                    <option key={turno.id} value={turno.id}>
                      {turno.nombre}
                    </option>
                  ))}
                </select>

                {formErrors.tipo_turno_id && (
                  <span className="field-error">
                    {formErrors.tipo_turno_id}
                  </span>
                )}
              </div>
              <div className="form-field">
                <label htmlFor="hora_entrada">Hora de entrada</label>

                <input
                  id="hora_entrada"
                  className={
                    formErrors.hora_entrada ? "input-error" : ""
                  }
                  type="time"
                  name="hora_entrada"
                  value={form.hora_entrada}
                  onChange={handleChange}
                />

                {formErrors.hora_entrada && (
                  <span className="field-error">
                    {formErrors.hora_entrada}
                  </span>
                )}
              </div>

              <div className="form-field">
                <label htmlFor="hora_salida">Hora de salida</label>

                <input
                  id="hora_salida"
                  className={
                    formErrors.hora_salida ? "input-error" : ""
                  }
                  type="time"
                  name="hora_salida"
                  value={form.hora_salida}
                  onChange={handleChange}
                />

                {formErrors.hora_salida && (
                  <span className="field-error">
                    {formErrors.hora_salida}
                  </span>
                )}
              </div>
              <div className="form-field">
                <label htmlFor="tolerancia_entrada_minutos">
                  Tolerancia entrada
                </label>

                <input
                  id="tolerancia_entrada_minutos"
                  className={
                    formErrors.tolerancia_entrada_minutos
                      ? "input-error"
                      : ""
                  }
                  type="number"
                  name="tolerancia_entrada_minutos"
                  min="0"
                  value={form.tolerancia_entrada_minutos}
                  onChange={handleChange}
                />

                <span className="field-help">
                  Ejemplo: 10 minutos antes de considerar retardo.
                </span>

                {formErrors.tolerancia_entrada_minutos && (
                  <span className="field-error">
                    {formErrors.tolerancia_entrada_minutos}
                  </span>
                )}
              </div>

              <div className="form-field">
                <label htmlFor="descanso_minutos">
                  Descanso/comida
                </label>

                <input
                  id="descanso_minutos"
                  className={
                    formErrors.descanso_minutos
                      ? "input-error"
                      : ""
                  }
                  type="number"
                  name="descanso_minutos"
                  min="0"
                  value={form.descanso_minutos}
                  onChange={handleChange}
                />

                <span className="field-help">
                  Déjalo en 0 si la jornada ya contempla las horas efectivas.
                </span>

                {formErrors.descanso_minutos && (
                  <span className="field-error">
                    {formErrors.descanso_minutos}
                  </span>
                )}
              </div>

              <div className="form-field">
                <label htmlFor="descripcion">Descripción</label>

                <input
                  id="descripcion"
                  type="text"
                  name="descripcion"
                  value={form.descripcion}
                  onChange={handleChange}
                  placeholder="Horario de prueba o uso administrativo"
                />
              </div>

              <label className="checkbox-field">
                <input
                  type="checkbox"
                  name="permite_tiempo_extra"
                  checked={form.permite_tiempo_extra}
                  onChange={handleChange}
                />
                Permite tiempo extra
              </label>

              <label className="checkbox-field">
                <input
                  type="checkbox"
                  name="activo"
                  checked={form.activo}
                  onChange={handleChange}
                />
                Horario activo
              </label>
            </div>

            <div className="form-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setForm(INITIAL_FORM);
                  setFormErrors({});
                }}
                disabled={isSaving}
              >
                Cancelar
              </button>

              <button
                className="primary-button"
                type="submit"
                disabled={isSaving}
              >
                <Plus size={17} />
                {isSaving ? "Guardando..." : "Crear horario"}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="panel-card">
        <div className="section-toolbar">
          <div>
            <h3>Horarios registrados</h3>
            <p>
              Estos horarios son los que pueden asignarse a los
              empleados.
            </p>
          </div>

          <div className="search-box">
            <Search size={17} />

            <input
              type="search"
              placeholder="Buscar horario..."
              value={searchTerm}
              onChange={(event) =>
                setSearchTerm(event.target.value)
              }
            />
          </div>
        </div>

        {isLoading ? (
          <div className="empty-state">
            <CalendarClock size={42} />

            <h3>Cargando horarios</h3>

            <p>Consultando información del backend.</p>
          </div>
        ) : filteredHorarios.length === 0 ? (
          <div className="empty-state">
            <CalendarClock size={42} />

            <h3>Sin horarios</h3>

            <p>
              No hay horarios que coincidan con la búsqueda actual.
            </p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Horario</th>
                  <th>Turno</th>
                  <th>Entrada</th>
                  <th>Salida</th>
                  <th>Tolerancia</th>
                  <th>Descanso</th>
                  <th>Tiempo extra</th>
                  <th>Asignados</th>
                  <th>Estatus</th>
                  <th>Acción</th>
                </tr>
              </thead>

              <tbody>
                {filteredHorarios.map((horario) => (
                  <tr key={horario.id}>
                    <td>
                      <strong>{horario.codigo}</strong>
                    </td>

                    <td>
                      <strong>{horario.nombre}</strong>
                      <span className="muted-table-text">
                        {horario.descripcion || "Sin descripción"}
                      </span>
                    </td>

                    <td>
                      <strong>{horario.tipo_turno_nombre}</strong>
                      <span className="muted-table-text">
                        {getTurnoDescription(horario)}
                      </span>
                    </td>

                    <td>{formatTime(horario.hora_entrada)}</td>

                    <td>{formatTime(horario.hora_salida)}</td>

                    <td>
                      {horario.tolerancia_entrada_minutos} min
                    </td>

                    <td>
                      {horario.descanso_minutos} min
                    </td>

                    <td>
                      {formatBoolean(horario.permite_tiempo_extra)}
                    </td>

                    <td>
                      {horario.empleados_asignados ?? 0}
                    </td>

                    <td>
                      <span className={getStatusClass(horario.activo)}>
                        {horario.activo ? "Activo" : "Inactivo"}
                      </span>
                    </td>

                    <td>
                      <button
                        className="secondary-button compact-button"
                        type="button"
                        onClick={() => handleToggleStatus(horario)}
                      >
                        {horario.activo ? "Desactivar" : "Activar"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default SchedulesPage;