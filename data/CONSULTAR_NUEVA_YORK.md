# 🗽 CÓMO CONSULTAR DATOS DE NUEVA YORK

## 📊 **RESULTADOS ENCONTRADOS**

Según los datos más recientes, **Nueva York tiene:**
- **5 mediciones** de calidad del aire
- **OZONO MÁS ALTO** de todas las ciudades: **176.78 ppb** (AQI: 275, "Very Unhealthy")
- Contaminantes detectados: CO, O3, PM10, PM25, SO2

## 🔍 **MÉTODOS PARA CONSULTAR NUEVA YORK**

### 1. **Consulta Python Simple**
```bash
cd /home/magma/Desktop/hackathon_backend

python3 -c "
import json
import glob

# Buscar en todos los archivos
files = glob.glob('data/air_quality/air_quality_mock_*.json')

for file_path in sorted(files, reverse=True):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    ny_data = [m for m in data['measurements'] if m['city'].lower() == 'new york']
    
    if ny_data:
        print(f'🗽 NUEVA YORK ({file_path.split(\"/\")[-1]}):')
        for m in ny_data:
            print(f'  {m[\"parameter\"].upper()}: {m[\"value\"]} {m[\"unit\"]} (AQI: {m.get(\"aqi\", \"N/A\")})')
        break
"
```

### 2. **Filtro por Ciudad en JSON**
```bash
# Buscar "New York" en todos los archivos
grep -l "New York" data/air_quality/air_quality_mock_*.json

# Ver el contenido filtrado
python3 -c "
import json
import glob

for file in glob.glob('data/air_quality/air_quality_mock_*.json'):
    with open(file) as f:
        data = json.load(f)
    ny_measurements = [m for m in data['measurements'] if 'new york' in m['city'].lower()]
    if ny_measurements:
        print(f'Archivo: {file}')
        print(f'Mediciones NYC: {len(ny_measurements)}')
        for m in ny_measurements:
            print(f'  - {m[\"parameter\"].upper()}: {m[\"value\"]} {m[\"unit\"]}')
        print()
"
```

### 3. **API REST (con servidor activo)**
```bash
# Iniciar el servidor
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload &

# Consultar por ciudad
curl "http://localhost:8001/air-quality/by-location?city=New York"

# Consultar estado de Nueva York
curl "http://localhost:8001/air-quality/by-location?state=NY"

# Ver con formato JSON legible
curl -s "http://localhost:8001/air-quality/by-location?city=New York" | python3 -m json.tool
```

### 4. **Búsqueda Avanzada con jq**
```bash
# Instalar jq si no lo tienes
sudo apt-get install jq

# Buscar Nueva York en todos los archivos
for file in data/air_quality/air_quality_mock_*.json; do
    echo "=== $file ==="
    jq '.measurements[] | select(.city == "New York")' "$file"
done

# Obtener solo los valores de contaminantes
jq '.measurements[] | select(.city == "New York") | {parameter, value, unit, aqi, category}' data/air_quality/air_quality_mock_*.json
```

### 5. **Script Personalizado para NYC**
```python
#!/usr/bin/env python3
import json
import glob
from datetime import datetime

def consultar_nueva_york():
    """Consulta específica para datos de Nueva York"""
    
    files = glob.glob('data/air_quality/air_quality_mock_*.json')
    
    print("🗽 BÚSQUEDA DE DATOS DE NUEVA YORK")
    print("=" * 50)
    
    total_mediciones_ny = 0
    archivos_con_ny = 0
    
    for file_path in sorted(files, reverse=True):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            ny_measurements = [m for m in data['measurements'] 
                              if m['city'].lower() == 'new york']
            
            if ny_measurements:
                archivos_con_ny += 1
                total_mediciones_ny += len(ny_measurements)
                
                print(f"\n📁 {file_path.split('/')[-1]}")
                print(f"🕐 {data['extraction_time']}")
                print(f"📊 {len(ny_measurements)} mediciones de NYC")
                
                # Mostrar cada contaminante
                for m in ny_measurements:
                    aqi = m.get('aqi', 'N/A')
                    emoji = get_aqi_emoji(aqi)
                    print(f"  {emoji} {m['parameter'].upper()}: {m['value']} {m['unit']} (AQI: {aqi})")
                
                # Solo mostrar el archivo más reciente con datos
                break
        
        except Exception as e:
            continue
    
    if total_mediciones_ny == 0:
        print("❌ No se encontraron datos de Nueva York")
        print("💡 Intenta ejecutar el servidor para generar nuevos datos")
    else:
        print(f"\n📈 RESUMEN:")
        print(f"   Archivos con datos de NYC: {archivos_con_ny}")
        print(f"   Total mediciones encontradas: {total_mediciones_ny}")

def get_aqi_emoji(aqi):
    """Retorna emoji según el nivel de AQI"""
    if aqi == 'N/A' or aqi is None:
        return '⚪'
    elif aqi <= 50:
        return '🟢'
    elif aqi <= 100:
        return '🟡'
    elif aqi <= 150:
        return '🟠'
    elif aqi <= 200:
        return '🔴'
    else:
        return '🟣'

if __name__ == "__main__":
    consultar_nueva_york()
```

