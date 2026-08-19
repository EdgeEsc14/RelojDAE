# RelojDAE - Contexto de Producto

## Objetivo del Sistema

RelojDAE es un sistema de control de asistencia institucional desarrollado para la
DAE (Dirección de Administración Escolar). Su propósito es registrar, procesar y
gestionar la asistencia del personal mediante la integración con dispositivos
biométricos ZKTeco y una plataforma web administrativa.

El sistema automatiza el ciclo completo: captura de marcaciones biométricas,
sincronización con la base de datos central, procesamiento de asistencia diaria,
gestión de incidencias y generación de reportes.

## Principales Funcionalidades

1. **Gestión de Empleados**: Alta integral, edición, asignación de horarios,
   vinculación con dispositivos ZKTeco, gestión de estatus (activo/inactivo).

2. **Integración con Relojes ZKTeco**: Lectura de usuarios del reloj, sincronización
   de marcaciones crudas hacia PostgreSQL, vinculación/desvinculación de empleados
   con user IDs del reloj, sincronización de hora del dispositivo.

3. **Procesamiento de Asistencia**: Transformación de marcaciones crudas en registros
   de asistencia diaria procesados (entrada, salida, retardos, faltas).

4. **Checadas Crudas**: Visualización de marcaciones sin procesar directamente
   desde el reloj o desde la base de datos ya sincronizada.

5. **Horarios y Turnos**: Definición de horarios laborales, tipos de turno,
   asignación de horarios a empleados con historial.

6. **Incidencias y Justificantes**: Registro de incidencias laborales, solicitud
   y aprobación de justificantes.

7. **Dashboard**: Resumen ejecutivo con métricas de asistencia, empleados activos,
   dispositivos conectados y marcaciones recientes.

8. **Reportes**: Reportes por empleado y por departamento.

9. **Dispositivos**: Administración de relojes checadores (IP, puerto, estado de
   conexión, última sincronización).

10. **Auditoría**: Registro de acciones del sistema y auditoría de login.

11. **Usuarios del Sistema**: Gestión de cuentas de acceso al sistema web,
    independiente del catálogo de empleados.

12. **Configuración**: Parámetros generales del sistema.

## Usuarios y Roles

El sistema define 5 roles con una matriz de permisos por módulo:

| Rol | Descripción | Alcance |
|-----|-------------|---------|
| **super_admin** | Administrador total del sistema | Acceso TOTAL a todos los módulos |
| **rh_admin** | Recursos Humanos / Administrador | TOTAL en empleados, asistencia, horarios, incidencias, reportes. Sin acceso a dispositivos, usuarios del sistema, auditoría ni configuración |
| **supervisor** | Supervisor de área | Acceso de AREA en empleados, asistencia, incidencias y reportes. Limitado a sus unidades organizacionales |
| **empleado** | Empleado estándar | Solo acceso PROPIO a su asistencia, incidencias y reportes personales |
| **auditor** | Auditor institucional | Acceso de LECTURA a la mayoría de módulos excepto dispositivos, usuarios y configuración |

### Niveles de Acceso (DataScope backend)

Los DataScope reconocidos actualmente por el backend son:

- **TOTAL**: Sin restricción de datos.
- **AREA**: Limitado a unidades organizacionales asignadas.
- **PROPIO**: Solo datos del empleado vinculado al usuario.
- **NINGUNO**: Módulo no visible ni accesible.

**Nota sobre LECTURA**: El frontend define un nivel "LECTURA" en su matriz de
permisos (usado para el rol auditor). Sin embargo, el backend actualmente NO
reconoce LECTURA como DataScope válido — cualquier valor distinto de
TOTAL/AREA/PROPIO se normaliza a NINGUNO. La correspondencia entre el concepto
frontend de LECTURA y el backend necesita revisión e implementación.

## Flujo Funcional

