from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import glob
import logging

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from src.schemas import (
    AirQualityMeasurement, DataExtractionStatus, StationQuery,
    PollutantType, DataSource, APIResponse, Coordinates
)
from src.air_quality_client import air_quality_client
from src.scheduler import air_quality_scheduler

# Configurar logging
logger = logging.getLogger(__name__)

# Router para rutas de calidad del aire
router = APIRouter()


@router.get("/status", response_model=APIResponse)
async def get_system_status():
    """Obtener estado del sistema de extracción de datos"""
    try:
        # Estado del scheduler
        scheduler_status = air_quality_scheduler.get_job_status()
        
        # Estado del cliente de extracción
        extraction_status = air_quality_client.get_extraction_status()
        
        # Contar archivos de datos disponibles
        data_dir = Path("data/air_quality")
        data_files = list(data_dir.glob("*.json")) if data_dir.exists() else []
        
        system_status = {
            "system_running": scheduler_status["status"] == "running",
            "scheduler": scheduler_status,
            "extraction": extraction_status.model_dump(),
            "data_files_count": len(data_files),
            "last_file": max(data_files, key=lambda x: x.stat().st_mtime).name if data_files else None,
            "system_time": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="System status retrieved successfully",
            data=system_status,
            source=DataSource.OPENAQ  # Placeholder source
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/measurements/latest", response_model=APIResponse)
async def get_latest_measurements(
    pollutant: Optional[PollutantType] = Query(None, description="Filtrar por tipo de contaminante"),
    state: Optional[str] = Query(None, description="Filtrar por estado (código de 2 letras)"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de mediciones a retornar")
):
    """Obtener las mediciones más recientes de calidad del aire"""
    try:
        measurements = await _load_latest_measurements()
        
        # Aplicar filtros
        filtered_measurements = measurements
        
        if pollutant:
            filtered_measurements = [
                m for m in filtered_measurements 
                if m.parameter == pollutant
            ]
        
        if state:
            filtered_measurements = [
                m for m in filtered_measurements 
                if m.state and m.state.upper() == state.upper()
            ]
        
        # Ordenar por timestamp más reciente y limitar
        filtered_measurements.sort(key=lambda x: x.last_updated, reverse=True)
        limited_measurements = filtered_measurements[:limit]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(limited_measurements)} measurements",
            data=[m.model_dump() for m in limited_measurements],
            source=DataSource.OPENAQ  # Mixed sources
        )
        
    except Exception as e:
        logger.error(f"Error getting latest measurements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/measurements/by-location", response_model=APIResponse)
