import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Plus,
  RefreshCcw,
  Save,
  X,
} from "lucide-react";

import PageHeader from "../layout/PageHeader";
import {
  getScheduleDescription,
  mockDepartments,
  mockSchedules,
} from "../../data/mockCatalogs";

import { mockEmployees } from "../../data/mockEmployees";
const WEEK_DAYS = [
  "Lunes",
  "Martes",
  "Miércoles",
  "Jueves",
  "Viernes",
  "Sábado",
  "Domingo",
];

const INITIAL_SCHEDULE_FORM = {
  name: "",
  days: [],
  startTime: "08:00",
  endTime: "17:00",
  toleranceMinutes: "10",
  breakMinutes: "0",
};
function getNextEmployeeCode(employees) {
  const highestNumber = employees.reduce((maximum, employee) => {
    const match = employee.employeeCode?.match(/^EMP-(\d+)$/);

    if (!match) {
      return maximum;
    }

    return Math.max(maximum, Number(match[1]));
  }, 0);

  return `EMP-${String(highestNumber + 1).padStart(4, "0")}`;
}

function getNextAvailableZkUserId(employees) {
  const usedIds = new Set(
    employees
      .map((employee) => Number(employee.zkUserId))
      .filter((value) => Number.isInteger(value) && value > 0),
  );

  let availableId = 1;

  while (usedIds.has(availableId)) {
    availableId += 1;
  }

  return String(availableId);
}

function isSupervisorCandidate(employee) {
  const supervisorTerms =
    /supervisor|coordinador|jefe|director|gerente/i;

  return (
    employee.status === "Activo" &&
    supervisorTerms.test(employee.position)
  );
}

function normalizeName(value) {
  return value
    .trim()
    .replace(/\s+/g, " ")
    .toUpperCase();
}
function getEmployeeNameParts(employee) {
  if (!employee) {
    return {
      firstNames: "",
      paternalSurname: "",
      maternalSurname: "",
    };
  }

  /*
   * Cuando PostgreSQL tenga los campos separados,
   * utilizaremos directamente estos valores.
   */
  if (
    employee.firstNames ||
    employee.paternalSurname ||
    employee.maternalSurname
  ) {
    return {
      firstNames: employee.firstNames ?? "",
      paternalSurname: employee.paternalSurname ?? "",
      maternalSurname: employee.maternalSurname ?? "",
    };
  }

  /*
   * Adaptación temporal para los empleados mock que
   * todavía solamente tienen fullName.
   */
  const nameParts = String(employee.fullName ?? "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (nameParts.length === 1) {
    return {
      firstNames: nameParts[0],
      paternalSurname: "",
      maternalSurname: "",
    };
  }

  if (nameParts.length === 2) {
    return {
      firstNames: nameParts[0],
      paternalSurname: nameParts[1],
      maternalSurname: "",
    };
  }

  return {
    firstNames: nameParts.slice(0, -2).join(" "),
    paternalSurname: nameParts.at(-2),
    maternalSurname: nameParts.at(-1),
  };
}