```
Empleado registra huella/PIN en reloj ZKTeco
        |
        v
Reloj almacena marcación (uid, user_id, timestamp, punch, status)
        |
        v
Admin ejecuta sincronización desde el sistema web
        |
        v
Backend lee marcaciones crudas del reloj vía PyZK (protocolo UDP/TCP)
        |
        v
Marcaciones crudas se insertan en asistencia.marcaciones_crudas (PostgreSQL)
  (deduplicación por índice UNIQUE: dispositivo_origen + zk_uid_registro +
   zk_user_id + fecha_hora + punch + status — definido en migración 056)
        |
        v
Admin ejecuta procesamiento de asistencia (rango de fechas)
        |
        v
Sistema calcula asistencia diaria por empleado:
  - Vincula marcaciones crudas con empleados (vía zk_user_id)
  - Aplica horario asignado
  - Determina estatus: ASISTENCIA, RETARDO, FALTA, INCIDENCIA
        |
        v
Resultados en asistencia.asistencias_diarias
        |
        v
Supervisores/RH revisan asistencia, gestionan incidencias, generan reportes
```

## Integración con Dispositivos ZKTeco

### Comunicación

- Protocolo: UDP/TCP directo al reloj vía librería `pyzk`.
- Configuración por dispositivo: IP, puerto, password de comunicación.
- Soporte para múltiples relojes por empleado.

### Operaciones Soportadas

| Operación | Endpoint | Descripción |
|-----------|----------|-------------|
| Health check | `GET /api/zk/health` | Verifica conectividad |
| Listar usuarios | `GET /api/zk/users` | Lee usuarios registrados en el reloj |
| Leer marcaciones | `GET /api/zk/attendance/raw` | Lee checadas directamente del reloj |
| Sincronizar a BD | `POST /api/zk/attendance/sync` | Copia marcaciones a PostgreSQL |
| Consultar BD | `GET /api/zk/attendance/db` | Lee marcaciones ya sincronizadas |
| Sincronizar hora | `POST /api/zk/time/sync` | Corrige desfase de hora del reloj |
| Conciliar empleados | `GET /api/zk/reconciliation/employees` | Compara usuarios ZK vs empleados BD |
| Vincular empleado | `PATCH /api/zk/reconciliation/employees/{codigo}/link` | Asocia empleado con user_id ZK |
| Desvincular | `PATCH /api/zk/reconciliation/employees/{codigo}/unlink` | Remueve asociación |

### Seguridad de Dispositivos

- Usuarios protegidos (admin del reloj) no se pueden vincular ni borrar.
- Escrituras al reloj requieren `ZK_ALLOW_WRITES=true` explícito.
- La sincronización de hora tiene límites diarios configurables.
- El dispositivo se deshabilita durante operaciones de lectura para evitar corrupción.

## Procesamiento de Asistencia

1. **Marcaciones Crudas** (`asistencia.marcaciones_crudas`): Copia fiel de lo que
   reporta el reloj, con sync_run_id para trazabilidad. La deduplicación se
   garantiza mediante un índice UNIQUE sobre: `dispositivo_origen`,
   `COALESCE(zk_uid_registro, -1)`, `zk_user_id`, `fecha_hora`,
   `COALESCE(punch, -1)`, `COALESCE(status, -1)` (migración 056).

2. **Asistencia Diaria** (`asistencia.asistencias_diarias`): Resultado procesado
   que consolida marcaciones de un día en un registro por empleado con estatus final.

3. **Políticas**: El sistema contempla políticas de asistencia y tolerancias
   configurables por horario. Sin embargo, actualmente el procesamiento usa
   umbrales hardcoded (10/20/30 minutos) en vez de leer la tolerancia configurada
   del horario (ver business_rules.md para detalle).

## Organización Institucional

- **Unidades Organizacionales**: Estructura jerárquica (divisiones, departamentos).
- **Puestos**: Catálogo con niveles jerárquicos.
- **Supervisores**: Relación jerárquica entre empleados basada en puestos.
- La estructura actual responde al organigrama de la DAE con divisiones como:
  - División de Admisión y Control Escolar
  - División de Registro y Certificación de Estudios
  - Departamento de Servicios Administrativos
