# Estado del Proyecto — RelojChecador

**Última actualización:** 2026-11-05  
**Rama activa:** `hardening/nucleo-asistencia`  
**Tests:** 205/205 PASSING (0 FAIL, 0 XFAIL)

---

## Resumen ejecutivo

| Sección | Avance estimado |
|---------|----------------|
| Núcleo de asistencia (motor) | ~95% |
| Backend — API y endpoints | ~90% |
| Integración ZKTeco | ~75% |
| Frontend | ~80% |
| Tests | ~85% |
| Ops / producción | ~30% |
| **Total estimado** | **~75%** |

---

## 1. Núcleo de asistencia (`asistencia_procesamiento_repo.py`)

### Completado
- [x] Universo desde empleados activos + asignación vigente + fecha (§2 contrato)
- [x] Día laboral via calendario_eventos + horario_dias + fallback (§3)
- [x] Horario efectivo con soporte `cruza_medianoche` (§4, §12)
- [x] Política sin hardcoding — valores en segundos desde BD (§5)
- [x] Ausencia total → FALTA solo después de resolver 5 condiciones (§6)
- [x] OMISION_ENTRADA y OMISION_SALIDA con `requiere_revision = TRUE` (§7, §8)
- [x] Fuente: `marcaciones_crudas` exclusivamente (§9)
- [x] Múltiples marcaciones deterministas: MIN(entrada) / MAX(salida) (§11)
- [x] Idempotencia con `ON CONFLICT DO UPDATE` (§13)
- [x] Transaccionalidad explícita por lote (§14)
- [x] Jornadas en curso: no genera FALTA/OMISION_SALIDA prematura (§15)
- [x] Tiempo extra con margen configurable desde política (§19)
- [x] Autorización TOTAL/AREA/PROPIO/LECTURA en backend (§16)

### Pendiente / Deuda técnica
- [ ] `asistencia.marcaciones` (tabla legacy) — pendiente decisión formal (§9): no eliminar, no conectar, no migrar todavía
- [ ] Criterio exacto de "cierre de jornada" aún no formalizado como config (§15): funciona pero sin campo dedicado
- [ ] Fases 10–11 del orden de hardening (§20): Dashboard/AttendancePage y limpieza legacy

---

## 2. Backend — API, servicios y repositorios

### Completado
- [x] FastAPI + arquitectura en capas: endpoint → service → repository → schema
- [x] 23 endpoints registrados en `api/v1`
- [x] Autenticación JWT con primer login obligatorio y cambio de password
- [x] Auditoría de login (`login_auditoria`) con atribución por usuario
- [x] Control de acceso por módulo + alcance (TOTAL/AREA/PROPIO/LECTURA)
- [x] Roles: super_admin, rh_admin, supervisor, empleado, auditor, lectura
- [x] Empleados: CRUD integral (creación, edición, desactivación, vinculación ZK)
- [x] Horarios: asignación por empleado con vigencia
- [x] Políticas de asistencia: CRUD, vigencia, sin hardcoding
- [x] Calendario laboral: días no laborales, laborables extraordinarios
- [x] Incidencias: flujo empleado → supervisor (crear, aprobar, rechazar, justificar)
- [x] Reportes: JSON + CSV + PDF con logo institucional (branding)
- [x] Dashboard con métricas (asistencia, retardos, faltas, puntos)
- [x] Puntos acumulación + descansos obligatorios + faltas consecutivas
- [x] Dispositivos: CRUD, estado, hora
- [x] Auditoría general exportable
- [x] Catálogos (tipos de incidencia, puestos, unidades organizacionales)
- [x] Endpoint debug solo en `development` y solo para `super_admin`

### Pendiente / Deuda técnica
- [ ] No hay endpoint dedicado para periodos de evaluación (existe el servicio, no está expuesto en la API)
- [ ] `debug.py` debe desactivarse/eliminarse antes de producción formal
- [ ] Warning de httpx deprecation en `testclient` (cosmético, no funcional)
- [ ] Validar que reportes PDF generan correctamente con datos reales (solo probado con datos sintéticos)

---

