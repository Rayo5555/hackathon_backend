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
        description="Parameter to query (pm10, pm25, no2, co2, so2, o3)"
    ),
    state: Optional[str] = Query(None, description="Filter by US state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(1000, description="Maximum number of results", ge=1, le=10000)
):
    """
    Get latest air quality measurements for a specific parameter in the US
    
    Parameters:
    - pm10: Particulate Matter 10 micrometers
    - pm25: Particulate Matter 2.5 micrometers
    - no2: Nitrogen Dioxide (ppm)
    - co2: Carbon Dioxide (ppm)
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
    Get latest measurements for all monitored parameters (pm10, pm2.5, NO2, CO2, SO2, O3)
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
    Get a list of US states with air quality monitoring stations
    Note: This is a comprehensive list of US states that may have monitoring stations
    """
    us_states = {
        "states": [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
            "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
            "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
            "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
            "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
            "New Hampshire", "New Jersey", "New Mexico", "New York",
            "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
            "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
            "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
            "West Virginia", "Wisconsin", "Wyoming", "District of Columbia"
        ],
        "note": "Use these state names when filtering air quality data"
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
    - 1: PM10 (Particulate Matter 10 micrometers)
    - 2: PM2.5 (Particulate Matter 2.5 micrometers)
    - 7: NO2 ppm (Nitrogen Dioxide)
    - 8: CO2 ppm (Carbon Dioxide)
    - 9: SO2 ppm (Sulfur Dioxide)
    - 10: O3 ppm (Ozone)
    
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
                   f"(1=PM10, 2=PM2.5, 7=NO2, 8=CO2, 9=SO2, 10=O3)"
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
        description="Nombre de la ubicación a buscar (puede ser parcial, case insensitive)"
    ),
    bbox: str = Query(
        "-109.05,37,-102.04,41",
        description="Área de búsqueda (default: Colorado). Formato: min_lon,min_lat,max_lon,max_lat"
    )
):
    """
    🆕 API 2: Buscar ubicación por nombre y obtener todas las mediciones de contaminación
    
    Esta API:
    1. Busca ubicaciones en el área especificada (bbox)
    2. Filtra por el nombre proporcionado
    3. Devuelve TODAS las mediciones de contaminación de esa ubicación
    
    Args:
        location_name: Nombre de la ubicación a buscar (ej: "Downtown", "Denver", "Station 5")
        bbox: Coordenadas del área de búsqueda (default: área de Colorado)
        
    Returns:
        JSON con:
        - found: Si se encontró la ubicación
        - location_id, location_name, locality, coordinates: Información de la ubicación
        - measurements: Diccionario con mediciones de cada tipo de contaminación:
            - pm10, pm25, no2, co2, so2, o3
            - Cada uno incluye: valor más reciente, unidad, timestamp, historial
        
    Ejemplos de bbox útiles:
        - Colorado: -109.05,37,-102.04,41
        - USA Continental: -125.0,24.0,-66.0,49.0
        - California: -124.4,32.5,-114.1,42.0
        - Texas: -106.6,25.8,-93.5,36.5
        
    Ejemplo de uso:
        GET /air-quality/measurements/by-location-name?location_name=Denver&bbox=-109.05,37,-102.04,41
    """
    try:
        data = await client.search_location_and_get_all_measurements(
            location_name=location_name,
            bbox=bbox
        )
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching location: {str(e)}"
        )


