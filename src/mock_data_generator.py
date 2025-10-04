import random
import asyncio
from datetime import datetime, timedelta
from typing import List
import json
from pathlib import Path

from src.schemas import (
    AirQualityMeasurement, Coordinates, PollutantType, 
    DataSource, AQICategory
)

class MockDataGenerator:
    """Generador de datos simulados de calidad del aire para pruebas"""
    
    def __init__(self):
        # Ciudades principales de Estados Unidos con coordenadas
        self.cities = [
            {"name": "New York", "state": "NY", "lat": 40.7128, "lon": -74.0060},
            {"name": "Los Angeles", "state": "CA", "lat": 34.0522, "lon": -118.2437},
            {"name": "Chicago", "state": "IL", "lat": 41.8781, "lon": -87.6298},
            {"name": "Houston", "state": "TX", "lat": 29.7604, "lon": -95.3698},
            {"name": "Phoenix", "state": "AZ", "lat": 33.4484, "lon": -112.0740},
            {"name": "Philadelphia", "state": "PA", "lat": 39.9526, "lon": -75.1652},
            {"name": "San Antonio", "state": "TX", "lat": 29.4241, "lon": -98.4936},
            {"name": "San Diego", "state": "CA", "lat": 32.7157, "lon": -117.1611},
            {"name": "Dallas", "state": "TX", "lat": 32.7767, "lon": -96.7970},
            {"name": "San Jose", "state": "CA", "lat": 37.3382, "lon": -121.8863},
            {"name": "Austin", "state": "TX", "lat": 30.2672, "lon": -97.7431},
            {"name": "Jacksonville", "state": "FL", "lat": 30.3322, "lon": -81.6557},
            {"name": "Fort Worth", "state": "TX", "lat": 32.7555, "lon": -97.3308},
            {"name": "Columbus", "state": "OH", "lat": 39.9612, "lon": -82.9988},
            {"name": "Charlotte", "state": "NC", "lat": 35.2271, "lon": -80.8431},
            {"name": "San Francisco", "state": "CA", "lat": 37.7749, "lon": -122.4194},
            {"name": "Indianapolis", "state": "IN", "lat": 39.7684, "lon": -86.1581},
            {"name": "Seattle", "state": "WA", "lat": 47.6062, "lon": -122.3321},
            {"name": "Denver", "state": "CO", "lat": 39.7392, "lon": -104.9903},
            {"name": "Washington", "state": "DC", "lat": 38.9072, "lon": -77.0369}
        ]
        
        # Rangos típicos para cada contaminante (valores realistas)
        self.pollutant_ranges = {
            PollutantType.OZONE: {"min": 10, "max": 180, "unit": "ppb"},
            PollutantType.NO2: {"min": 5, "max": 100, "unit": "ppb"},
            PollutantType.PM25: {"min": 2, "max": 55, "unit": "µg/m³"},
            PollutantType.PM10: {"min": 5, "max": 150, "unit": "µg/m³"},
            PollutantType.SO2: {"min": 1, "max": 75, "unit": "ppb"},
            PollutantType.CO: {"min": 0.1, "max": 15, "unit": "ppm"}
        }
    
    def _calculate_aqi(self, pollutant: PollutantType, concentration: float) -> tuple[int, AQICategory]:
        """Calcular AQI y categoría basado en la concentración"""
        # Breakpoints simplificados para AQI (valores aproximados)
        breakpoints = {
            PollutantType.OZONE: [0, 54, 70, 85, 105, 200],  # ppb
            PollutantType.NO2: [0, 53, 100, 360, 649, 1249],  # ppb
            PollutantType.PM25: [0, 12, 35.5, 55.5, 150.5, 250.5],  # µg/m³
            PollutantType.PM10: [0, 54, 154, 254, 354, 424],  # µg/m³
            PollutantType.SO2: [0, 35, 75, 185, 304, 604],  # ppb
            PollutantType.CO: [0, 4.4, 9.4, 12.4, 15.4, 30.4]  # ppm
        }
        
        aqi_levels = [0, 50, 100, 150, 200, 300]
        categories = [
            AQICategory.GOOD,
            AQICategory.MODERATE,
            AQICategory.UNHEALTHY_SENSITIVE,
            AQICategory.UNHEALTHY,
            AQICategory.VERY_UNHEALTHY,
            AQICategory.HAZARDOUS
        ]
        
        if pollutant not in breakpoints:
            return 50, AQICategory.GOOD
        
        bp = breakpoints[pollutant]
        
        # Encontrar el rango correcto
        for i in range(len(bp) - 1):
            if concentration <= bp[i + 1]:
                # Calcular AQI usando interpolación lineal
                c_lo, c_hi = bp[i], bp[i + 1]
                aqi_lo, aqi_hi = aqi_levels[i], aqi_levels[i + 1]
                
                aqi = int(((aqi_hi - aqi_lo) / (c_hi - c_lo)) * (concentration - c_lo) + aqi_lo)
                return aqi, categories[i]
        
        # Si excede todos los breakpoints
        return 300, AQICategory.HAZARDOUS
    
    def generate_measurements(self, count: int = 100) -> List[AirQualityMeasurement]:
        """Generar mediciones simuladas"""
        measurements = []
        
        for _ in range(count):
            # Seleccionar ciudad aleatoria
            city = random.choice(self.cities)
            
            # Seleccionar contaminante aleatorio
            pollutant = random.choice(list(PollutantType))
            
            if pollutant not in self.pollutant_ranges:
                continue
            
            # Generar concentración realista
            range_info = self.pollutant_ranges[pollutant]
            concentration = random.uniform(range_info["min"], range_info["max"])
            
            # Calcular AQI
            aqi, category = self._calculate_aqi(pollutant, concentration)
            
            # Generar timestamp reciente (últimas 24 horas)
            hours_ago = random.uniform(0, 24)
            timestamp = datetime.utcnow() - timedelta(hours=hours_ago)
            
            # Agregar algo de variación a las coordenadas para simular múltiples estaciones
            lat_offset = random.uniform(-0.1, 0.1)
            lon_offset = random.uniform(-0.1, 0.1)
            
            # Seleccionar fuente aleatoria
            source = random.choice([DataSource.OPENAQ, DataSource.AIRNOW])
            
            measurement = AirQualityMeasurement(
                parameter=pollutant,
                value=round(concentration, 2),
                unit=range_info["unit"],
                last_updated=timestamp,
                aqi=aqi,
                category=category,
                coordinates=Coordinates(
                    latitude=city["lat"] + lat_offset,
                    longitude=city["lon"] + lon_offset
                ),
                location_name=f"{city['name']} Monitor {random.randint(1, 5)}",
                city=city["name"],
                state=city["state"],
                country="US",
                source=source,
                site_id=f"{source.value}_{random.randint(1000, 9999)}"
            )
            
            measurements.append(measurement)
        
        return measurements
    
    async def save_mock_data(self):
        """Guardar datos simulados en archivos JSON"""
        data_dir = Path("data/air_quality")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar datos para diferentes fuentes
        openaq_measurements = []
        airnow_measurements = []
        
        all_measurements = self.generate_measurements(200)
        
        for measurement in all_measurements:
            if measurement.source == DataSource.OPENAQ:
                openaq_measurements.append(measurement)
            else:
                airnow_measurements.append(measurement)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Guardar datos de OpenAQ simulados
        if openaq_measurements:
            openaq_data = {
                "extraction_time": datetime.utcnow().isoformat(),
                "source": "openaq",
                "count": len(openaq_measurements),
                "measurements": [m.model_dump() for m in openaq_measurements],
                "note": "Datos simulados para demostración"
            }
            
            openaq_file = data_dir / f"air_quality_openaq_{timestamp}.json"
            with open(openaq_file, 'w', encoding='utf-8') as f:
                json.dump(openaq_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Guardados {len(openaq_measurements)} datos simulados de OpenAQ en {openaq_file.name}")
        
        # Guardar datos de AirNow simulados
        if airnow_measurements:
            airnow_data = {
                "extraction_time": datetime.utcnow().isoformat(),
                "source": "airnow",
                "count": len(airnow_measurements),
                "measurements": [m.model_dump() for m in airnow_measurements],
                "note": "Datos simulados para demostración"
            }
            
            airnow_file = data_dir / f"air_quality_airnow_{timestamp}.json"
            with open(airnow_file, 'w', encoding='utf-8') as f:
                json.dump(airnow_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Guardados {len(airnow_measurements)} datos simulados de AirNow en {airnow_file.name}")
        
        return {
            "openaq": openaq_measurements,
            "airnow": airnow_measurements
        }


# Función para generar datos desde línea de comandos
async def main():
    generator = MockDataGenerator()
    print("🔄 Generando datos simulados de calidad del aire...")
    
    data = await generator.save_mock_data()
    total = sum(len(measurements) for measurements in data.values())
    
    print(f"🎯 Total generado: {total} mediciones simuladas")
    print("📊 Distribución:")
    for source, measurements in data.items():
        if measurements:
            pollutants = {}
            for m in measurements:
                if m.parameter not in pollutants:
                    pollutants[m.parameter] = 0
                pollutants[m.parameter] += 1
            
            print(f"  {source}: {len(measurements)} mediciones")
            for pollutant, count in pollutants.items():
                print(f"    - {pollutant.value}: {count}")

if __name__ == "__main__":
    asyncio.run(main())