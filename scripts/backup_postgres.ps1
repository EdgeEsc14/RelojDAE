# Script PowerShell para backup automático de PostgreSQL - RelojDAE
# Este script puede ser programado con Windows Task Scheduler

param(
    [ValidateSet("daily", "weekly", "clean", "list")]
    [string]$Type = "daily"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$PythonScript = Join-Path $ScriptDir "backup_postgres.py"
$LogFile = Join-Path $ScriptDir "backup_scheduler.log"

# Configuración
$PythonExe = "$ProjectDir\backend\.v_relojdae\Scripts\python.exe"
$BackupDir = "$ProjectDir\backups"

# Crear directorio de backups si no existe
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Force -Path $BackupDir
    New-Item -ItemType Directory -Force -Path "$BackupDir\daily"
    New-Item -ItemType Directory -Force -Path "$BackupDir\weekly"
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Level - $Message"
    
    # Escribir a archivo
    Add-Content -Path $LogFile -Value $logMessage
    
    # Mostrar en consola
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARN" { Write-Host $logMessage -ForegroundColor Yellow }
        "INFO" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage }
    }
}

try {
    Write-Log "========================================="
    Write-Log "Iniciando script de backup PostgreSQL"
    Write-Log "Tipo: $Type"
    Write-Log "Fecha: $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')"
    Write-Log "========================================="
    
    # Verificar que el script Python existe
    if (-not (Test-Path $PythonScript)) {
        Write-Log "Error: No se encontró el script Python $PythonScript" -Level "ERROR"
        exit 1
    }
    
    # Verificar que Python existe
    if (-not (Test-Path $PythonExe)) {
        Write-Log "Error: No se encontró Python en $PythonExe" -Level "ERROR"
        exit 1
    }
    
    # Construir comando
    $pythonArgs = @("$PythonScript")
    
    switch ($Type) {
        "daily" { $pythonArgs += "--type", "daily" }
        "weekly" { $pythonArgs += "--type", "weekly" }
        "clean" { $pythonArgs += "--clean" }
        "list" { $pythonArgs += "--list" }
    }
    
    # Ejecutar script Python
    Write-Log "Ejecutando: $PythonExe $pythonArgs"
    
    $process = Start-Process -FilePath $PythonExe `
        -ArgumentList $pythonArgs `
        -NoNewWindow `
        -Wait `
        -PassThru `
        -RedirectStandardError "temp_error.txt" `
        -RedirectStandardOutput "temp_output.txt"
    
    # Leer salida
    if (Test-Path "temp_output.txt") {
        $output = Get-Content "temp_output.txt" -Raw
        Write-Log "Salida del script Python:`n$output"
        Remove-Item "temp_output.txt" -Force
    }
    
    if (Test-Path "temp_error.txt") {
        $errorOutput = Get-Content "temp_error.txt" -Raw
        if ($errorOutput.Trim()) {
            Write-Log "Errores del script Python:`n$errorOutput" -Level "ERROR"
        }
        Remove-Item "temp_error.txt" -Force
    }
    
    if ($process.ExitCode -eq 0) {
        Write-Log "Backup completado exitosamente"
        
        # Verificar espacio de disco
        $totalSize = (Get-ChildItem "$BackupDir\*.sql", "$BackupDir\daily\*.sql", "$BackupDir\weekly\*.sql" -Recurse -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum
        $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
        
        Write-Log "Espacio total en backups: $totalSizeMB MB"
        
        # Contar backups
        $dailyCount = (Get-ChildItem "$BackupDir\daily\*.sql" -ErrorAction SilentlyContinue).Count
        $weeklyCount = (Get-ChildItem "$BackupDir\weekly\*.sql" -ErrorAction SilentlyContinue).Count
        
        Write-Log "Backups diarios: $dailyCount, Backups semanales: $weeklyCount"
        
    } else {
        Write-Log "El script Python falló con código de salida: $($process.ExitCode)" -Level "ERROR"
        exit 1
    }
    
} catch {
    Write-Log "Error inesperado: $($_.Exception.Message)" -Level "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"
    exit 1
} finally {
    Write-Log "========================================="
    Write-Log "Script de backup finalizado"
    Write-Log "=========================================`n"
}