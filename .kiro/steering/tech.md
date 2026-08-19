# RelojDAE - Contexto Técnico

## Stack Tecnológico

### Backend

| Tecnología | Uso | Versión |
|------------|-----|---------|
| Python | Lenguaje principal del backend | 3.14 (según venv) |
| FastAPI | Framework web / API REST | Sin fijar en requirements.txt |
| Uvicorn | Servidor ASGI | Con extras `[standard]` |
| SQLAlchemy | ORM / Query builder (modo Core con `text()`) | Sin fijar |
| psycopg | Driver PostgreSQL (bindings binarias) | `psycopg[binary]` |
| Pydantic Settings | Configuración desde .env | pydantic-settings |
| python-dotenv | Carga de variables de entorno | Sin fijar |
| pyzk (zk) | Comunicación con relojes ZKTeco | Importado como `from zk import ZK` |

**Nota sobre requirements.txt**: No se fijan versiones exactas. Solo se listan
nombres de paquetes sin `==` ni `>=`.

### Frontend

| Tecnología | Uso | Versión |
|------------|-----|---------|
| React | UI library | ^19.2.6 |
| React DOM | Renderizado | ^19.2.6 |
| Vite | Build tool / dev server | ^8.0.12 |
| react-router-dom | Enrutamiento SPA | ^7.17.0 |
| Lucide React | Iconografía | ^1.17.0 |
| Recharts | Gráficas / visualizaciones | ^3.8.1 |
| ESLint | Linter | ^10.3.0 |
| @vitejs/plugin-react | Plugin Vite para React | ^6.0.1 |

**Nota**: No se usa TypeScript. El frontend es JSX puro. Los type packages
(`@types/react`, `@types/react-dom`) están en devDependencies pero no hay
evidencia de uso de TS en el código.

### Base de Datos

| Tecnología | Uso | Versión |
|------------|-----|---------|
| PostgreSQL | Base de datos relacional | No determinada (mínimo 12+ por features) |
| Schemas PostgreSQL | Organización lógica | `personal`, `asistencia`, `dispositivos`, `seguridad` |

### Dispositivos

| Tecnología | Uso |
|------------|-----|
| ZKTeco (hardware) | Relojes biométricos de asistencia |
| pyzk | Librería Python para protocolo ZK UDP/TCP |
| Protocolo ZK | Puerto 4370 (estándar ZKTeco) |

## Configuración

### Variables de Entorno Backend (.env)

```
# Aplicación
APP_NAME=RelojDAE API
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true
API_PREFIX=/api/v1

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=dae_reloj
POSTGRES_USER=reloj_app
POSTGRES_PASSWORD=<secreto>

DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# CORS
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Autenticación
AUTH_SECRET_KEY=<clave 32+ caracteres>
AUTH_ACCESS_TOKEN_MINUTES=480

# Reloj ZKTeco
ZK_IP=<ip_del_reloj>
ZK_PORT=4370
ZK_PASSWORD=171
ZK_TIMEOUT=5
ZK_FORCE_UDP=false
ZK_OMMIT_PING=false
ZK_ALLOW_WRITES=false
ZK_PROTECTED_USER_IDS=1
ZK_PROTECTED_NAMES=admin

# Sincronización de hora
ZK_AUTO_SYNC_TIME=true
ZK_ALLOW_TIME_SYNC=false
ZK_TIME_SYNC_MAX_CHECKS_PER_DAY=5
ZK_TIME_SYNC_MIN_INTERVAL_HOURS=4
ZK_MAX_TIME_DRIFT_SECONDS=120
```

### Variables de Entorno Frontend (.env)

```
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_ZK_API_BASE_URL=http://127.0.0.1:8000/api
```

## Autenticación y Seguridad

- **Tipo**: JWT HS256 implementado manualmente (sin dependencia de PyJWT).
- **Almacenamiento**: `localStorage` bajo clave `relojdae_access_token`.
- **Duración token**: Configurable (default 480 min = 8 horas).
- **Hash de passwords**: PBKDF2-SHA256 con 390,000 iteraciones y salt aleatorio.
- **Formato hash**: `pbkdf2_sha256$iteraciones$salt_b64$hash_b64`.
- **Control de acceso**: Sistema modular por módulos con AccessScope
  (TOTAL/AREA/PROPIO/NINGUNO) resuelto en backend. Nota: LECTURA existe como
  concepto frontend pero no como DataScope backend (ver architecture.md).
- **Auditoría de login**: Se registra cada intento (exitoso/fallido) con IP,
  user-agent, motivo del resultado.

## Entornos

| Entorno | Backend | Frontend |
|---------|---------|----------|
| Desarrollo | `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` | `npm run dev` (Vite, puerto 5173) |
| Producción | No configurado aún | `npm run build` genera `dist/` |

### Ejecución Local (según run.txt)

```powershell
# Backend
cd C:\RelojChecador\backend
.\.v_relojdae\Scripts\Activate.ps1
.\.v_relojdae\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd C:\RelojChecador\frontend
npm.cmd run dev
```

## Herramientas de Desarrollo

- **Virtual environment**: `.v_relojdae/` (Python venv local en backend/).
- **Jupyter/IPython**: Instalado en el venv (scripts/pruebas.ipynb para exploración).
- **Scripts de prueba**: `backend/scripts/` con smoke tests de ZKTeco.
- **ESLint**: Configurado para el frontend.
- **Documentación API**: FastAPI genera automáticamente en `/docs` (Swagger UI).

## Patrones Técnicos Clave

### Backend

- **Sin ORM models**: Se usa SQLAlchemy Core con `text()` para queries SQL raw.
  No hay modelos declarativos (Base, Table, etc.).
- **Repository pattern**: Cada módulo tiene su `*_repo.py` con funciones que
  ejecutan SQL directo y retornan diccionarios.
- **Pydantic para validación**: Schemas de entrada/salida definidos en `app/schemas/`.
- **Dependency Injection**: Mediante `Depends()` de FastAPI para DB session,
  autenticación y control de acceso.
- **Sin migraciones automáticas**: Las migraciones son scripts SQL manuales
  ejecutados con `psql` (sin Alembic).
- **Autorización mixta** (deuda técnica): Coexisten `require_module_access()`
  (sistema modular con AccessScope) y `require_roles()` (legacy). Ver
  `architecture.md` sección Seguridad para detalle.

### Frontend

- **Fetch nativo**: No usa axios. Cliente HTTP centralizado en `src/api/client.js`.
- **Context API**: AuthContext para estado de autenticación global.
- **Componentes funcionales**: Todo React hooks, sin clases.
- **Mock data**: Archivos en `src/data/mock*.js` (probablemente residuales
  del desarrollo inicial).
- **CSS puro**: Archivos `.css` sin preprocesadores ni Tailwind.
- **Dos clientes HTTP** (deuda técnica): `api/client.js` usa `VITE_API_BASE_URL`
  (/api/v1) y `api/zkApi.js` tiene su propio `request()` con `VITE_ZK_API_BASE_URL`
  (/api). Lógica duplicada.

### Base de Datos

- **Schemas PostgreSQL**: Separación lógica por dominio:
  - `personal` - empleados, puestos, unidades organizacionales
  - `asistencia` - marcaciones, asistencia diaria, horarios
  - `dispositivos` - relojes, relaciones empleado-dispositivo
  - `seguridad` - usuarios, roles, permisos, auditoría
- **Migraciones numeradas**: De 002 a 061, ejecutadas secuencialmente.
- **Sin ORM migrations**: No usa Alembic. SQL manual.
