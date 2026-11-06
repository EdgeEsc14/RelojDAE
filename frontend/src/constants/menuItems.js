import {
  AlertTriangle,
  CalendarClock,
  CalendarDays,
  ClipboardList,
  Clock,
  FileText,
  Fingerprint,
  LayoutDashboard,
  Settings,
  ShieldCheck,
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
    ownLabel: "Mi perfil",
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
    label: "Usuarios del sistema",
    path: "/system-users",
    icon: ShieldCheck,
    module: MODULES.USUARIOS_SISTEMA,
  },
  {
    label: "Auditoría",
    path: "/audit",
    icon: ClipboardList,
    module: MODULES.AUDITORIA,
    hidden: true,
  },
  {
    label: "Configuración",
    path: "/settings",
    icon: Settings,
    module: MODULES.CONFIGURACION,
  },
];