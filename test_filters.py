#!/usr/bin/env python3
"""
Script para probar los filtros de la API de calidad del aire
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_api_filters():
    """Probar todos los filtros de la API"""
    
    base_url = "http://localhost:8001/air-quality"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("🧪 PRUEBAS DE FILTROS DE API")
        print("=" * 50)
        
        try:
            # 1. Probar estado del sistema
            print("1️⃣ Probando estado del sistema...")
            response = await client.get(f"{base_url}/status")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Sistema funcionando: {data['data']['system_running']}")
                print(f"   📊 Archivos de datos: {data['data']['data_files_count']}")
            else:
                print(f"   ❌ Error en status: {response.status_code}")
            print()
            
            # 2. Probar opciones de filtros
            print("2️⃣ Probando opciones de filtros...")
            response = await client.get(f"{base_url}/filter-options")
            if response.status_code == 200:
                data = response.json()
                options = data['data']
                print(f"   ✅ Contaminantes disponibles: {len(options['pollutants'])}")
                print(f"   🗺️  Estados disponibles: {len(options['states'])}")
                print(f"   🏙️  Ciudades disponibles: {len(options['cities'])}")
                print(f"   📈 Total mediciones: {options['total_measurements']}")
                
                # Mostrar algunas opciones
                if options['pollutants']:
                    pollutants = [p['value'] for p in options['pollutants'][:3]]
                    print(f"   🔬 Ejemplos contaminantes: {pollutants}")
                
                if options['states']:
                    states = [s['value'] for s in options['states'][:5]]
                    print(f"   🗺️  Ejemplos estados: {states}")
                    
                # Guardar para usar en pruebas
                available_pollutants = [p['value'] for p in options['pollutants']]
                available_states = [s['value'] for s in options['states']]
                available_cities = [c['value'] for c in options['cities']]
                
            else:
                print(f"   ❌ Error en filter-options: {response.status_code}")
                return
            print()
            
            # 3. Probar filtro por contaminante
            print("3️⃣ Probando filtro por contaminante...")
            if available_pollutants:
                test_pollutant = available_pollutants[0]
                response = await client.get(
                    f"{base_url}/measurements/latest",
                    params={"pollutant": test_pollutant, "limit": 5}
                )
                if response.status_code == 200:
                    data = response.json()
                    count = len(data['data'])
                    print(f"   ✅ Filtro pollutant='{test_pollutant}': {count} resultados")
                    if count > 0:
                        example = data['data'][0]
                        print(f"   📊 Ejemplo: {example['parameter']} = {example['value']} {example['unit']}")
                else:
                    print(f"   ❌ Error en filtro pollutant: {response.status_code}")
            print()
            
            # 4. Probar filtro por estado
            print("4️⃣ Probando filtro por estado...")
            if available_states:
                test_state = available_states[0]
                response = await client.get(
                    f"{base_url}/measurements/latest",
                    params={"state": test_state, "limit": 5}
                )
                if response.status_code == 200:
                    data = response.json()
                    count = len(data['data'])
                    print(f"   ✅ Filtro state='{test_state}': {count} resultados")
                    if count > 0:
                        example = data['data'][0]
                        print(f"   📍 Ejemplo: {example['city']}, {example['state']}")
                else:
                    print(f"   ❌ Error en filtro state: {response.status_code}")
            print()
            
            # 5. Probar filtro combinado
            print("5️⃣ Probando filtros combinados...")
            if available_pollutants and available_states:
                test_pollutant = available_pollutants[0]
                test_state = available_states[0]
                response = await client.get(
                    f"{base_url}/measurements/latest",
                    params={
                        "pollutant": test_pollutant, 
                        "state": test_state, 
                        "limit": 10
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    count = len(data['data'])
                    print(f"   ✅ Filtros combinados ({test_pollutant} + {test_state}): {count} resultados")
                    message = data.get('message', '')
                    print(f"   💬 Mensaje: {message}")
                else:
                    print(f"   ❌ Error en filtros combinados: {response.status_code}")
            print()
            
            # 6. Probar filtro por ubicación
            print("6️⃣ Probando filtro por ciudad...")
            if available_cities:
                test_city = available_cities[0]
                response = await client.get(
                    f"{base_url}/by-location",
                    params={"city": test_city, "limit": 5}
                )
                if response.status_code == 200:
                    data = response.json()
                    count = len(data['data'])
                    print(f"   ✅ Filtro city='{test_city}': {count} resultados")
                    if count > 0:
                        example = data['data'][0]
                        print(f"   🏙️  Ejemplo: {example['city']}, {example['state']}")
                else:
                    print(f"   ❌ Error en filtro city: {response.status_code}")
            print()
            
            # 7. Probar Nueva York específicamente
            print("7️⃣ Probando Nueva York específicamente...")
            response = await client.get(
                f"{base_url}/by-location",
                params={"city": "New York", "limit": 10}
            )
            if response.status_code == 200:
                data = response.json()
                count = len(data['data'])
                print(f"   ✅ Nueva York: {count} resultados")
                if count > 0:
                    for i, measurement in enumerate(data['data'][:3]):
                        print(f"   🗽 {i+1}. {measurement['parameter'].upper()}: {measurement['value']} {measurement['unit']}")
                else:
                    print("   ℹ️  No hay datos de Nueva York en el archivo actual")
            else:
                print(f"   ❌ Error buscando Nueva York: {response.status_code}")
            print()
            
            print("✅ TODAS LAS PRUEBAS COMPLETADAS")
            
        except httpx.ConnectError:
            print("❌ No se pudo conectar al servidor")
            print("💡 Asegúrate de que el servidor esté ejecutándose en localhost:8001")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_filters())