### 6. **Consulta por Estado (NY)**
```bash
python3 -c "
import json
import glob

files = glob.glob('data/air_quality/air_quality_mock_*.json')

print('🗽 TODOS LOS DATOS DEL ESTADO DE NUEVA YORK')
print('=' * 50)

for file_path in sorted(files, reverse=True):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    ny_state_data = [m for m in data['measurements'] if m['state'] == 'NY']
    
    if ny_state_data:
        print(f'📁 {file_path.split(\"/\")[-1]}')
        print(f'📊 {len(ny_state_data)} mediciones en el estado de NY')
        
        ciudades = set(m['city'] for m in ny_state_data)
        for ciudad in ciudades:
            city_data = [m for m in ny_state_data if m['city'] == ciudad]
            print(f'  🏙️  {ciudad}: {len(city_data)} mediciones')
            for m in city_data:
                print(f'    - {m[\"parameter\"].upper()}: {m[\"value\"]} {m[\"unit\"]}')
        break
"
```

### 7. **Comparación NYC vs Otras Ciudades**
```bash
python3 -c "
import json
import glob
from collections import defaultdict

files = glob.glob('data/air_quality/air_quality_mock_*.json')
latest_file = max(files)

with open(latest_file, 'r') as f:
    data = json.load(f)

print('🏙️  NUEVA YORK vs OTRAS CIUDADES PRINCIPALES')
print('=' * 55)

# Agrupar por ciudad
cities = defaultdict(list)
for m in data['measurements']:
    cities[m['city']].append(m)

# Comparar NYC con otras ciudades principales
target_cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']

for city in target_cities:
    city_data = cities.get(city, [])
    if city_data:
        avg_aqi = sum(m.get('aqi', 0) for m in city_data if m.get('aqi')) / len([m for m in city_data if m.get('aqi')])
        print(f'{city}: {len(city_data)} mediciones, AQI promedio: {avg_aqi:.1f}')
        
        # Mostrar el contaminante más alto
        worst = max(city_data, key=lambda x: x.get('aqi', 0))
        print(f'  ⚠️  Peor: {worst[\"parameter\"].upper()} = {worst[\"value\"]} {worst[\"unit\"]} (AQI: {worst.get(\"aqi\", \"N/A\")})')
    else:
        print(f'{city}: Sin datos en este archivo')
    print()
"
```

## 🚨 **DATOS ACTUALES DE NUEVA YORK**

Según el análisis más reciente:

- **🟣 OZONO (O3)**: 176.78 ppb - AQI: 275 (**Very Unhealthy**)
- **🟢 CO**: 1 medición disponible
- **🟡 PM10**: 1 medición disponible  
- **🟠 PM25**: 1 medición disponible
- **🔴 SO2**: 1 medición disponible

**⚠️ ALERTA**: El nivel de ozono en NYC está en categoría "Very Unhealthy" (AQI > 200)

## 📝 **COMANDO RÁPIDO**

Para una consulta rápida de NYC, usa:

```bash
cd /home/magma/Desktop/hackathon_backend

python3 -c "
import json, glob
for f in sorted(glob.glob('data/air_quality/air_quality_mock_*.json'), reverse=True):
    data = json.load(open(f))
    ny = [m for m in data['measurements'] if m['city'].lower() == 'new york']
    if ny:
        print(f'🗽 NYC ({len(ny)} mediciones):')
        for m in ny: print(f'  {m[\"parameter\"].upper()}: {m[\"value\"]} {m[\"unit\"]} (AQI: {m.get(\"aqi\", \"N/A\")})')
        break
"
```