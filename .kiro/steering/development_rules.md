# RelojDAE - Reglas de Desarrollo para Agentes

## Principio general

RelojDAE es un sistema en desarrollo activo con funcionalidades ya implementadas,
migraciones SQL existentes, integración con PostgreSQL, frontend React, backend
FastAPI y dispositivos biométricos ZKTeco.

Los cambios deben ser incrementales, verificables y compatibles con la arquitectura
actual.

Antes de modificar código, analizar siempre todas las capas relacionadas.

---

## 1. Análisis obligatorio antes de modificar

Antes de realizar cualquier cambio:

1. Identificar el archivo principal involucrado.
2. Revisar sus imports.
3. Buscar todos sus consumidores.
4. Revisar endpoints relacionados.
5. Revisar schemas Pydantic relacionados.
6. Revisar repositories relacionados.
7. Revisar services relacionados.
8. Revisar tablas y migraciones relacionadas.
9. Revisar clientes API del frontend relacionados.
10. Revisar componentes y páginas React relacionados.

Cuando una modificación afecte contratos entre capas, analizar siempre:

Frontend
→ API
→ Schema
→ Service
→ Repository
→ PostgreSQL

No modificar una sola capa si el cambio requiere coordinación entre varias.

---

## 2. Estrategia de cambios

Preferir cambios:

- pequeños
- incrementales
- verificables
- reversibles

Evitar refactors masivos mientras se implementan funcionalidades.

No reescribir módulos completos únicamente por razones de estilo.

No modificar código que funciona correctamente si no existe una razón técnica
concreta.

Separar siempre que sea posible:

- corrección de bugs
- nuevas funcionalidades
- refactoring
- cambios de base de datos
- mejoras visuales

---

## 3. Operaciones prohibidas sin autorización explícita

No ejecutar automáticamente:

- git commit
- git push
- git reset --hard
- git clean
- DROP TABLE
- DROP SCHEMA
- TRUNCATE
- DELETE masivos
- eliminación de datos reales
- eliminación de migraciones existentes
- sobrescritura de archivos .env
- operaciones destructivas sobre relojes ZKTeco

No modificar secretos ni credenciales.

No realizar cambios irreversibles sin autorización explícita.

---

## 4. Git

Antes de realizar cambios importantes ejecutar o revisar:

git status

Nunca asumir que el working tree está limpio.

No sobrescribir modificaciones locales existentes.

No eliminar archivos no versionados sin analizar primero su propósito.

Al finalizar una tarea informar:

- archivos modificados
- archivos creados
- archivos eliminados
- pruebas ejecutadas
- pruebas pendientes
- riesgos conocidos

Solo realizar commit o push cuando sea solicitado explícitamente.

---

## 5. PostgreSQL

PostgreSQL es la fuente de verdad para datos persistentes.

Las migraciones existentes deben tratarse como históricas.

Si se necesita modificar el esquema:

crear una nueva migración SQL.

No editar silenciosamente una migración que ya pudo haber sido ejecutada.

Antes de crear una migración revisar:

1. migraciones anteriores relacionadas
2. tablas existentes
3. foreign keys
4. constraints
5. índices
6. datos existentes
7. repositories afectados
8. schemas Pydantic afectados
9. endpoints afectados
10. frontend afectado

Utilizar transacciones cuando una operación de escritura requiera atomicidad.

No realizar cambios destructivos sobre datos existentes sin autorización.

---

## 6. Marcaciones biométricas

Las marcaciones provenientes de los relojes ZKTeco son datos fuente.

Las marcaciones crudas deben conservarse sin modificaciones destructivas.

No corregir resultados de asistencia modificando marcaciones originales.

Las correcciones deben realizarse sobre:

- lógica de procesamiento
- registros derivados
- configuraciones
- incidencias

según corresponda.

Toda sincronización debe prevenir duplicados.

La sincronización debe ser idempotente cuando sea técnicamente posible.

---

## 7. Integración ZKTeco

Los dispositivos ZKTeco deben tratarse como sistemas externos potencialmente
no disponibles.

Toda comunicación con dispositivos debe considerar:

- timeout
- pérdida de conexión
- errores de red
- dispositivo ocupado
- respuestas inesperadas
- reconexión
- cleanup
- disconnect

Cerrar siempre correctamente la conexión al dispositivo.

