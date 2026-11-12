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

## 11. Múltiples marcaciones — modelo de sesiones

El motor debe manejar múltiples checadas de forma determinista mediante **emparejamiento posicional cronológico**.

**Regla de emparejamiento:**

Todas las marcaciones del día se ordenan por `fecha_hora ASC` y se emparejan posicionalmente:

```
Marca 1 (posición impar)  → entrada  ┐ Sesión 1 — jornada regular
Marca 2 (posición par)    → salida   ┘
Marca 3 (posición impar)  → entrada  ┐ Sesión 2 — tiempo extra
Marca 4 (posición par)    → salida   ┘
```

**Límite de sesiones:**

El motor procesa un máximo de **dos sesiones** (cuatro marcaciones) por día.

- Si el empleado tiene **más de 4 marcaciones**, se procesan solo las primeras 4 y se fuerza `requiere_revision = TRUE` con una observación que indica cuántas marcas se ignoraron.
- Si el total de marcaciones es impar, la última sesión queda sin salida → `OMISION_SALIDA` sobre ese segmento.

**Sesión regular vs. sesión de tiempo extra (DESPUES_SALIDA):**

- **Sesión 1** es siempre la jornada regular. Se clasifica contra el horario programado (retardo, omisiones, etc.).
- **Sesión 2** es tiempo extra si su entrada ocurre después de `salida_programada + margen_tiempo_extra_segundos`. Si la entrada de la sesión 2 ocurre antes de ese umbral, no se reconoce como tiempo extra válido.

**Sesión de tiempo extra (ANTES_ENTRADA):**

Para turnos `ANTES_ENTRADA`, el tiempo extra está integrado en la misma Sesión 1 (el empleado llega antes de la entrada programada y no hay segunda sesión). La lógica existente de `entrada_programada - primera_entrada - margen` sigue aplicando.

**Códigos de punch:**

Los códigos numéricos de punch (`0`, `1`, etc.) son detalles del adaptador ZKTeco y no forman parte de este contrato. El motor construye sesiones por orden cronológico, independientemente del código reportado por el dispositivo.

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

**Dos ventanas de cierre independientes:**

**Para `FALTA` por ausencia total (cero marcaciones):**

La ventana cierra cuando:

```
datetime.now() >= entrada_programada + limite_retardo_mayor_segundos
```

Una vez que la última entrada posible según la política ha pasado, la ausencia es definitiva. No es necesario esperar `salida_programada`. El empleado que no ha llegado después de que incluso el retardo_mayor cerró, ya no puede llegar "a tiempo" bajo ningún criterio de la política.

La fuente de `limite_retardo_mayor_segundos` es `asistencia.politicas_asistencia` — no se hardcodea.

**Para `OMISION_SALIDA` (tiene entrada, falta salida):**

La ventana sigue siendo `salida_programada`. Un empleado cuyo turno termina a las 16:00 no puede marcarse como omisión de salida a las 14:00.

**Reglas generales:**

- No se puede cerrar anticipadamente una jornada usando valores hardcodeados.
- Si la jornada aún está abierta y no es posible clasificar definitivamente, el registro **no debe crearse** o debe marcarse con un estatus provisional que no genere puntos ni penalizaciones.
- Al reprocesar después de que la jornada cierre, el motor debe poder generar el resultado definitivo correcto.
- Para turnos nocturnos, `salida_programada` puede caer en el día siguiente al de la fila procesada.

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

## 19. Margen de tiempo extra

El motor reconoce tiempo extra según la modalidad configurada en
`tipos_turno.modalidad_tiempo_extra`:

- `DESPUES_SALIDA`: excedente entre `MAX(salida)` y `salida_programada`.
- `ANTES_ENTRADA`: excedente entre `entrada_programada` y `MIN(entrada)`.

Cada turno solo evalúa su propia modalidad. Un turno `DESPUES_SALIDA`
que llega temprano, o un turno `ANTES_ENTRADA` que sale tarde, no
generan tiempo extra por el lado que no les corresponde.

**Margen configurable:**

La fuente oficial de este margen es:

```
asistencia.politicas_asistencia.margen_tiempo_extra_segundos
```

Queda prohibido hardcodear este valor en el motor (Contrato §5/§17).
El motor debe resolver la política vigente para la fecha procesada,
igual que los demás límites de la política.

**Regla de cálculo — modelo de sesiones:**

Para `DESPUES_SALIDA`: el tiempo extra es la **duración real de la Sesión 2** (§11), siempre que su entrada ocurra después de `salida_programada + margen`. El margen actúa como umbral de validez, no como deducción sobre la duración:

```
# Si sesion_2.entrada >= salida_programada + margen:
minutos_extra = (sesion_2.salida - sesion_2.entrada) / 60

# Si sesion_2.entrada < salida_programada + margen, o no hay sesion_2:
minutos_extra = 0
```

Para `ANTES_ENTRADA`: el tiempo extra sigue siendo el excedente anterior a la entrada programada menos el margen:

```
minutos_extra = max(0, entrada_programada - primera_entrada - margen) / 60
```

Ejemplo `DESPUES_SALIDA`: turno 8–14, margen 30 min. El empleado checa salida a las 14:00, regresa a las 14:35 (Sesión 2), sale a las 17:00. `minutos_extra = 17:00 − 14:35 = 145 min`. El gap 14:00–14:35 no cuenta como trabajo ni se cobra.

Este margen es independiente de `limite_tolerancia_segundos` (que
clasifica retardos de entrada) y no debe confundirse con él.

---

## 20. Orden de hardening

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
