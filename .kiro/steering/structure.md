# RelojDAE - Estructura del Proyecto

## Estructura Real de Carpetas

```
RelojChecador/
├── .gitignore
├── .kiro/steering/              # Documentación contextual para IA
├── run.txt                      # Instrucciones de ejecución local
├── EmployeeForm_actual.txt      # Snapshot del componente EmployeeForm (referencia)
│
├── backend/
│   ├── .env                     # Variables de entorno (no versionado)
│   ├── .env.example             # Plantilla de configuración
│   ├── .v_relojdae/             # Virtual environment Python (no versionado)
│   ├── requirements.txt         # Dependencias Python
│   ├── sonido.py                # Script experimental de sonido ZKTeco
│   ├── runtime/                 # Estado de ejecución (no versionado)
│   │   └── zk_time_sync_state.json
│   ├── scripts/                 # Utilidades y pruebas
│   │   ├── create_super_admin.py
│   │   ├── check_empleados_columns.py
│   │   ├── pruebas.ipynb
│   │   ├── zk_attendance_smoke.py
│   │   ├── zk_cleanup_test_users.py
│   │   ├── zk_service_smoke.py
│   │   ├── zk_smoke_test.py
│   │   └── zk_sync_time.py
│   └── app/                     # Aplicación FastAPI
│       ├── __init__.py
│       ├── main.py              # Entry point de FastAPI
│       ├── core/                # Infraestructura transversal
│       │   ├── config.py        # Settings desde .env (Pydantic)
│       │   ├── database.py      # Engine SQLAlchemy + get_db()
│       │   ├── security.py      # Hash, JWT manual, tokens
│       │   ├── auth_dependencies.py  # get_current_user, require_roles, require_module_access
│       │   └── access_control.py     # AccessScope dataclass
│       ├── api/
│       │   ├── routes/          # Routers legacy / especiales
│       │   │   ├── auth.py      # Login, /auth/me
│       │   │   └── zk.py       # Endpoints ZKTeco (/api/zk/*)
│       │   └── v1/             # API versionada principal
│       │       ├── router.py    # Registra todos los endpoints v1
│       │       └── endpoints/
│       │           ├── health.py
│       │           ├── dashboard.py
│       │           ├── empleados.py
│       │           ├── empleados_config.py
│       │           ├── asistencia.py
│       │           ├── marcaciones.py
│       │           ├── catalogos.py
│       │           ├── horarios.py
│       │           └── debug.py
│       ├── schemas/             # Pydantic models (request/response)
│       │   ├── auth.py
│       │   ├── empleados.py
│       │   ├── empleados_write.py
│       │   ├── empleados_config.py
│       │   ├── empleados_integral.py
│       │   ├── empleados_sincronizacion.py
│       │   ├── asistencia.py
│       │   ├── asistencia_procesamiento.py
│       │   ├── marcaciones.py
│       │   ├── horarios.py
│       │   ├── catalogos.py
│       │   ├── dashboard.py
│       │   └── zk.py
│       ├── repositories/        # Acceso a datos (SQL directo)
│       │   ├── auth_repo.py
│       │   ├── access_repo.py
│       │   ├── empleados_repo.py
│       │   ├── empleados_write_repo.py
│       │   ├── empleados_config_repo.py
│       │   ├── empleados_integral_repo.py
│       │   ├── asistencia_repo.py
│       │   ├── asistencia_procesamiento_repo.py
│       │   ├── marcaciones_repo.py
│       │   ├── horarios_repo.py
│       │   ├── catalogos_repo.py
│       │   ├── dashboard_repo.py
│       │   ├── debug_repo.py
│       │   ├── zk_attendance_repo.py
│       │   ├── zk_employee_link_repo.py
│       │   └── zk_reconciliation_repo.py
│       └── services/            # Lógica de negocio compleja
│           ├── zk_service.py                     # ZKDeviceService (comunicación con reloj)
│           ├── zk_time_sync_service.py           # Sincronización de hora del reloj
│           └── empleados_sincronizacion_service.py  # Sincronización empleado-dispositivo
│
├── database/
│   ├── 059_consolidate_asistencias_diarias.sql  # Migración fuera de migrations/
│   └── migrations/              # Migraciones SQL secuenciales (002-061)
│       ├── 002_create_puestos.sql
│       ├── 003_create_empleados.sql
│       ├── ...
│       ├── 060_empleados_integrales.sql
│       └── 061_corregir_formatos_empleados.sql
│
└── frontend/
    ├── .env                     # Variables Vite
    ├── .gitignore
    ├── index.html               # Entry HTML
    ├── package.json             # Dependencias npm
    ├── package-lock.json
    ├── vite.config.js           # Configuración Vite
    ├── eslint.config.js
    ├── dist/                    # Build de producción (no versionado)
    └── src/
        ├── main.jsx             # Entry point React
        ├── App.jsx              # BrowserRouter + AppRoutes
        ├── App.css
        ├── index.css
        ├── api/                 # Clientes HTTP hacia FastAPI
        │   ├── client.js        # apiRequest() base
        │   ├── authApi.js       # Login, token, /auth/me
        │   ├── empleadosApi.js  # CRUD empleados
        │   ├── asistenciaApi.js # Asistencia diaria, procesar
        │   ├── catalogosApi.js  # Catálogos (unidades, puestos, horarios)
        │   ├── dashboardApi.js  # Resumen dashboard
        │   ├── horariosApi.js   # CRUD horarios
        │   └── zkApi.js         # Operaciones ZKTeco (base URL distinta)
        ├── context/
        │   └── AuthContext.jsx  # Provider de autenticación
        ├── constants/
        │   ├── roles.js         # Definición de roles
        │   ├── permissions.js   # Matriz de permisos ROLE_PERMISSIONS
        │   └── menuItems.js     # Elementos del menú lateral
        ├── routes/
        │   ├── AppRoutes.jsx    # Todas las rutas de la app
        │   └── ProtectedRoute.jsx  # Guard por módulo y nivel de acceso
        ├── components/
        │   ├── layout/
        │   │   ├── AppLayout.jsx
        │   │   ├── Sidebar.jsx
        │   │   ├── Topbar.jsx
        │   │   └── PageHeader.jsx
        │   ├── ui/
        │   │   ├── MetricCard.jsx
        │   │   ├── PanelCard.jsx
        │   │   ├── SearchFilterBar.jsx
        │   │   └── StatusBadge.jsx
        │   ├── employees/
        │   │   ├── EmployeeForm.jsx
        │   │   └── EmployeeForm.jsx.bak    # Backup anterior
        │   ├── attendance/
        │   ├── charts/
        │   ├── dashboard/
        │   ├── devices/
        │   ├── incidents/
        │   └── reports/
        ├── pages/
        │   ├── auth/            # LoginPage
        │   ├── dashboard/       # DashboardPage
        │   ├── employees/       # EmployeesPage, EmployeeDetailPage, NewEmployeePage, EditEmployeePage
        │   ├── attendance/      # AttendancePage, AttendanceRawPage
        │   ├── incidents/       # IncidentsPage, IncidentDetailPage
        │   ├── reports/         # ReportsPage, EmployeeReportPage, DepartmentReportPage
        │   ├── devices/         # DevicesPage, DeviceDetailPage
        │   ├── schedules/       # SchedulesPage
        │   ├── users/           # SystemUsersPage
        │   ├── audit/           # AuditPage
        │   ├── settings/        # SettingsPage
        │   └── errors/          # AccessDeniedPage
        ├── data/                # Mock data (posiblemente residual)
        │   ├── mockAttendance.js
        │   ├── mockAudit.js
        │   ├── mockCatalogs.js
        │   ├── mockCharts.js
        │   ├── mockDevices.js
        │   ├── mockEmployees.js
        │   ├── mockIncidents.js
        │   ├── mockReports.js
        │   ├── mockSchedules.js
        │   ├── mockSettings.js
        │   └── mockSystemUsers.js
        ├── styles/              # Archivos CSS adicionales
        └── utils/
            └── permissions.js   # Utilidades de permisos en frontend
```

