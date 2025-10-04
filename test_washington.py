"""
Script de prueba para el endpoint optimizado de Washington
"""
import httpx
import asyncio
import time

async def test_washington():
    base_url = "http://localhost:8000"
    
    tests = [
        {"name": "Rápido (20 ubicaciones)", "max_process": 20, "show_locations": True},
        {"name": "Medio (50 ubicaciones)", "max_process": 50, "show_locations": False},
        {"name": "Completo (100 ubicaciones)", "max_process": 100, "show_locations": False},
    ]
    
    print("🧪 Testing Washington State Air Quality API")
    print("=" * 70)
    
    for test in tests:
        print(f"\n📊 Test: {test['name']}")
        print("-" * 70)
        
        url = f"{base_url}/air-quality/test/washington"
        params = {
            "max_process": test["max_process"],
            "sampling": "distributed"
        }
        
        start = time.time()
        
        # AUMENTADO: Timeout de 120s a 180s para tests grandes
        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                print(f"⏳ Procesando... (esto puede tardar hasta {test['max_process'] // 2} segundos)")
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                elapsed = time.time() - start
                
                print(f"✅ Status: Success")
                print(f"⏱️  Tiempo total: {elapsed:.2f}s")
                print(f"📍 Ubicaciones procesadas: {data.get('locations_processed', 0)}")
                print(f"✅ Ubicaciones exitosas: {data.get('successful_locations', 0)}")
                print(f"❌ Ubicaciones con error: {data.get('failed_locations', 0)}")
                print(f"📊 Ubicaciones encontradas: {data.get('total_locations_found', 0)}")
                print(f"📈 Cobertura: {data.get('sampling_info', {}).get('percentage_covered', 'N/A')}")
                
                if 'performance' in data:
                    perf = data['performance']
                    print(f"⚡ Velocidad: {perf.get('locations_per_second', 0):.2f} ubicaciones/seg")
                    print(f"⏲️  Tiempo promedio por ubicación: {perf.get('average_time_per_location_ms', 0):.2f}ms")
                
                if 'parameter_coverage' in data:
                    print(f"\n🔬 Disponibilidad de parámetros:")
                    for param, stats in data['parameter_coverage'].items():
                        print(f"   • {param.upper():<6}: {stats['available_at']:>3} ubicaciones ({stats['percentage']})")
                
                # NUEVO: Mostrar ubicaciones para el test rápido
                if test.get('show_locations', False) and data.get('found'):
                    print(f"\n📍 Ubicaciones del Test Rápido:")
                    print("-" * 70)
                    locations = data.get('locations', [])
                    for i, loc in enumerate(locations, 1):
                        coords = loc.get('coordinates', {})
                        lon = coords.get('longitude', 'N/A')
                        lat = coords.get('latitude', 'N/A')
                        name = loc.get('name', 'Unknown')
                        locality = loc.get('locality', 'N/A')
                        
                        # Contar parámetros disponibles
                        measurements = loc.get('measurements', {})
                        available_params = sum(1 for m in measurements.values() if m.get('available', False))
                        
                        print(f"   {i:2d}. {name}")
                        print(f"       📍 Coordenadas: ({lat}, {lon})")
                        print(f"       📌 Localidad: {locality}")
                        print(f"       🔬 Parámetros disponibles: {available_params}/6")
                        
                        # Mostrar valores si están disponibles
                        if available_params > 0:
                            values = []
                            for param_name, measurement in measurements.items():
                                if measurement.get('available'):
                                    value = measurement.get('latest_value')
                                    unit = measurement.get('unit', '')
                                    if value is not None:
                                        values.append(f"{param_name.upper()}={value:.2f}{unit}")
                            if values:
                                print(f"       📊 Valores: {', '.join(values[:3])}")  # Mostrar primeros 3
                        print()
                
            except httpx.TimeoutException:
                elapsed = time.time() - start
                print(f"❌ Error: Timeout después de {elapsed:.2f}s")
                print(f"💡 Sugerencia: Reduce max_process o aumenta el timeout")
            except httpx.HTTPError as e:
                print(f"❌ Error HTTP: {str(e)}")
            except Exception as e:
                print(f"❌ Error inesperado: {str(e)}")
        
        print()
    
    print("=" * 70)
    print("✨ Tests completados!")

if __name__ == "__main__":
    asyncio.run(test_washington())