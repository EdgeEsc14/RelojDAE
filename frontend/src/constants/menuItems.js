import {
  AlertTriangle,
  CalendarClock,
  CalendarDays,
  ClipboardList,
  Clock,
  Database,
  FileText,
  Fingerprint,
  LayoutDashboard,
  Settings,
  Users,
} from "lucide-react";

import { MODULES } from "./permissions";

export const menuItems = [
  {
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
    module: MODULES.DASHBOARD,
  },
  {
    label: "Usuarios",
    path: "/employees",
    icon: Users,
    module: MODULES.EMPLEADOS,
  },
  {
    label: "Asistencia",
    path: "/attendance",
    icon: Clock,
    module: MODULES.ASISTENCIA,
  },
  {
    label: "Marcaciones",
    path: "/attendance/raw",
    icon: Database,
    module: MODULES.CHECADAS_CRUDAS,
  },
  {
    label: "Incidencias",
    path: "/incidents",
    icon: AlertTriangle,
    module: MODULES.INCIDENCIAS,
  },
  {
    label: "Reportes",
    path: "/reports",
    icon: FileText,
    module: MODULES.REPORTES,
  },
  {
    label: "Dispositivos",
    path: "/devices",
    icon: Fingerprint,
    module: MODULES.DISPOSITIVOS,
  },
  {
    label: "Horarios",
    path: "/schedules",
    icon: CalendarClock,
    module: MODULES.HORARIOS,
  },
  {
    label: "Calendario",
    path: "/calendar",
    icon: CalendarDays,
    module: MODULES.HORARIOS,
  },
  {
    label: "Auditoría",
    path: "/audit",
    icon: ClipboardList,
    module: MODULES.AUDITORIA,
  },
  {
    label: "Configuración",
    path: "/settings",
    icon: Settings,
    module: MODULES.CONFIGURACION,
  },
];