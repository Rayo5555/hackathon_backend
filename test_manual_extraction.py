import requests
import time

def test_manual_extraction():
    """Probar la extracción manual de datos"""
    print("🚀 INICIANDO EXTRACCIÓN MANUAL DE DATOS")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/air-quality"
    
    try:
        # Trigger manual extraction
        print("📡 Solicitando extracción manual...")
        response = requests.post(f"{base_url}/extract/run-now", timeout=60)
        
        if response.status_code == 200:
            print("✅ Extracción iniciada correctamente")
            data = response.json()
            print(f"📄 Mensaje: {data.get('message', 'N/A')}")
        else:
            print(f"❌ Error en extracción: {response.status_code}")
            return
        
        # Wait a bit for extraction to complete
        print("⏳ Esperando 15 segundos para que complete la extracción...")
        time.sleep(15)
        
        # Check status
        print("🔍 Verificando estado del sistema...")
        status_response = requests.get(f"{base_url}/status", timeout=30)
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            system_data = status_data.get('data', {})
            print(f"📊 Archivos de datos: {system_data.get('data_files_count', 'N/A')}")
            print(f"📄 Último archivo: {system_data.get('last_file', 'N/A')}")
        
        # Get latest measurements
        print("📈 Obteniendo mediciones más recientes...")
        measurements_response = requests.get(f"{base_url}/measurements/latest?limit=10", timeout=30)
        
        if measurements_response.status_code == 200:
            measurements_data = measurements_response.json()
            print(f"✅ Éxito: {measurements_data.get('success', False)}")
            print(f"📄 Mensaje: {measurements_data.get('message', 'N/A')}")
            
            data_list = measurements_data.get('data', [])
            print(f"📊 Número de mediciones: {len(data_list)}")
            
            if data_list:
                sample = data_list[0]
                print(f"📍 Ejemplo - Parámetro: {sample.get('parameter')}")
                print(f"📍 Ejemplo - Valor: {sample.get('value')} {sample.get('unit')}")
                print(f"📍 Ejemplo - Fuente: {sample.get('source')}")
                print(f"📍 Ejemplo - Ubicación: {sample.get('location_name', 'N/A')}")
        
        print("=" * 50)
        print("🎯 PRUEBA COMPLETADA")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_manual_extraction()