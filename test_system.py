#!/usr/bin/env python3
"""
Script de prueba para el sistema de extracción de datos de calidad del aire
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_openaq_extraction():
    """Probar extracción de datos de OpenAQ (no requiere API key)"""
    try:
        from src.air_quality_client import AirQualityAPIClient
        from src.schemas import Coordinates
        
        print("🚀 Iniciando prueba de extracción de OpenAQ...")
        
        async with AirQualityAPIClient() as client:
            # Probar extracción de OpenAQ cerca de Nueva York
            nyc_coords = Coordinates(latitude=40.7128, longitude=-74.0060)
            measurements = await client.get_openaq_measurements(
                coordinates=nyc_coords,
                radius=50000,  # 50km
                limit=50
            )
            
            print(f"✅ Extraídas {len(measurements)} mediciones de OpenAQ")
            
            if measurements:
                print("📊 Ejemplos de datos:")
                for i, measurement in enumerate(measurements[:3]):
                    print(f"  {i+1}. {measurement.parameter.value}: {measurement.value} {measurement.unit}")
                    print(f"     Ubicación: {measurement.location_name}")
                    print(f"     Coordenadas: {measurement.coordinates.latitude}, {measurement.coordinates.longitude}")
                    print(f"     Última actualización: {measurement.last_updated}")
                    print()
            
            return measurements
            
    except Exception as e:
        print(f"❌ Error en prueba de OpenAQ: {e}")
        return []

async def test_data_storage():
    """Probar almacenamiento de datos"""
    try:
        from src.air_quality_client import AirQualityAPIClient
        
        print("💾 Probando almacenamiento de datos...")
        
        async with AirQualityAPIClient() as client:
            # Simular datos mínimos
            test_data = {
                "openaq": await test_openaq_extraction()
            }
            
            # Guardar datos
            await client.save_data_to_json(test_data)
            
            # Verificar que se crearon archivos
            data_dir = Path("data/air_quality")
            json_files = list(data_dir.glob("*.json"))
            
            print(f"✅ Datos guardados. Archivos JSON creados: {len(json_files)}")
            
            if json_files:
                latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
                print(f"📁 Último archivo: {latest_file.name}")
                
                # Mostrar tamaño del archivo
                file_size = latest_file.stat().st_size
                print(f"📏 Tamaño: {file_size} bytes")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en prueba de almacenamiento: {e}")
        return False

async def test_api_routes():
    """Probar que las rutas de la API se pueden importar"""
    try:
        print("🔌 Probando importación de rutas de API...")
        
        from src.routes.air_quality import router
        from src.main import app
        
        print("✅ Rutas importadas correctamente")
        print(f"📋 Rutas disponibles en el router: {len(router.routes)}")
        
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods)
                print(f"  {methods} {route.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en importación de rutas: {e}")
        return False

async def main():
    print("🧪 Iniciando pruebas del sistema de calidad del aire\n")
    
    # Verificar estructura de directorios
    data_dir = Path("data/air_quality")
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Directorio de datos: {data_dir.absolute()}")
    
    # Ejecutar pruebas
    tests = [
        ("Rutas de API", test_api_routes()),
        ("Extracción de OpenAQ", test_openaq_extraction()),
        ("Almacenamiento de datos", test_data_storage())
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\n🔍 Ejecutando: {test_name}")
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Fallo en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "="*50)
    print("📈 RESUMEN DE PRUEBAS")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} pruebas exitosas")
    
    if passed == len(results):
        print("\n🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
        print("💡 Para iniciar el servidor:")
        print("   uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")

if __name__ == "__main__":
    asyncio.run(main())