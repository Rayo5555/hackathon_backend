#!/usr/bin/env python3
"""
Script para probar la API de OpenAQ v3 y encontrar el endpoint correcto
"""
import asyncio
import httpx
from dotenv import load_dotenv
import os

async def test_openaq_endpoints():
    """Probar diferentes endpoints de OpenAQ v3"""
    load_dotenv()
    
    api_key = os.getenv("OPENAQ_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    headers = {"X-API-Key": api_key}
    
    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        
        # Test 1: Base API info
        print("🔍 Testing base API endpoints...")
        test_urls = [
            "https://api.openaq.org/v3",
            "https://api.openaq.org/v3/measurements",
            "https://api.openaq.org/v2/measurements",  # Try v2
        ]
        
        for url in test_urls:
            try:
                print(f"\n📡 Testing: {url}")
                response = await client.get(url)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                elif response.status_code == 404:
                    print("❌ 404 - Endpoint not found")
                elif response.status_code == 401:
                    print("❌ 401 - Authentication failed")
                else:
                    print(f"❌ {response.status_code} - {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Test 2: Try with minimal parameters
        print("\n🔍 Testing with minimal parameters...")
        minimal_urls = [
            "https://api.openaq.org/v3/measurements?limit=5",
            "https://api.openaq.org/v2/measurements?limit=5",
            "https://api.openaq.org/v3/measurements?limit=5&country=US",
            "https://api.openaq.org/v2/measurements?limit=5&country=US",
        ]
        
        for url in minimal_urls:
            try:
                print(f"\n📡 Testing: {url}")
                response = await client.get(url)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"Response keys: {list(data.keys())}")
                        if 'results' in data:
                            print(f"Results count: {len(data['results'])}")
                        elif 'measurements' in data:
                            print(f"Measurements count: {len(data['measurements'])}")
                elif response.status_code == 404:
                    print("❌ 404 - Endpoint not found")
                else:
                    print(f"❌ {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_openaq_endpoints())