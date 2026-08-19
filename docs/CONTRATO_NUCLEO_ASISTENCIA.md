# Contrato del Núcleo de Asistencia — RelojDAE

**Rama:** `hardening/nucleo-asistencia`  
**Fecha de creación:** 19 de agosto de 2026  
**Estado:** VIGENTE — todo cambio al motor debe respetar este documento.

---

## 1. Fuente oficial del resultado diario

La única tabla oficial del resultado diario es:

```
asistencia.asistencias_diarias
```

No se crearán tablas alternativas como `asistencia.asistencia_diaria`.

---

## 2. Universo del procesamiento

El procesamiento **NO** debe comenzar desde las marcaciones.

Debe comenzar desde:

```
empleados activos + asignación de horario vigente + fecha a evaluar
```

Para cada empleado y fecha se resuelve primero si debía laborar.  
Después se consultan sus marcaciones mediante LEFT JOIN o lógica equivalente.

Un empleado con **cero marcaciones** debe existir dentro del universo del procesamiento.

Queda eliminado conceptualmente el modelo:

```
marcaciones → procesar presentes → parche posterior de faltantes
```

El objetivo es un único flujo coherente.

---

## 3. Calendario y día laboral

La resolución respeta la arquitectura existente del calendario.

**Prioridad:**

1. Evento explícito del calendario laboral (`asistencia.calendario_eventos`).
2. `asistencia.horario_dias`.
3. Comportamiento por defecto definido por `calendario_service`.

**Reglas:**

- Los eventos `DIA_NO_LABORAL` nunca pueden producir `FALTA` únicamente por ausencia de marcaciones.
- Los eventos `LABORABLE_EXTRAORDINARIO` sí permiten procesamiento normal.
- No debe existir un segundo bloque de generación de faltas que ignore esta resolución.

---

## 4. Horario

Fuente:

```
asistencia.asignaciones_horario
  → asistencia.horarios
  → asistencia.horario_dias
```

La asignación debe estar vigente para la fecha procesada.

`horario_dias` debe poder sobrescribir entrada/salida del horario base para el día correspondiente.

Debe soportarse explícitamente `cruza_medianoche`.

---

## 5. Política de asistencia

La fuente oficial de reglas es:

```
asistencia.politicas_asistencia
```

**Queda prohibido** utilizar en el motor valores hardcodeados como:

- 10 minutos
- 20 minutos
- 30 minutos
- 1 punto
- 2 puntos
- 10 puntos para descanso
- `politica_asistencia_id = 1`

El motor debe resolver una política vigente para la fecha procesada.

La clasificación debe utilizar los límites almacenados **en segundos** para no perder precisión en fronteras como `08:10:59`, `08:20:59` y `08:30:59`.

**Regla de clasificación:**

| Condición | Estatus |
|-----------|---------|
| Llegada en hora o antes de la entrada programada | `COMPLETO` |
| Después de entrada y dentro de `limite_tolerancia_segundos` | `TOLERANCIA` |
| Después de tolerancia y dentro de `limite_retardo_menor_segundos` | `RETARDO_MENOR` |
| Después de retardo menor y dentro de `limite_retardo_mayor_segundos` | `RETARDO_MAYOR` |
| Después del límite mayor | `FALTA` |

Los puntos deben proceder igualmente de la política:

- `TOLERANCIA` → 0 puntos
- `RETARDO_MENOR` → `puntos_retardo_menor`
- `RETARDO_MAYOR` → `puntos_retardo_mayor`
- `FALTA` → 0 puntos (la falta se contabiliza como evento, no como puntos)

**Unicidad de política:**

Debe existir **exactamente una** política aplicable por (empleado, fecha). El motor debe resolver la política vigente según las fechas de vigencia (`vigencia_desde`, `vigencia_hasta`) y el estado `activo`.

- Si existen **cero políticas** aplicables → el procesamiento debe producir un error explícito y auditable para ese empleado/fecha. No se permite procesar sin política.
- Si existen **múltiples políticas** incompatibles (rangos de vigencia solapados) → el procesamiento debe producir un error explícito y auditable. No se permite seleccionar silenciosamente la primera ni la más reciente sin criterio documentado.
- El error debe registrarse de forma que un administrador pueda identificar y corregir la configuración.

