# RelojDAE - Principios de Arquitectura

## Arquitectura general

RelojDAE utiliza una arquitectura web por capas.

Flujo principal:

ZKTeco
→ FastAPI
→ PostgreSQL
→ API REST
→ React

Para asistencia:

ZKTeco
→ marcaciones_crudas
→ procesamiento
→ asistencias_diarias
→ FastAPI
→ React

Las marcaciones biométricas originales son datos fuente y deben conservarse.

---

## Backend

Mantener la separación:

Router / Endpoint
→ Schema
→ Service cuando exista lógica de negocio
→ Repository
→ PostgreSQL

### Endpoint

Responsable de:

- HTTP
- autenticación
- autorización
- validación de parámetros
- coordinación

Los endpoints deben mantenerse ligeros.

### Schema

Responsable de:

- request models
- response models
- validación de estructura
- tipos

### Repository

Responsable del acceso a PostgreSQL.

Debe concentrar:

- SELECT
- INSERT
- UPDATE
- DELETE controlados
- joins
- filtros
- transacciones relacionadas con persistencia

No introducir lógica de presentación.

### Service

Utilizar services para:

- lógica de negocio compleja
- coordinación de múltiples repositories
- procesamiento de asistencia
- integración ZKTeco
- procesos de varios pasos
- operaciones externas

No crear services innecesarios para operaciones CRUD simples.

---

## Frontend

React es responsable de:

- interfaz
- interacción
- navegación
- formularios
- visualización
- experiencia de usuario

Las llamadas HTTP deben centralizarse en:

frontend/src/api/

No duplicar lógica crítica de negocio dentro del frontend.

Las validaciones frontend sirven para UX.

El backend continúa siendo la autoridad sobre:

- permisos
- reglas de negocio
- integridad
- resultados de procesamiento

---

## PostgreSQL

PostgreSQL es la fuente de verdad de datos persistentes.

La integridad importante debe protegerse mediante:

- primary keys
- foreign keys
- unique constraints
- check constraints
- índices

cuando corresponda.

Los cambios estructurales deben realizarse mediante nuevas migraciones SQL.

No modificar migraciones históricas ejecutadas.

---

## ZKTeco

Los dispositivos ZKTeco son sistemas externos.

La comunicación con el dispositivo debe permanecer aislada dentro de la capa
correspondiente.

El resto de la aplicación no debe depender directamente de pyzk.

Preferir:

Endpoint
→ Service ZKTeco
→ pyzk
→ dispositivo

y no:

Endpoint
→ llamadas directas dispersas a pyzk

La aplicación debe tolerar que el reloj:

- esté apagado
- esté desconectado
- tenga timeout
- tenga diferencia de hora
- responda parcialmente
- se encuentre ocupado

---

## Marcaciones

Las marcaciones crudas constituyen evidencia fuente del dispositivo.

No modificar destructivamente una marcación cruda para corregir una asistencia.

Los resultados derivados deben poder recalcularse a partir de los datos fuente
cuando la arquitectura lo permita.

La sincronización debe evitar duplicados.

---

## Seguridad

La autorización real pertenece al backend.

Frontend:

ProtectedRoute
→ UX

Backend:

Depends()
→ autenticación
→ autorización
→ AccessScope
→ seguridad real

Ocultar elementos en React nunca sustituye la autorización de FastAPI.

### AccessScope — DataScope reales

Los DataScope reconocidos actualmente por `access_control.py` son:

- TOTAL
- AREA
- PROPIO
- NINGUNO

LECTURA **no** es un DataScope backend. Existe únicamente como concepto
frontend para el rol auditor. La correspondencia con backend está pendiente
de diseño (ver `business_rules.md` sección Alcances).

### Deuda técnica: sistema de autorización unificado

Todos los endpoints activos del sistema utilizan `require_module_access()`.
La migración desde `require_roles()` está completada.

Casos especiales correctos:
- `catalogos.py` usa `get_current_user` — los catálogos son datos de referencia
  accesibles para cualquier usuario autenticado sin restricción de módulo.
- `auth.py` `/me` usa `get_current_user` — endpoint de identidad.
- `debug.py` usa `require_roles("super_admin")` pero NO está registrado en el
  router (inactivo).

### debug.py — endpoint no registrado

El archivo `backend/app/api/v1/endpoints/debug.py` existe y contiene endpoints
protegidos por `require_roles("super_admin")`. Sin embargo, **no está importado
ni registrado** en `backend/app/api/v1/router.py`.

Esto significa que debug.py está actualmente inactivo. No se eliminará sin
análisis previo, pero su estado debe considerarse al modificar el router.

---

## Contratos

Los contratos frontend/backend deben mantenerse estables.

Antes de modificar:

- endpoint
- método HTTP
- payload
- response
- nombres de campos
- tipos

buscar todos sus consumidores.

---

## Arquitectura evolutiva

No introducir tecnologías nuevas sin necesidad técnica demostrable.

No agregar:

- Redux
- otro ORM
- Alembic
- Axios
- nuevos frameworks
- nuevas capas

solo por preferencia.

Primero evaluar si la arquitectura existente resuelve correctamente el problema.

Evitar sobrearquitectura.

---

## Principio de responsabilidad única

Cuando un archivo acumule demasiadas responsabilidades:

1. identificar responsabilidades;
2. proponer separación;
3. verificar dependencias;
4. realizar refactor incremental.

No dividir archivos únicamente para reducir líneas de código.