function validateEmployee(form, editingEmployeeId = null) {
  const errors = {};

  const employeeCode = form.employeeCode.trim().toUpperCase();
  const zkUserId = form.zkUserId.trim();
  const firstNames = form.firstNames.trim();
  const paternalSurname = form.paternalSurname.trim();
  const rfc = form.rfc.trim().toUpperCase();

  if (!employeeCode) {
    errors.employeeCode =
      "El código de empleado es obligatorio.";
  } else if (!/^EMP-\d{4,}$/.test(employeeCode)) {
    errors.employeeCode =
      "Utiliza el formato EMP-0001.";
  } else if (
    mockEmployees.some(
      (employee) =>
        employee.id !== editingEmployeeId &&
        employee.employeeCode.toUpperCase() === employeeCode,
    )
  ) {
    errors.employeeCode =
      "Ya existe un empleado con este código.";
  }

  if (!zkUserId) {
    errors.zkUserId =
      "El usuario Reloj es obligatorio.";
  } else if (!/^\d+$/.test(zkUserId)) {
    errors.zkUserId =
      "El usuario Reloj debe contener solo números.";
  } else if (Number(zkUserId) <= 0) {
    errors.zkUserId =
      "El usuario Reloj debe ser mayor que cero.";
  } else if (
    mockEmployees.some(
      (employee) =>
        employee.id !== editingEmployeeId &&
        String(employee.zkUserId) === zkUserId,
    )
  ) {
    errors.zkUserId =
      "Este usuario Reloj ya está asignado.";
  }

  if (!firstNames) {
    errors.firstNames =
      "El nombre o los nombres son obligatorios.";
  }

  if (!paternalSurname) {
    errors.paternalSurname =
      "El apellido paterno es obligatorio.";
  }

  if (!rfc) {
    errors.rfc = "El RFC es obligatorio.";
  } else if (
    !/^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$/.test(rfc)
  ) {
    errors.rfc =
      "El RFC debe tener 13 caracteres y un formato válido.";
  } else if (
    mockEmployees.some(
      (employee) =>
        employee.id !== editingEmployeeId &&
        employee.rfc?.toUpperCase() === rfc,
    )
  ) {
    errors.rfc =
      "Ya existe un empleado registrado con este RFC.";
  }

  if (!form.departmentId) {
    errors.departmentId =
      "Selecciona un departamento.";
  }

  if (!form.position.trim()) {
    errors.position =
      "El puesto es obligatorio.";
  }

  if (!form.supervisorId) {
    errors.supervisorId =
      "Selecciona un supervisor o indica que no aplica.";
  }

  if (!form.scheduleId) {
    errors.scheduleId =
      "Selecciona un horario.";
  }

  return errors;
}

