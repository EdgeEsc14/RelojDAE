@echo off
echo =========================================
echo PRUEBA DE SISTEMA DE BACKUP - RELOJDAE
echo =========================================
echo.

echo 1. Verificando directorios...
if exist "c:\RelojChecador\backups" (
    echo   ✓ Directorio principal encontrado
) else (
    echo   ✗ Directorio principal NO encontrado
)

if exist "c:\RelojChecador\backups\daily" (
    echo   ✓ Directorio diario encontrado
) else (
    echo   ✗ Directorio diario NO encontrado
)

if exist "c:\RelojChecador\backups\weekly" (
    echo   ✓ Directorio semanal encontrado
) else (
    echo   ✗ Directorio semanal NO encontrado
)

echo.
echo 2. Verificando scripts...
if exist "c:\RelojChecador\scripts\backup_postgres.py" (
    echo   ✓ backup_postgres.py encontrado
) else (
    echo   ✗ backup_postgres.py NO encontrado
)

if exist "c:\RelojChecador\scripts\backup_postgres.ps1" (
    echo   ✓ backup_postgres.ps1 encontrado
) else (
    echo   ✗ backup_postgres.ps1 NO encontrado
)

if exist "c:\RelojChecador\backend\.env" (
    echo   ✓ .env encontrado
) else (
    echo   ✗ .env NO encontrado
)

echo.
echo 3. Instrucciones para configurar:
echo.
echo Para probar backup manualmente:
echo   1. Abrir PowerShell como Administrador
echo   2. Ejecutar:
echo      cd c:\RelojChecador\scripts
echo      powershell -ExecutionPolicy Bypass -File backup_postgres.ps1 -Type list
echo.
echo Para programar backups automáticos:
echo   1. Abrir "Task Scheduler" (Programador de tareas)
echo   2. Importar tarea desde:
echo      c:\RelojChecador\scripts\programar_backup.xml
echo.
echo Para más detalles, ver:
echo   c:\RelojChecador\scripts\README_Backup.md
echo.
echo =========================================
pause