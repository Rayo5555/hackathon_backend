import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from src.air_quality_client import air_quality_client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirQualityScheduler:
    """Planificador de tareas para extracción automática de datos de calidad del aire"""
    
    def __init__(self):
        # Configurar jobstore y executor
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        self.is_running = False
        self.extraction_job_id = "air_quality_extraction"
        self.cleanup_job_id = "data_cleanup"
        
    async def extract_air_quality_data(self):
        """Tarea principal de extracción de datos"""
        try:
            logger.info("Starting scheduled air quality data extraction...")
            
            # Usar context manager para el cliente
            async with air_quality_client as client:
                # Extraer datos de todas las fuentes
                measurements = await client.extract_all_data()
                
                # Guardar datos en JSON
                await client.save_data_to_json(measurements)
                
                # Log del resumen
                total_measurements = sum(len(data) for data in measurements.values())
                logger.info(f"Extraction completed successfully: {total_measurements} measurements")
                
                # Actualizar timestamp de próxima extracción
                next_run = datetime.utcnow() + timedelta(minutes=30)
                status = client.get_extraction_status()
                status.next_extraction = next_run
                
        except Exception as e:
            logger.error(f"Error in scheduled extraction: {e}")
            # Actualizar estado de error
            status = air_quality_client.get_extraction_status()
            status.last_error = str(e)
    
    async def cleanup_old_data(self):
        """Tarea de limpieza de datos antiguos"""
        try:
            logger.info("Starting data cleanup task...")
            
            from pathlib import Path
            import os
            
            data_dir = Path("data/air_quality")
            if not data_dir.exists():
                return
            
            # Eliminar archivos más antiguos de 7 días
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            cleaned_files = 0
            for file_path in data_dir.glob("*.json"):
                try:
                    # Obtener timestamp del archivo
                    file_stat = file_path.stat()
                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        cleaned_files += 1
                        logger.info(f"Removed old data file: {file_path.name}")
                        
                except Exception as e:
                    logger.warning(f"Error removing file {file_path}: {e}")
            
            logger.info(f"Cleanup completed: {cleaned_files} files removed")
            
        except Exception as e:
            logger.error(f"Error in data cleanup: {e}")
    
    def start_scheduler(self):
        """Iniciar el planificador de tareas"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Agregar tarea de extracción cada 30 minutos
            self.scheduler.add_job(
                func=self.extract_air_quality_data,
                trigger=IntervalTrigger(minutes=30),
                id=self.extraction_job_id,
                name="Air Quality Data Extraction",
                replace_existing=True,
                next_run_time=datetime.utcnow() + timedelta(seconds=10)  # Empezar en 10 segundos
            )
            
            # Agregar tarea de limpieza diaria a las 02:00 UTC
            self.scheduler.add_job(
                func=self.cleanup_old_data,
                trigger=CronTrigger(hour=2, minute=0),
                id=self.cleanup_job_id,
                name="Data Cleanup",
                replace_existing=True
            )
            
            # Iniciar el scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Air Quality Scheduler started successfully")
            logger.info("- Data extraction: every 30 minutes")
            logger.info("- Data cleanup: daily at 02:00 UTC")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop_scheduler(self):
        """Detener el planificador de tareas"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Air Quality Scheduler stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            raise
    
    def get_job_status(self) -> dict:
        """Obtener estado de las tareas programadas"""
        if not self.is_running:
            return {"status": "stopped", "jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            jobs.append(job_info)
        
        return {
            "status": "running",
            "jobs": jobs,
            "scheduler_state": self.scheduler.state
        }
    
    async def run_extraction_now(self):
        """Ejecutar extracción inmediatamente (para testing)"""
        logger.info("Running manual air quality data extraction...")
        await self.extract_air_quality_data()
    
    def reschedule_extraction(self, interval_minutes: int = 30):
        """Reconfigurar intervalo de extracción"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            # Remover tarea existente
            self.scheduler.remove_job(self.extraction_job_id)
            
            # Agregar con nuevo intervalo
            self.scheduler.add_job(
                func=self.extract_air_quality_data,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id=self.extraction_job_id,
                name="Air Quality Data Extraction",
                replace_existing=True,
                next_run_time=datetime.utcnow() + timedelta(seconds=10)
            )
            
            logger.info(f"Extraction interval updated to {interval_minutes} minutes")
            
        except Exception as e:
            logger.error(f"Error rescheduling extraction: {e}")
            raise


# Instancia global del scheduler
air_quality_scheduler = AirQualityScheduler()


# Funciones de utilidad para FastAPI events
async def start_background_tasks():
    """Iniciar tareas en background (llamar en startup event)"""
    try:
        air_quality_scheduler.start_scheduler()
        logger.info("Background tasks started successfully")
    except Exception as e:
        logger.error(f"Error starting background tasks: {e}")


async def stop_background_tasks():
    """Detener tareas en background (llamar en shutdown event)"""
    try:
        air_quality_scheduler.stop_scheduler()
        logger.info("Background tasks stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping background tasks: {e}")