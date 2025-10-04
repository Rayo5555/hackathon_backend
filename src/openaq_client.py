"""
OpenAQ API Client for fetching air quality data
"""
import httpx
import os
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class OpenAQClient:
    """Client to interact with OpenAQ API v3"""
    
    BASE_URL = "https://api.openaq.org/v3"  # OpenAQ API base URL
    
    # Parameter IDs according to OpenAQ
    PARAMETERS = {
        "pm10": 1,
        "pm25": 2,
        "no2": 7,
        "co2": 8,
        "so2": 9,
        "o3": 10
    }
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize OpenAQ client
        
        Args:
            api_key: OpenAQ API key (if not provided, will try to read from OPENAQ_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENAQ_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAQ_API_KEY not found. Please set it in your .env file or pass it to the constructor.")
        self.timeout = timeout
        
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key if available"""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    async def get_latest_measurements(
        self,
        parameter_id: int,
        country: str = "US",
        limit: int = 1000,
        state: Optional[str] = None,
        city: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get latest measurements for a specific parameter
        
        Args:
            parameter_id: Parameter ID (1=pm10, 2=pm2.5, 7=NO2, 8=CO2, 9=SO2, 10=O3)
            country: Country code (default: US)
            limit: Maximum number of results to return (after filtering)
            state: Optional state filter (applied client-side)
            city: Optional city filter (applied client-side)
            **kwargs: Additional query parameters
            
        Returns:
            JSON response from OpenAQ API (filtered if state/city provided)
        """
        # Note: OpenAQ API v3 /parameters/{id}/latest doesn't support geographic filters
        # We need to fetch more data and filter client-side
        
        # If filtering by state/city, fetch more results to ensure we get enough matches
        api_limit = limit * 10 if (state or city) else limit
        api_limit = min(api_limit, 10000)  # API max
        
        params = {
            "limit": api_limit,
            "countries_id": 237 if country.upper() in ["US", "USA"] else None,
            **kwargs
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.BASE_URL}/parameters/{parameter_id}/latest?bbox=-109.05,37,-102.04,41",
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            # Filter results client-side if state or city specified
            if state or city:
                original_results = data.get("results", [])
                filtered_results = []
                
                for result in original_results:
                    location = result.get("location", {})
                    locality = location.get("locality", "")
                    
                    # Check state filter
                    if state and locality:
                        # Locality format is usually "City, State" or just "State"
                        if state.lower() not in locality.lower():
                            continue
                    
                    # Check city filter
                    if city and locality:
                        if city.lower() not in locality.lower():
                            continue
                    
                    filtered_results.append(result)
                    
                    # Stop when we have enough results
                    if len(filtered_results) >= limit:
                        break
                
                # Update data with filtered results
                data["results"] = filtered_results
                data["meta"]["found"] = len(filtered_results)
                data["meta"]["filtered"] = True
                data["meta"]["filter_note"] = "Results filtered client-side by state/city"
            
            return data
    
    async def get_all_parameters_latest(
        self,
        country: str = "US",
        limit: int = 1000,
        state: Optional[str] = None,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get latest measurements for all monitored parameters
        
        Args:
            country: Country code (default: US)
            limit: Maximum number of results per parameter
            state: Optional state filter (applied client-side)
            city: Optional city filter (applied client-side)
            
        Returns:
            Dictionary with parameter names as keys and their data as values
        """
        results = {}
        
        # Fetch more data if filtering to ensure we get enough results
        fetch_limit = limit * 10 if (state or city) else limit
        fetch_limit = min(fetch_limit, 10000)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for param_name, param_id in self.PARAMETERS.items():
                params = {
                    "limit": fetch_limit,
                    "countries_id": 237 if country.upper() in ["US", "USA"] else None,
                }
                
                # Remove None values
                params = {k: v for k, v in params.items() if v is not None}
                
                try:
                    response = await client.get(
                        f"{self.BASE_URL}/parameters/{param_id}/latest?bbox=-109.05,37,-102.04,41",
                        params=params,
                        headers=self._get_headers()
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Filter results client-side if state or city specified
                    if state or city:
                        original_results = data.get("results", [])
                        filtered_results = []
                        
                        for result in original_results:
                            location = result.get("location", {})
                            locality = location.get("locality", "")
                            
                            # Check state filter
                            if state and locality:
                                if state.lower() not in locality.lower():
                                    continue
                            
                            # Check city filter
                            if city and locality:
                                if city.lower() not in locality.lower():
                                    continue
                            
                            filtered_results.append(result)
                            
                            # Stop when we have enough results
                            if len(filtered_results) >= limit:
                                break
                        
                        # Update data with filtered results
                        data["results"] = filtered_results
                        data["meta"]["found"] = len(filtered_results)
                        data["meta"]["filtered"] = True
                    
                    results[param_name] = data
                except httpx.HTTPError as e:
                    results[param_name] = {"error": str(e)}
        
        return results

    async def search_location_and_get_all_measurements(
        self,
        location_name: str,
        bbox: str = "-109.05,37,-102.04,41"
    ) -> Dict[str, Any]:
        """
        Search for a location by name and get all pollution measurements
        
        Args:
            location_name: Name of the location to search for (case insensitive, partial match)
            bbox: Bounding box to search within (default: Colorado area)
            
        Returns:
            Dictionary with location info and all parameter measurements
        """
        # Get locations using bbox parameter (OpenAQ v3 supports this!)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Get locations within the bounding box
            locations_response = await client.get(
                f"{self.BASE_URL}/locations",
                params={"limit": 1000, "bbox": bbox},
                headers=self._get_headers()
            )
            locations_response.raise_for_status()
            locations_data = locations_response.json()
        
        # Filter locations by name
        all_locations = locations_data.get("results", [])
        matching_locations = []
        
        for loc in all_locations:
            # Check name match - handle None values safely
            loc_name = (loc.get("name") or "").lower()
            loc_locality = (loc.get("locality") or "").lower()
            search_name = location_name.lower()
            
            # Match by name or locality
            if search_name in loc_name or search_name in loc_locality:
                matching_locations.append(loc)
        
        # If no matches found
        if not matching_locations:
            return {
                "found": False,
                "message": f"No location found matching '{location_name}' in the specified area",
                "search_criteria": {
                    "location_name": location_name,
                    "bbox": bbox
                },
                "total_locations_searched": len(all_locations)
            }
        
        # Use the first matching location
        location = matching_locations[0]
        location_id = location.get("id")
        
        # Get measurements for all parameters
        results = {
            "found": True,
            "location_id": location_id,
            "location_name": location.get("name"),
            "locality": location.get("locality"),
            "coordinates": location.get("coordinates"),
            "country": location.get("country", {}).get("name"),
            "matches_found": len(matching_locations),
            "measurements": {}
        }
        
        # If multiple matches, include them
        if len(matching_locations) > 1:
            results["other_matches"] = [
                {
                    "id": loc.get("id"),
                    "name": loc.get("name"),
                    "locality": loc.get("locality")
                }
                for loc in matching_locations[1:6]  # Show up to 5 other matches
            ]
        
        # Fetch measurements for all parameters (create new client context)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Define async function to fetch one parameter
            async def fetch_parameter(param_name: str, param_id: int):
                try:
                    # Get latest measurements for this parameter
                    measurements_response = await client.get(
                        f"{self.BASE_URL}/parameters/{param_id}/latest",
                        params={"locations_id": location_id, "limit": 100},
                        headers=self._get_headers()
                    )
                    measurements_response.raise_for_status()
                    param_data = measurements_response.json()
                    
                    measurements_list = param_data.get("results", [])
                    
                    if measurements_list:
                        # Get the latest measurement
                        latest = measurements_list[0]
                        
                        return (param_name, {
                            "parameter_id": param_id,
                            "parameter_name": param_name.upper(),
                            "latest_value": latest.get("value"),
                            "unit": latest.get("parameter", {}).get("units", "N/A"),
                            "datetime": latest.get("datetime", {}),
                            "total_measurements_available": len(measurements_list),
                            "available": True,
                            "all_measurements": [
                                {
                                    "value": m.get("value"),
                                    "datetime": m.get("datetime", {}).get("utc")
                                }
                                for m in measurements_list[:10]  # Include last 10 measurements
                            ]
                        })
                    else:
                        return (param_name, {
                            "parameter_id": param_id,
                            "parameter_name": param_name.upper(),
                            "available": False,
                            "message": "No measurements available for this parameter"
                        })
                        
                except httpx.HTTPError as e:
                    return (param_name, {
                        "parameter_id": param_id,
                        "parameter_name": param_name.upper(),
                        "available": False,
                        "error": f"Could not fetch data: {str(e)}"
                    })
            
            # Fetch all parameters concurrently
            tasks = [fetch_parameter(param_name, param_id) for param_name, param_id in self.PARAMETERS.items()]
            param_results = await asyncio.gather(*tasks)
            
            # Add results to the measurements dict
            for param_name, param_data in param_results:
                results["measurements"][param_name] = param_data
        
        return results

    
    async def get_locations(
        self,
        country: Optional[str] = None,
        limit: int = 1000,
        page: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get all monitoring locations
        
        Args:
            country: Country code (e.g., "US") - will be converted to countries_id
            limit: Maximum number of results per page (max 1000)
            page: Page number for pagination
            **kwargs: Additional query parameters
            
        Returns:
            JSON response with locations
        """
        params = {
            "limit": min(limit, 1000),  # API max is 1000 per page
            "page": page,
            **kwargs
        }
        
        # Convert country code to countries_id if provided
        if country:
            # For US, the countries_id is typically 237
            country_ids = {
                "US": 237,
                "USA": 237,
            }
            if country.upper() in country_ids:
                params["countries_id"] = country_ids[country.upper()]
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.BASE_URL}/locations",
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_measurements_by_parameter(
        self,
        parameter_id: int,
        bbox: str = "-109.05,37,-102.04,41",
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Get all measurements for a specific pollution parameter
        
        Args:
            parameter_id: Parameter ID (1=pm10, 2=pm2.5, 7=NO2, 8=CO2, 9=SO2, 10=O3)
            bbox: Bounding box for geographic filter (default: Colorado area)
            limit: Maximum number of results
            
        Returns:
            JSON response from OpenAQ API with all measurements
        """
        params = {
            "limit": min(limit, 10000),  # API max
            "bbox": bbox
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.BASE_URL}/parameters/{parameter_id}/latest",
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def get_measurements_by_location(
        self,
        location_id: int,
        include_full_data: bool = False
    ) -> Dict[str, Any]:
        """
        Get all measurements (all parameters) for a specific location in USA
        
        Args:
            location_id: OpenAQ location ID
            include_full_data: If True, includes all measurements; if False, only summary with latest values
            
        Returns:
            Dictionary with all parameters and their measurements for the location
        """
        results = {
            "location_id": location_id,
            "parameters": {},
            "summary": {}
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # First, get location details
            try:
                location_response = await client.get(
                    f"{self.BASE_URL}/locations/{location_id}",
                    headers=self._get_headers()
                )
                location_response.raise_for_status()
                location_data = location_response.json()
                results["location_info"] = location_data
                
                # Extract location name and coordinates for easy access
                if "results" in location_data and len(location_data["results"]) > 0:
                    loc = location_data["results"][0]
                    results["location_name"] = loc.get("name", "Unknown")
                    results["coordinates"] = loc.get("coordinates", {})
                    results["locality"] = loc.get("locality", "Unknown")
            except httpx.HTTPError as e:
                results["location_info"] = {"error": str(e)}
            
            # Then, fetch measurements for all parameters
            for param_name, param_id in self.PARAMETERS.items():
                try:
                    response = await client.get(
                        f"{self.BASE_URL}/locations/{location_id}/parameters/{param_id}/measurements",
                        params={"limit": 100},  # Get last 100 measurements
                        headers=self._get_headers()
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Store full data if requested
                    if include_full_data:
                        results["parameters"][param_name] = data
                    else:
                        # Only store metadata
                        results["parameters"][param_name] = {
                            "available": True,
                            "total_measurements": len(data.get("results", [])),
                            "meta": data.get("meta", {})
                        }
                    
                    # Create summary with latest values
                    measurements = data.get("results", [])
                    if measurements:
                        latest = measurements[0]  # First result is usually the latest
                        results["summary"][param_name] = {
                            "parameter_id": param_id,
                            "latest_value": latest.get("value"),
                            "unit": latest.get("parameter", {}).get("units", "N/A"),
                            "datetime": latest.get("datetime", {}),
                            "total_measurements": len(measurements),
                            "available": True
                        }
                    else:
                        results["summary"][param_name] = {
                            "parameter_id": param_id,
                            "available": False,
                            "message": "No measurements available"
                        }
                        
                except httpx.HTTPError as e:
                    # If parameter not available for this location
                    results["parameters"][param_name] = {
                        "error": str(e),
                        "available": False
                    }
                    results["summary"][param_name] = {
                        "parameter_id": param_id,
                        "available": False,
                        "error": str(e)
                    }
        
        return results
