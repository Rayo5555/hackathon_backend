import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import os
from dotenv import load_dotenv

import httpx
from fastapi import HTTPException

from src.schemas import (
    AirQualityMeasurement, AirQualityStation, Coordinates,
    PollutantType, AQICategory, DataSource,
    AirNowCurrentObservation, OpenAQMeasurement,
    APIResponse, DataExtractionStatus
)

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirQualityAPIClient:
    """Cliente para extraer datos de calidad del aire de múltiples fuentes"""
    
    def __init__(self):
        self.airnow_api_key = os.getenv("AIRNOW_API_KEY", "")
        self.openaq_api_key = os.getenv("OPENAQ_API_KEY", "")
        self.openaq_base_url = "https://api.openaq.org/v3"
        self.airnow_base_url = "https://www.airnowapi.org/aq"
        self.data_dir = Path("data/air_quality")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Debug: Verificar API keys
        logger.info(f"OpenAQ API Key configured: {'Yes' if self.openaq_api_key else 'No'}")
        logger.info(f"AirNow API Key configured: {'Yes' if self.airnow_api_key else 'No'}")
        if self.openaq_api_key:
            logger.info(f"OpenAQ API Key length: {len(self.openaq_api_key)} characters")
        
        # Headers para OpenAQ API v3
        headers = {}
        if self.openaq_api_key:
            headers["X-API-Key"] = self.openaq_api_key
        
        # Configurar cliente HTTP
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=100),
            headers=headers
        )
        
        # Status tracking
        self.extraction_status = DataExtractionStatus()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _convert_pollutant_name(self, parameter: str, source: DataSource) -> Optional[PollutantType]:
        """Convertir nombres de parámetros entre APIs"""
        parameter = parameter.lower().strip()
        
        # Mapeo común
        param_mapping = {
            "ozone": PollutantType.OZONE,
            "o3": PollutantType.OZONE,
            "no2": PollutantType.NO2,
            "nitrogen dioxide": PollutantType.NO2,
            "pm2.5": PollutantType.PM25,
            "pm25": PollutantType.PM25,
            "pm10": PollutantType.PM10,
            "co": PollutantType.CO,
            "carbon monoxide": PollutantType.CO,
            "so2": PollutantType.SO2,
            "sulfur dioxide": PollutantType.SO2,
            "hcho": PollutantType.HCHO,
            "formaldehyde": PollutantType.HCHO
        }
        
        return param_mapping.get(parameter)
    
    def _determine_aqi_category(self, aqi: int) -> AQICategory:
        """Determinar categoría AQI basada en el valor"""
        if aqi <= 50:
            return AQICategory.GOOD
        elif aqi <= 100:
            return AQICategory.MODERATE
        elif aqi <= 150:
            return AQICategory.UNHEALTHY_SENSITIVE
        elif aqi <= 200:
            return AQICategory.UNHEALTHY
        elif aqi <= 300:
            return AQICategory.VERY_UNHEALTHY
        else:
            return AQICategory.HAZARDOUS
    
    async def get_airnow_current_observations(
        self, 
        bbox: Optional[Dict[str, float]] = None,
        zip_code: Optional[str] = None
    ) -> List[AirQualityMeasurement]:
        """Obtener observaciones actuales de AirNow API"""
        
        if not self.airnow_api_key:
            logger.warning("AirNow API key not configured")
            return []
        
        measurements = []
        
        try:
            # Si no se especifica bbox, usar un bbox que cubra Estados Unidos
            if not bbox and not zip_code:
                bbox = {
                    "minX": -125.0,  # Costa oeste
                    "minY": 25.0,    # Sur
                    "maxX": -66.0,   # Costa este
                    "maxY": 49.0     # Norte
                }
            
            if bbox:
                url = f"{self.airnow_base_url}/observation/bbox"
                params = {
                    "minX": bbox["minX"],
                    "minY": bbox["minY"], 
                    "maxX": bbox["maxX"],
                    "maxY": bbox["maxY"],
                    "api_key": self.airnow_api_key,
                    "format": "application/json",
                    "verbose": 1,
                    "nowcastonly": 0,
                    "includerawconcentrations": 1
                }
            else:
                url = f"{self.airnow_base_url}/observation/zipCode/current"
                params = {
                    "zipCode": zip_code,
                    "api_key": self.airnow_api_key,
                    "format": "application/json"
                }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"AirNow API returned {len(data)} observations")
            
            for obs in data:
                try:
                    pollutant = self._convert_pollutant_name(
                        obs.get("ParameterName", ""), 
                        DataSource.AIRNOW
                    )
                    
                    if not pollutant:
                        continue
                    
                    # Construir timestamp
                    date_str = obs.get("DateObserved", "")
                    hour = obs.get("HourObserved", 0)
                    
                    if date_str:
                        timestamp = datetime.strptime(f"{date_str} {hour:02d}:00", "%Y-%m-%d %H:%M")
                    else:
                        timestamp = datetime.utcnow()
                    
                    aqi = obs.get("AQI", 0)
                    category = None
                    if aqi > 0:
                        category = self._determine_aqi_category(aqi)
                    
                    measurement = AirQualityMeasurement(
                        parameter=pollutant,
                        value=obs.get("Value", 0.0),
                        unit=obs.get("Unit", ""),
                        last_updated=timestamp,
                        aqi=aqi if aqi > 0 else None,
                        category=category,
                        coordinates=Coordinates(
                            latitude=obs.get("Latitude", 0.0),
                            longitude=obs.get("Longitude", 0.0)
                        ),
                        location_name=obs.get("ReportingArea", ""),
                        state=obs.get("StateCode", ""),
                        country="US",
                        source=DataSource.AIRNOW,
                        site_id=obs.get("SiteId", "")
                    )
                    
                    measurements.append(measurement)
                    
                except Exception as e:
                    logger.warning(f"Error processing AirNow observation: {e}")
                    continue
            
        except httpx.HTTPStatusError as e:
            logger.error(f"AirNow API HTTP error: {e}")
        except Exception as e:
            logger.error(f"Error fetching AirNow data: {e}")
        
        return measurements
    
    async def get_openaq_measurements(
        self,
        coordinates: Optional[Coordinates] = None,
        radius: int = 50000,  # metros
        limit: int = 1000
    ) -> List[AirQualityMeasurement]:
        """Obtener mediciones de OpenAQ API v3"""
        
        measurements = []
        
        if not self.openaq_api_key:
            logger.warning("OpenAQ API key not configured")
            return []
        
        try:
            url = f"{self.openaq_base_url}/measurements"
            
            # Parámetros base para la API v3
            base_params = {
                "limit": min(limit, 1000),  # API v3 permite hasta 1000
                "page": 1,
                "sort_order": "desc",
                "order_by": "datetime",
                "date_from": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),  # Últimas 24 horas
                "date_to": datetime.utcnow().strftime("%Y-%m-%d")
            }
            
            # Si se especifican coordenadas, usarlas
            if coordinates:
                base_params.update({
                    "coordinates": f"{coordinates.latitude},{coordinates.longitude}",
                    "radius": radius
                })
            else:
                # Sin coordenadas específicas, buscar en EE.UU.
                base_params["countries_id"] = 840  # ID de Estados Unidos
            
            # Intentar obtener datos para diferentes parámetros
            target_parameters = [
                ("pm25", 2),   # PM2.5 
                ("pm10", 1),   # PM10
                ("no2", 8),    # Nitrogen dioxide  
                ("o3", 7),     # Ozone
                ("so2", 21),   # Sulfur dioxide
                ("co", 6)      # Carbon monoxide
            ]
            
            for param_name, param_id in target_parameters:
                try:
                    # Parámetros específicos para este contaminante
                    params = base_params.copy()
                    params["parameters_id"] = param_id
                    
                    logger.info(f"Requesting OpenAQ data for {param_name} (ID: {param_id})")
                    logger.debug(f"Request URL: {url}")
                    logger.debug(f"Request params: {params}")
                    
                    response = await self.client.get(url, params=params)
                    
                    # Log de la respuesta
                    logger.info(f"OpenAQ response status for {param_name}: {response.status_code}")
                    
                    if response.status_code == 401:
                        logger.error("OpenAQ API key is invalid or expired")
                        break
                    elif response.status_code == 429:
                        logger.warning("OpenAQ API rate limit exceeded, waiting...")
                        await asyncio.sleep(5)
                        continue
                    elif response.status_code != 200:
                        logger.warning(f"OpenAQ API returned status {response.status_code} for {param_name}")
                        continue
                    
                    data = response.json()
                    results = data.get("results", [])
                    
                    logger.info(f"OpenAQ API v3 returned {len(results)} measurements for {param_name}")
                    
                    if len(results) == 0:
                        logger.warning(f"No results found for {param_name}")
                        continue
                    
                    # Procesar cada resultado
                    for result in results:
                        try:
                            measurement = self._parse_openaq_v3_measurement(result, param_name)
                            if measurement:
                                measurements.append(measurement)
                            
                        except Exception as e:
                            logger.warning(f"Error processing OpenAQ v3 measurement for {param_name}: {e}")
                            continue
                    
                    # Pausa respetuosa entre requests
                    await asyncio.sleep(1)
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"OpenAQ API v3 HTTP error for {param_name}: {e}")
                    if e.response.status_code == 401:
                        logger.error("API key is invalid or expired")
                        break
                except Exception as e:
                    logger.error(f"Error fetching OpenAQ v3 data for {param_name}: {e}")
            
            logger.info(f"Total OpenAQ measurements collected: {len(measurements)}")
            
        except Exception as e:
            logger.error(f"Error in OpenAQ v3 data extraction: {e}")
        
        return measurements
    
    def _get_parameter_id(self, parameter: str) -> Optional[int]:
        """Obtener ID del parámetro para OpenAQ API v3"""
        # IDs de parámetros en OpenAQ v3
        parameter_ids = {
            "o3": 7,      # Ozone
            "no2": 8,     # Nitrogen dioxide
            "pm25": 2,    # PM2.5
            "pm10": 1,    # PM10
            "so2": 21,    # Sulfur dioxide
            "co": 6       # Carbon monoxide
        }
        return parameter_ids.get(parameter.lower())
    
    def _parse_openaq_v3_measurement(self, result: dict, parameter: str) -> Optional[AirQualityMeasurement]:
        """Parsear medición de OpenAQ API v3"""
        try:
            pollutant = self._convert_pollutant_name(parameter, DataSource.OPENAQ)
            if not pollutant:
                logger.debug(f"Unable to convert parameter: {parameter}")
                return None
            
            # Obtener valor y unidad
            value = result.get("value")
            if value is None:
                logger.debug("No value found in measurement")
                return None
            
            unit = result.get("unit", "")
            
            # Procesar coordenadas - OpenAQ v3 puede tener diferentes estructuras
            coordinates_data = result.get("coordinates", {})
            if not coordinates_data and "location" in result:
                # Intentar obtener de location
                location_data = result.get("location", {})
                coordinates_data = location_data.get("coordinates", {})
            
            if not coordinates_data:
                # Último intento: buscar lat/lon directamente
                if "latitude" in result and "longitude" in result:
                    coordinates_data = {
                        "latitude": result["latitude"],
                        "longitude": result["longitude"]
                    }
            
            if not coordinates_data or "latitude" not in coordinates_data:
                logger.debug(f"No valid coordinates found for measurement: {result}")
                return None
            
            coords = Coordinates(
                latitude=float(coordinates_data.get("latitude", 0.0)),
                longitude=float(coordinates_data.get("longitude", 0.0))
            )
            
            # Validar coordenadas
            if coords.latitude == 0.0 and coords.longitude == 0.0:
                logger.debug("Invalid coordinates (0,0)")
                return None
            
            # Procesar fecha y hora
            datetime_str = result.get("datetime") or result.get("date", {}).get("utc")
            timestamp = datetime.utcnow()  # Default
            
            if datetime_str:
                try:
                    if isinstance(datetime_str, str):
                        # Manejar diferentes formatos de fecha
                        if "T" in datetime_str:
                            datetime_str = datetime_str.replace("Z", "+00:00")
                            timestamp = datetime.fromisoformat(datetime_str)
                        else:
                            timestamp = datetime.fromisoformat(datetime_str)
                    else:
                        # Si es un dict con formato de fecha
                        utc_date = datetime_str.get("utc") if isinstance(datetime_str, dict) else None
                        if utc_date:
                            timestamp = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
                except Exception as e:
                    logger.debug(f"Error parsing datetime '{datetime_str}': {e}")
                    # Mantener timestamp por defecto
            
            # Obtener información de ubicación
            location_info = result.get("location", {})
            if isinstance(location_info, str):
                location_name = location_info
                city = None
            elif isinstance(location_info, dict):
                location_name = location_info.get("name", location_info.get("label", ""))
                city = location_info.get("city")
            else:
                location_name = str(result.get("location", ""))
                city = None
            
            # Obtener estado si está disponible
            state = None
            if isinstance(location_info, dict):
                state = location_info.get("state") or location_info.get("region")
            
            # Crear la medición
            measurement = AirQualityMeasurement(
                parameter=pollutant,
                value=float(value),
                unit=unit,
                last_updated=timestamp,
                coordinates=coords,
                location_name=location_name,
                city=city,
                state=state,
                country="US",
                source=DataSource.OPENAQ,
                site_id=str(result.get("location_id", result.get("locationId", result.get("id", ""))))
            )
            
            logger.debug(f"Successfully parsed measurement: {pollutant.value} = {value} {unit} at ({coords.latitude}, {coords.longitude})")
            return measurement
            
        except Exception as e:
            logger.warning(f"Error parsing OpenAQ v3 measurement: {e}")
            logger.debug(f"Problematic result: {result}")
            return None
    
    async def extract_all_data(self) -> Dict[str, List[AirQualityMeasurement]]:
        """Extraer datos de todas las fuentes disponibles"""
        
        logger.info("Starting air quality data extraction...")
        self.extraction_status.total_extractions += 1
        
        all_measurements = {
            "airnow": [],
            "openaq": [],
            "mock": []
        }
        
        try:
            # Intentar extraer datos reales de AirNow si hay API key
            if self.airnow_api_key:
                logger.info("Attempting to extract AirNow data...")
                # (El código de AirNow se mantiene igual)
                regions = [
                    {"minX": -125.0, "minY": 32.0, "maxX": -110.0, "maxY": 49.0},
                    {"minX": -110.0, "minY": 25.0, "maxX": -95.0, "maxY": 49.0},
                    {"minX": -95.0, "minY": 25.0, "maxX": -80.0, "maxY": 49.0},
                    {"minX": -80.0, "minY": 25.0, "maxX": -66.0, "maxY": 45.0},
                ]
                
                airnow_tasks = [
                    self.get_airnow_current_observations(bbox=region) 
                    for region in regions
                ]
                
                airnow_results = await asyncio.gather(*airnow_tasks, return_exceptions=True)
                
                for result in airnow_results:
                    if isinstance(result, list):
                        all_measurements["airnow"].extend(result)
                    else:
                        logger.error(f"AirNow extraction failed: {result}")
            
            # Intentar extraer datos de OpenAQ si hay API key - PRIORIDAD ALTA
            if self.openaq_api_key:
                logger.info("Attempting to extract OpenAQ data with comprehensive approach...")
                
                # Estrategia 1: Datos generales de EE.UU. sin coordenadas específicas
                try:
                    general_measurements = await self.get_openaq_measurements(limit=500)
                    all_measurements["openaq"].extend(general_measurements)
                    logger.info(f"General US data: {len(general_measurements)} measurements")
                except Exception as e:
                    logger.warning(f"General OpenAQ extraction failed: {e}")
                
                # Estrategia 2: Ciudades principales de EE.UU.
                major_cities = [
                    ("New York", Coordinates(latitude=40.7128, longitude=-74.0060)),
                    ("Los Angeles", Coordinates(latitude=34.0522, longitude=-118.2437)),
                    ("Chicago", Coordinates(latitude=41.8781, longitude=-87.6298)),
                    ("Houston", Coordinates(latitude=29.7604, longitude=-95.3698)),
                    ("Phoenix", Coordinates(latitude=33.4484, longitude=-112.0740)),
                    ("Philadelphia", Coordinates(latitude=39.9526, longitude=-75.1652)),
                    ("San Antonio", Coordinates(latitude=29.4241, longitude=-98.4936)),
                    ("San Diego", Coordinates(latitude=32.7157, longitude=-117.1611)),
                    ("Dallas", Coordinates(latitude=32.7767, longitude=-96.7970)),
                    ("San Jose", Coordinates(latitude=37.3382, longitude=-121.8863))
                ]
                
                for city_name, coord in major_cities:
                    try:
                        city_measurements = await self.get_openaq_measurements(
                            coordinates=coord, 
                            radius=75000,  # 75km radio
                            limit=200
                        )
                        all_measurements["openaq"].extend(city_measurements)
                        logger.info(f"{city_name}: {len(city_measurements)} measurements")
                        
                        # Pausa entre ciudades
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.warning(f"OpenAQ extraction failed for {city_name}: {e}")
                
                # Eliminar duplicados basados en coordenadas y timestamp
                unique_measurements = []
                seen = set()
                for m in all_measurements["openaq"]:
                    key = (m.coordinates.latitude, m.coordinates.longitude, m.parameter, m.last_updated.isoformat())
                    if key not in seen:
                        seen.add(key)
                        unique_measurements.append(m)
                
                all_measurements["openaq"] = unique_measurements
                logger.info(f"After deduplication: {len(unique_measurements)} unique OpenAQ measurements")
            
            # Solo usar datos simulados como ÚLTIMO RECURSO
            total_real_data = sum(len(measurements) for key, measurements in all_measurements.items() if key != "mock")
            
            logger.info(f"Real data summary - AirNow: {len(all_measurements['airnow'])}, OpenAQ: {len(all_measurements['openaq'])}, Total: {total_real_data}")
            
            if total_real_data == 0:  # Solo si NO hay datos reales en absoluto
                logger.warning("⚠️  NO REAL DATA AVAILABLE - Using mock data as fallback")
                logger.warning("⚠️  Check your API keys and network connection")
                from src.mock_data_generator import MockDataGenerator
                
                generator = MockDataGenerator()
                mock_measurements = generator.generate_measurements(50)  # Reducido a 50
                all_measurements["mock"] = mock_measurements
                
                logger.warning(f"Generated {len(mock_measurements)} mock measurements as fallback")
            else:
                logger.info(f"✅ SUCCESS: Using {total_real_data} real measurements from APIs")
                # No generar datos simulados si tenemos datos reales
            
            # Actualizar estado
            total_extracted = sum(len(measurements) for measurements in all_measurements.values())
            
            if total_extracted > 0:
                self.extraction_status.successful_extractions += 1
                self.extraction_status.last_error = None
            else:
                self.extraction_status.failed_extractions += 1
                self.extraction_status.last_error = "No data extracted from any source"
            
            self.extraction_status.last_extraction = datetime.utcnow()
            
            # Actualizar fuentes activas
            active_sources = []
            if all_measurements["airnow"]:
                active_sources.append(DataSource.AIRNOW)
            if all_measurements["openaq"]:
                active_sources.append(DataSource.OPENAQ)
            if all_measurements["mock"]:
                active_sources.append("mock")
            
            self.extraction_status.active_sources = active_sources
            
            logger.info(f"Extraction completed: {total_extracted} total measurements")
            logger.info(f"AirNow: {len(all_measurements['airnow'])} measurements")
            logger.info(f"OpenAQ: {len(all_measurements['openaq'])} measurements")
            logger.info(f"Mock: {len(all_measurements['mock'])} measurements")
            
        except Exception as e:
            logger.error(f"Error in data extraction: {e}")
            self.extraction_status.failed_extractions += 1
            self.extraction_status.last_error = str(e)
        
        return all_measurements
    
    async def save_data_to_json(self, measurements: Dict[str, List[AirQualityMeasurement]]):
        """Guardar datos extraídos en archivos JSON"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        for source, data in measurements.items():
            if not data:
                continue
                
            filename = f"air_quality_{source}_{timestamp}.json"
            filepath = self.data_dir / filename
            
            # Convertir a dict para serialización JSON
            json_data = {
                "extraction_time": datetime.utcnow().isoformat(),
                "source": source,
                "count": len(data),
                "measurements": [measurement.model_dump() for measurement in data]
            }
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
                
                logger.info(f"Saved {len(data)} measurements to {filepath}")
                
            except Exception as e:
                logger.error(f"Error saving data to {filepath}: {e}")
    
    def get_extraction_status(self) -> DataExtractionStatus:
        """Obtener estado actual de las extracciones"""
        return self.extraction_status


# Instancia global del cliente
air_quality_client = AirQualityAPIClient()