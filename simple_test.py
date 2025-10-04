import requests
import json

# Test simple
try:
    print("🔥 TRIGGERING MANUAL EXTRACTION...")
    response = requests.post("http://localhost:8000/api/air-quality/extract/run-now", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n⏳ Waiting 5 seconds...")
    import time
    time.sleep(5)
    
    print("\n📊 CHECKING LATEST DATA...")
    data_response = requests.get("http://localhost:8000/api/air-quality/measurements/latest?limit=5", timeout=10)
    print(f"Status: {data_response.status_code}")
    
    if data_response.status_code == 200:
        data = data_response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        measurements = data.get('data', [])
        print(f"Count: {len(measurements)}")
        
        if measurements:
            first = measurements[0]
            print(f"First measurement:")
            print(f"  - Parameter: {first.get('parameter')}")
            print(f"  - Value: {first.get('value')} {first.get('unit')}")
            print(f"  - Source: {first.get('source')}")
            print(f"  - Location: {first.get('location_name')}")
    
except Exception as e:
    print(f"Error: {e}")