"""
Pydantic schemas for OpenAQ air quality data
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Coordinates(BaseModel):
    """Geographic coordinates"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Location(BaseModel):
    """Location information"""
    id: Optional[int] = None
    name: Optional[str] = None
    locality: Optional[str] = None
    timezone: Optional[str] = None
    country: Optional[Dict[str, Any]] = None
    owner: Optional[Dict[str, Any]] = None
    provider: Optional[Dict[str, Any]] = None
    is_mobile: Optional[bool] = None
    is_monitor: Optional[bool] = None
    instruments: Optional[List[Dict[str, Any]]] = None
    sensors: Optional[List[Dict[str, Any]]] = None
    coordinates: Optional[Coordinates] = None
    bounds: Optional[List[float]] = None
    distance: Optional[float] = None
    datetime_first: Optional[Dict[str, Any]] = None
    datetime_last: Optional[Dict[str, Any]] = None


class Period(BaseModel):
    """Time period information"""
    label: Optional[str] = None
    interval: Optional[str] = None
    datetime_from: Optional[Dict[str, Any]] = None
    datetime_to: Optional[Dict[str, Any]] = None


class Summary(BaseModel):
    """Summary statistics"""
    min: Optional[float] = None
    q02: Optional[float] = None
    q25: Optional[float] = None
    median: Optional[float] = None
    q75: Optional[float] = None
    q98: Optional[float] = None
    max: Optional[float] = None
    sd: Optional[float] = None


class Coverage(BaseModel):
    """Data coverage information"""
    expected_count: Optional[int] = None
    expected_interval: Optional[str] = None
    observed_count: Optional[int] = None
    observed_interval: Optional[str] = None
    percent_complete: Optional[float] = None
    percent_coverage: Optional[float] = None
    datetime_from: Optional[Dict[str, Any]] = None
    datetime_to: Optional[Dict[str, Any]] = None


class Parameter(BaseModel):
    """Parameter information"""
    id: Optional[int] = None
    name: Optional[str] = None
    units: Optional[str] = None
    display_name: Optional[str] = None


class Measurement(BaseModel):
    """Air quality measurement data"""
    location_id: Optional[int] = None
    sensors_id: Optional[int] = None
    location: Optional[Location] = None
    parameter: Optional[Parameter] = None
    value: Optional[float] = None
    period: Optional[Period] = None
    coverage: Optional[Coverage] = None
    summary: Optional[Summary] = None
    coordinates: Optional[Coordinates] = None


class OpenAQResponse(BaseModel):
    """OpenAQ API response"""
    meta: Optional[Dict[str, Any]] = None
    results: Optional[List[Measurement]] = []


class AirQualityData(BaseModel):
    """Simplified air quality data for response"""
    location_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    parameter: str
    value: Optional[float] = None
    unit: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_updated: Optional[str] = None


class MultiParameterResponse(BaseModel):
    """Response for multiple parameters"""
    location: str
    coordinates: Optional[Coordinates] = None
    measurements: Dict[str, Optional[float]] = {}
    last_updated: Optional[str] = None