## Responsabilidades por Capa

### backend/

Servicio API REST que expone toda la lógica de negocio. Responsable de:

- Autenticación y autorización (JWT, AccessScope).
- CRUD de empleados con control de acceso por módulo.
- Comunicación directa con relojes ZKTeco (lectura de usuarios, marcaciones,
  creación de usuarios en el reloj, sincronización de hora).
- Procesamiento de asistencia (transformar marcaciones crudas en asistencia diaria).
- Catálogos institucionales (unidades, puestos, horarios, roles).
- Auditoría de operaciones.

### frontend/

SPA React que consume la API. Responsable de:

- Interfaz de usuario para todos los módulos.
- Autenticación visual (login, manejo de token).
- Navegación protegida por permisos (ProtectedRoute).
- Visualización de datos, formularios CRUD.
- No contiene lógica de negocio significativa; delega al backend.

### database/

Esquema y evolución de la base de datos. Responsable de:

- Definición de tablas, constraints, índices.
- Seeds iniciales (organigrama, roles, permisos, usuario admin).
- Correcciones de integridad.
- No usa herramienta de migración (las migraciones son SQL puro ejecutado
  manualmente con `psql`).

## Módulos Principales

| Módulo Backend | Router | Repositorio(s) | Schema(s) |
|----------------|--------|-----------------|-----------|
| Empleados | `v1/endpoints/empleados.py` | `empleados_repo`, `empleados_write_repo`, `empleados_integral_repo` | `empleados`, `empleados_write`, `empleados_integral` |
| Empleados Config | `v1/endpoints/empleados_config.py` | `empleados_config_repo` | `empleados_config` |
| Asistencia | `v1/endpoints/asistencia.py` | `asistencia_repo`, `asistencia_procesamiento_repo` | `asistencia`, `asistencia_procesamiento` |
| Marcaciones | `v1/endpoints/marcaciones.py` | `marcaciones_repo` | `marcaciones` |
| Horarios | `v1/endpoints/horarios.py` | `horarios_repo` | `horarios` |
| Catálogos | `v1/endpoints/catalogos.py` | `catalogos_repo` | `catalogos` |
| Dashboard | `v1/endpoints/dashboard.py` | `dashboard_repo` | `dashboard` |
| ZKTeco | `routes/zk.py` | `zk_attendance_repo`, `zk_employee_link_repo`, `zk_reconciliation_repo` | `zk` |
| Auth | `routes/auth.py` | `auth_repo` | `auth` |
| Health | `v1/endpoints/health.py` | - | - |
| Debug | `v1/endpoints/debug.py` | `debug_repo` | - |

