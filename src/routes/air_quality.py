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
        description="Área de búsqueda en formato bbox (min_lon,min_lat,max_lon,max_lat). Ejemplos: '-109.05,37,-102.04,41' (Colorado), '-74.3,40.4,-73.7,40.9' (NYC)"
    ),
    limit: int = Query(
        100,
        description="Número máximo de ubicaciones a retornar",
        ge=1,
        le=1000
    )
):
    """
    Obtener TODAS las ubicaciones de monitoreo dentro de un área específica con sus mediciones
    
    **API 3: Mapa de Ubicaciones con Datos**
    
    Esta API te permite visualizar todos los puntos de monitoreo en un área geográfica
    y obtener las mediciones de contaminación de cada uno.
    
    Ideal para:
    - Mostrar todos los sensores en un mapa interactivo
    - Comparar niveles de contaminación entre diferentes puntos de una ciudad
    - Análisis de densidad de estaciones de monitoreo
    
    Ejemplos de bbox útiles:
    - Colorado: "-109.05,37,-102.04,41"
    - New York City: "-74.3,40.4,-73.7,40.9"
    - Los Angeles: "-118.67,33.70,-118.15,34.34"
    - Chicago: "-87.94,41.64,-87.52,42.02"
    - Miami: "-80.32,25.71,-80.13,25.86"
    
    Cada ubicación incluye:
    - location_id: ID único de la ubicación
    - name: Nombre del lugar
    - locality: Área/región
    - coordinates: Latitud y longitud
    - measurements: Mediciones de PM10, PM2.5, NO2, CO, SO2, O3
    - measurements_summary: Resumen de parámetros disponibles
    
    Returns:
        JSON con todas las ubicaciones y sus mediciones de contaminación
    """
    try:
        data = await client.get_all_locations_in_bbox_with_measurements(
            bbox=bbox,
            limit=limit
        )
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching locations: {str(e)}"
        )
