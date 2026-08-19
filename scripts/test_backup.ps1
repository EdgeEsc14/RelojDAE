# Script de prueba para verificar sistema de backup RelojDAE

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "PRUEBA DE SISTEMA DE BACKUP - RELOJDAE" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

# 1. Verificar directorios
Write-Host "1. Verificando directorios..." -ForegroundColor Yellow

$backupDir = "c:\RelojChecador\backups"
$dailyDir = "$backupDir\daily"
$weeklyDir = "$backupDir\weekly"

if (Test-Path $backupDir) {
    Write-Host "   ✓ Directorio principal encontrado: $backupDir" -ForegroundColor Green
} else {
    Write-Host "   ✗ Directorio principal NO encontrado" -ForegroundColor Red
}

if (Test-Path $dailyDir) {
    Write-Host "   ✓ Directorio diario encontrado: $dailyDir" -ForegroundColor Green
} else {
    Write-Host "   ✗ Directorio diario NO encontrado" -ForegroundColor Red
}

if (Test-Path $weeklyDir) {
    Write-Host "   ✓ Directorio semanal encontrado: $weeklyDir" -ForegroundColor Green
} else {
    Write-Host "   ✗ Directorio semanal NO encontrado" -ForegroundColor Red
}

# 2. Verificar scripts
Write-Host "`n2. Verificando scripts..." -ForegroundColor Yellow

$scripts = @(
    "c:\RelojChecador\scripts\backup_postgres.py",
    "c:\RelojChecador\scripts\backup_postgres.ps1",
    "c:\RelojChecador\backend\.env"
)

foreach ($script in $scripts) {
    if (Test-Path $script) {
        Write-Host "   ✓ $(Split-Path $script -Leaf) encontrado" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $(Split-Path $script -Leaf) NO encontrado" -ForegroundColor Red
    }
}

# 3. Verificar PostgreSQL
Write-Host "`n3. Verificando PostgreSQL..." -ForegroundColor Yellow

try {
    $pgdumpTest = Get-Command pg_dump -ErrorAction Stop
    Write-Host "   ✓ pg_dump encontrado: $($pgdumpTest.Source)" -ForegroundColor Green
    
    # Probar versión
    $pgVersion = & pg_dump --version 2>&1
    Write-Host "   ✓ $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "   ✗ pg_dump NO encontrado en PATH" -ForegroundColor Red
    Write-Host "      Añadir PostgreSQL al PATH o modificar script" -ForegroundColor Yellow
}

# 4. Verificar Python
Write-Host "`n4. Verificando Python..." -ForegroundColor Yellow

$pythonExe = "c:\RelojChecador\backend\.v_relojdae\Scripts\python.exe"
if (Test-Path $pythonExe) {
    Write-Host "   ✓ Python encontrado: $pythonExe" -ForegroundColor Green
    
    # Probar versión
    $pythonVersion = & $pythonExe --version 2>&1
    Write-Host "   ✓ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ✗ Python NO encontrado en el virtual environment" -ForegroundColor Red
}

# 5. Verificar archivo .env
Write-Host "`n5. Verificando configuración de base de datos..." -ForegroundColor Yellow

$envFile = "c:\RelojChecador\backend\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    
    $requiredVars = @{
        "POSTGRES_HOST" = $envContent -match "POSTGRES_HOST="
        "POSTGRES_DB" = $envContent -match "POSTGRES_DB="
        "POSTGRES_USER" = $envContent -match "POSTGRES_USER="
        "POSTGRES_PASSWORD" = $envContent -match "POSTGRES_PASSWORD="
    }
    
    foreach ($var in $requiredVars.Keys) {
        if ($requiredVars[$var]) {
            Write-Host "   ✓ $var configurado" -ForegroundColor Green
        } else {
            Write-Host "   ✗ $var NO configurado" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   ✗ Archivo .env NO encontrado" -ForegroundColor Red
}

# 6. Resumen
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "RESUMEN DE PRUEBA" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

Write-Host "`nPara probar el sistema de backup:" -ForegroundColor White
Write-Host "1. Abrir PowerShell como Administrador" -ForegroundColor White
Write-Host "2. Ejecutar:" -ForegroundColor White
Write-Host "   cd c:\RelojChecador\scripts" -ForegroundColor Gray
Write-Host "   powershell -ExecutionPolicy Bypass -File backup_postgres.ps1 -Type list" -ForegroundColor Gray

Write-Host "`nPara programar backups automáticos:" -ForegroundColor White
Write-Host "1. Importar task desde Task Scheduler:" -ForegroundColor White
Write-Host "   c:\RelojChecador\scripts\programar_backup.xml" -ForegroundColor Gray

Write-Host "`nPara backup manual inmediato:" -ForegroundColor White
Write-Host "   powershell -ExecutionPolicy Bypass -File backup_postgres.ps1 -Type daily" -ForegroundColor Gray

Write-Host "`nPara más detalles, ver:" -ForegroundColor White
Write-Host "   c:\RelojChecador\scripts\README_Backup.md" -ForegroundColor Gray

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "PRUEBA COMPLETADA" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Pausar para leer resultados
Read-Host "`nPresiona Enter para salir..."