async def get_measurements_by_location(
    latitude: float = Query(..., ge=-90, le=90, description="Latitud"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitud"),
    radius_km: float = Query(50, ge=1, le=200, description="Radio de búsqueda en kilómetros"),
    pollutant: Optional[PollutantType] = Query(None, description="Filtrar por tipo de contaminante")
):
    """Obtener mediciones cerca de una ubicación específica"""
    try:
        measurements = await _load_latest_measurements()
        
        # Filtrar por ubicación (aproximación simple usando grados)
        # 1 grado ≈ 111 km
        lat_range = radius_km / 111.0
        lon_range = radius_km / (111.0 * abs(latitude * 3.14159 / 180))  # Ajuste por latitud
        
        nearby_measurements = []
        for measurement in measurements:
            lat_diff = abs(measurement.coordinates.latitude - latitude)
            lon_diff = abs(measurement.coordinates.longitude - longitude)
            
            if lat_diff <= lat_range and lon_diff <= lon_range:
                # Calcular distancia aproximada
                distance_km = ((lat_diff * 111) ** 2 + (lon_diff * 111) ** 2) ** 0.5
                if distance_km <= radius_km:
                    nearby_measurements.append(measurement)
        
        # Aplicar filtro de contaminante si se especifica
        if pollutant:
            nearby_measurements = [
                m for m in nearby_measurements 
                if m.parameter == pollutant
            ]
        
        # Ordenar por distancia (aproximada)
        nearby_measurements.sort(key=lambda x: 
            ((x.coordinates.latitude - latitude) ** 2 + 
             (x.coordinates.longitude - longitude) ** 2) ** 0.5
        )
        
        return APIResponse(
            success=True,
            message=f"Found {len(nearby_measurements)} measurements within {radius_km}km",
            data=[m.model_dump() for m in nearby_measurements],
            source=DataSource.OPENAQ
        )
        
    except Exception as e:
        logger.error(f"Error getting measurements by location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/measurements/summary", response_model=APIResponse)
async def get_measurements_summary():
    """Obtener resumen estadístico de las mediciones"""
    try:
        measurements = await _load_latest_measurements()
        
        # Agrupar por contaminante
        by_pollutant = {}
        by_state = {}
        by_source = {}
        
        for measurement in measurements:
            # Por contaminante
            pollutant = measurement.parameter
            if pollutant not in by_pollutant:
                by_pollutant[pollutant] = []
            by_pollutant[pollutant].append(measurement.value)
            
            # Por estado
            state = measurement.state or "Unknown"
            if state not in by_state:
                by_state[state] = 0
            by_state[state] += 1
            
            # Por fuente
            source = measurement.source
            if source not in by_source:
                by_source[source] = 0
            by_source[source] += 1
        
        # Calcular estadísticas
        pollutant_stats = {}
        for pollutant, values in by_pollutant.items():
            pollutant_stats[pollutant] = {
                "count": len(values),
                "average": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
                "unit": measurements[0].unit if measurements else ""
            }
        
        summary = {
            "total_measurements": len(measurements),
            "by_pollutant": pollutant_stats,
            "by_state": by_state,
            "by_source": by_source,
            "time_range": {
                "oldest": min(m.last_updated for m in measurements).isoformat() if measurements else None,
                "newest": max(m.last_updated for m in measurements).isoformat() if measurements else None
            }
        }
        
        return APIResponse(
            success=True,
            message="Summary statistics calculated",
            data=summary,
            source=DataSource.OPENAQ
        )
        
    except Exception as e:
        logger.error(f"Error generating measurements summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/run-now", response_model=APIResponse)
async def run_extraction_now(background_tasks: BackgroundTasks):
    """Ejecutar extracción de datos inmediatamente"""
    try:
        # Ejecutar en background para no bloquear la respuesta
        background_tasks.add_task(air_quality_scheduler.run_extraction_now)
        
        return APIResponse(
            success=True,
            message="Data extraction started in background",
            data={"started_at": datetime.utcnow().isoformat()},
            source=DataSource.OPENAQ
        )
        
    except Exception as e:
        logger.error(f"Error starting manual extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/start", response_model=APIResponse)
async def start_scheduler():
    """Iniciar el planificador de tareas"""
    try:
        air_quality_scheduler.start_scheduler()
        
        return APIResponse(
            success=True,
            message="Scheduler started successfully",
            data=air_quality_scheduler.get_job_status(),
            source=DataSource.OPENAQ
        )
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/stop", response_model=APIResponse)
async def stop_scheduler():
    """Detener el planificador de tareas"""
    try:
        air_quality_scheduler.stop_scheduler()
        
        return APIResponse(
            success=True,
            message="Scheduler stopped successfully",
            data={"status": "stopped"},
            source=DataSource.OPENAQ
        )
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/scheduler/interval", response_model=APIResponse)
async def update_extraction_interval(
    interval_minutes: int = Query(..., ge=5, le=1440, description="Intervalo en minutos (5-1440)")
):
    """Actualizar intervalo de extracción"""
    try:
        air_quality_scheduler.reschedule_extraction(interval_minutes)
        
        return APIResponse(
            success=True,
            message=f"Extraction interval updated to {interval_minutes} minutes",
            data=air_quality_scheduler.get_job_status(),
            source=DataSource.OPENAQ
        )
        
    except Exception as e:
        logger.error(f"Error updating extraction interval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _load_latest_measurements() -> List[AirQualityMeasurement]:
    """Cargar las mediciones más recientes de los archivos JSON"""
    data_dir = Path("data/air_quality")
    
    if not data_dir.exists():
        return []
    
    # Buscar los archivos JSON más recientes
    json_files = list(data_dir.glob("*.json"))
    
    if not json_files:
        return []
    
    # Obtener archivos de las últimas 2 horas para tener datos frescos
    cutoff_time = datetime.utcnow() - timedelta(hours=2)
    recent_files = []
    
    for file_path in json_files:
        file_stat = file_path.stat()
        file_time = datetime.fromtimestamp(file_stat.st_mtime)
        if file_time >= cutoff_time:
            recent_files.append(file_path)
    
    # Si no hay archivos recientes, usar los 3 más recientes
    if not recent_files:
        recent_files = sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
    
    measurements = []
    
    for file_path in recent_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            measurement_dicts = data.get("measurements", [])
            
            for measurement_dict in measurement_dicts:
                try:
                    # Convertir datetime strings de vuelta a datetime objects
                    if isinstance(measurement_dict.get("last_updated"), str):
                        measurement_dict["last_updated"] = datetime.fromisoformat(
                            measurement_dict["last_updated"].replace("Z", "+00:00")
                        )
                    
                    measurement = AirQualityMeasurement(**measurement_dict)
                    measurements.append(measurement)
                    
                except Exception as e:
                    logger.warning(f"Error parsing measurement from {file_path}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error loading data from {file_path}: {e}")
            continue
    
    return measurements