function EmployeeForm({
  mode = "create",
  initialEmployee = null,
}) {
  const isEditMode = mode === "edit";

  const suggestedEmployeeCode = useMemo(
    () => getNextEmployeeCode(mockEmployees),
    [],
  );

  const suggestedZkUserId = useMemo(
    () => getNextAvailableZkUserId(mockEmployees),
    [],
  );

  const initialForm = useMemo(() => {
    if (isEditMode && initialEmployee) {
      const nameParts =
        getEmployeeNameParts(initialEmployee);

      return {
        employeeCode:
          initialEmployee.employeeCode ?? "",

        zkUserId:
          String(initialEmployee.zkUserId ?? ""),

        firstNames: nameParts.firstNames,

        paternalSurname:
          nameParts.paternalSurname,

        maternalSurname:
          nameParts.maternalSurname,

        rfc: initialEmployee.rfc ?? "",

        status:
          initialEmployee.status ?? "Activo",

        departmentId:
          String(initialEmployee.departmentId ?? ""),

        position:
          initialEmployee.position ?? "",

        supervisorId:
          initialEmployee.supervisorId
            ? String(initialEmployee.supervisorId)
            : "none",

        scheduleId:
          initialEmployee.scheduleId
            ? String(initialEmployee.scheduleId)
            : "",
      };
    }

    return {
      employeeCode: suggestedEmployeeCode,
      zkUserId: suggestedZkUserId,
      firstNames: "",
      paternalSurname: "",
      maternalSurname: "",
      rfc: "",
      status: "Activo",
      departmentId: "",
      position: "",
      supervisorId: "",
      scheduleId: "",
    };
  }, [
    isEditMode,
    initialEmployee,
    suggestedEmployeeCode,
    suggestedZkUserId,
  ]);

  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [savedEmployee, setSavedEmployee] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [
    automaticEmployeeCode,
    setAutomaticEmployeeCode,
  ] = useState(!isEditMode);
  useEffect(() => {
    setForm(initialForm);
    setErrors({});
    setSavedEmployee(null);
    setAutomaticEmployeeCode(!isEditMode);
  }, [initialForm, isEditMode]);
  const [schedules, setSchedules] = useState(mockSchedules);

  const [showScheduleModal, setShowScheduleModal] =
    useState(false);

  const [scheduleForm, setScheduleForm] = useState(
    INITIAL_SCHEDULE_FORM,
  );

  const [scheduleErrors, setScheduleErrors] = useState({});


  

  const activeDepartments = useMemo(
    () =>
      mockDepartments.filter(
        (department) => department.isActive,
      ),
    [],
  );

  const activeSchedules = useMemo(
    () =>
      schedules.filter(
        (schedule) => schedule.isActive,
      ),
    [schedules],
  );

  const supervisorCandidates = useMemo(
    () => mockEmployees.filter(isSupervisorCandidate),
    [],
  );

  const selectedDepartmentId = Number(form.departmentId);

  const sameDepartmentSupervisors =
    supervisorCandidates.filter(
      (employee) =>
        employee.departmentId === selectedDepartmentId,
    );

  const otherDepartmentSupervisors =
    supervisorCandidates.filter(
      (employee) =>
        employee.departmentId !== selectedDepartmentId,
    );

  function handleChange(event) {
    const { name, value } = event.target;

    let nextValue = value;

    if (name === "employeeCode" || name === "rfc") {
      nextValue = value.toUpperCase();
    }

    setForm((currentForm) => {
      const nextForm = {
        ...currentForm,
        [name]: nextValue,
      };

      if (name === "departmentId") {
        nextForm.supervisorId = "";
      }

      return nextForm;
    });

    setErrors((currentErrors) => ({
      ...currentErrors,
      [name]: undefined,
      ...(name === "departmentId"
        ? { supervisorId: undefined }
        : {}),
    }));

    setSavedEmployee(null);
  }

  function handleAutomaticCodeChange(event) {
    const checked = event.target.checked;

    setAutomaticEmployeeCode(checked);

    if (checked) {
      setForm((currentForm) => ({
        ...currentForm,
        employeeCode: suggestedEmployeeCode,
      }));

      setErrors((currentErrors) => ({
        ...currentErrors,
        employeeCode: undefined,
      }));
    }
  }

  function suggestEmployeeCode() {
    setAutomaticEmployeeCode(true);

    setForm((currentForm) => ({
      ...currentForm,
      employeeCode: suggestedEmployeeCode,
    }));

    setErrors((currentErrors) => ({
      ...currentErrors,
      employeeCode: undefined,
    }));
  }

  function suggestZkUserId() {
    setForm((currentForm) => ({
      ...currentForm,
      zkUserId: suggestedZkUserId,
    }));

    setErrors((currentErrors) => ({
      ...currentErrors,
      zkUserId: undefined,
    }));
  }
  function openScheduleModal() {
    setScheduleForm(INITIAL_SCHEDULE_FORM);
    setScheduleErrors({});
    setShowScheduleModal(true);
  }

  function closeScheduleModal() {
    setShowScheduleModal(false);
    setScheduleForm(INITIAL_SCHEDULE_FORM);
    setScheduleErrors({});
  }

  function handleScheduleChange(event) {
    const { name, value } = event.target;

    setScheduleForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));

    if (scheduleErrors[name]) {
      setScheduleErrors((currentErrors) => ({
        ...currentErrors,
        [name]: undefined,
      }));
    }
  }

  function toggleScheduleDay(day) {
    setScheduleForm((currentForm) => {
      const dayIsSelected = currentForm.days.includes(day);

      return {
        ...currentForm,
        days: dayIsSelected
          ? currentForm.days.filter(
              (selectedDay) => selectedDay !== day,
            )
          : [...currentForm.days, day],
      };
    });

    setScheduleErrors((currentErrors) => ({
      ...currentErrors,
      days: undefined,
    }));
  }

  function validateSchedule() {
    const validationErrors = {};

    if (!scheduleForm.name.trim()) {
      validationErrors.name =
        "El nombre del horario es obligatorio.";
    }

    if (scheduleForm.days.length === 0) {
      validationErrors.days =
        "Selecciona al menos un día laboral.";
    }

    if (!scheduleForm.startTime) {
      validationErrors.startTime =
        "Selecciona la hora de entrada.";
    }

    if (!scheduleForm.endTime) {
      validationErrors.endTime =
        "Selecciona la hora de salida.";
    }

    if (
      scheduleForm.startTime &&
      scheduleForm.endTime &&
      scheduleForm.startTime === scheduleForm.endTime
    ) {
      validationErrors.endTime =
        "La entrada y la salida no pueden ser iguales.";
    }

    if (
      Number(scheduleForm.toleranceMinutes) < 0
    ) {
      validationErrors.toleranceMinutes =
        "La tolerancia no puede ser negativa.";
    }

    if (Number(scheduleForm.breakMinutes) < 0) {
      validationErrors.breakMinutes =
        "El descanso no puede ser negativo.";
    }

    return validationErrors;
  }

  function saveQuickSchedule() {
    const validationErrors = validateSchedule();

    if (Object.keys(validationErrors).length > 0) {
      setScheduleErrors(validationErrors);
      return;
    }

    const nextScheduleId =
      Math.max(
        0,
        ...schedules.map((schedule) => schedule.id),
      ) + 1;

    const orderedDays = WEEK_DAYS.filter((day) =>
      scheduleForm.days.includes(day),
    );

    const newSchedule = {
      id: nextScheduleId,
      name: scheduleForm.name.trim(),
      days: orderedDays,
      startTime: scheduleForm.startTime,
      endTime: scheduleForm.endTime,
      toleranceMinutes: Number(
        scheduleForm.toleranceMinutes,
      ),
      breakMinutes: Number(
        scheduleForm.breakMinutes,
      ),
      crossesMidnight:
        scheduleForm.endTime < scheduleForm.startTime,
      isActive: true,
    };

    setSchedules((currentSchedules) => [
      ...currentSchedules,
      newSchedule,
    ]);

    setForm((currentForm) => ({
      ...currentForm,
      scheduleId: String(newSchedule.id),
    }));

    setErrors((currentErrors) => ({
      ...currentErrors,
      scheduleId: undefined,
    }));

    closeScheduleModal();
  }
  function handleSubmit(event) {
    event.preventDefault();

    const validationErrors = validateEmployee(
      form,
      isEditMode ? initialEmployee?.id : null,
    );

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      setSavedEmployee(null);

      const firstErrorField =
        Object.keys(validationErrors)[0];

      document
        .querySelector(`[name="${firstErrorField}"]`)
        ?.focus();

      return;
    }

    setIsSubmitting(true);

    const department = mockDepartments.find(
      (item) =>
        item.id === Number(form.departmentId),
    );

    const schedule = schedules.find(
      (item) =>
        item.id === Number(form.scheduleId),
    );

    const supervisor =
      form.supervisorId === "none"
        ? null
        : mockEmployees.find(
            (item) =>
              item.id === Number(form.supervisorId),
          );

    const firstNames = normalizeName(form.firstNames);
    const paternalSurname = normalizeName(
      form.paternalSurname,
    );

    const maternalSurname = normalizeName(
      form.maternalSurname,
    );

    const fullName = [
      firstNames,
      paternalSurname,
      maternalSurname,
    ]
      .filter(Boolean)
      .join(" ");

    const employeeId = isEditMode
      ? initialEmployee.id
      : Math.max(
          0,
          ...mockEmployees.map((employee) => employee.id),
        ) + 1;

    const employeePayload  = {
      id: employeeId,

      employeeCode: form.employeeCode
        .trim()
        .toUpperCase(),

      zkUserId: form.zkUserId.trim(),

      firstNames,
      paternalSurname,
      maternalSurname,
      fullName,

      rfc: form.rfc.trim().toUpperCase(),

      departmentId: Number(form.departmentId),
      department: department?.name ?? "",

      position: form.position.trim(),

      supervisorId: supervisor?.id ?? null,
      supervisor:
        supervisor?.fullName ??
        "Sin supervisor asignado",

      scheduleId: Number(form.scheduleId),
      schedule:
        getScheduleDescription(schedule),

      status: form.status,

      lastPunch: "Sin registros",

      attendanceStatus:
        form.status === "Activo"
          ? "Sin registro"
          : "Baja",
    };

    console.log(
      isEditMode
        ? "Empleado actualizado:"
        : "Empleado creado:",
      employeePayload,
    );

    setSavedEmployee(employeePayload);
    setErrors({});
    setIsSubmitting(false);
  }

  function handleReset() {
    setForm(initialForm);
    setErrors({});
    setSavedEmployee(null);
    setAutomaticEmployeeCode(!isEditMode);
  }

  return (
    <div className="page-stack">
      <PageHeader
        title={
          isEditMode
            ? "Editar empleado"
            : "Nuevo empleado"
        }
        description={
          isEditMode
            ? `Actualiza la información de ${
                initialEmployee?.fullName ?? "este empleado"
              }.`
            : "Registra los datos laborales del empleado y su relación con el reloj checador."
        }
      >
        <Link
          className="secondary-button link-button"
          to="/employees"
        >
          <ArrowLeft size={17} />
          Volver
        </Link>
      </PageHeader>

      {savedEmployee && (
        <section
          className="form-alert success"
          role="status"
        >
          <CheckCircle2 size={22} />

          <div>
            <strong>
              {isEditMode
                ? "Empleado actualizado correctamente"
                : "Empleado validado correctamente"}
            </strong>

            <p>
              {isEditMode
                ? `${savedEmployee.fullName} backend.`
                : `${savedEmployee.fullName} backend.`}
            </p>
          </div>
        </section>
      )}

      {Object.keys(errors).length > 0 && (
        <section
          className="form-alert danger"
          role="alert"
        >
          <AlertCircle size={22} />

          <div>
            <strong>
              Revisa la información
            </strong>

            <p>
              Existen campos obligatorios o valores
              duplicados que deben corregirse.
            </p>
          </div>
        </section>
      )}

      <form
        className="panel-card form-card"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Identificación</h3>

              <p>
                Datos administrativos y registro en el reloj
                checador.
              </p>
            </div>
          </div>

          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="employeeCode">
                Código de empleado
              </label>

              <div className="input-action-row">
                <input
                  id="employeeCode"
                  className={
                    errors.employeeCode
                      ? "input-error"
                      : ""
                  }
                  type="text"
                  name="employeeCode"
                  value={form.employeeCode}
                  onChange={handleChange}
                  readOnly={automaticEmployeeCode}
                  placeholder="EMP-0008"
                  autoComplete="off"
                />

                {!isEditMode && (
                  <button
                    className="secondary-button compact-button"
                    type="button"
                    onClick={suggestEmployeeCode}
                    title="Restablecer código sugerido"
                  >
                    <RefreshCcw size={16} />
                  </button>
                )}
              </div>

              {!isEditMode && (
                <label
                  className="checkbox-control"
                  htmlFor="automaticEmployeeCode"
                >
                  <input
                    id="automaticEmployeeCode"
                    type="checkbox"
                    checked={automaticEmployeeCode}
                    onChange={handleAutomaticCodeChange}
                  />

                  Generar automáticamente
                </label>
              )}

              {errors.employeeCode && (
                <span className="field-error">
                  {errors.employeeCode}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="zkUserId">
                Usuario Reloj
              </label>

              <div className="input-action-row">
                <input
                  id="zkUserId"
                  className={
                    errors.zkUserId
                      ? "input-error"
                      : ""
                  }
                  type="text"
                  name="zkUserId"
                  value={form.zkUserId}
                  onChange={handleChange}
                  placeholder="8"
                  inputMode="numeric"
                  autoComplete="off"
                />

                <button
                  className="secondary-button compact-button"
                  type="button"
                  onClick={suggestZkUserId}
                >
                  Sugerir disponible
                </button>
              </div>

              <span className="field-help">
                Se propone el menor identificador disponible.
              </span>

              {errors.zkUserId && (
                <span className="field-error">
                  {errors.zkUserId}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="firstNames">
                Nombre(s)
              </label>

              <input
                id="firstNames"
                className={
                  errors.firstNames
                    ? "input-error"
                    : ""
                }
                type="text"
                name="firstNames"
                value={form.firstNames}
                onChange={handleChange}
                placeholder="REBECA"
                autoComplete="given-name"
              />

              {errors.firstNames && (
                <span className="field-error">
                  {errors.firstNames}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="paternalSurname">
                Apellido paterno
              </label>

              <input
                id="paternalSurname"
                className={
                  errors.paternalSurname
                    ? "input-error"
                    : ""
                }
                type="text"
                name="paternalSurname"
                value={form.paternalSurname}
                onChange={handleChange}
                placeholder="SOLANO"
                autoComplete="family-name"
              />

              {errors.paternalSurname && (
                <span className="field-error">
                  {errors.paternalSurname}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="maternalSurname">
                Apellido materno
              </label>

              <input
                id="maternalSurname"
                type="text"
                name="maternalSurname"
                value={form.maternalSurname}
                onChange={handleChange}
                placeholder="ALAMEDA"
                autoComplete="additional-name"
              />

              <span className="field-help">
                Opcional.
              </span>
            </div>

            <div className="form-field">
              <label htmlFor="rfc">
                RFC
              </label>

              <input
                id="rfc"
                className={
                  errors.rfc ? "input-error" : ""
                }
                type="text"
                name="rfc"
                value={form.rfc}
                onChange={handleChange}
                placeholder="SOLR231129LOV"
                maxLength={13}
                autoComplete="off"
              />

              {errors.rfc && (
                <span className="field-error">
                  {errors.rfc}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="status">
                Estatus
              </label>

              <select
                id="status"
                name="status"
                value={form.status}
                onChange={handleChange}
              >
                <option value="Activo">
                  Activo
                </option>

                <option value="Inactivo">
                  Inactivo
                </option>
              </select>
            </div>
          </div>
        </div>

        <div className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Organización</h3>

              <p>
                Departamento, puesto, supervisor y horario.
              </p>
            </div>
          </div>

          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="departmentId">
                Departamento
              </label>

              <select
                id="departmentId"
                className={
                  errors.departmentId
                    ? "input-error"
                    : ""
                }
                name="departmentId"
                value={form.departmentId}
                onChange={handleChange}
              >
                <option value="">
                  Selecciona departamento
                </option>

                {activeDepartments.map((department) => (
                  <option
                    key={department.id}
                    value={department.id}
                  >
                    {department.name}
                  </option>
                ))}
              </select>

              {errors.departmentId && (
                <span className="field-error">
                  {errors.departmentId}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="position">
                Puesto
              </label>

              <input
                id="position"
                className={
                  errors.position
                    ? "input-error"
                    : ""
                }
                type="text"
                name="position"
                value={form.position}
                onChange={handleChange}
                placeholder="Puesto del empleado"
              />

              {errors.position && (
                <span className="field-error">
                  {errors.position}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="supervisorId">
                Supervisor
              </label>

              <select
                id="supervisorId"
                className={
                  errors.supervisorId
                    ? "input-error"
                    : ""
                }
                name="supervisorId"
                value={form.supervisorId}
                onChange={handleChange}
                disabled={!form.departmentId}
              >
                <option value="">
                  {form.departmentId
                    ? "Selecciona supervisor"
                    : "Primero selecciona departamento"}
                </option>

                <option value="none">
                  Sin supervisor asignado
                </option>

                {sameDepartmentSupervisors.length > 0 && (
                  <optgroup label="Del mismo departamento">
                    {sameDepartmentSupervisors.map(
                      (supervisor) => (
                        <option
                          key={supervisor.id}
                          value={supervisor.id}
                        >
                          {supervisor.fullName}
                        </option>
                      ),
                    )}
                  </optgroup>
                )}

                {otherDepartmentSupervisors.length > 0 && (
                  <optgroup label="De otros departamentos">
                    {otherDepartmentSupervisors.map(
                      (supervisor) => (
                        <option
                          key={supervisor.id}
                          value={supervisor.id}
                        >
                          {supervisor.fullName}
                          {" · "}
                          {supervisor.department}
                        </option>
                      ),
                    )}
                  </optgroup>
                )}
              </select>

              {errors.supervisorId && (
                <span className="field-error">
                  {errors.supervisorId}
                </span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="scheduleId">
                Horario asignado
              </label>

              <div className="input-action-row">
                <select
                  id="scheduleId"
                  className={
                    errors.scheduleId
                      ? "input-error"
                      : ""
                  }
                  name="scheduleId"
                  value={form.scheduleId}
                  onChange={handleChange}
                >
                  <option value="">
                    Selecciona horario
                  </option>

                  {activeSchedules.map((schedule) => (
                    <option
                      key={schedule.id}
                      value={schedule.id}
                    >
                      {schedule.name}
                      {" · "}
                      {getScheduleDescription(schedule)}
                    </option>
                  ))}
                </select>

                <button
                  className="secondary-button compact-button"
                  type="button"
                  onClick={openScheduleModal}
                >
                  <Plus size={16} />
                  Nuevo horario
                </button>
              </div>

              {errors.scheduleId && (
                <span className="field-error">
                  {errors.scheduleId}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="form-actions">
          <Link
            className="secondary-button link-button"
            to={
              isEditMode && initialEmployee
                ? `/employees/${initialEmployee.id}`
                : "/employees"
            }
          >
            Cancelar
          </Link>

          <button
            className="secondary-button"
            type="button"
            onClick={handleReset}
          >
            Limpiar formulario
          </button>

          <button
            className="primary-button"
            type="submit"
            disabled={isSubmitting}
          >
            <Save size={17} />

            {isSubmitting
              ? "Guardando..."
              : isEditMode
                ? "Guardar cambios"
                : "Guardar empleado"}
          </button>
        </div>
            </form>

      {showScheduleModal && (
        <div
          className="modal-backdrop"
          role="presentation"
          onMouseDown={closeScheduleModal}
        >
          <section
            className="modal-card schedule-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="schedule-modal-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <h2 id="schedule-modal-title">
                  Nuevo horario
                </h2>

                <p>
                  Crea una jornada rápida y asígnala
                  automáticamente al empleado.
                </p>
              </div>

              <button
                className="icon-button"
                type="button"
                onClick={closeScheduleModal}
                aria-label="Cerrar modal"
              >
                <X size={20} />
              </button>
            </div>

            <div className="modal-content">
              <div className="form-field">
                <label htmlFor="scheduleName">
                  Nombre del horario
                </label>

                <input
                  id="scheduleName"
                  className={
                    scheduleErrors.name
                      ? "input-error"
                      : ""
                  }
                  type="text"
                  name="name"
                  value={scheduleForm.name}
                  onChange={handleScheduleChange}
                  placeholder="Jornada especial"
                  autoFocus
                />

                {scheduleErrors.name && (
                  <span className="field-error">
                    {scheduleErrors.name}
                  </span>
                )}
              </div>

              <div className="form-field">
                <label>Días laborales</label>

                <div className="day-selector">
                  {WEEK_DAYS.map((day) => {
                    const isSelected =
                      scheduleForm.days.includes(day);

                    return (
                      <button
                        key={day}
                        className={
                          isSelected
                            ? "day-button selected"
                            : "day-button"
                        }
                        type="button"
                        onClick={() =>
                          toggleScheduleDay(day)
                        }
                      >
                        {day.slice(0, 3)}
                      </button>
                    );
                  })}
                </div>

                {scheduleErrors.days && (
                  <span className="field-error">
                    {scheduleErrors.days}
                  </span>
                )}
              </div>

              <div className="modal-form-grid">
                <div className="form-field">
                  <label htmlFor="scheduleStartTime">
                    Hora de entrada
                  </label>

                  <input
                    id="scheduleStartTime"
                    className={
                      scheduleErrors.startTime
                        ? "input-error"
                        : ""
                    }
                    type="time"
                    name="startTime"
                    value={scheduleForm.startTime}
                    onChange={handleScheduleChange}
                  />

                  {scheduleErrors.startTime && (
                    <span className="field-error">
                      {scheduleErrors.startTime}
                    </span>
                  )}
                </div>

                <div className="form-field">
                  <label htmlFor="scheduleEndTime">
                    Hora de salida
                  </label>

                  <input
                    id="scheduleEndTime"
                    className={
                      scheduleErrors.endTime
                        ? "input-error"
                        : ""
                    }
                    type="time"
                    name="endTime"
                    value={scheduleForm.endTime}
                    onChange={handleScheduleChange}
                  />

                  {scheduleErrors.endTime && (
                    <span className="field-error">
                      {scheduleErrors.endTime}
                    </span>
                  )}
                </div>

                <div className="form-field">
                  <label htmlFor="scheduleTolerance">
                    Tolerancia
                  </label>

                  <div className="number-input-with-unit">
                    <input
                      id="scheduleTolerance"
                      className={
                        scheduleErrors.toleranceMinutes
                          ? "input-error"
                          : ""
                      }
                      type="number"
                      name="toleranceMinutes"
                      value={
                        scheduleForm.toleranceMinutes
                      }
                      onChange={handleScheduleChange}
                      min="0"
                    />

                    <span>min</span>
                  </div>

                  {scheduleErrors.toleranceMinutes && (
                    <span className="field-error">
                      {
                        scheduleErrors.toleranceMinutes
                      }
                    </span>
                  )}
                </div>

                <div className="form-field">
                  <label htmlFor="scheduleBreak">
                    Descanso
                  </label>

                  <div className="number-input-with-unit">
                    <input
                      id="scheduleBreak"
                      className={
                        scheduleErrors.breakMinutes
                          ? "input-error"
                          : ""
                      }
                      type="number"
                      name="breakMinutes"
                      value={scheduleForm.breakMinutes}
                      onChange={handleScheduleChange}
                      min="0"
                    />

                    <span>min</span>
                  </div>

                  {scheduleErrors.breakMinutes && (
                    <span className="field-error">
                      {scheduleErrors.breakMinutes}
                    </span>
                  )}
                </div>
              </div>

              {scheduleForm.startTime &&
                scheduleForm.endTime &&
                scheduleForm.endTime <
                  scheduleForm.startTime && (
                  <div className="form-alert warning">
                    <AlertCircle size={20} />

                    <div>
                      <strong>Horario nocturno</strong>

                      <p>
                        La hora de salida corresponde al día
                        siguiente.
                      </p>
                    </div>
                  </div>
                )}
            </div>

            <div className="modal-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={closeScheduleModal}
              >
                Cancelar
              </button>

              <button
                className="primary-button"
                type="button"
                onClick={saveQuickSchedule}
              >
                <Plus size={17} />
                Crear y seleccionar
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

export default EmployeeForm;