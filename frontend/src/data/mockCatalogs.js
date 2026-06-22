export const mockDepartments = [
  {
    id: 1,
    name: "Departamento de Certificación",
    isActive: true,
  },
  {
    id: 2,
    name: "Operaciones",
    isActive: true,
  },
  {
    id: 3,
    name: "Administración",
    isActive: true,
  },
  {
    id: 4,
    name: "Recursos Humanos",
    isActive: true,
  },
  {
    id: 5,
    name: "Mantenimiento",
    isActive: true,
  },
];

export const mockSchedules = [
  {
    id: 1,
    name: "Jornada de certificación",
    days: [
      "Lunes",
      "Martes",
      "Miércoles",
      "Jueves",
      "Viernes",
    ],
    startTime: "08:00",
    endTime: "15:00",
    toleranceMinutes: 10,
    breakMinutes: 0,
    crossesMidnight: false,
    isActive: true,
  },
  {
    id: 2,
    name: "Jornada de recursos humanos",
    days: [
      "Lunes",
      "Martes",
      "Miércoles",
      "Jueves",
      "Viernes",
    ],
    startTime: "08:00",
    endTime: "16:00",
    toleranceMinutes: 10,
    breakMinutes: 0,
    crossesMidnight: false,
    isActive: true,
  },
  {
    id: 3,
    name: "Jornada administrativa",
    days: [
      "Lunes",
      "Martes",
      "Miércoles",
      "Jueves",
      "Viernes",
    ],
    startTime: "08:00",
    endTime: "17:00",
    toleranceMinutes: 10,
    breakMinutes: 60,
    crossesMidnight: false,
    isActive: true,
  },
  {
    id: 4,
    name: "Jornada operativa",
    days: [
      "Lunes",
      "Martes",
      "Miércoles",
      "Jueves",
      "Viernes",
      "Sábado",
    ],
    startTime: "07:00",
    endTime: "15:00",
    toleranceMinutes: 10,
    breakMinutes: 0,
    crossesMidnight: false,
    isActive: true,
  },
];

export function getScheduleDescription(schedule) {
  if (!schedule) {
    return "";
  }

  const firstDay = schedule.days[0];
  const lastDay = schedule.days[schedule.days.length - 1];

  const daysText =
    schedule.days.length === 1
      ? firstDay
      : `${firstDay} a ${lastDay}`;

  return `${daysText} ${schedule.startTime} - ${schedule.endTime}`;
}