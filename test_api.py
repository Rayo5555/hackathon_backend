#!/usr/bin/env python3
import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print("Root endpoint:")
        print(json.dumps(response.json(), indent=2))
        print(f"Status: {response.status_code}")
        print("-" * 50)
    except Exception as e:
        print(f"Error testing root endpoint: {e}")
    
    # Test filter options
    try:
        response = requests.get(f"{base_url}/api/air-quality/filter-options")
        print("Filter options endpoint:")
        print(json.dumps(response.json(), indent=2))
        print(f"Status: {response.status_code}")
        print("-" * 50)
    except Exception as e:
        print(f"Error testing filter options: {e}")
    
    # Test latest measurements
    try:
        response = requests.get(f"{base_url}/api/air-quality/measurements/latest?limit=5")
        print("Latest measurements endpoint:")
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        print(f"Data count: {len(data.get('data', []))}")
        print(f"Status: {response.status_code}")
        print("-" * 50)
    except Exception as e:
        print(f"Error testing latest measurements: {e}")

if __name__ == "__main__":
    test_api()