# RelojDAE - Reglas de Negocio

## Principio general

Este documento contiene reglas funcionales conocidas del sistema.

Estas reglas no deben modificarse durante refactoring sin autorización.

Cuando exista discrepancia entre estas reglas y la implementación actual,
reportarla antes de modificar código.

---

## Marcaciones biométricas

Las marcaciones provenientes de dispositivos ZKTeco son datos fuente.

Las marcaciones crudas deben conservarse.

La asistencia diaria es información derivada del procesamiento de dichas
marcaciones.

No corregir asistencias modificando destructivamente los datos biométricos
originales.

---

## Puntualidad

**Estado**: IMPLEMENTADO con limitaciones conocidas.

Para una entrada programada, el procesamiento actual aplica las siguientes reglas.

Ejemplo con hora de entrada 08:00.

### Puntual

08:00:00 a 08:10:59

Resultado:

- estatus: COMPLETO
- 0 puntos

### Retardo menor

08:11:00 a 08:20:59

Resultado:

- estatus: RETARDO_MENOR
- 1 punto

### Retardo mayor

08:21:00 a 08:30:59

Resultado:

- estatus: RETARDO_MAYOR
- 2 puntos

### Falta

A partir de:

08:31:00

Resultado:

- estatus: FALTA
- 0 puntos (la falta se contabiliza como evento, no como puntos)

### Limitación conocida: umbrales hardcoded

Los umbrales 10/20/30 minutos están actualmente hardcoded en la función
`_calcular_estatus_y_puntos()` de `asistencia_procesamiento_repo.py`.

La tabla `asistencia.horarios` tiene un campo `tolerancia_entrada_minutos`
configurable por horario, y el procesamiento lo consulta en su query SQL,
pero actualmente **no lo utiliza** en el cálculo de estatus. El campo se
ignora en la lógica Python.

No se ha decidido aún cuál comportamiento debe prevalecer:

- umbrales fijos institucionales (10/20/30); o
- umbrales derivados de `tolerancia_entrada_minutos` del horario asignado.

Esta decisión requiere autorización antes de modificar código.

---

## Sistema de puntos

### Reglas de negocio — IMPLEMENTADAS

Las siguientes reglas están implementadas en
`backend/app/services/puntos_acumulacion_service.py` y se ejecutan
automáticamente al finalizar el procesamiento de asistencia diaria.

**10 puntos acumulados → 1 DO (Día de Omisión)**

- Estado: IMPLEMENTADO.
- El servicio calcula puntos acumulados por periodo y registra un movimiento
  tipo "Día de Omisión (DO)" en `asistencia.movimientos_puntos` cada vez que
  se alcanza un múltiplo de 10 puntos.

**7 DO → condición de revisión de baja**

- Estado: IMPLEMENTADO.
- Cuando un empleado acumula 7 o más DOs en un periodo, el sistema marca
  `requiere_revision_baja = TRUE` en `asistencia.resumen_periodo_empleado`
  con el motivo correspondiente.
- NOTA: El sistema solo marca la condición para revisión humana. No ejecuta
  la baja automáticamente.

**3 faltas continuas → condición de revisión de baja**

- Estado: IMPLEMENTADO.
- El servicio detecta secuencias de 3+ faltas consecutivas usando
  técnica de gaps-and-islands en SQL. Marca `requiere_revision_baja = TRUE`
  en el resumen del periodo.
- NOTA: El sistema solo marca la condición para revisión humana. No ejecuta
  la baja automáticamente.

### Restricciones

No modificar estas equivalencias sin autorización.

No presentar estas reglas como funcionalidades existentes en interfaces o
documentación dirigida a usuarios hasta que estén implementadas.

---

## Jornadas

**Estado**: IMPLEMENTADO — configuración dinámica en PostgreSQL.

Actualmente existen al menos:

### Turno matutino

Duración por defecto:

7 horas (420 minutos).

### Turno vespertino

Duración por defecto:

6 horas (360 minutos).

### Configurabilidad

La duración de cada turno se define mediante el campo
`duracion_jornada_minutos` en la tabla `asistencia.tipos_turno`.

Las duraciones NO están hardcoded en el código. Se leen dinámicamente
desde PostgreSQL durante el procesamiento de asistencia.

Los horarios pueden manejar:

- días aplicables
- hora de entrada
- hora de salida
- tolerancia (campo existe pero no gobierna el cálculo — ver sección Puntualidad)
- descanso
- estado activo
- vigencia
- cruce de medianoche (ver siguiente sección)

