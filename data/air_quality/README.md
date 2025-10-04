# Configuración del sistema de monitoreo de calidad del aire

Este directorio contiene los datos extraídos de las APIs de calidad del aire.

## Estructura de archivos:

- `air_quality_openaq_YYYYMMDD_HHMMSS.json`: Datos de OpenAQ API
- `air_quality_airnow_YYYYMMDD_HHMMSS.json`: Datos de AirNow API

## Formato de datos:

```json
{
  "extraction_time": "2025-10-04T12:00:00Z",
  "source": "openaq|airnow",
  "count": 150,
  "measurements": [
    {
      "parameter": "o3|no2|pm25|pm10|so2|co|hcho",
      "value": 45.2,
      "unit": "µg/m³",
      "last_updated": "2025-10-04T11:30:00Z",
      "aqi": 42,
      "category": "Good",
      "coordinates": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "location_name": "New York",
      "city": "New York",
      "state": "NY",
      "country": "US",
      "source": "openaq",
      "site_id": "12345"
    }
  ]
}
```

## Limpieza automática:

Los archivos de más de 7 días se eliminan automáticamente a las 02:00 UTC diariamente.