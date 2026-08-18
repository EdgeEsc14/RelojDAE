import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import AppLayout from "../components/layout/AppLayout";
import ProtectedRoute from "./ProtectedRoute";

import {
  DATA_SCOPES,
  MODULES,
} from "../constants/permissions";

// Alias para compatibilidad con prop allowedAccessLevels
const ACCESS_LEVELS = DATA_SCOPES;

import LoginPage from "../pages/auth/LoginPage";
import DashboardPage from "../pages/dashboard/DashboardPage";

import EmployeesPage from "../pages/employees/EmployeesPage";
import EmployeeDetailPage from "../pages/employees/EmployeeDetailPage";
import NewEmployeePage from "../pages/employees/NewEmployeePage";
import EmployeeLinkingPage from "../pages/employees/EmployeeLinkingPage";

import AttendancePage from "../pages/attendance/AttendancePage";
import AttendanceRawPage from "../pages/attendance/AttendanceRawPage";

import IncidentsPage from "../pages/incidents/IncidentsPage";
import IncidentDetailPage from "../pages/incidents/IncidentDetailPage";

import ReportsPage from "../pages/reports/ReportsPage";
import EmployeeReportPage from "../pages/reports/EmployeeReportPage";
import DepartmentReportPage from "../pages/reports/DepartmentReportPage";

import DevicesPage from "../pages/devices/DevicesPage";
import DeviceDetailPage from "../pages/devices/DeviceDetailPage";

import SchedulesPage from "../pages/schedules/SchedulesPage";

import CalendarPage from "../pages/calendar/CalendarPage";

import AuditPage from "../pages/audit/AuditPage";

import SettingsPage from "../pages/settings/SettingsPage";

import AccessDeniedPage from "../pages/errors/AccessDeniedPage";

import EditEmployeePage from "../pages/employees/EditEmployeePage";

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/"
        element={<Navigate to="/login" replace />}
      />

      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route element={<AppLayout />}>
        {/* Página de error sin protección */}
        <Route
          path="/access-denied"
          element={<AccessDeniedPage />}
        />

        {/* Dashboard */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute
              requiredModule={MODULES.DASHBOARD}
            >
              <DashboardPage />
            </ProtectedRoute>
          }
        />

        {/* Empleados */}
        <Route
          path="/employees"
          element={
            <ProtectedRoute
              requiredModule={MODULES.EMPLEADOS}
            >
              <EmployeesPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/employees/new"
          element={
            <ProtectedRoute
              requiredModule={MODULES.EMPLEADOS}
              allowedAccessLevels={[
                ACCESS_LEVELS.TOTAL,
              ]}
            >
              <NewEmployeePage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/employees/linking"
          element={
            <ProtectedRoute
              requiredModule={MODULES.EMPLEADOS}
              allowedAccessLevels={[
                ACCESS_LEVELS.TOTAL,
              ]}
            >
              <EmployeeLinkingPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/employees/:employeeId/edit"
          element={
            <ProtectedRoute
              requiredModule={MODULES.EMPLEADOS}
              allowedAccessLevels={[
                ACCESS_LEVELS.TOTAL,
              ]}
            >
              <EditEmployeePage />
            </ProtectedRoute>
          }
        />


        <Route
          path="/employees/:employeeId"
          element={
            <ProtectedRoute
              requiredModule={MODULES.EMPLEADOS}
            >
              <EmployeeDetailPage />
            </ProtectedRoute>
          }
        />

        {/* Asistencia procesada */}
        <Route
          path="/attendance"
          element={
            <ProtectedRoute
              requiredModule={MODULES.ASISTENCIA}
            >
              <AttendancePage />
            </ProtectedRoute>
          }
        />

        {/* Checadas crudas */}
        <Route
          path="/attendance/raw"
          element={
            <ProtectedRoute
              requiredModule={MODULES.CHECADAS_CRUDAS}
            >
              <AttendanceRawPage />
            </ProtectedRoute>
          }
        />

        {/* Incidencias */}
        <Route
          path="/incidents"
          element={
            <ProtectedRoute
              requiredModule={MODULES.INCIDENCIAS}
            >
              <IncidentsPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/incidents/:incidentId"
          element={
            <ProtectedRoute
              requiredModule={MODULES.INCIDENCIAS}
            >
              <IncidentDetailPage />
            </ProtectedRoute>
          }
        />

        {/* Reportes */}
        <Route
          path="/reports"
          element={
            <ProtectedRoute
              requiredModule={MODULES.REPORTES}
            >
              <ReportsPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/reports/employee/:employeeId"
          element={
            <ProtectedRoute
              requiredModule={MODULES.REPORTES}
            >
              <EmployeeReportPage />
            </ProtectedRoute>
          }
        />

        {/*
          El empleado tiene permiso "propio" en Reportes,
          pero no debe consultar reportes departamentales.
        */}
        <Route
          path="/reports/department"
          element={
            <ProtectedRoute
              requiredModule={MODULES.REPORTES}
              allowedAccessLevels={[
                ACCESS_LEVELS.TOTAL,
                ACCESS_LEVELS.AREA,
              ]}
            >
              <DepartmentReportPage />
            </ProtectedRoute>
          }
        />

        {/* Dispositivos */}
        <Route
          path="/devices"
          element={
            <ProtectedRoute
              requiredModule={MODULES.DISPOSITIVOS}
            >
              <DevicesPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/devices/:deviceId"
          element={
            <ProtectedRoute
              requiredModule={MODULES.DISPOSITIVOS}
            >
              <DeviceDetailPage />
            </ProtectedRoute>
          }
        />

        {/* Horarios */}
        <Route
          path="/schedules"
          element={
            <ProtectedRoute
              requiredModule={MODULES.HORARIOS}
            >
              <SchedulesPage />
            </ProtectedRoute>
          }
        />

        {/* Calendario Laboral */}
        <Route
          path="/calendar"
          element={
            <ProtectedRoute
              requiredModule={MODULES.HORARIOS}
            >
              <CalendarPage />
            </ProtectedRoute>
          }
        />

        {/* Auditoría */}
        <Route
          path="/audit"
          element={
            <ProtectedRoute
              requiredModule={MODULES.AUDITORIA}
            >
              <AuditPage />
            </ProtectedRoute>
          }
        />

        {/* Configuración */}
        <Route
          path="/settings"
          element={
            <ProtectedRoute
              requiredModule={MODULES.CONFIGURACION}
            >
              <SettingsPage />
            </ProtectedRoute>
          }
        />
      </Route>

      {/*
        Usamos Asistencia como ruta de respaldo porque todos
        los roles definidos actualmente tienen acceso a ella.
      */}
      <Route
        path="*"
        element={<Navigate to="/attendance" replace />}
      />
    </Routes>
  );
}

export default AppRoutes;