---

## Horarios que cruzan medianoche

**Estado**: IMPLEMENTADO.

Un horario puede terminar al día siguiente.

Si:

endTime < startTime

el horario cruza medianoche.

### Comportamiento implementado

La función `_calcular_salida_programada(fecha, hora_entrada, hora_salida)` en
`asistencia_procesamiento_repo.py` detecta si `hora_salida < hora_entrada`
y suma 1 día a la fecha de salida programada.

La query SQL del procesamiento de asistencia:
- Identifica días de trabajo a partir de marcaciones de ENTRADA (punch=0).
- Para turnos nocturnos (`cruza_medianoche = true`), busca la salida tanto
  en el mismo día como en el día siguiente.
- La fecha del registro de asistencia corresponde al día de ENTRADA.

### Restricción

Si un empleado no registra salida al día siguiente pero sí registra entrada
al otro turno, el sistema podría confundir las marcaciones. Este caso
extremo requiere revisión manual vía incidencias.

---

## Empleado y ZKTeco

Los empleados pueden vincularse con identificadores ZKTeco.

Antes de crear o modificar una asociación debe verificarse:

- que el identificador no esté ocupado de forma incompatible;
- que el empleado no genere asociaciones duplicadas;
- que no corresponda a un usuario protegido del dispositivo.

Los usuarios administrativos del reloj no deben utilizarse como empleados
ordinarios.

### Riesgo conocido: vinculación directa sin validación de duplicados

La vinculación directa mediante el endpoint
`PATCH /api/zk/reconciliation/employees/{codigo}/link` actualiza
`personal.empleados.zk_user_id` pero actualmente **no verifica** si otro
empleado ya tiene asignado el mismo `zk_user_id`.

El servicio de sincronización (`empleados_sincronizacion_service.py`) sí
valida si el user_id está ocupado en el reloj por otro nombre, pero la
validación en PostgreSQL contra otros empleados no existe en el endpoint
de vinculación directa.

Esto podría generar dos empleados apuntando al mismo usuario del reloj.

---

## Usuarios protegidos

Las cuentas protegidas configuradas mediante:

ZK_PROTECTED_USER_IDS
ZK_PROTECTED_NAMES

no deben:

- eliminarse
- sobrescribirse
- desvincularse
- modificarse accidentalmente

---

## Roles

Roles actuales:

- super_admin
- rh_admin
- supervisor
- empleado
- auditor

Los roles y sus alcances deben ser coherentes entre frontend y backend.

La autorización definitiva pertenece al backend.

---

## Alcances (DataScope)

### DataScope backend (implementado)

Los niveles de acceso reconocidos actualmente por el backend son:

- **TOTAL** — Sin restricción de datos.
- **AREA** — Limitado a unidades organizacionales asignadas al usuario.
- **PROPIO** — Solo datos del empleado vinculado al usuario.
- **NINGUNO** — Sin acceso al módulo.

Estos son los únicos valores aceptados por `access_control.py` y
`access_repo.py`. Cualquier otro valor se normaliza a NINGUNO.

### LECTURA (concepto resuelto)

El frontend anteriormente definía un nivel `LECTURA` separado. Este concepto
fue eliminado y reemplazado por la combinación de `DataScope = TOTAL` con
`canRead = true` y todas las demás capacidades en `false`.

La función `isReadOnly(role, module)` en `frontend/src/utils/permissions.js`
detecta este caso para la UI (ocultar botones de acción).

No es necesario un DataScope adicional. El sistema actual cubre correctamente
el caso del auditor.

### Comportamiento esperado

Las consultas deben respetar el alcance del usuario cuando corresponda.

Un supervisor con alcance AREA no debe obtener automáticamente información de
otras unidades organizacionales.

Un empleado con alcance PROPIO debe limitarse a sus propios datos.

---

## Consistencia de reglas

No implementar diferentes versiones de una regla en:

React
FastAPI
PostgreSQL

Debe existir una autoridad funcional clara.

Cuando React necesite conocer una regla para mostrar información, esto no
convierte al frontend en la fuente autoritativa del resultado.

---

## Configurabilidad

Cuando una política pueda cambiar institucionalmente, preferir parámetros o
configuración sobre números mágicos distribuidos por el código.

No convertir automáticamente todas las reglas en configuración.

Primero determinar si realmente son variables de negocio.