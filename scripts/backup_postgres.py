#!/usr/bin/env python3
"""
Script de backup automático para PostgreSQL de RelojDAE.
Este script crea backups diarios y gestiona rotación semanal.

Uso:
    python backup_postgres.py --type daily    # Backup diario (preserva 7 días)
    python backup_postgres.py --type weekly   # Backup semanal (preserva 4 semanas)
    python backup_postgres.py --clean         # Limpiar backups antiguos
"""

import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv


# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_postgres.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_environment():
    """Cargar variables de entorno desde .env"""
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    env_path = backend_dir / ".env"
    
    if not env_path.exists():
        logger.error(f"No se encontró el archivo .env en {env_path}")
        return None
    
    load_dotenv(env_path)
    
    config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'dae_reloj'),
        'user': os.getenv('POSTGRES_USER', 'reloj_app'),
        'password': os.getenv('POSTGRES_PASSWORD', 'DAE'),
    }
    
    # Validar configuración
    missing = [k for k, v in config.items() if not v]
    if missing:
        logger.error(f"Faltan variables de entorno: {missing}")
        return None
    
    return config


def create_backup_dirs():
    """Crear directorios de backup si no existen"""
    base_dir = Path("c:/RelojChecador/backups")
    daily_dir = base_dir / "daily"
    weekly_dir = base_dir / "weekly"
    
    daily_dir.mkdir(parents=True, exist_ok=True)
    weekly_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        'base': base_dir,
        'daily': daily_dir,
        'weekly': weekly_dir
    }


def run_backup(config, backup_type, dirs):
    """Ejecutar backup de PostgreSQL usando pg_dump"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if backup_type == 'daily':
        backup_dir = dirs['daily']
        filename = f"dae_reloj_daily_{timestamp}.sql"
    elif backup_type == 'weekly':
        backup_dir = dirs['weekly']
        filename = f"dae_reloj_weekly_{timestamp}.sql"
    else:
        logger.error(f"Tipo de backup no válido: {backup_type}")
        return False
    
    backup_path = backup_dir / filename
    
    # Crear string de conexión
    pg_dump_cmd = [
        'pg_dump',
        '-h', config['host'],
        '-p', config['port'],
        '-U', config['user'],
        '-d', config['database'],
        '-f', str(backup_path),
        '-F', 'p',  # Formato plain text (SQL)
        '--clean',  # Agregar DROP statements
        '--if-exists',
        '--no-owner',
        '--no-privileges',
    ]
    
    # Configurar variable de entorno para contraseña
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    logger.info(f"Iniciando backup {backup_type}...")
    logger.info(f"Base de datos: {config['database']}")
    logger.info(f"Destino: {backup_path}")
    
    try:
        result = subprocess.run(
            pg_dump_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Verificar si el archivo se creó correctamente
        if backup_path.exists():
            file_size = backup_path.stat().st_size
            logger.info(f"✓ Backup completado: {filename} ({file_size / 1024 / 1024:.2f} MB)")
            
            # Crear archivo de metadata
            metadata_path = backup_path.with_suffix('.json')
            metadata = {
                'backup_type': backup_type,
                'timestamp': timestamp,
                'database': config['database'],
                'host': config['host'],
                'size_bytes': file_size,
                'created_at': datetime.now().isoformat(),
            }
            
            import json
            metadata_path.write_text(json.dumps(metadata, indent=2))
            
            return True
        else:
            logger.error("El archivo de backup no se creó")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error en pg_dump: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return False


def cleanup_old_backups(dirs, days_to_keep_daily=7, weeks_to_keep_weekly=4):
    """Eliminar backups antiguos según políticas de retención"""
    
    def delete_old_files(directory, pattern, days_to_keep):
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for file_path in directory.glob(pattern):
            try:
                # Extraer fecha del nombre del archivo
                # Formato: dae_reloj_daily_YYYYMMDD_HHMMSS.sql
                filename = file_path.name
                date_str = filename.split('_')[3]  # Obtener YYYYMMDD
                file_date = datetime.strptime(date_str, '%Y%m%d')
                
                if file_date < cutoff_date:
                    # También eliminar el archivo de metadata si existe
                    metadata_file = file_path.with_suffix('.json')
                    
                    file_path.unlink(missing_ok=True)
                    metadata_file.unlink(missing_ok=True)
                    
                    logger.info(f"Eliminado backup antiguo: {filename}")
                    deleted_count += 1
                    
            except (ValueError, IndexError) as e:
                logger.warning(f"No se pudo procesar fecha de {file_path.name}: {str(e)}")
                continue
        
        return deleted_count
    
    # Limpiar backups diarios (7 días)
    daily_deleted = delete_old_files(dirs['daily'], "dae_reloj_daily_*.sql", days_to_keep_daily)
    logger.info(f"Eliminados {daily_deleted} backups diarios antiguos")
    
    # Limpiar backups semanales (28 días = 4 semanas)
    weekly_deleted = delete_old_files(dirs['weekly'], "dae_reloj_weekly_*.sql", weeks_to_keep_weekly * 7)
    logger.info(f"Eliminados {weekly_deleted} backups semanales antiguos")
    
    return daily_deleted + weekly_deleted


def main():
    parser = argparse.ArgumentParser(description='Backup automático PostgreSQL para RelojDAE')
    parser.add_argument('--type', choices=['daily', 'weekly'], 
                       help='Tipo de backup a realizar')
    parser.add_argument('--clean', action='store_true',
                       help='Limpiar backups antiguos sin crear nuevo backup')
    parser.add_argument('--list', action='store_true',
                       help='Listar backups existentes')
    
    args = parser.parse_args()
    
    # Cargar configuración
    config = load_environment()
    if not config:
        sys.exit(1)
    
    # Crear directorios
    dirs = create_backup_dirs()
    
    # Listar backups existentes
    if args.list:
        logger.info("=== BACKUPS DIARIOS ===")
        daily_files = sorted(dirs['daily'].glob("dae_reloj_daily_*.sql"))
        for f in daily_files[-10:]:  # Últimos 10
            if f.exists():
                size = f.stat().st_size / 1024 / 1024
                logger.info(f"  {f.name} ({size:.2f} MB)")
        
        logger.info("\n=== BACKUPS SEMANALES ===")
        weekly_files = sorted(dirs['weekly'].glob("dae_reloj_weekly_*.sql"))
        for f in weekly_files[-5:]:  # Últimos 5
            if f.exists():
                size = f.stat().st_size / 1024 / 1024
                logger.info(f"  {f.name} ({size:.2f} MB)")
        
        return
    
    # Limpiar backups antiguos
    if args.clean:
        logger.info("Limpiando backups antiguos...")
        cleanup_old_backups(dirs)
        logger.info("Limpieza completada")
        return
    
    # Crear backup
    if args.type:
        success = run_backup(config, args.type, dirs)
        
        if success:
            logger.info("✓ Operación de backup completada exitosamente")
            
            # Limpiar backups antiguos después de crear uno nuevo
            cleanup_old_backups(dirs)
            
            # Verificar espacio
            total_size = sum(f.stat().st_size for f in dirs['base'].rglob("*.sql"))
            logger.info(f"Espacio total en backups: {total_size / 1024 / 1024:.2f} MB")
        else:
            logger.error("✗ La operación de backup falló")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()