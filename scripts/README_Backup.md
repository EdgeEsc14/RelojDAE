# Sistema de Backup Automático PostgreSQL - RelojDAE

## Descripción
Sistema de backup automático para la base de datos PostgreSQL del sistema RelojDAE. Incluye backups diarios y semanales con rotación automática.

## Estructura
```
c:\RelojChecador\
├── backups/
│   ├── daily/      # Backups diarios (7 días de retención)
│   └── weekly/     # Backups semanales (4 semanas de retención)
├── scripts/
│   ├── backup_postgres.py      # Script principal Python
│   ├── backup_postgres.ps1     # Wrapper PowerShell
│   ├── programar_backup.xml    # Configuración Task Scheduler
│   └── backup_postgres.log     # Log de ejecuciones
```

## Requisitos Previos

### 1. PostgreSQL instalado con pg_dump disponible
- Asegurarse que `pg_dump.exe` esté en el PATH del sistema
- O especificar ruta completa en el script

### 2. Permisos de lectura/escritura
- El usuario que ejecute el script necesita:
  - Acceso a la base de datos `dae_reloj`
  - Permisos de escritura en `c:\RelojChecador\backups\`
  - Permisos para crear tareas programadas (opcional)

## Uso Manual

### Backup diario
```powershell
cd c:\RelojChecador\scripts
powershell -ExecutionPolicy Bypass -File backup_postgres.ps1 -Type daily
```

### Backup semanal
```powershell
cd c:\RelojChecador\scripts
powershell -ExecutionPolicy Bypass -File backup_postgres.ps1 -Type weekly
```

### Limpiar backups antiguos
```powershell
cd c:\RelojChecador\scripts
powershell -ExecutionPolicy Bypass -File backup_postgres.ps1 -Type clean
```

### Listar backups existentes
```powershell
cd c:\RelojChecador\scripts
powershell -ExecutionPolicy Bypass -File backup_postgres.ps1 -Type list
```

## Configuración Automática (Windows Task Scheduler)

### Opción 1: Usar interfaz gráfica
1. Abrir **Task Scheduler** (Programador de tareas)
2. En el panel derecho, hacer clic en **"Import Task..."**
3. Seleccionar `c:\RelojChecador\scripts\programar_backup.xml`
4. Configurar credenciales de usuario

### Opción 2: Usar PowerShell (Administrador)
```powershell
# Importar tarea
$taskPath = "RelojDAE"
$xmlPath = "c:\RelojChecador\scripts\programar_backup.xml"

Register-ScheduledTask -TaskName "RelojDAE_Backup" `
    -TaskPath $taskPath `
    -Xml (Get-Content $xmlPath | Out-String) `
    -User "SYSTEM" `
    -RunLevel Highest
```

### Opción 3: Crear manualmente
1. Abrir Task Scheduler → **Create Task**
2. **General:**
   - Nombre: `RelojDAE PostgreSQL Backup`
   - Ejecutar independientemente del usuario
   - Ejecutar con privilegios más altos

3. **Triggers:**
   - Diario: 23:00 (todos los días)
   - Semanal: Domingo 00:00

4. **Actions:**
   - Program: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "c:\RelojChecador\scripts\backup_postgres.ps1" -Type daily`
   - Start in: `c:\RelojChecador`

5. **Conditions:**
   - Deshabilitar: "Start only if computer is on AC power"

## Políticas de Retención

### Backups Diarios
- **Frecuencia:** 1 vez al día (23:00)
- **Retención:** 7 días
- **Ubicación:** `backups\daily\`
- **Formato:** `dae_reloj_daily_YYYYMMDD_HHMMSS.sql`

### Backups Semanales
- **Frecuencia:** 1 vez por semana (domingo 00:00)
- **Retención:** 4 semanas (28 días)
- **Ubicación:** `backups\weekly\`
- **Formato:** `dae_reloj_weekly_YYYYMMDD_HHMMSS.sql`

### Archivos de Metadata
Cada backup genera un archivo `.json` con:
- Tipo de backup
- Timestamp
- Base de datos
- Host
- Tamaño
- Fecha de creación

## Monitoreo

### Archivos de Log
- `scripts\backup_postgres.log` - Log principal
- `scripts\backup_scheduler.log` - Log del scheduler

### Verificación Manual
```powershell
# Verificar últimos backups
Get-ChildItem "c:\RelojChecador\backups\daily\*.sql" | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# Verificar espacio
$totalSize = (Get-ChildItem "c:\RelojChecador\backups\*.sql" -Recurse | Measure-Object -Property Length -Sum).Sum
Write-Host "Espacio total: $($totalSize / 1MB) MB"

# Verificar log reciente
Get-Content "c:\RelojChecador\scripts\backup_postgres.log" -Tail 20
```

## Restauración de Backup

### Desde PowerShell
```powershell
# 1. Detener aplicación si está corriendo
# 2. Restaurar backup más reciente
$latestBackup = Get-ChildItem "c:\RelojChecador\backups\daily\*.sql" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# 3. Restaurar
$env:PGPASSWORD = "DAE"
psql -h localhost -p 5432 -U reloj_app -d postgres -c "DROP DATABASE IF EXISTS dae_reloj;"
psql -h localhost -p 5432 -U reloj_app -d postgres -c "CREATE DATABASE dae_reloj;"
psql -h localhost -p 5432 -U reloj_app -d dae_reloj -f $latestBackup.FullName
```

### Desde pgAdmin o DBeaver
1. Crear nueva base de datos `dae_reloj_restored`
2. Ejecutar el script SQL del backup
3. Renombrar base de datos si es necesario

## Solución de Problemas

### Error: "pg_dump no se reconoce"
- Agregar PostgreSQL al PATH:
```powershell
$pgPath = "C:\Program Files\PostgreSQL\14\bin"  # Ajustar versión
$env:Path += ";$pgPath"
```

### Error de permisos
- Ejecutar PowerShell como Administrador
- Verificar que el usuario `reloj_app` tenga permisos de backup

### Error de conexión
- Verificar que PostgreSQL esté corriendo
- Verificar credenciales en `.env`

### Espacio en disco
- Los backups diarios ocupan ~50-100 MB cada uno
- Mantener al menos 2 GB libres en la unidad

## Personalización

### Modificar horarios
Editar `programar_backup.xml`:
```xml
<StartBoundary>2026-08-14T23:00:00</StartBoundary>
```

### Cambiar retención
Editar `backup_postgres.py`:
```python
days_to_keep_daily=7      # 7 días para diarios
weeks_to_keep_weekly=4    # 4 semanas para semanales
```

### Backup comprimido
Modificar script para usar `-F c` (formato custom) en lugar de `-F p` (plain text)

## Contacto y Soporte
- Sistema: RelojDAE
- Mantenimiento: Equipo de desarrollo
- Ubicación: DAE (Dirección de Administración Escolar)

---
*Última actualización: 14 de agosto de 2026*