No dejar el reloj deshabilitado después de una operación fallida.

Respetar las variables de seguridad existentes:

- ZK_ALLOW_WRITES
- ZK_PROTECTED_USER_IDS
- ZK_PROTECTED_NAMES

No borrar ni modificar usuarios protegidos del reloj.

No ejecutar operaciones destructivas sobre dispositivos durante auditorías,
pruebas o análisis.

---

## 8. Backend FastAPI

Mantener separación de responsabilidades.

### Endpoints

Responsables de:

- HTTP
- validación inicial
- autenticación
- autorización
- coordinación

Los endpoints deben permanecer ligeros.

### Schemas

Los schemas Pydantic definen:

- contratos de entrada
- contratos de salida
- validaciones

### Repositories

Responsables de:

- consultas SQL
- persistencia
- acceso a PostgreSQL

No colocar lógica visual ni lógica del frontend en repositories.

### Services

Responsables de:

- lógica de negocio compleja
- procesos de múltiples pasos
- coordinación entre repositories
- integración con dispositivos externos

No introducir lógica compleja directamente en endpoints si corresponde a un
service.

---

## 9. Frontend React

Mantener componentes funcionales y hooks.

Centralizar llamadas HTTP dentro de:

frontend/src/api/

No realizar fetch dispersos directamente desde componentes cuando exista o
deba existir un cliente API.

No duplicar reglas críticas de negocio dentro de React.

Las validaciones frontend mejoran la experiencia de usuario, pero las
validaciones definitivas deben existir en backend.

Evitar componentes excesivamente grandes.

Cuando un componente sea demasiado grande, primero analizar y proponer una
separación antes de realizar un refactor amplio.

---

## 10. Seguridad y permisos

La autorización real siempre debe ejecutarse en backend.

Los permisos del frontend sirven para:

- navegación
- ocultar opciones
- experiencia de usuario

pero no constituyen una frontera de seguridad.

No confiar únicamente en:

- ProtectedRoute
- botones ocultos
- botones deshabilitados
- menús ocultos
- permisos calculados en frontend

Todo endpoint sensible debe validar autorización en backend.

Mantener los roles existentes:

- super_admin
- rh_admin
- supervisor
- empleado
- auditor

No crear nuevos roles ni cambiar permisos existentes sin analizar primero toda
la matriz de acceso.

---

## 11. Contratos frontend / backend

Cuando se modifique un endpoint revisar siempre:

- método HTTP
- URL
- path parameters
- query parameters
- request body
- response body
- códigos HTTP
- nombres de campos
- tipos
- campos obligatorios
- campos opcionales
- manejo de errores

Después buscar todos los consumidores frontend.

No cambiar silenciosamente nombres de campos utilizados por React.

---

## 12. Código temporal y legado

No eliminar automáticamente archivos aparentemente obsoletos.

Ejemplos existentes:

- EmployeeForm.jsx.bak
- EmployeeForm_actual.txt
- mock*.js
- sonido.py
- debug.py
- migraciones aparentemente duplicadas

Antes de eliminar cualquier archivo:

1. buscar referencias
2. analizar imports
3. revisar Git
4. determinar su función

Clasificarlo como:

- SAFE_TO_DELETE
- REQUIRES_REVIEW
- STILL_IN_USE

La eliminación requiere autorización.

---

## 13. Testing

Después de cualquier modificación relevante:

1. comprobar sintaxis
2. comprobar imports
3. ejecutar tests relacionados disponibles
4. ejecutar ESLint cuando corresponda
5. comprobar endpoints afectados
6. comprobar contratos frontend/backend
7. revisar errores de consola
8. revisar errores del backend
9. comprobar regresiones evidentes

No afirmar que algo funciona si no fue probado.

Diferenciar claramente entre:

- analizado
- modificado
- probado
- no probado

Si una prueba no pudo ejecutarse, indicarlo explícitamente.

---

## 14. Auditorías

Cuando se solicite una auditoría:

NO modificar código inicialmente.

Primero analizar y producir hallazgos.

Clasificar problemas como:

- CRITICAL
- HIGH
- MEDIUM
- LOW
- INFORMATIONAL

Cada hallazgo debe incluir cuando sea posible:

- archivo
- ubicación
- problema
- impacto
- evidencia
- solución propuesta

Separar hechos comprobados de recomendaciones.

No presentar preferencias de estilo como errores.