## 3. Integración ZKTeco

### Completado
- [x] `ZKDeviceService` con manejo de timeout, desconexión y errores de protocolo
- [x] Endpoints: health, usuarios ZK, descargar marcaciones, sincronizar a BD, reconciliar
- [x] Resolución canónica de identidad: `dispositivos.empleado_dispositivo` (§10 contrato)
- [x] Fallback legacy a `personal.empleados.zk_user_id` cuando no hay relación canónica
- [x] Vinculación / desvinculación de empleado ↔ dispositivo ↔ ZK user ID
- [x] Conflicto ambiguo reportado explícitamente (no silencioso)
- [x] Sincronización de hora del dispositivo (`zk_time_sync_service`)
- [x] Estado de sincronización de tiempo en `runtime/zk_time_sync_state.json`

### Pendiente / Deuda técnica
- [ ] `personal.empleados.zk_user_id` campo legacy aún presente — migración completa a `empleado_dispositivo` pendiente (§10)
- [ ] Flujo de sincronización de empleados al reloj aún usa campo legacy en parte del flujo
- [ ] No hay tests de integración con reloj físico (ni pueden haberlos en CI)
- [ ] Validación de códigos `punch` (0–5) en hardware real pendiente (marcada como provisional en código)
- [ ] El endpoint `sync_zk_attendance_to_db` no tiene test de error parcial / rollback

---

## 4. Frontend (React + Vite)

### Páginas completadas
- [x] Auth: Login, ChangePassword (primer login)
- [x] Dashboard: métricas generales
- [x] Asistencia: AttendancePage (consulta diaria), AttendanceRawPage (marcaciones crudas)
- [x] Incidencias: IncidentsPage (lista), IncidentDetailPage (detalle + flujo)
- [x] Reportes: ReportsPage, DepartmentReportPage, EmployeeReportPage
- [x] Empleados: EmployeesPage, NewEmployeePage, EditEmployeePage, EmployeeDetailPage, EmployeeLinkingPage
- [x] Dispositivos: DevicesPage, DeviceDetailPage
- [x] Horarios: SchedulesPage
- [x] Calendario: CalendarPage
- [x] Auditoría: AuditPage
- [x] Configuración: SettingsPage
- [x] Usuarios del sistema: SystemUsersPage

### Pendiente / Deuda técnica
- [ ] No hay tests de frontend (ni unitarios ni E2E)
- [ ] Validar AttendancePage con datos reales de múltiples empleados y fechas
- [ ] Validar Dashboard con volumen real (datos actuales son sintéticos de prueba)
- [ ] No se ha probado el flujo completo de incidencias de supervisor en UI real
- [ ] Revisar comportamiento de `requiere_revision` en AttendancePage — ¿se muestra correctamente?
- [ ] Responsive / mobile: no revisado

---

## 5. Tests

### Estado actual: 205/205 PASSING

| Archivo | Tests | Estado |
|---------|-------|--------|
| `test_auditoria.py` | 12 | ✅ PASS |
| `test_authorization_http.py` | 6 | ✅ PASS |
| `test_characterization.py` | 28 | ✅ PASS |
| `test_contract.py` | 19 | ✅ PASS |
| `test_dashboard.py` | 6 | ✅ PASS |
| `test_infra_integration.py` | 23 | ✅ PASS |
| `test_motor_integration.py` | 35 | ✅ PASS |
| `test_politicas_asistencia.py` | 20 | ✅ PASS |
| `test_puntos_acumulacion.py` | 5 | ✅ PASS |
| `test_reportes.py` | 22 | ✅ PASS |
| `test_usuarios_alta.py` | 16 | ✅ PASS |
| `test_zk_identity_resolution.py` | 11 | ✅ PASS |

### Áreas sin cobertura de tests
- [ ] Endpoints de reportes PDF (solo JSON y CSV cubiertos)
- [ ] Flujo completo de incidencias supervisor → empleado con HTTP real
- [ ] Branding / subida de logo
- [ ] Sincronización ZK con dispositivo físico (inherentemente no automatizable)
- [ ] Periodos de evaluación (servicio existe, sin tests propios)
- [ ] Frontend (ningún test)