## Flujo entre Capas

```
[Frontend SPA]
      |
      | HTTP (fetch) → Bearer token
      v
[FastAPI (main.py)]
      |
      | Depends() → auth + access_scope
      v
[Router/Endpoint]
      |
      | Llama a repository o service
      v
[Repository (SQL text())]  ←→  [Service (lógica compleja)]
      |                              |
      v                              v
[PostgreSQL]                   [ZKTeco Device (pyzk)]
```

## Ubicación de Componentes Clave

| Concepto | Ubicación |
|----------|-----------|
| Entry point backend | `backend/app/main.py` |
| Configuración | `backend/app/core/config.py` |
| Conexión DB | `backend/app/core/database.py` |
| JWT + Hashing | `backend/app/core/security.py` |
| Auth middleware | `backend/app/core/auth_dependencies.py` |
| Permisos backend | `backend/app/core/access_control.py` |
| Routers v1 | `backend/app/api/v1/endpoints/*.py` |
| Routers especiales | `backend/app/api/routes/{auth,zk}.py` |
| Repositories | `backend/app/repositories/*.py` |
| Schemas Pydantic | `backend/app/schemas/*.py` |
| Services | `backend/app/services/*.py` |
| Migraciones | `database/migrations/*.sql` |
| Entry point frontend | `frontend/src/main.jsx` |
| Router frontend | `frontend/src/routes/AppRoutes.jsx` |
| Auth context | `frontend/src/context/AuthContext.jsx` |
| API clients | `frontend/src/api/*.js` |
| Permisos frontend | `frontend/src/constants/permissions.js` |
| Componentes UI | `frontend/src/components/ui/*.jsx` |
| Páginas | `frontend/src/pages/{modulo}/*.jsx` |

