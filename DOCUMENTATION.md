# US Air Quality Monitoring API - Technical Documentation

**Version:** 1.0.0  
**Last Updated:** October 5, 2025  
**Repository:** hackathon_backend  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [Data Sources](#data-sources)
6. [API Reference](#api-reference)
7. [Data Models](#data-models)
8. [Configuration](#configuration)
9. [Deployment](#deployment)
10. [Performance Considerations](#performance-considerations)
11. [Error Handling](#error-handling)
12. [Future Enhancements](#future-enhancements)

---

## 1. Executive Summary

### 1.1 Project Overview

The US Air Quality Monitoring API is a comprehensive backend system designed to aggregate, process, and serve real-time air quality data for the United States. The system integrates two primary data sources:

1. **Ground-based measurements** from OpenAQ's global air quality monitoring network
2. **Satellite observations** from NASA's TEMPO (Tropospheric Emissions: Monitoring of Pollution) mission

### 1.2 Key Features

- **Real-time Data Access**: Retrieval of current air quality measurements from thousands of monitoring stations
- **Satellite Integration**: NASA TEMPO satellite data with automated 30-minute update cycles
- **Intelligent Location Search**: Natural language location search with state-based filtering
- **Geographic Filtering**: Bounding box queries for regional data analysis
- **Concurrent Processing**: Optimized asynchronous data processing for high performance
- **Distributed Sampling**: Smart geographic distribution of monitoring locations
- **Comprehensive Coverage**: Monitoring of 6 ground-based pollutants and 5 satellite-observed parameters

### 1.3 Target Use Cases

- Environmental monitoring and reporting
- Public health research
- Climate science applications
- Air quality visualization platforms
- Policy-making data support
- Educational and awareness tools

---

## 2. System Architecture

### 2.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│         (Web Apps, Mobile Apps, Data Consumers)             │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS/REST
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application Layer                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Air Quality  │  │    TEMPO     │  │    CORS      │     │
│  │   Router     │  │   Router     │  │  Middleware  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────┬───────────────────┬──────────────────────────┘
             │                   │
             ▼                   ▼
┌─────────────────────┐ ┌────────────────────────────────────┐
│  OpenAQ API Client  │ │  NASA TEMPO Data Processors        │
│  ┌──────────────┐   │ │  ┌──────────┐ ┌──────────────┐   │
│  │   Async      │   │ │  │  O3/SO2  │ │  NO2/HCHO    │   │
│  │   HTTP       │   │ │  │  Processor│ │  Processor   │   │
│  │   Client     │   │ │  └──────────┘ └──────────────┘   │
│  └──────────────┘   │ │                                    │
│  ┌──────────────┐   │ │  Scheduled Updates (30 min cycle)  │
│  │  Concurrent  │   │ └────────────────────────────────────┘
│  │  Processing  │   │
│  └──────────────┘   │
└────────────┬────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│               External Data Sources                          │
│  ┌─────────────────────┐    ┌─────────────────────────┐    │
│  │    OpenAQ API v3    │    │  NASA Earthdata         │    │
│  │  (Ground stations)  │    │  (TEMPO Satellite)      │    │
│  └─────────────────────┘    └─────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Flow

#### Ground-Based Data Flow
```
Client Request → FastAPI Router → OpenAQ Client → 
HTTP Request to OpenAQ API → Data Processing → 
Schema Validation → JSON Response
```

#### Satellite Data Flow
```
APScheduler Trigger (every 30 min) → 
TEMPO Data Processor → NASA Earthdata Authentication → 
NetCDF Data Download → xarray Processing → 
JSON Serialization → File Storage → 
API Request → Geographic Filtering → JSON Response
```

### 2.3 Design Patterns

- **Repository Pattern**: OpenAQClient encapsulates all external API interactions
- **Router Pattern**: FastAPI routers organize endpoints by domain
- **Async/Await Pattern**: Asynchronous operations for I/O-bound tasks
- **Middleware Pattern**: CORS and request processing
- **Scheduled Tasks**: APScheduler for periodic satellite data updates
- **Schema Validation**: Pydantic models for type safety

---

## 3. Technology Stack

### 3.1 Core Framework
- **FastAPI 0.118.0**: Modern async web framework
  - Automatic API documentation (OpenAPI/Swagger)
  - Built-in data validation
  - High performance with async support

### 3.2 HTTP & Networking
- **HTTPX 0.28.1**: Async HTTP client for external API calls
- **Uvicorn 0.37.0**: ASGI server for production deployment

### 3.3 Data Processing
- **xarray 2025.9.1**: Multi-dimensional array processing (satellite data)
- **NumPy**: Numerical operations
- **NetCDF4 1.7.2**: NetCDF file format support
- **earthaccess 0.15.1**: NASA Earthdata access library

### 3.4 Data Validation & Configuration
- **Pydantic**: Data validation using Python type hints
- **python-dotenv 1.0.0**: Environment variable management

### 3.5 Task Scheduling
- **APScheduler 3.11.0**: Advanced Python Scheduler for background tasks

### 3.6 Visualization & Geospatial (Dependencies)
- **matplotlib 3.10.6**: Data visualization
- **cartopy 0.25.0**: Geospatial data processing

### 3.7 Database (Optional)
- **SQLAlchemy 2.0.43**: SQL toolkit (for future persistence needs)

### 3.8 Development Tools
- **UV Package Manager**: Ultra-fast Python package installer
- **Python 3.13+**: Latest Python runtime

---

## 4. Core Components

### 4.1 Main Application (`src/main.py`)

**Purpose**: Application entry point and configuration

**Responsibilities**:
- FastAPI application instantiation
- CORS middleware configuration
- Router registration
- Environment variable loading
- Root endpoint with API navigation

**Key Configuration**:
```python
CORS Origins: Multiple localhost ports + wildcard for development
API Title: "US Air Quality Monitoring API"
Version: "1.0.0"
```

**Routers**:
- `/tempo`: NASA TEMPO satellite data endpoints
- `/air-quality`: OpenAQ ground-based data endpoints

---

### 4.2 OpenAQ Client (`src/openaq_client.py`)

**Purpose**: Abstraction layer for OpenAQ API v3 interactions

**Class**: `OpenAQClient`

**Key Methods**:

#### 4.2.1 Core API Methods

##### `get_latest_measurements()`
```python
async def get_latest_measurements(
    parameter_id: int,
    country: str = "US",
    limit: int = 1000,
    state: Optional[str] = None,
    city: Optional[str] = None
) -> dict
```
**Purpose**: Fetch latest measurements for a specific pollutant parameter

**Parameters**:
- `parameter_id`: Pollutant identifier (1-10)
- `country`: ISO country code
- `limit`: Maximum results (1-10,000)
- `state`: Optional state filter
- `city`: Optional city filter

**Returns**: Dictionary with metadata and measurement results

---

##### `get_all_parameters_latest()`
```python
async def get_all_parameters_latest(
    country: str = "US",
    limit: int = 1000,
    **filters
) -> dict
```
**Purpose**: Concurrently fetch data for all 6 monitored parameters

**Approach**: Uses `asyncio.gather()` for parallel requests

**Returns**: Dictionary with parameter names as keys, each containing measurement data

---

##### `get_locations()`
```python
async def get_locations(
    country: str = "US",
    limit: int = 10000,
    **filters
) -> dict
```
**Purpose**: Retrieve monitoring station locations with metadata

**Returns**: List of location objects with coordinates, names, and IDs

---

##### `search_locations()`
```python
async def search_locations(
    location_name: str,
    bbox: Optional[str] = None,
    limit: int = 1000
) -> dict
```
**Purpose**: Search for monitoring locations by name within geographic bounds

**Features**:
- Case-insensitive partial matching
- Geographic filtering via bounding box
- Fuzzy search capabilities

---

##### `get_measurements_for_location()`
```python
async def get_measurements_for_location(
    location_id: int,
    include_full_data: bool = False
) -> dict
```
**Purpose**: Retrieve all pollutant measurements for a specific location

**Process**:
1. Fetch location metadata
2. Get sensor-to-parameter mapping
3. Retrieve latest measurements
4. Correlate sensors with parameters
5. Build comprehensive measurement dictionary

**Optimization**: Only includes available measurements (no null placeholders)

---

##### `get_locations_in_area_with_measurements()`
```python
async def get_locations_in_area_with_measurements(
    bbox: str,
    limit: int = 1000,
    max_process: int = 100,
    sampling: str = "distributed"
) -> dict
```
**Purpose**: High-performance endpoint for bulk location data retrieval

**Features**:
- Geographic bounding box filtering
- Distributed geographic sampling
- Concurrent processing with semaphores
- Performance metrics tracking
- Parameter coverage statistics

**Sampling Strategies**:
- `distributed`: Grid-based geographic distribution
- `random`: Random selection
- `first`: First N locations

**Performance Controls**:
- `max_concurrent=10`: Parallel request limit
- Timeout: 30s per request, 10s connect timeout
- Rate limiting via semaphore

---

#### 4.2.2 Helper Methods

##### `_distribute_locations()`
**Purpose**: Implement intelligent geographic distribution sampling

**Algorithm**:
1. Parse bounding box coordinates
2. Create spatial grid (√n × √n cells)
3. Assign locations to grid cells
4. Sample one location per cell
5. Fill remaining quota randomly

**Benefits**: Better geographic coverage than random sampling

---

##### `_process_locations_concurrently()`
**Purpose**: Concurrent processing with error handling

**Features**:
- Semaphore-based concurrency control
- Individual location error isolation
- Progress tracking
- Graceful degradation

---

### 4.3 Data Schemas (`src/schemas.py`)

**Purpose**: Pydantic models for type safety and validation

**Key Models**:

#### `Coordinates`
```python
class Coordinates(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
```

#### `Location`
```python
class Location(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    locality: Optional[str] = None
    timezone: Optional[str] = None
    country: Optional[Dict[str, Any]] = None
    coordinates: Optional[Coordinates] = None
    # ... additional fields
```

#### `Parameter`
```python
class Parameter(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    units: Optional[str] = None
    display_name: Optional[str] = None
```

#### `Measurement`
```python
class Measurement(BaseModel):
    location_id: Optional[int] = None
    sensors_id: Optional[int] = None
    location: Optional[Location] = None
    parameter: Optional[Parameter] = None
    value: Optional[float] = None
    coordinates: Optional[Coordinates] = None
    # ... additional fields
```

**Benefits**:
- Automatic request/response validation
- Clear API contracts
- IDE autocompletion
- Runtime type checking

---

### 4.4 Air Quality Routes (`src/routes/air_quality.py`)

**Purpose**: HTTP endpoints for ground-based air quality data

**Key Endpoints**:

#### GET `/air-quality/latest`
**Purpose**: Latest measurements for specific parameter  
**Query Params**: `parameter`, `state`, `city`, `limit`  
**Response**: Measurements with metadata

#### GET `/air-quality/latest/all`
**Purpose**: Latest measurements for all parameters  
**Query Params**: `state`, `city`, `limit`  
**Response**: Nested dictionary by parameter

#### GET `/air-quality/locations`
**Purpose**: Monitoring station locations  
**Query Params**: `state`, `city`, `limit`  
**Response**: Location list with coordinates

#### GET `/air-quality/summary`
**Purpose**: Aggregated statistics  
**Query Params**: `state`, `city`, `limit`  
**Response**: Parameter counts and location counts

#### GET `/air-quality/states`
**Purpose**: List of predefined US state bounding boxes  
**Response**: State names with search keys

#### GET `/air-quality/measurements/by-parameter/{parameter_id}`
**Purpose**: All measurements for specific pollutant  
**Path Params**: `parameter_id` (1, 2, 7, 8, 9, 10)  
**Query Params**: `bbox`, `limit`  
**Response**: Filtered measurements by geography

#### GET `/air-quality/measurements/by-location/{location_id}`
**Purpose**: All parameters for specific location (DEPRECATED)  
**Path Params**: `location_id`  
**Query Params**: `full_data`  
**Status**: Deprecated in favor of by-location-name

#### GET `/air-quality/measurements/by-location-name`
**Purpose**: Intelligent location search with measurements  
**Query Params**: `location_name`, `state`, `bbox`  
**Response**: Location match with all measurements

#### GET `/air-quality/locations/in-area`
**Purpose**: Optimized bulk location retrieval  
**Query Params**: `bbox`, `limit`, `max_process`, `sampling`  
**Response**: Multiple locations with measurements and performance metrics

#### GET `/air-quality/test/washington`
**Purpose**: Test endpoint for Washington State  
**Query Params**: `max_process`, `sampling`  
**Response**: Test results with performance statistics

---

### 4.5 TEMPO Routes (`src/routes/tempo.py`)

**Purpose**: HTTP endpoints for NASA TEMPO satellite data

**Key Endpoints**:

#### GET `/tempo/get_data_NO2/{lat_min}/{lat_max}/{lon_min}/{lon_max}`
**Purpose**: Nitrogen dioxide satellite observations  
**Path Params**: Geographic bounds  
**Response**: Filtered NO₂ measurements

#### GET `/tempo/get_data_SO2/{lat_min}/{lat_max}/{lon_min}/{lon_max}`
**Purpose**: Sulfur dioxide satellite observations  
**Path Params**: Geographic bounds  
**Response**: Filtered SO₂ measurements

#### GET `/tempo/get_data_O3/{lat_min}/{lat_max}/{lon_min}/{lon_max}`
**Purpose**: Ozone satellite observations  
**Path Params**: Geographic bounds  
**Response**: Filtered O₃ measurements

#### GET `/tempo/get_data_HCHO/{lat_min}/{lat_max}/{lon_min}/{lon_max}`
**Purpose**: Formaldehyde satellite observations  
**Path Params**: Geographic bounds  
**Response**: Filtered HCHO measurements

#### GET `/tempo/get_data_AER/{lat_min}/{lat_max}/{lon_min}/{lon_max}`
**Purpose**: UV Aerosol Index satellite observations  
**Path Params**: Geographic bounds  
**Response**: Filtered aerosol measurements

**Data Processing Flow**:
1. Read pre-processed JSON file
2. Parse JSON array
3. Filter by latitude/longitude bounds
4. Return matched data points

**Scheduled Updates**:
- Frequency: Every 30 minutes
- Scheduler: APScheduler AsyncIOScheduler
- Processors: 
  - `tempoNacho.main()` - O₃, SO₂, AER
  - `tempoNachoHCHO.main()` - HCHO
  - `tempoNachoNO2.main()` - NO₂

---

### 4.6 TEMPO Data Processors

#### 4.6.1 `src/tempoNacho.py` (O₃, SO₂, AER)

**Purpose**: Download and process NASA TEMPO data for ozone, sulfur dioxide, and aerosols

**Processing Pipeline**:

1. **Authentication**
   ```python
   earthaccess.login(strategy="environment")
   ```
   Uses `EARTHDATA_TOKEN` from environment

2. **Data Search**
   ```python
   earthaccess.search_data(
       short_name="TEMPO_O3TOT_L2",  # or SO2, AER
       temporal=(date_range_start, date_range_end)
   )
   ```

3. **Data Download**
   - Downloads NetCDF4 files from NASA servers
   - Filters by temporal coverage

4. **NetCDF Processing**
   ```python
   ds = xr.open_dataset(file, engine='h5netcdf')
   lat = ds['latitude'].values
   lon = ds['longitude'].values
   values = ds['<parameter>_column'].values
   ```

5. **Data Transformation**
   - Extract lat, lon, value triplets
   - Filter valid data (non-NaN)
   - Convert to JSON format

6. **Output Generation**
   ```json
   [
     {"lat": 37.5, "lon": -108.3, "value": 45.2},
     {"lat": 38.1, "lon": -107.8, "value": 42.7},
     ...
   ]
   ```

7. **File Storage**
   - `o3_heatmap.json`
   - `so2_heatmap.json`
   - `aer_heatmap.json`

**Performance Features**:
- Progress tracking with ETA
- Concurrent processing with ProcessPoolExecutor
- Dask for lazy evaluation
- Memory-efficient streaming

---

#### 4.6.2 `src/tempoNachoNO2.py`

**Purpose**: Process TEMPO NO₂ tropospheric column data

**Differences from tempoNacho.py**:
- Short name: `TEMPO_NO2_L2`
- Variable: `nitrogen_dioxide_tropospheric_vertical_column`
- Output: `no2_heatmap.json`

**Similar pipeline**: Authentication → Search → Download → Process → Export

---

#### 4.6.3 `src/tempoNachoHCHO.py`

**Purpose**: Process TEMPO formaldehyde vertical column data

**Differences**:
- Short name: `TEMPO_HCHO_L2`
- Variable: `formaldehyde_vertical_column`
- Output: `hcho_heatmap.json`

---

## 5. Data Sources

### 5.1 OpenAQ API v3

**Provider**: OpenAQ  
**Website**: https://openaq.org/  
**Documentation**: https://docs.openaq.org/  

**Description**: 
OpenAQ aggregates air quality data from government monitoring networks, research institutions, and citizen science projects worldwide.

**Coverage**:
- 10,000+ monitoring locations globally
- 2,000+ locations in the United States
- Real-time and historical data

**Parameters Monitored**:
| ID | Parameter | Full Name | Units | Description |
|----|-----------|-----------|-------|-------------|
| 1 | PM10 | Particulate Matter 10µm | µg/m³ | Coarse particles |
| 2 | PM2.5 | Particulate Matter 2.5µm | µg/m³ | Fine particles |
| 7 | NO₂ | Nitrogen Dioxide | ppm | Traffic/combustion |
| 8 | CO | Carbon Monoxide | ppm | Incomplete combustion |
| 9 | SO₂ | Sulfur Dioxide | ppm | Industrial emissions |
| 10 | O₃ | Ozone | ppm | Secondary pollutant |

**API Characteristics**:
- RESTful JSON API
- Rate limiting: Varies by plan
- Authentication: API key via header (`X-API-Key`)
- Base URL: `https://api.openaq.org/v3`

**Key Endpoints Used**:
- `/v3/locations` - Location search
- `/v3/locations/{id}` - Location details
- `/v3/locations/{id}/latest` - Latest measurements
- `/v3/sensors` - Sensor listings

---

### 5.2 NASA TEMPO

**Mission**: Tropospheric Emissions: Monitoring of Pollution  
**Website**: https://tempo.si.edu/  
**Data Portal**: https://earthdata.nasa.gov/  

**Description**:
TEMPO is the first space-based instrument to monitor air quality over North America on an hourly basis throughout the day.

**Mission Characteristics**:
- Launch: 2023
- Orbit: Geostationary (fixed above North America)
- Coverage: CONUS, Mexico, Caribbean
- Temporal Resolution: Hourly (daylight hours)
- Spatial Resolution: 2-8 km at nadir

**Parameters Observed**:
| Parameter | Full Name | Product Code | Variable Name |
|-----------|-----------|--------------|---------------|
| O₃ | Ozone Tropospheric Column | TEMPO_O3TOT_L2 | ozone_column |
| SO₂ | Sulfur Dioxide Index | TEMPO_SO2_L2 | sulfur_dioxide_column |
| NO₂ | Nitrogen Dioxide Column | TEMPO_NO2_L2 | nitrogen_dioxide_tropospheric_vertical_column |
| HCHO | Formaldehyde Column | TEMPO_HCHO_L2 | formaldehyde_vertical_column |
| AER | UV Aerosol Index | TEMPO_AER_L2 | uv_aerosol_index |

**Data Format**:
- NetCDF4/HDF5
- Multi-dimensional arrays (latitude, longitude, time)
- Quality flags and uncertainty estimates

**Access Requirements**:
- NASA Earthdata account
- Authentication token
- earthaccess library for Python

---

## 6. API Reference

### 6.1 Base URL

```
Production: https://your-domain.com
Development: http://localhost:8000
```

### 6.2 Authentication

**OpenAQ**: Configured server-side via `OPENAQ_API_KEY` environment variable  
**NASA TEMPO**: Configured server-side via `EARTHDATA_TOKEN` environment variable  
**Client**: No authentication required for public endpoints

### 6.3 Response Format

All endpoints return JSON with the following general structure:

#### Success Response
```json
{
  "meta": {
    "found": 1234,
    "page": 1,
    "limit": 100
  },
  "results": [...]
}
```

#### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### 6.4 HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | External API unavailable |

### 6.5 Rate Limiting

**Current Implementation**: None (relies on OpenAQ rate limits)

**Recommendations for Production**:
- Implement Redis-based rate limiting
- Set limits: 100 requests/minute per IP
- Add caching layer for frequent queries

### 6.6 CORS Configuration

**Allowed Origins** (Development):
```
http://localhost:5173
http://localhost:5174
http://localhost:3000
http://127.0.0.1:5173
http://127.0.0.1:5174
http://127.0.0.1:3000
*  (wildcard for development)
```

**Production Recommendation**: Restrict to specific frontend domains

### 6.7 Interactive Documentation

**Swagger UI**: `http://localhost:8000/docs`  
**ReDoc**: `http://localhost:8000/redoc`  

Features:
- Automatic from FastAPI/OpenAPI
- Interactive request testing
- Schema exploration
- Code generation

---

## 7. Data Models

### 7.1 Geographic Coordinates

```json
{
  "latitude": 39.7392,
  "longitude": -104.9903
}
```

### 7.2 Location Object

```json
{
  "id": 2178,
  "name": "Denver - Downtown",
  "locality": "Denver, Colorado",
  "timezone": "America/Denver",
  "country": {
    "id": 1,
    "name": "United States of America",
    "code": "US"
  },
  "coordinates": {
    "latitude": 39.7392,
    "longitude": -104.9903
  },
  "is_mobile": false,
  "is_monitor": true
}
```

### 7.3 Measurement Object

```json
{
  "parameter": {
    "id": 2,
    "name": "pm25",
    "units": "µg/m³",
    "display_name": "PM2.5"
  },
  "value": 12.5,
  "datetime": {
    "utc": "2025-10-05T14:00:00Z",
    "local": "2025-10-05T08:00:00-06:00"
  },
  "coordinates": {
    "latitude": 39.7392,
    "longitude": -104.9903
  },
  "location_id": 2178,
  "sensors_id": 12345
}
```

### 7.4 Location with Measurements

```json
{
  "location_id": 2178,
  "name": "Denver - Downtown",
  "locality": "Denver, Colorado",
  "coordinates": {
    "latitude": 39.7392,
    "longitude": -104.9903
  },
  "country": "United States of America",
  "measurements": {
    "pm10": {
      "parameter_id": 1,
      "parameter_name": "PM10",
      "latest_value": 15.3,
      "unit": "µg/m³",
      "datetime": {
        "utc": "2025-10-05T14:00:00Z",
        "local": "2025-10-05T08:00:00-06:00"
      },
      "available": true
    },
    "pm25": {
      "parameter_id": 2,
      "parameter_name": "PM25",
      "latest_value": 8.7,
      "unit": "µg/m³",
      "datetime": {...},
      "available": true
    }
  },
  "measurements_summary": {
    "total_parameters": 6,
    "available_parameters": 4,
    "missing_parameters": 2
  }
}
```

### 7.5 TEMPO Satellite Data Point

```json
{
  "lat": 37.5,
  "lon": -108.3,
  "value": 45.2
}
```

### 7.6 Performance Metrics

```json
{
  "performance": {
    "total_time_seconds": 18.42,
    "locations_per_second": 2.71,
    "average_time_per_location_ms": 368.4,
    "successful_locations": 50,
    "failed_locations": 0
  },
  "parameter_coverage": {
    "pm10": {
      "available_at": 42,
      "percentage": "84.0%"
    },
    "pm25": {
      "available_at": 48,
      "percentage": "96.0%"
    }
  }
}
```

---

## 8. Configuration

### 8.1 Environment Variables

**File**: `.env` (root directory)

```env
# OpenAQ API
OPENAQ_API_KEY=your_openaq_api_key_here

# NASA Earthdata
EARTHDATA_TOKEN=your_earthdata_token_here

# Application Settings
LOG_LEVEL=INFO
EXTRACTION_INTERVAL_MINUTES=30
DATA_RETENTION_DAYS=7

# Server Configuration (Optional)
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

### 8.2 Variable Descriptions

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAQ_API_KEY` | Yes | - | API key from OpenAQ platform |
| `EARTHDATA_TOKEN` | Yes | - | Authentication token from NASA Earthdata |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `EXTRACTION_INTERVAL_MINUTES` | No | 30 | Frequency of TEMPO data updates |
| `DATA_RETENTION_DAYS` | No | 7 | Number of days to retain cached data |
| `HOST` | No | 0.0.0.0 | Server bind address |
| `PORT` | No | 8000 | Server port |
| `WORKERS` | No | 4 | Number of Uvicorn workers |

### 8.3 Obtaining API Keys

#### OpenAQ API Key
1. Visit https://openaq.org/
2. Create an account
3. Navigate to API section
4. Generate new API key
5. Copy to `.env` file

#### NASA Earthdata Token
1. Visit https://urs.earthdata.nasa.gov/
2. Register for an Earthdata account
3. Navigate to "Generate Token"
4. Create new token with appropriate permissions
5. Copy to `.env` file

### 8.4 Project Dependencies

**File**: `pyproject.toml`

```toml
[project]
name = "backend"
version = "0.1.0"
requires-python = ">=3.13"

dependencies = [
    "fastapi>=0.118.0",
    "uvicorn>=0.37.0",
    "httpx>=0.28.1",
    "python-dotenv>=1.0.0",
    "xarray>=2025.9.1",
    "netcdf4>=1.7.2",
    "earthaccess>=0.15.1",
    "apscheduler>=3.11.0",
    "matplotlib>=3.10.6",
    "cartopy>=0.25.0",
    "sqlalchemy>=2.0.43",
    "requests>=2.32.5"
]
```

---

## 9. Deployment

### 9.1 Development Setup

```bash
# Clone repository
git clone <repository-url>
cd hackathon_backend

# Install UV package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run development server
uv run uvicorn src.main:app --reload --port 8000
```

### 9.2 Production Deployment

#### Option 1: Direct Uvicorn

```bash
# Install production dependencies
uv sync --no-dev

# Run with multiple workers
uv run uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

#### Option 2: Docker

**Dockerfile**:
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy application
COPY src/ ./src/
COPY .env ./

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Docker Compose**:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAQ_API_KEY=${OPENAQ_API_KEY}
      - EARTHDATA_TOKEN=${EARTHDATA_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

#### Option 3: Cloud Platforms

**AWS Elastic Beanstalk**:
```bash
eb init -p python-3.13 air-quality-api
eb create production-env
eb deploy
```

**Google Cloud Run**:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/air-quality-api
gcloud run deploy --image gcr.io/PROJECT_ID/air-quality-api --platform managed
```

**Azure App Service**:
```bash
az webapp up --name air-quality-api --runtime "PYTHON:3.13"
```

### 9.3 Monitoring & Logging

**Recommended Tools**:
- **Application Monitoring**: Sentry, New Relic, Datadog
- **Log Aggregation**: ELK Stack, CloudWatch, Google Cloud Logging
- **Metrics**: Prometheus + Grafana
- **Uptime Monitoring**: UptimeRobot, Pingdom

**Logging Configuration**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 9.4 Security Best Practices

1. **Environment Variables**: Never commit `.env` to version control
2. **HTTPS**: Use TLS/SSL certificates in production
3. **CORS**: Restrict origins to frontend domains only
4. **Rate Limiting**: Implement request throttling
5. **Input Validation**: Leverage Pydantic schemas
6. **API Keys**: Rotate periodically
7. **Dependencies**: Regular security updates via `uv update`

---

## 10. Performance Considerations

### 10.1 Current Optimizations

#### Async I/O
- All HTTP requests use `async`/`await`
- Non-blocking operations for high concurrency
- HTTPX async client for parallel requests

#### Concurrent Processing
- `asyncio.gather()` for parallel API calls
- Semaphore-based concurrency control (max 10 concurrent)
- Distributed geographic sampling reduces redundant data

#### Data Processing
- Lazy evaluation with xarray/Dask
- Streaming NetCDF processing
- In-memory JSON caching for TEMPO data

#### Request Optimization
- Configurable limits and timeouts
- Early termination on errors
- Optimized query parameters

### 10.2 Performance Benchmarks

**Hardware**: Standard cloud VM (2 vCPU, 4GB RAM)

| Operation | Locations | Time | Rate |
|-----------|-----------|------|------|
| Single location lookup | 1 | ~0.3s | 3.3 loc/s |
| Small area query | 20 | ~5-8s | 2.5-4 loc/s |
| Medium area query | 50 | ~15-20s | 2.5-3.3 loc/s |
| Large area query | 100 | ~30-40s | 2.5-3.3 loc/s |

**TEMPO Data Processing**:
- NetCDF download: ~10-30s per file
- Processing: ~5-15s per file
- Total cycle (3 processors): ~2-5 minutes

### 10.3 Bottlenecks

1. **OpenAQ API Rate Limits**: External dependency bottleneck
2. **Network Latency**: HTTP round-trip times
3. **NASA Data Download**: Large NetCDF4 files
4. **Memory Usage**: xarray dataset loading

### 10.4 Scalability Recommendations

#### Short-term
- Implement Redis caching for frequent queries
- Add request deduplication
- Optimize sampling algorithms

#### Medium-term
- Add database layer for persistent caching
- Implement CDN for static TEMPO data
- Use message queue for background processing

#### Long-term
- Microservices architecture
- Kubernetes orchestration
- Distributed caching (Redis Cluster)
- Database sharding by geography

### 10.5 Caching Strategy

**Recommended Implementation**:
```python
from functools import lru_cache
import redis

# In-memory caching
@lru_cache(maxsize=1000)
def get_cached_location(location_id):
    return fetch_location(location_id)

# Redis caching
redis_client = redis.Redis(host='localhost', port=6379)

def get_with_cache(key, fetch_func, ttl=300):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    data = fetch_func()
    redis_client.setex(key, ttl, json.dumps(data))
    return data
```

**Cache Keys**:
- Location data: `loc:{location_id}` (TTL: 1 hour)
- Measurements: `meas:{location_id}:{parameter}` (TTL: 5 minutes)
- TEMPO data: `tempo:{parameter}:{date}` (TTL: 30 minutes)

---

## 11. Error Handling

### 11.1 Error Types

#### 400 Bad Request
**Causes**:
- Invalid parameter IDs
- Malformed bounding box
- Out-of-range limits

**Example Response**:
```json
{
  "detail": "Invalid parameter ID. Must be one of: [1, 2, 7, 8, 9, 10]"
}
```

#### 404 Not Found
**Causes**:
- Non-existent location ID
- No data for specified filters

**Example Response**:
```json
{
  "detail": "Location not found"
}
```

#### 500 Internal Server Error
**Causes**:
- OpenAQ API timeout
- NASA Earthdata connection failure
- Data processing errors

**Example Response**:
```json
{
  "detail": "Error fetching data: Connection timeout"
}
```

#### 503 Service Unavailable
**Causes**:
- OpenAQ API maintenance
- NASA servers down
- Rate limit exceeded

### 11.2 Client Error Handling

**Recommended Pattern**:
```python
import httpx

async def fetch_air_quality_data():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/air-quality/latest",
                params={"parameter": "pm25", "limit": 100},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException:
        print("Request timed out")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code}")
        print(f"Detail: {e.response.json().get('detail')}")
    except httpx.RequestError as e:
        print(f"Request error: {e}")
```

### 11.3 Logging

**Current Implementation**:
```python
import logging

logger = logging.getLogger(__name__)

try:
    data = await fetch_data()
except Exception as e:
    logger.error(f"Error fetching data: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

**Recommended Production Logging**:
```python
import structlog

logger = structlog.get_logger()

logger.info("api_request", 
            endpoint="/air-quality/latest",
            parameters={"parameter": "pm25"},
            user_ip="192.168.1.1")

logger.error("api_error",
             endpoint="/air-quality/latest",
             error_type="OpenAQTimeout",
             error_message=str(e))
```

### 11.4 Retry Logic

**Recommended Pattern**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()
```

---

## 12. Future Enhancements

### 12.1 Short-term (1-3 months)

1. **Caching Layer**
   - Redis integration
   - TTL-based invalidation
   - Cache warming strategies

2. **Rate Limiting**
   - Per-IP request limits
   - API key-based quotas
   - Fair usage policies

3. **Enhanced Error Responses**
   - Structured error codes
   - Detailed error messages
   - Troubleshooting hints

4. **Monitoring Dashboard**
   - Real-time API metrics
   - Error rate tracking
   - Performance graphs

5. **Automated Testing**
   - Unit tests (pytest)
   - Integration tests
   - End-to-end tests

### 12.2 Medium-term (3-6 months)

1. **Database Persistence**
   - PostgreSQL + PostGIS
   - Historical data storage
   - Time-series optimization

2. **Advanced Querying**
   - Time-range queries
   - Trend analysis
   - Statistical aggregations

3. **Data Visualization**
   - Heatmap generation
   - Chart API endpoints
   - GeoJSON export

4. **Webhooks & Notifications**
   - Air quality alerts
   - Threshold notifications
   - Email/SMS integration

5. **API Versioning**
   - `/v2/` endpoints
   - Deprecation notices
   - Migration guides

### 12.3 Long-term (6-12 months)

1. **Machine Learning Integration**
   - Air quality predictions
   - Anomaly detection
   - Pattern recognition

2. **Additional Data Sources**
   - Purple Air citizen sensors
   - NOAA weather data
   - Traffic data correlation

3. **GraphQL API**
   - Flexible queries
   - Reduced over-fetching
   - Real-time subscriptions

4. **Mobile SDK**
   - iOS/Android libraries
   - Offline caching
   - Push notifications

5. **White-label Solutions**
   - Customizable branding
   - Multi-tenant architecture
   - SaaS deployment

### 12.4 Research & Development

1. **AI-powered Air Quality Forecasting**
   - LSTM/Transformer models
   - Multi-day predictions
   - Confidence intervals

2. **Satellite-Ground Data Fusion**
   - Calibration algorithms
   - Data assimilation
   - Hybrid models

3. **Real-time Heatmap Generation**
   - Interpolation algorithms (IDW, Kriging)
   - Dynamic resolution
   - WebGL rendering

4. **Citizen Science Integration**
   - Crowdsourced data validation
   - Low-cost sensor networks
   - Community engagement

---

## 13. Appendix

### 13.1 Glossary

| Term | Definition |
|------|------------|
| **AQI** | Air Quality Index - standardized indicator of air quality |
| **Bbox** | Bounding box - geographic rectangle defined by min/max lat/lon |
| **CONUS** | Contiguous United States |
| **EPA** | Environmental Protection Agency |
| **Geostationary** | Satellite orbit that appears fixed over one point on Earth |
| **HDF5** | Hierarchical Data Format - scientific data file format |
| **L2 Product** | Level 2 data product - geolocated and calibrated measurements |
| **NetCDF** | Network Common Data Form - array-oriented data format |
| **TEMPO** | Tropospheric Emissions: Monitoring of Pollution |
| **Troposphere** | Lowest layer of Earth's atmosphere (0-12 km altitude) |
| **UTC** | Coordinated Universal Time |

### 13.2 Parameter Reference

#### Ground-Based (OpenAQ)
- **PM10**: Particles ≤10 micrometers (inhalable particles)
- **PM2.5**: Particles ≤2.5 micrometers (fine particles, lung penetration)
- **NO₂**: Nitrogen dioxide (traffic, combustion, respiratory irritant)
- **CO**: Carbon monoxide (incomplete combustion, toxic gas)
- **SO₂**: Sulfur dioxide (industrial emissions, acid rain precursor)
- **O₃**: Ozone (secondary pollutant, respiratory issues)

#### Satellite (TEMPO)
- **O₃ Column**: Total ozone in atmospheric column
- **SO₂ Index**: Measure of sulfur dioxide concentration
- **NO₂ Column**: Tropospheric nitrogen dioxide vertical column
- **HCHO**: Formaldehyde vertical column (VOC indicator)
- **Aerosol Index**: UV light absorption by particles

### 13.3 US State Bounding Boxes

| State | Bbox (min_lon,min_lat,max_lon,max_lat) |
|-------|----------------------------------------|
| Colorado | -109.05,37,-102.04,41 |
| California | -124.41,32.53,-114.13,42 |
| New York | -79.76,40.50,-71.86,45.01 |
| Texas | -106.65,25.84,-93.51,36.50 |
| Washington | -124.85,45.54,-116.92,49.00 |

### 13.4 HTTP Status Code Reference

| Code | Name | Meaning | Action |
|------|------|---------|--------|
| 200 | OK | Success | Process response |
| 400 | Bad Request | Invalid input | Check parameters |
| 401 | Unauthorized | Invalid credentials | Check API key |
| 403 | Forbidden | Access denied | Check permissions |
| 404 | Not Found | Resource missing | Verify ID/path |
| 429 | Too Many Requests | Rate limited | Implement backoff |
| 500 | Internal Server Error | Server issue | Retry with exponential backoff |
| 502 | Bad Gateway | Upstream failure | Check external APIs |
| 503 | Service Unavailable | Maintenance | Wait and retry |
| 504 | Gateway Timeout | Upstream timeout | Increase timeout |

### 13.5 Useful Resources

**Documentation**:
- FastAPI: https://fastapi.tiangolo.com/
- OpenAQ API: https://docs.openaq.org/
- NASA TEMPO: https://tempo.si.edu/data.html
- xarray: https://docs.xarray.dev/

**Community**:
- OpenAQ Community: https://openaq.org/community
- NASA Earth Science: https://earthdata.nasa.gov/learn

**Tools**:
- API Testing: Postman, Insomnia, HTTPie
- Data Visualization: Matplotlib, Plotly, Folium
- GIS Tools: QGIS, ArcGIS, Leaflet

---

### Data Attribution

**OpenAQ**:
Data provided by OpenAQ (openaq.org). OpenAQ aggregates data from various governmental and research sources worldwide. Please review and comply with individual data provider licenses.

**NASA TEMPO**:
TEMPO data courtesy of NASA Earth Science Data and Information System (ESDIS). Data is freely available for research and educational purposes.

### Acknowledgments
- OpenAQ team for air quality data access
- NASA TEMPO mission team
- FastAPI framework developers
- Python data science community

---

**Document Version**: 1.0.0  
**Last Updated**: October 5, 2025  
**Maintained By**: Air Computing
