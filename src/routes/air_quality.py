"""
Air Quality endpoints using OpenAQ API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from src.openaq_client import OpenAQClient
from src.schemas import AirQualityData, OpenAQResponse

router = APIRouter()
client = OpenAQClient()


@router.get("/latest", response_model=dict)
async def get_latest_air_quality(
    parameter: str = Query(
        ..., 
        description="Parameter to query (pm10, pm25, no2, co, so2, o3)"
    ),
    state: Optional[str] = Query(None, description="Filter by US state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(1000, description="Maximum number of results", ge=1, le=10000)
):
    """
    Get latest air quality measurements for a specific parameter in the US
    
    Parameters:
    - pm10: Particulate Matter 10 micrometers (µg/m³)
    - pm25: Particulate Matter 2.5 micrometers (µg/m³)
    - no2: Nitrogen Dioxide (ppm)
    - co: Carbon Monoxide (ppm)
    - so2: Sulfur Dioxide (ppm)
    - o3: Ozone (ppm)
    """
    parameter_lower = parameter.lower()
    
    if parameter_lower not in client.PARAMETERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameter. Must be one of: {', '.join(client.PARAMETERS.keys())}"
        )
    
    try:
        parameter_id = client.PARAMETERS[parameter_lower]
        data = await client.get_latest_measurements(
            parameter_id=parameter_id,
            country="US",
            limit=limit,
            state=state,
            city=city
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@router.get("/latest/all", response_model=dict)
async def get_all_parameters_latest(
    state: Optional[str] = Query(None, description="Filter by US state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(1000, description="Maximum number of results per parameter", ge=1, le=10000)
):
    """
    Get latest measurements for all monitored parameters (PM10, PM2.5, NO2, CO, SO2, O3)
    """
    try:
        data = await client.get_all_parameters_latest(
            country="US",
            limit=limit,
            state=state,
            city=city
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@router.get("/locations", response_model=dict)
async def get_monitoring_locations(
    limit: int = Query(10000, description="Maximum number of locations", ge=1, le=10000),
    state: Optional[str] = Query(None, description="Filter by US state"),
    city: Optional[str] = Query(None, description="Filter by city")
):
    """
    Get all air quality monitoring locations in the US
    """
    try:
        params = {}
        if state:
            params["state"] = state
        if city:
            params["city"] = city
            
        data = await client.get_locations(
            country="US",
            limit=limit,
            **params
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching locations: {str(e)}")


@router.get("/summary", response_model=dict)
async def get_air_quality_summary(
    state: Optional[str] = Query(None, description="Filter by US state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=1000)
):
    """
    Get a summary of air quality across all parameters for easier consumption
    """
    try:
        all_data = await client.get_all_parameters_latest(
            country="US",
            limit=limit,
            state=state,
            city=city
        )
        
        # Process and summarize the data
        summary = {
            "query": {
                "country": "US",
                "state": state,
                "city": city,
                "limit": limit
            },
            "parameters": {}
        }
        
        for param_name, param_data in all_data.items():
            if "error" in param_data:
                summary["parameters"][param_name] = {
                    "error": param_data["error"],
                    "count": 0
                }
            else:
                results = param_data.get("results", [])
                summary["parameters"][param_name] = {
                    "count": len(results),
                    "locations": len(set(r.get("location_id") for r in results if r.get("location_id")))
                }
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@router.get("/states", response_model=dict)
async def get_available_states():
    """
    Get a list of US states with predefined bounding boxes for easy searching
    """
    us_states = {
        "available_states": [
            {"name": "Colorado", "key": "colorado"},
            {"name": "California", "key": "california"},
            {"name": "New York", "key": "new_york"},
            {"name": "Texas", "key": "texas"},
            {"name": "Florida", "key": "florida"},
            {"name": "Washington", "key": "washington"},
            {"name": "Illinois", "key": "illinois"},
            {"name": "Pennsylvania", "key": "pennsylvania"},
            {"name": "Ohio", "key": "ohio"},
            {"name": "Michigan", "key": "michigan"},
            {"name": "Entire USA", "key": "entire_us"}
        ],
        "note": "Use the 'key' value in the 'state' parameter when searching locations",
        "example": "/measurements/by-location-name?location_name=denver&state=colorado"
    }
    return us_states


@router.get("/measurements/by-parameter/{parameter_id}", response_model=dict)
async def get_measurements_by_parameter(
    parameter_id: int,
    bbox: str = Query(
        "-109.05,37,-102.04,41",
        description="Bounding box coordinates (min_lon,min_lat,max_lon,max_lat)"
    ),
    limit: int = Query(1000, description="Maximum number of results", ge=1, le=10000)
):
    """
    Obtener todas las mediciones de un tipo específico de contaminación
    
    Parámetros disponibles:
    - 1: PM10 (Particulate Matter 10 micrometers) - µg/m³
    - 2: PM2.5 (Particulate Matter 2.5 micrometers) - µg/m³
    - 7: NO2 (Nitrogen Dioxide) - ppm
    - 8: CO (Carbon Monoxide) - ppm
    - 9: SO2 (Sulfur Dioxide) - ppm
    - 10: O3 (Ozone) - ppm
    
    Args:
        parameter_id: ID del parámetro a consultar (1, 2, 7, 8, 9, 10)
        bbox: Coordenadas del área geográfica (default: área de Colorado)
        limit: Número máximo de resultados
        
    Returns:
        JSON con todas las mediciones del parámetro especificado
    """
    valid_parameters = [1, 2, 7, 8, 9, 10]
    
    if parameter_id not in valid_parameters:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameter ID. Must be one of: {valid_parameters}. "
                   f"(1=PM10, 2=PM2.5, 7=NO2, 8=CO, 9=SO2, 10=O3)"
        )
    
    try:
        data = await client.get_measurements_by_parameter(
            parameter_id=parameter_id,
            bbox=bbox,
            limit=limit
        )
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching measurements: {str(e)}"
        )


@router.get("/measurements/by-location/{location_id}", response_model=dict)
async def get_measurements_by_location(
    location_id: int,
    full_data: bool = Query(
        False,
        description="Si es True, incluye todas las mediciones; si es False, solo resumen con últimos valores"
    )
):
    """
    [DEPRECADO] Obtener mediciones por ID de ubicación
    
    Se recomienda usar /measurements/by-location-name en su lugar
    """
    try:
        data = await client.get_measurements_by_location(
            location_id=location_id,
            include_full_data=full_data
        )
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching location measurements: {str(e)}"
        )


@router.get("/measurements/by-location-name", response_model=dict)
async def get_measurements_by_location_name(
    location_name: str = Query(
        ...,
        description="Nombre de la ubicación a buscar (búsqueda parcial, insensible a mayúsculas)"
    ),
    state: Optional[str] = Query(
        None,
        description="Estado de USA donde buscar (ej: 'colorado', 'new_york', 'california'). Si no se especifica, busca en todo USA"
    ),
    bbox: Optional[str] = Query(
        None,
        description="[Opcional] Área de búsqueda personalizada en formato bbox (min_lon,min_lat,max_lon,max_lat)"
    )
):
    """
    Buscar ubicación por nombre y obtener todas las mediciones de contaminación
    
    **NUEVO: Ya no necesitas especificar bbox!**
    
    Ejemplos de uso simplificado:
    - `/measurements/by-location-name?location_name=Denver` → Busca en todo USA
    - `/measurements/by-location-name?location_name=New York&state=new_york` → Busca solo en NY
    - `/measurements/by-location-name?location_name=Los Angeles&state=california` → Busca en CA
    
    Estados disponibles:
    - colorado, california, new_york, texas, florida, washington, illinois,
    - pennsylvania, ohio, michigan, entire_us (todo USA, es el default)
    
    Parámetros de contaminación devueltos: PM10, PM2.5, NO2, CO, SO2, O3
    
    Cada parámetro incluye:
    - latest_value: Último valor medido
    - unit: Unidad de medida
    - datetime: Fecha y hora de la medición
    - all_measurements: Array con los últimos 10 valores históricos
    """
    try:
        data = await client.search_location_and_get_all_measurements(
            location_name=location_name,
            bbox=bbox,
            state=state
        )
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching location: {str(e)}"
        )


@router.get("/locations/in-area")
async def get_all_locations_in_area(
    bbox: str = Query(
        ...,
        description="Área de búsqueda en formato bbox (min_lon,min_lat,max_lon,max_lat)"
    ),
    limit: int = Query(
        1000,
        description="Número máximo de ubicaciones a obtener de la API",
        ge=1,
        le=10000
    ),
    max_process: int = Query(
        100,
        description="Número máximo de ubicaciones a procesar (limita tiempo de espera)",
        ge=1,
        le=200
    ),
    sampling: str = Query(
        "distributed",
        description="Estrategia de muestreo: 'random', 'distributed', 'first'",
        regex="^(random|distributed|first)$"
    )
):
    """
    Obtener ubicaciones de monitoreo con sus mediciones - OPTIMIZADO
    
    **Control de tiempo de respuesta:**
    
    - `max_process`: Límite de ubicaciones a procesar (default: 100)
      - 20 ubicaciones: ~5-8 segundos
      - 50 ubicaciones: ~10-15 segundos
      - 100 ubicaciones: ~20-30 segundos
    
    - `sampling`: Estrategia de selección cuando hay muchas ubicaciones
      - `distributed` (recomendado): Distribuye uniformemente en el área
      - `random`: Selección aleatoria
      - `first`: Toma las primeras N ubicaciones
    
    Ejemplos para diferentes estados:
    - Colorado: `?bbox=-109.05,37,-102.04,41&max_process=50`
    - California: `?bbox=-124.48,32.53,-114.13,42.01&max_process=100`
    - New York: `?bbox=-79.76,40.50,-71.86,45.01&max_process=50`
    - Washington: `?bbox=-124.85,45.54,-116.92,49&max_process=100`
    """
    try:
        data = await client.get_all_locations_in_bbox_with_measurements(
            bbox=bbox,
            limit=limit,
            max_locations_to_process=max_process,
            sampling_strategy=sampling
        )
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching locations: {str(e)}"
        )


@router.get("/test/washington")
async def test_washington_state(
    max_process: int = Query(
        100,
        description="Número de ubicaciones a procesar (default: 100)",
        ge=10,
        le=200
    ),
    sampling: str = Query(
        "distributed",
        description="Estrategia: 'distributed', 'random', 'first'",
        regex="^(random|distributed|first)$"
    )
):
    """
    🧪 ENDPOINT DE TEST: Washington State
    
    Prueba la API optimizada con el estado de Washington.
    
    **NOTA:** Tests grandes (100+ ubicaciones) pueden tardar 30-60 segundos.
    
    Configuraciones de prueba:
    - Rápida (20 loc): `/test/washington?max_process=20` (~5-10s)
    - Media (50 loc): `/test/washington?max_process=50` (~15-20s)
    - Completa (100 loc): `/test/washington?max_process=100` (~30-40s)
    
    Compara diferentes estrategias:
    - Distribuido: `?max_process=50&sampling=distributed`
    - Aleatorio: `?max_process=50&sampling=random`
    - Primeros: `?max_process=50&sampling=first`
    """
    import time
    
    # Bbox de Washington State
    washington_bbox = "-124.85,45.54,-116.92,49"
    
    start_time = time.time()
    
    try:
        data = await client.get_all_locations_in_bbox_with_measurements(
            bbox=washington_bbox,
            limit=1000,
            max_locations_to_process=max_process,
            sampling_strategy=sampling
        )
        
        elapsed_time = time.time() - start_time
        
        # Agregar métricas de performance
        successful = data.get('successful_locations', data.get('locations_processed', 0))
        failed = data.get('failed_locations', 0)
        
        data["performance"] = {
            "total_time_seconds": round(elapsed_time, 2),
            "locations_per_second": round(successful / elapsed_time, 2) if elapsed_time > 0 and successful > 0 else 0,
            "average_time_per_location_ms": round((elapsed_time / successful) * 1000, 2) if successful > 0 else 0,
            "successful_locations": successful,
            "failed_locations": failed
        }
        
        # Agregar estadísticas de cobertura
        if data.get("found"):
            locations = data.get("locations", [])
            
            # Calcular estadísticas de parámetros (solo de ubicaciones exitosas)
            param_stats = {param: 0 for param in client.PARAMETERS.keys()}
            for loc in locations:
                if "error" not in loc:  # Solo contar ubicaciones sin error
                    for param, measurement in loc.get("measurements", {}).items():
                        if measurement.get("available"):
                            param_stats[param] += 1
            
            data["parameter_coverage"] = {
                param: {
                    "available_at": count,
                    "percentage": f"{(count / successful * 100):.1f}%" if successful > 0 else "0%"
                }
                for param, count in param_stats.items()
            }
        
        return data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing Washington: {str(e)}"
        )