## Convenciones Actualmente Utilizadas

### Naming

- **Backend Python**: snake_case para funciones, variables, archivos.
- **Frontend JS/JSX**: camelCase para variables/funciones, PascalCase para componentes.
- **Base de datos**: snake_case para tablas y columnas.
- **Endpoints**: Sustantivos en español (`/empleados`, `/asistencia`, `/horarios`).
- **Schemas SQL**: Nombres en español que reflejan el dominio (`personal`, `asistencia`).

### Estructura de Archivos

- Un archivo por router/endpoint en el backend.
- Un archivo por repositorio, alineado con el endpoint que lo usa.
- Un archivo por schema Pydantic, alineado con el endpoint.
- Páginas del frontend en carpetas por módulo funcional.
- Componentes compartidos en `components/ui/`.

### Patrones de Código

- Los repositories retornan `dict` (no objetos ORM).
- Los endpoints usan `Annotated[Session, Depends(get_db)]` para inyección de DB.
- AccessScope se pasa como parámetro a repositories para filtrar datos por alcance.
- El frontend delega toda la autorización al backend; la UI solo oculta elementos
  según la matriz local de permisos.

### Enrutamiento API

- **API v1**: Prefijo `/api/v1` para endpoints estándar (empleados, asistencia, etc.).
- **API ZK**: Prefijo `/api/zk` para operaciones de dispositivos (registrado aparte).
- **Auth**: Prefijo `/api/v1/auth` para login y sesión.

## Observaciones e Inconsistencias

1. **EmployeeForm.jsx.bak**: Existe un archivo de backup en
   `frontend/src/components/employees/`. Probablemente temporal.

2. **EmployeeForm_actual.txt**: Snapshot extenso del componente EmployeeForm
   guardado en la raíz. Posiblemente usado como referencia durante refactoring.
   Contiene caracteres UTF-8 mal codificados (ej. "MiÃ©rcoles" en vez de "Miércoles").

3. **sonido.py**: Script experimental en la raíz de backend/ para reproducir
   sonidos en el reloj. No forma parte del flujo principal.

4. **Migración 059 duplicada**: Existe `database/059_consolidate_asistencias_diarias.sql`
   fuera de la carpeta `migrations/` y también dentro de ella.

5. **Mock data residual**: `frontend/src/data/mock*.js` contiene datos de prueba.
   Algunos componentes aún importan funciones de `mockCatalogs.js`
   (ej. `getScheduleDescription` en EmployeeForm).

6. **Dos clientes HTTP en frontend**: `api/client.js` (para endpoints v1) y
   `api/zkApi.js` (con su propio `request()` usando URL base distinta).
   La funcionalidad está duplicada.

7. **Carpeta hooks vacía**: `frontend/src/hooks/` existe pero está vacía.

8. **Numeración de migraciones con salto**: De 044 salta a 050 (sin 045-049).

9. **Endpoints auth registrados dos veces**: En `main.py`, el router de auth se
   registra con prefijo `/api/v1` pero el router ZK con `/api`. Esto genera que
   auth esté en `/api/v1/auth/login` mientras que ZK está en `/api/zk/health`.

10. **debug endpoint**: Existe `v1/endpoints/debug.py` con protección
    `require_roles("super_admin")`, pero **no está importado ni registrado** en
    `v1/router.py`. Actualmente inactivo.