---

## 6. Ausencia total

Un empleado que debía laborar y tiene cero marcaciones puede producir `FALTA`.

Pero **únicamente** después de resolver:

1. Empleado activo.
2. Asignación de horario vigente.
3. Día laboral (según calendario + horario_dias).
4. Horario efectivo.
5. Política vigente.

Nunca se generará `FALTA` simplemente porque no exista una fila en `marcaciones_crudas`.

---

## 7. Omisiones

Si existe entrada pero no salida, cuando ya sea válido evaluar la salida:

```
estatus = OMISION_SALIDA
```

Si existe salida pero no entrada:

```
estatus = OMISION_ENTRADA
```

Ambas deben marcar:

```
requiere_revision = TRUE
```

---

## 8. Revisión

`requiere_revision` es un atributo **independiente** del `estatus`.

No se creará un estatus ficticio `REVISION`.

Una fila puede ser simultáneamente:

```
estatus = FALTA
requiere_revision = TRUE
```

---

## 9. Marcaciones

Para esta fase de hardening, la fuente utilizada por el núcleo sigue siendo:

```
asistencia.marcaciones_crudas
```

`asistencia.marcaciones` queda clasificada como implementación paralela/legacy pendiente de decisión.

- NO eliminarla.
- NO migrarla todavía.
- NO conectar el procesamiento a ambas simultáneamente.

---

## 10. Identidad ZK

Existe actualmente duplicidad entre:

```
personal.empleados.zk_user_id
dispositivos.empleado_dispositivo.zk_user_id
```

**Arquitectura objetivo:**

`dispositivos.empleado_dispositivo` será la relación canónica empleado ↔ dispositivo ↔ usuario ZK.

`personal.empleados.zk_user_id` permanecerá temporalmente como compatibilidad durante el hardening.

- No eliminar columnas.
- No cambiar todavía el flujo de sincronización.
- Se resolverá en una fase posterior independiente.

---

## 11. Múltiples marcaciones

El motor debe manejar múltiples checadas de forma determinista.

Como mínimo:

- Primera marcación clasificada como entrada (`MIN(fecha_hora)` del día entre marcaciones de entrada).
- Última marcación clasificada como salida (`MAX(fecha_hora)` del día o día siguiente si cruza medianoche, entre marcaciones de salida).

Los códigos numéricos de punch (`0`, `1`, etc.) son detalles del adaptador/mapeo ZKTeco y no forman parte de este contrato del núcleo. El motor trabaja con marcaciones ya clasificadas como "entrada" o "salida" independientemente del protocolo de origen.

Las marcaciones duplicadas no deben generar más de una asistencia diaria por (empleado, fecha).

---

## 12. Turnos que cruzan medianoche

El procesamiento debe asociar correctamente la salida del día siguiente con la jornada iniciada el día anterior.

No se debe construir siempre entrada y salida usando la misma fecha.

Detección: `hora_salida < hora_entrada` implica cruce de medianoche.

---

## 13. Idempotencia

Procesar dos veces `(empleado, fecha)` debe producir el mismo resultado final.

La restricción única existente de `asistencias_diarias (empleado_id, fecha)` debe respetarse.

El reprocesamiento debe actualizar de forma determinista el resultado cuando corresponda (vía `ON CONFLICT DO UPDATE`).

---

## 14. Transaccionalidad

El procesamiento debe definir una unidad transaccional explícita.

**Garantía mínima:** una fecha/unidad lógica de procesamiento nunca puede quedar parcialmente procesada. Si se procesan N empleados para una fecha, o todos se persisten correctamente o ninguno de esa unidad se persiste.

La granularidad definitiva de la transacción (por fecha, por lote, por rango completo) debe considerar:

- Integridad de datos.
- Volumen esperado de registros.
- Tiempo de bloqueo en PostgreSQL.
- Capacidad de reintentar lotes fallidos sin corromper datos ya procesados.

No se impone que todo un rango extenso sea una única transacción atómica, pero sí que no existan estados intermedios incoherentes dentro de una unidad lógica.

