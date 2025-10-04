from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PollutantType(str, Enum):
    """Tipos de contaminantes soportados"""
    OZONE = "o3"
    NO2 = "no2"
    PM25 = "pm25"
    PM10 = "pm10"
    SO2 = "so2"
    CO = "co"
    HCHO = "hcho"  # Formaldehído


class AQICategory(str, Enum):
    """Categorías del Índice de Calidad del Aire"""
    GOOD = "Good"
    MODERATE = "Moderate"
    UNHEALTHY_SENSITIVE = "Unhealthy for Sensitive Groups"
    UNHEALTHY = "Unhealthy"
    VERY_UNHEALTHY = "Very Unhealthy"
    HAZARDOUS = "Hazardous"


class DataSource(str, Enum):
    """Fuentes de datos de calidad del aire"""
    AIRNOW = "airnow"
    OPENAQ = "openaq"
    TEMPO = "tempo"


class Coordinates(BaseModel):
    """Coordenadas geográficas"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class AirQualityMeasurement(BaseModel):
    """Medición individual de calidad del aire"""
    parameter: PollutantType
    value: float
    unit: str
    last_updated: datetime
    aqi: Optional[int] = None
    category: Optional[AQICategory] = None
    coordinates: Coordinates
    location_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "US"
    source: DataSource
    site_id: Optional[str] = None


class AirQualityStation(BaseModel):
    """Estación de monitoreo de calidad del aire"""
    station_id: str
    name: str
    coordinates: Coordinates
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "US"
    measurements: List[AirQualityMeasurement] = []
    last_updated: datetime
    source: DataSource
    is_active: bool = True


class AirQualityForecast(BaseModel):
    """Pronóstico de calidad del aire"""
    location: str
    coordinates: Coordinates
    date: datetime
    aqi: int
    category: AQICategory
    primary_pollutant: PollutantType
    source: DataSource


class RegionalAirQuality(BaseModel):
    """Datos regionales de calidad del aire"""
    region: str
    state: str
    stations: List[AirQualityStation]
    summary: Dict[PollutantType, float] = {}
    average_aqi: Optional[float] = None
    last_updated: datetime


class AirNowCurrentObservation(BaseModel):
    """Respuesta de la API de AirNow para observaciones actuales"""
    DateObserved: str
    HourObserved: int
    LocalTimeZone: str
    ReportingArea: str
    StateCode: str
    Latitude: float
    Longitude: float
    ParameterName: str
    AQI: int
    Category: Dict[str, Any]


class OpenAQMeasurement(BaseModel):
    """Respuesta de la API de OpenAQ"""
    locationId: int
    location: str
    parameter: str
    value: float
    unit: str
    country: str
    city: Optional[str] = None
    coordinates: Dict[str, float]
    date: Dict[str, datetime]
    isMobile: bool = False
    entity: str
    sensorType: str


class APIResponse(BaseModel):
    """Respuesta genérica de la API"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: DataSource


class DataExtractionStatus(BaseModel):
    """Estado de la extracción de datos"""
    last_extraction: Optional[datetime] = None
    next_extraction: Optional[datetime] = None
    total_extractions: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    active_sources: List[DataSource] = []
    last_error: Optional[str] = None


class StationQuery(BaseModel):
    """Parámetros de consulta para estaciones"""
    coordinates: Optional[Coordinates] = None
    radius_km: Optional[float] = Field(None, ge=1, le=100)
    state: Optional[str] = None
    city: Optional[str] = None
    pollutants: Optional[List[PollutantType]] = None
    active_only: bool = True


class AggregatedAirQuality(BaseModel):
    """Datos agregados de calidad del aire"""
    region: str
    time_period: str
    pollutant_averages: Dict[PollutantType, float]
    station_count: int
    data_completeness: float
    timestamp: datetime