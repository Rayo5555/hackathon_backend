#!/usr/bin/env python3
"""
Script para probar específicamente la API de OpenAQ
"""
import asyncio
import os
from dotenv import load_dotenv
import sys
sys.path.append('/home/magma/Desktop/hackathon_backend')

from src.air_quality_client import AirQualityAPIClient
from src.schemas import Coordinates

async def test_openaq_api():
    """Probar la API de OpenAQ directamente"""
    load_dotenv()
    
    print("🔧 PROBANDO API DE OPENAQ")
    print("=" * 50)
    
    # Verificar API key
    api_key = os.getenv("OPENAQ_API_KEY")
    print(f"🔑 API Key configurada: {'✅ Sí' if api_key else '❌ No'}")
    if api_key:
        print(f"🔑 Longitud de la key: {len(api_key)} caracteres")
    else:
        print("❌ ERROR: No se encontró OPENAQ_API_KEY en .env")
        return
    
    print("-" * 50)
    
    # Crear cliente
    client = AirQualityAPIClient()
    
    try:
        print("🌍 Probando extracción general de EE.UU...")
        general_data = await client.get_openaq_measurements(limit=100)
        print(f"📊 Datos generales obtenidos: {len(general_data)}")
        
        if general_data:
            sample = general_data[0]
            print(f"📍 Ejemplo: {sample.parameter.value} = {sample.value} {sample.unit}")
            print(f"📍 Ubicación: {sample.location_name or 'Sin nombre'}")
            print(f"📍 Coordenadas: ({sample.coordinates.latitude}, {sample.coordinates.longitude})")
            print(f"📍 Fecha: {sample.last_updated}")
        
        print("-" * 50)
        
        # Probar con coordenadas específicas (Los Angeles)
        print("🌴 Probando con coordenadas de Los Angeles...")
        la_coords = Coordinates(latitude=34.0522, longitude=-118.2437)
        la_data = await client.get_openaq_measurements(
            coordinates=la_coords, 
            radius=50000, 
            limit=50
        )
        print(f"📊 Datos de LA obtenidos: {len(la_data)}")
        
        if la_data:
            sample = la_data[0]
            print(f"📍 Ejemplo LA: {sample.parameter.value} = {sample.value} {sample.unit}")
            print(f"📍 Ubicación: {sample.location_name or 'Sin nombre'}")
        
        print("-" * 50)
        
        # Resumen
        total_data = len(general_data) + len(la_data)
        print(f"🎯 TOTAL DE DATOS OBTENIDOS: {total_data}")
        
        if total_data > 0:
            print("✅ ¡ÉXITO! La API de OpenAQ está funcionando correctamente")
        else:
            print("⚠️  No se obtuvieron datos. Posibles causas:")
            print("   - API key inválida")
            print("   - Problemas de conectividad")
            print("   - Cambios en la API de OpenAQ")
            
    except Exception as e:
        print(f"❌ ERROR durante la prueba: {e}")
        
    finally:
        await client.client.aclose()

if __name__ == "__main__":
    asyncio.run(test_openaq_api())