---

## 15. Regla de no invención

No asumir que una funcionalidad existe solamente porque aparece en:

- documentación
- comentarios
- mock data
- nombres de archivos
- código antiguo

Verificar siempre contra el código actual.

Si la documentación y el código difieren, reportar la discrepancia.

No inventar:

- endpoints
- tablas
- columnas
- roles
- variables de entorno
- funcionalidades
- dependencias

---

## 16. Prioridad de fuentes

Para determinar cómo funciona realmente el sistema utilizar este orden:

1. código actual
2. esquema actual de PostgreSQL
3. migraciones ejecutadas
4. configuración actual
5. tests
6. steering/documentación
7. comentarios
8. mock data

Si existen contradicciones, reportarlas antes de modificar código.

---

## 17. Regla final

Ante una modificación con riesgo significativo:

analizar
→ explicar
→ proponer
→ esperar aprobación
→ implementar
→ probar
→ reportar resultados

No utilizar la estrategia "arreglar todo" de manera automática.

---

## 18. Deuda técnica conocida

Este inventario se mantiene actualizado conforme se detectan inconsistencias.
Ninguna de estas entradas debe corregirse sin análisis previo y autorización.

### CRÍTICA

| ID | Descripción | Archivos relacionados | Impacto |
|----|-------------|----------------------|---------|
| ~~DT-01~~ | ~~RESUELTO~~ — LECTURA ya no se usa como DataScope. El frontend define al auditor con `TOTAL` + `canRead: true` + `canExport: true` sin capacidades de escritura, que es exactamente lo que el backend tiene en `seguridad.permisos_rol`. La función `isReadOnly()` en `utils/permissions.js` cubre el caso de "solo lectura" sin necesidad de un DataScope especial. | — | — |

### ALTA

| ID | Descripción | Archivos relacionados | Impacto |
|----|-------------|----------------------|---------|
| ~~DT-02~~ | ~~RESUELTO~~ — Acumulación de puntos implementada en `puntos_acumulacion_service.py`. Se ejecuta automáticamente después del procesamiento de asistencia diaria. Detecta 10pts→DO, 7DO→revisión baja, 3 faltas consecutivas→revisión baja. | — | — |
| ~~DT-03~~ | ~~RESUELTO~~ — Cruce de medianoche implementado en `asistencia_procesamiento_repo.py`. `_calcular_salida_programada` suma 1 día si `hora_salida < hora_entrada`. La query busca salidas en el día siguiente para turnos nocturnos. | — | — |
| ~~DT-04~~ | ~~RESUELTO~~ — Todos los endpoints activos usan `require_module_access`. Solo `debug.py` (inactivo, no registrado en router) usa `require_roles`. `catalogos.py` usa `get_current_user` intencionalmente (catálogos accesibles por cualquier usuario autenticado). | — | — |

### MEDIA

| ID | Descripción | Archivos relacionados | Impacto |
|----|-------------|----------------------|---------|
| DT-05 | Umbrales de puntualidad (10/20/30 min) hardcoded vs `tolerancia_entrada_minutos` configurable | `asistencia_procesamiento_repo.py` | El campo configurable existe pero se ignora |
| DT-06 | Vinculación directa ZK no valida si `zk_user_id` está asignado a otro empleado | `zk_employee_link_repo.py`, `api/routes/zk.py` | Posible doble asignación de usuario reloj |
| DT-07 | `debug.py` existe pero no está registrado en `v1/router.py` | `v1/endpoints/debug.py`, `v1/router.py` | Código inactivo sin clasificar (no se sabe si fue desactivado intencionalmente) |

### BAJA

| ID | Descripción | Archivos relacionados | Impacto |
|----|-------------|----------------------|---------|
| DT-08 | Roles no centralizados en backend (strings dispersos) | `auth_dependencies.py`, múltiples endpoints | Riesgo de typo en nombres de rol |
| DT-09 | Dos clientes HTTP en frontend con lógica duplicada | `api/client.js`, `api/zkApi.js` | Mantenimiento duplicado |

### Reglas para esta sección

- No corregir deuda técnica automáticamente durante implementación de features.
- Cada corrección requiere análisis de impacto previo.
- Las entradas se agregan al detectar inconsistencias y se eliminan al resolverlas.
- No convertir entradas de deuda técnica en features implementadas sin código.