# 📊 CÓMO REVISAR LOS DATOS DE CALIDAD DEL AIRE

## 📁 Organización de los Datos

### 🗂️ Estructura por Regiones

Los datos están organizados por **ciudades principales** de Estados Unidos, cubriendo todos los estados más importantes:

**Estados con mayor cobertura:**
- **Texas (TX)**: 24 mediciones - Houston, Dallas, Austin, San Antonio, Fort Worth
- **California (CA)**: 15 mediciones - Los Angeles, San Francisco, San Diego, San Jose
- **Illinois (IL)**: 9 mediciones - Chicago
- **Colorado (CO)**: 8 mediciones - Denver

**Otros estados incluidos:**
- New York (NY), Pennsylvania (PA), Florida (FL), Ohio (OH), Arizona (AZ), North Carolina (NC), Indiana (IN), Washington (WA), Washington DC

### 🔬 Contaminantes Monitoreados

**Tus contaminantes solicitados:**
- ✅ **Ozono (O3)** - ppb (partes por billón)
- ✅ **NO2 (Dióxido de Nitrógeno)** - ppb
- ✅ **PM2.5 (Partículas finas)** - µg/m³
- ❌ **HCHO** - No disponible en APIs públicas

**Contaminantes adicionales incluidos:**
- **PM10** (Partículas gruesas)
- **SO2** (Dióxido de azufre)
- **CO** (Monóxido de carbono)

## 🔍 Métodos para Revisar la Información

### 1. 📂 Archivos JSON Directos

```bash
# Ver archivos disponibles
ls -la data/air_quality/

# Leer el archivo más reciente (formato legible)
python3 -m json.tool data/air_quality/air_quality_mock_20251004_144503.json | head -50
```

### 2. 🖥️ API REST (cuando el servidor esté activo)

```bash
# Iniciar servidor
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload &

# Consultar estado del sistema
curl http://localhost:8001/air-quality/status

# Ver mediciones más recientes
curl http://localhost:8001/air-quality/measurements/latest

# Filtrar por ciudad
curl "http://localhost:8001/air-quality/by-location?city=New York"

# Filtrar por estado
curl "http://localhost:8001/air-quality/by-location?state=CA"

# Ver resumen estadístico
curl http://localhost:8001/air-quality/summary
```

### 3. 🐍 Scripts Python de Análisis

```python
# Análisis básico
import json
import glob

files = glob.glob('data/air_quality/air_quality_*.json')
latest_file = max(files)

with open(latest_file, 'r') as f:
    data = json.load(f)

print(f"Total mediciones: {data['count']}")
print(f"Hora: {data['extraction_time']}")

# Filtrar por contaminante específico
ozono = [m for m in data['measurements'] if m['parameter'] == 'o3']
print(f"Mediciones de ozono: {len(ozono)}")
```

### 4. 🌐 Documentación API Interactiva

Cuando el servidor esté ejecutándose, visita:
- http://localhost:8001/docs

## 📈 Información de Cada Medición

Cada medición incluye:

```json
{
  "parameter": "pm25",              // Tipo de contaminante
  "value": 24.42,                  // Valor medido
  "unit": "µg/m³",                 // Unidad de medida
  "last_updated": "2025-10-04...", // Timestamp
  "aqi": 76,                       // Índice de Calidad del Aire
  "category": "Moderate",          // Categoría (Good, Moderate, Unhealthy...)
  "coordinates": {
    "latitude": 29.418,
    "longitude": -98.410
  },
  "location_name": "Monitor 1",     // Nombre del monitor
  "city": "San Antonio",           // Ciudad
  "state": "TX",                   // Estado
  "country": "US",                 // País
  "source": "openaq",              // Fuente de datos
  "site_id": "openaq_4168"         // ID único del sitio
}
```

## ⏰ Automatización

- **Frecuencia**: Cada 30 minutos
- **Próxima extracción**: Automática
- **Almacenamiento**: Archivos JSON con timestamp
- **Limpieza**: Archivos antiguos se eliminan automáticamente

## 🚨 Categorías de Calidad del Aire (AQI)

- **Good (0-50)**: Verde - Aire limpio
- **Moderate (51-100)**: Amarillo - Aceptable
- **Unhealthy for Sensitive Groups (101-150)**: Naranja - Cuidado grupos sensibles
- **Unhealthy (151-200)**: Rojo - Dañino para todos
- **Very Unhealthy (201-300)**: Púrpura - Muy peligroso
- **Hazardous (301+)**: Granate - Emergencia sanitaria

## 🔧 Comandos Útiles

```bash
# Analizar archivo más reciente
python3 -c "
import json, glob
from collections import defaultdict

files = glob.glob('data/air_quality/air_quality_*.json')
data = json.load(open(max(files)))

# Estadísticas por contaminante
stats = defaultdict(list)
for m in data['measurements']:
    stats[m['parameter']].append(m['value'])

for param, values in stats.items():
    avg = sum(values) / len(values)
    print(f'{param.upper()}: {len(values)} mediciones, promedio: {avg:.2f}')
"

# Contar archivos de datos
ls data/air_quality/air_quality_*.json | wc -l

# Ver últimas 5 extracciones
ls -lt data/air_quality/air_quality_*.json | head -5
```

## 📊 Ejemplos de Consultas Específicas

```bash
# Ciudades con peor calidad de aire (ozono)
python3 -c "
import json, glob
data = json.load(open(max(glob.glob('data/air_quality/air_quality_*.json'))))
ozono = sorted([m for m in data['measurements'] if m['parameter'] == 'o3'], 
               key=lambda x: x['value'], reverse=True)[:5]
for m in ozono:
    print(f'{m[\"city\"]}, {m[\"state\"]}: {m[\"value\"]} ppb (AQI: {m[\"aqi\"]})')
"

# Estados con más mediciones
python3 -c "
import json, glob
from collections import Counter
data = json.load(open(max(glob.glob('data/air_quality/air_quality_*.json'))))
states = Counter(m['state'] for m in data['measurements'])
for state, count in states.most_common(5):
    print(f'{state}: {count} mediciones')
"
```