---

## 15. Evaluación de jornadas en curso

Queda **prohibido** generar resultados definitivos que dependan de marcaciones futuras mientras la jornada siga abierta.

**Reglas específicas:**

- `FALTA` por ausencia total: no debe generarse para el día en curso si la hora de salida programada del empleado aún no ha pasado. El empleado puede no haber llegado todavía.
- `OMISION_SALIDA`: no debe generarse mientras el turno del empleado siga dentro de su ventana válida de salida. Un empleado cuyo turno termina a las 16:00 no puede marcarse como omisión de salida a las 14:00.
- El motor debe considerar el **momento actual** respecto al horario efectivo de la jornada al determinar si un resultado es definitivo o prematuro.
- No se puede generar `OMISION_SALIDA` mientras todavía sea razonablemente posible registrar la salida dentro de la jornada que se está evaluando.
- No se puede cerrar anticipadamente una jornada usando valores hardcodeados.
- Si la jornada aún está abierta y no es posible clasificar definitivamente, el registro **no debe crearse** o debe marcarse con un estatus provisional que no genere puntos ni penalizaciones.
- Al reprocesar después de que la jornada cierre, el motor debe poder generar el resultado definitivo correcto.

**Criterio de cierre de jornada:**

El criterio exacto de cuándo una jornada se considera cerrada para evaluación definitiva deberá definirse durante la implementación mediante reglas existentes y tests.

- No crear campos, tablas ni constantes nuevas para un margen de cierre.
- Si posteriormente se determina que hace falta un margen adicional configurable, deberá identificarse primero una fuente de configuración existente (por ejemplo, un campo en `politicas_asistencia` o en `horarios`) o aprobarse explícitamente una modificación al contrato.
- No inventar nuevas configuraciones sin justificación.

---

## 16. Autorización

Mantener la protección actual:

```python
require_module_access("ASISTENCIA", "editar")
```

Con la comprobación de acceso completo (`has_complete_access`) para ejecutar procesamiento global.

**Alcances en backend (obligatorio):**

Los alcances `TOTAL`, `AREA`, `PROPIO` y `LECTURA` **deben aplicarse en backend** en los endpoints de consulta y procesamiento. Nunca depender exclusivamente de filtros en React o lógica de frontend para restringir acceso a datos.

- `TOTAL`: sin restricción de datos.
- `AREA`: el backend filtra por unidades organizacionales asignadas al usuario.
- `PROPIO`: el backend filtra por `empleado_id` vinculado al usuario.
- `LECTURA`: el backend permite consulta pero prohíbe operaciones de escritura/procesamiento.

Un usuario que invoque directamente la API sin pasar por el frontend debe recibir las mismas restricciones.

La autorización deberá cubrirse mediante tests.

---

## 17. Regla de cambio

A partir de este contrato:

- No crear nuevas tablas para resolver problemas existentes.
- No agregar columnas sin justificar por qué las actuales no sirven.
- No duplicar fuentes de verdad.
- No hardcodear reglas configurables.
- No modificar frontend para ocultar errores del motor.
- No eliminar estructuras legacy hasta completar migración y pruebas.
- No modificar migraciones históricas aplicadas.
- Todo cambio del motor debe estar respaldado por tests.

---

## 18. Orden de hardening

| Fase | Descripción |
|------|-------------|
| 1 | Crear infraestructura de tests |
| 2 | Crear tests del comportamiento esperado |
| 3 | Refactorizar procesamiento de asistencia |
| 4 | Integrar políticas |
| 5 | Validar calendario y horario_dias |
| 6 | Validar turnos nocturnos |
| 7 | Validar idempotencia y transacciones |
| 8 | Validar permisos |
| 9 | Corregir integración ZKTeco |
| 10 | Corregir Dashboard y AttendancePage |
| 11 | Atender tablas/código legacy |

---

## Firmas

Este documento es el contrato obligatorio para todo desarrollo sobre el núcleo de asistencia.

Cualquier PR que modifique el motor debe demostrar conformidad con estas reglas o solicitar una enmienda formal al contrato.
