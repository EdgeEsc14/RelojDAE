# Script para crear directorios de backup
$backupRoot = "c:\RelojChecador\backups"
$dailyDir = Join-Path $backupRoot "daily"
$weeklyDir = Join-Path $backupRoot "weekly"

if (-not (Test-Path $dailyDir)) {
    New-Item -ItemType Directory -Force -Path $dailyDir
    Write-Host "Directorio diario creado: $dailyDir"
}

if (-not (Test-Path $weeklyDir)) {
    New-Item -ItemType Directory -Force -Path $weeklyDir
    Write-Host "Directorio semanal creado: $weeklyDir"
}

Write-Host "Directorios de backup creados exitosamente"