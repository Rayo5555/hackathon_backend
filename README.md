# US Air Quality Monitoring API

API para monitorear la contaminación del aire en Estados Unidos usando datos en tiempo real de OpenAQ.

## 🌍 Descripción

Este backend proporciona acceso a datos de calidad del aire de todas las estaciones de monitoreo en Estados Unidos. Rastrea los siguientes parámetros contaminantes:

- **PM10**: Particulate Matter 10 micrometers (Parámetro ID: 1)
- **PM2.5**: Particulate Matter 2.5 micrometers (Parámetro ID: 2)
- **NO₂**: Nitrogen Dioxide (ppm) (Parámetro ID: 7)
- **CO₂**: Carbon Dioxide (ppm) (Parámetro ID: 8)
- **SO₂**: Sulfur Dioxide (ppm) (Parámetro ID: 9)
- **O₃**: Ozone (ppm) (Parámetro ID: 10)

## 🚀 Configuración

### Requisitos

- Python 3.13+
- UV package manager

### Instalación

1. Clona el repositorio:
```bash
git clone <repository-url>
cd hackathon_backend
```

2. Instala las dependencias con UV:
```bash
uv sync
```

3. Configura las variables de entorno:
```bash
cp .env.example .env
```

4. Obtén tu API key de OpenAQ:
   - Visita [https://openaq.org/](https://openaq.org/)
   - Regístrate y obtén tu API key
   - Agrega tu API key al archivo `.env`:
```
OPENAQ_API_KEY=tu_api_key_aqui
```

### Ejecutar el servidor

```bash
uv run uvicorn src.main:app --reload --port 8000
```

La API estará disponible en `http://localhost:8000`

## 📚 Documentación de APIs

### 🆕 Nuevas APIs Principales

#### 1. Obtener mediciones por tipo de contaminación

**Endpoint:** `GET /air-quality/measurements/by-parameter/{parameter_id}`

Devuelve todas las mediciones de un tipo específico de contaminación en formato JSON.

**Parámetros:**
- `parameter_id` (path, requerido): ID del parámetro de contaminación
  - `1` = PM10
  - `2` = PM2.5
  - `7` = NO2
  - `8` = CO2
  - `9` = SO2
  - `10` = O3
- `bbox` (query, opcional): Coordenadas del área geográfica (formato: `min_lon,min_lat,max_lon,max_lat`)
  - Default: `-109.05,37,-102.04,41` (área de Colorado)
- `limit` (query, opcional): Número máximo de resultados (default: 1000, máximo: 10000)

**Ejemplo:**
```bash
# Obtener mediciones de PM2.5
curl "http://localhost:8000/air-quality/measurements/by-parameter/2?limit=100&bbox=-109.05,37,-102.04,41"

# Obtener mediciones de NO2
curl "http://localhost:8000/air-quality/measurements/by-parameter/7?limit=50"
```

**Respuesta:**
```json
{
  "meta": {
    "name": "openaq-api",
    "website": "/",
    "page": 1,
    "limit": 100,
    "found": 22435
  },
  "results": [
    {
      "datetime": {
        "utc": "2025-10-04T16:00:00Z",
        "local": "2025-10-05T01:00:00+09:00"
      },
      "value": 8.0,
      "coordinates": {
        "latitude": 35.21815,
        "longitude": 128.57425
      },
      "sensorsId": 8539597,
      "locationsId": 2622686
    }
    // ... más resultados
  ]
}
```

---

#### 2. Obtener todas las mediciones de una ubicación

**Endpoint:** `GET /air-quality/measurements/by-location/{location_id}`

Devuelve todas las mediciones de TODOS los parámetros (PM10, PM2.5, NO2, CO2, SO2, O3) para una ubicación específica en USA.

**Parámetros:**
- `location_id` (path, requerido): ID de la ubicación en OpenAQ

**Ejemplo:**
```bash
# Primero, obtener IDs de ubicaciones disponibles
curl "http://localhost:8000/air-quality/locations?limit=10"

# Luego, obtener todas las mediciones para una ubicación específica
curl "http://localhost:8000/air-quality/measurements/by-location/8127"
```

**Respuesta:**
```json
{
  "location_id": 8127,
  "location_info": {
    "results": [
      {
        "id": 8127,
        "name": "RO0169A",
        "locality": "București",
        "timezone": "Europe/Bucharest",
        "coordinates": {
          "latitude": 44.48139,
          "longitude": 26.13528
        }
      }
    ]
  },
  "parameters": {
    "pm10": {
      "meta": {...},
      "results": [...]
    },
    "pm25": {
      "meta": {...},
      "results": [...]
    },
    "no2": {
      "meta": {...},
      "results": [...]
    },
    "co2": {
      "meta": {...},
      "results": [...]
    },
    "so2": {
      "meta": {...},
      "results": [...]
    },
    "o3": {
      "meta": {...},
      "results": [...]
    }
  }
}
```

---

### Otras APIs Disponibles

#### 1. Obtener mediciones por parámetro
```
GET /air-quality/latest?parameter=pm25&state=California&limit=10
```

**Parámetros:**
- `parameter` (requerido): pm10, pm25, no2, co2, so2, o3
- `state` (opcional): Nombre del estado (ej: "California", "Texas")
- `city` (opcional): Nombre de la ciudad
- `limit` (opcional): Número máximo de resultados (1-10000, default: 1000)

**Ejemplo de respuesta:**
```json
{
  "meta": {
    "found": 150
  },
  "results": [
    {
      "location_id": 12345,
      "location": {
        "name": "San Francisco - Downtown",
        "locality": "San Francisco"
      },
      "parameter": {
        "id": 2,
        "name": "pm25",
        "units": "µg/m³"
      },
      "value": 12.5,
      "coordinates": {
        "latitude": 37.7749,
        "longitude": -122.4194
      }
    }
  ]
}
```

#### 2. Obtener todas las mediciones de todos los parámetros
```
GET /air-quality/latest/all?state=California&limit=100
```

Devuelve datos de los 6 parámetros simultáneamente.

#### 3. Obtener ubicaciones de estaciones de monitoreo
```
GET /air-quality/locations?state=Texas&limit=50
```

#### 4. Obtener resumen de calidad del aire
```
GET /air-quality/summary?state=New York&limit=100
```

Devuelve un resumen con el conteo de mediciones por parámetro.

#### 5. Listar estados disponibles
```
GET /air-quality/states
```

Devuelve la lista de todos los estados de EE.UU. con estaciones de monitoreo.

## 🧪 Pruebas

Ejecuta el script de prueba para verificar la integración con OpenAQ:

```bash
.venv/bin/python test_openaq.py
```

Este script probará:
- Mediciones de PM2.5
- Mediciones filtradas por estado (California)
- Datos de todos los parámetros
- Ubicaciones de estaciones

## 📊 Estructura del Proyecto

```
hackathon_backend/
├── src/
│   ├── main.py                 # Aplicación FastAPI principal
│   ├── openaq_client.py        # Cliente para OpenAQ API
│   ├── schemas.py              # Modelos Pydantic
│   └── routes/
│       ├── air_quality.py      # Endpoints de calidad del aire
│       └── users.py            # Endpoints de usuarios
├── test_openaq.py              # Script de pruebas
├── pyproject.toml              # Configuración del proyecto
├── .env                        # Variables de entorno (no commitear)
└── README.md                   # Esta documentación
```

## 🔑 Variables de Entorno

| Variable | Descripción | Requerido |
|----------|-------------|-----------|
| `OPENAQ_API_KEY` | API key de OpenAQ | Sí |
| `LOG_LEVEL` | Nivel de logging | No (default: INFO) |
| `EXTRACTION_INTERVAL_MINUTES` | Intervalo de extracción | No |
| `DATA_RETENTION_DAYS` | Días de retención de datos | No |

## 🌐 Fuente de Datos

Los datos provienen de [OpenAQ](https://openaq.org/), una organización sin fines de lucro que agrega datos de calidad del aire de fuentes gubernamentales y de investigación en todo el mundo.

- **API Documentation**: https://docs.openaq.org/
- **API Version**: v3
- **Cobertura**: Todas las estaciones de monitoreo en Estados Unidos

## 📝 Notas

- Los datos se actualizan en tiempo real según la disponibilidad de las estaciones de monitoreo
- Los parámetros y su disponibilidad varían según la ubicación
- Se recomienda implementar caché para reducir las llamadas al API en producción
- El límite de rate limiting depende de tu plan de OpenAQ

## 🛠️ Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **HTTPX**: Cliente HTTP asíncrono
- **Pydantic**: Validación de datos
- **UV**: Gestor de paquetes Python ultrarrápido
- **OpenAQ API v3**: Fuente de datos de calidad del aire

## 📄 Licencia

[Especificar licencia]

## 👥 Contribuidores

[Agregar contribuidores]