---

## 6. Base de datos y migraciones

### Estado
- [x] 69 migraciones definidas (002 → 069)
- [x] Esquema separado por namespace: `personal`, `asistencia`, `dispositivos`, `seguridad`, `auditoria`
- [x] Constraints, FK e índices definidos
- [x] Datos sintéticos para pruebas: `relojdae_datos_sinteticos_*.sql`
- [x] Seeds de roles, permisos, organigrama, usuarios prueba

### Pendiente
- [ ] No hay herramienta de migración automática (Alembic u otro) — migraciones se aplican manualmente
- [ ] `059_consolidate_asistencias_diarias.sql` está fuera del directorio `migrations/` — pendiente organizar
- [ ] Validar que las 69 migraciones están aplicadas en el entorno de desarrollo (no hay tracking automático)

---

## 7. Operaciones / Producción

### Completado
- [x] Variables de entorno via `.env`
- [x] `requirements.txt` y `requirements-dev.txt` separados
- [x] Scripts utilitarios en `backend/scripts/`
- [x] Backup PostgreSQL (`scripts/backup_postgres.py`)

### Pendiente (crítico antes de producción)
- [ ] No hay Docker / docker-compose
- [ ] No hay CI/CD (GitHub Actions u otro)
- [ ] No hay configuración de servidor web (nginx, gunicorn)
- [ ] No hay manejo de logs estructurados (solo logging básico)
- [ ] No hay monitoreo ni alertas
- [ ] No hay script de despliegue documentado
- [ ] `DEBUG=True` debe desactivarse explícitamente en producción
- [ ] CORS `allow_origins` debe restringirse en producción
- [ ] El endpoint `/debug/schema` solo está protegido por rol y entorno, no eliminado del binario

---

## 8. Hardening del núcleo — Avance por fase (§20 contrato)

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Infraestructura de tests | ✅ Completa |
| 2 | Tests del comportamiento esperado | ✅ Completa |
| 3 | Refactorizar procesamiento de asistencia | ✅ Completa |
| 4 | Integrar políticas | ✅ Completa |
| 5 | Validar calendario y horario_dias | ✅ Completa |
| 6 | Validar turnos nocturnos | ✅ Completa |
| 7 | Validar idempotencia y transacciones | ✅ Completa |
| 8 | Validar permisos | ✅ Completa |
| 9 | Corregir integración ZKTeco | ⚠️ Parcial — identidad canónica OK, migración legacy pendiente |
| 10 | Corregir Dashboard y AttendancePage | ⚠️ Pendiente validación con datos reales |
| 11 | Atender tablas/código legacy | ⬜ No iniciada formalmente |

---

## 9. Siguiente trabajo recomendado

Ordenado por impacto / riesgo:

1. **Fase 9 completa:** migrar flujo de sincronización al campo canónico, deprecar `zk_user_id` en `personal.empleados`
2. **Fase 10:** validar Dashboard y AttendancePage con una sesión real de datos (captura con reloj o datos sintéticos ajustados)
3. **Fase 11:** decidir destino de `asistencia.marcaciones` (legacy) y `debug.py`
4. **Ops básico:** `docker-compose` mínimo para desarrollo reproducible
5. **Tests faltantes:** reportes PDF, flujo HTTP de incidencias, periodos de evaluación

---

## Archivos clave

| Rol | Ruta |
|-----|------|
| Contrato del núcleo | `docs/CONTRATO_NUCLEO_ASISTENCIA.md` |
| Motor de procesamiento | `backend/app/repositories/asistencia_procesamiento_repo.py` |
| Endpoints asistencia | `backend/app/api/v1/endpoints/asistencia.py` |
| Identidad ZK | `backend/app/repositories/zk_employee_link_repo.py` |
| Puntos / descansos | `backend/app/services/puntos_acumulacion_service.py` |
| Router principal | `backend/app/api/v1/router.py` |
| Config y tests | `backend/pytest.ini`, `backend/tests/conftest.py` |
| Migraciones | `database/migrations/` |
