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
        "pm10": 1,    # Particulate Matter 10 micrometers (µg/m³)
        "pm25": 2,    # Particulate Matter 2.5 micrometers (µg/m³)
        "no2": 7,     # Nitrogen Dioxide (ppm)
        "co": 8,      # Carbon Monoxide (ppm)
        "so2": 9,     # Sulfur Dioxide (ppm)
        "o3": 10      # Ozone (ppm)
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
            parameter_id: Parameter ID (1=pm10, 2=pm25, 7=NO2, 8=CO, 9=SO2, 10=O3)
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

    # Common bounding boxes for US regions (all 50 states + DC)
    US_BBOXES = {
        # Contiguous United States
        "alabama": "-88.47,30.22,-84.89,35.01",
        "arizona": "-114.82,31.33,-109.05,37.00",
        "arkansas": "-94.62,33.00,-89.64,36.50",
        "california": "-124.48,32.53,-114.13,42.01",
        "colorado": "-109.05,37.00,-102.04,41.00",
        "connecticut": "-73.73,40.98,-71.79,42.05",
        "delaware": "-75.79,38.45,-75.05,39.84",
        "florida": "-87.63,24.52,-80.03,31.00",
        "georgia": "-85.61,30.36,-80.84,35.00",
        "idaho": "-117.24,41.99,-111.04,49.00",
        "illinois": "-91.51,36.97,-87.02,42.51",
        "indiana": "-88.10,37.77,-84.78,41.76",
        "iowa": "-96.64,40.38,-90.14,43.50",
        "kansas": "-102.05,36.99,-94.59,40.00",
        "kentucky": "-89.57,36.50,-81.96,39.15",
        "louisiana": "-94.04,28.93,-88.82,33.02",
        "maine": "-71.08,43.06,-66.95,47.46",
        "maryland": "-79.49,37.97,-75.05,39.72",
        "massachusetts": "-73.51,41.24,-69.93,42.89",
        "michigan": "-90.42,41.70,-82.12,48.31",
        "minnesota": "-97.24,43.50,-89.49,49.38",
        "mississippi": "-91.66,30.17,-88.10,35.00",
        "missouri": "-95.77,35.99,-89.10,40.61",
        "montana": "-116.05,44.36,-104.04,49.00",
        "nebraska": "-104.05,40.00,-95.31,43.00",
        "nevada": "-120.01,35.00,-114.04,42.00",
        "new_hampshire": "-72.56,42.70,-70.61,45.31",
        "new_jersey": "-75.56,38.93,-73.89,41.36",
        "new_mexico": "-109.05,31.33,-103.00,37.00",
        "new_york": "-79.76,40.50,-71.86,45.01",
        "north_carolina": "-84.32,33.84,-75.46,36.59",
        "north_dakota": "-104.05,45.94,-96.55,49.00",
        "ohio": "-84.82,38.40,-80.52,42.32",
        "oklahoma": "-103.00,33.62,-94.43,37.00",
        "oregon": "-124.57,41.99,-116.46,46.29",
        "pennsylvania": "-80.52,39.72,-74.69,42.27",
        "rhode_island": "-71.91,41.15,-71.12,42.02",
        "south_carolina": "-83.35,32.03,-78.54,35.22",
        "south_dakota": "-104.06,42.48,-96.44,45.94",
        "tennessee": "-90.31,34.98,-81.65,36.68",
        "texas": "-106.65,25.84,-93.51,36.50",
        "utah": "-114.05,37.00,-109.04,42.00",
        "vermont": "-73.44,42.73,-71.46,45.02",
        "virginia": "-83.68,36.54,-75.24,39.47",
        "washington": "-124.85,45.54,-116.92,49.00",
        "west_virginia": "-82.64,37.20,-77.72,40.64",
        "wisconsin": "-92.89,42.49,-86.25,47.31",
        "wyoming": "-111.06,40.99,-104.05,45.01",
        # Non-contiguous states
        "alaska": "-179.15,51.21,179.78,71.44",
        "hawaii": "-160.25,18.91,-154.81,22.23",
        # District of Columbia
        "dc": "-77.12,38.79,-76.91,38.99",
        "district_of_columbia": "-77.12,38.79,-76.91,38.99",
        # Entire US
        "entire_us": "-125.0,24.0,-66.0,49.0",  # Continental USA
        "all_states": "-179.15,18.91,179.78,71.44"  # All 50 states including AK and HI
    }
    
    async def search_location_and_get_all_measurements(
        self,
        location_name: str,
        bbox: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for a location by name and get all pollution measurements
        
        Args:
            location_name: Name of the location to search for (case insensitive, partial match)
            bbox: Optional bounding box (if not provided, will search entire US or use state bbox)
            state: Optional state name (e.g., "colorado", "new_york") - uses predefined bbox for that state
            
        Returns:
            Dictionary with location info and all parameter measurements
        """
        # Determine which bbox to use
        search_bbox = bbox
        
        if not search_bbox and state:
            # Use predefined state bbox
            state_key = state.lower().replace(" ", "_")
            search_bbox = self.US_BBOXES.get(state_key)
            if not search_bbox:
                return {
                    "found": False,
                    "message": f"State '{state}' not found in predefined regions. Available: {', '.join(self.US_BBOXES.keys())}",
                    "search_criteria": {
                        "location_name": location_name,
                        "state": state
                    }
                }
        
        if not search_bbox:
            # Default to entire US
            search_bbox = self.US_BBOXES["entire_us"]
        
        # Get locations using bbox parameter (OpenAQ v3 supports this!)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Get locations within the bounding box
            locations_response = await client.get(
                f"{self.BASE_URL}/locations",
                params={"limit": 1000, "bbox": search_bbox},
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
                    "bbox": search_bbox,
                    "state": state if state else "entire_us"
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
        
        # Fetch measurements for all parameters using /locations/{id} endpoint first
        # to get sensor mapping, then /locations/{id}/latest for actual values
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Step 1: Get location info with sensor mapping
                location_info_response = await client.get(
                    f"{self.BASE_URL}/locations/{location_id}",
                    headers=self._get_headers()
                )
                location_info_response.raise_for_status()
                location_info_data = location_info_response.json()
                location_details = location_info_data.get("results", [{}])[0]
                
                # Create mapping: sensor_id -> parameter_id
                sensor_to_param = {}
                for sensor in location_details.get("sensors", []):
                    sensor_id = sensor.get("id")
                    param_info = sensor.get("parameter", {})
                    param_id = param_info.get("id")
                    if sensor_id and param_id:
                        sensor_to_param[sensor_id] = {
                            "parameter_id": param_id,
                            "units": param_info.get("units", "N/A")
                        }
                
                # Step 2: Get ALL latest measurements for this specific location
                measurements_response = await client.get(
                    f"{self.BASE_URL}/locations/{location_id}/latest",
                    headers=self._get_headers()
                )
                measurements_response.raise_for_status()
                location_data = measurements_response.json()
                
                measurements_list = location_data.get("results", [])
                
                # Create a map of parameterId -> measurement data using sensor mapping
                param_id_to_name = {v: k for k, v in self.PARAMETERS.items()}
                
                # Initialize all parameters as not available
                for param_name in self.PARAMETERS.keys():
                    results["measurements"][param_name] = {
                        "parameter_id": self.PARAMETERS[param_name],
                        "parameter_name": param_name.upper(),
                        "available": False,
                        "message": "No measurements available for this parameter"
                    }
                
                # Fill in the available measurements using sensor mapping
                for measurement in measurements_list:
                    sensor_id = measurement.get("sensorsId")
                    
                    # Get parameter info from sensor mapping
                    sensor_info = sensor_to_param.get(sensor_id)
                    if not sensor_info:
                        continue
                        
                    param_id = sensor_info["parameter_id"]
                    param_name = param_id_to_name.get(param_id)
                    
                    if param_name:
                        results["measurements"][param_name] = {
                            "parameter_id": param_id,
                            "parameter_name": param_name.upper(),
                            "latest_value": measurement.get("value"),
                            "unit": sensor_info["units"],
                            "datetime": measurement.get("datetime", {}),
                            "available": True
                        }
                
            except httpx.HTTPError as e:
                # If fetching fails, mark all parameters as unavailable
                for param_name, param_id in self.PARAMETERS.items():
                    results["measurements"][param_name] = {
                        "parameter_id": param_id,
                        "parameter_name": param_name.upper(),
                        "available": False,
                        "error": f"Could not fetch data: {str(e)}"
                    }
        
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
            parameter_id: Parameter ID (1=pm10, 2=pm25, 7=NO2, 8=CO, 9=SO2, 10=O3)
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

    async def get_all_locations_in_bbox_with_measurements(
        self,
        bbox: str,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Get all monitoring locations within a bounding box with their pollution measurements
        
        Args:
            bbox: Bounding box in format "min_lon,min_lat,max_lon,max_lat"
            limit: Maximum number of locations to return
            
        Returns:
            Dictionary with list of locations and their pollution measurements
        """
        # Get all locations within the bounding box
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            locations_response = await client.get(
                f"{self.BASE_URL}/locations",
                params={"limit": limit, "bbox": bbox},
                headers=self._get_headers()
            )
            locations_response.raise_for_status()
            locations_data = locations_response.json()
        
        all_locations = locations_data.get("results", [])
        
        if not all_locations:
            return {
                "found": False,
                "message": "No monitoring locations found in the specified area",
                "bbox": bbox,
                "total_locations": 0,
                "locations": []
            }
        
        # For each location, fetch measurements for all parameters
        locations_with_measurements = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for location in all_locations:
                location_id = location.get("id")
                
                location_info = {
                    "location_id": location_id,
                    "name": location.get("name"),
                    "locality": location.get("locality"),
                    "coordinates": location.get("coordinates"),
                    "country": location.get("country", {}).get("name"),
                    "measurements": {}
                }
                
                # Fetch location details to get sensor mapping, then get latest measurements
                try:
                    # Step 1: Get location info with sensor mapping
                    location_info_response = await client.get(
                        f"{self.BASE_URL}/locations/{location_id}",
                        headers=self._get_headers()
                    )
                    location_info_response.raise_for_status()
                    location_info_data = location_info_response.json()
                    location_details = location_info_data.get("results", [{}])[0]
                    
                    # Create mapping: sensor_id -> parameter_id
                    sensor_to_param = {}
                    for sensor in location_details.get("sensors", []):
                        sensor_id = sensor.get("id")
                        param_info = sensor.get("parameter", {})
                        param_id = param_info.get("id")
                        if sensor_id and param_id:
                            sensor_to_param[sensor_id] = {
                                "parameter_id": param_id,
                                "units": param_info.get("units", "N/A")
                            }
                    
                    # Step 2: Get latest measurements
                    measurements_response = await client.get(
                        f"{self.BASE_URL}/locations/{location_id}/latest",
                        headers=self._get_headers()
                    )
                    measurements_response.raise_for_status()
                    location_data = measurements_response.json()
                    
                    measurements_list = location_data.get("results", [])
                    
                    # Create a map of parameterId -> measurement data using sensor mapping
                    param_id_to_name = {v: k for k, v in self.PARAMETERS.items()}
                    
                    # Initialize all parameters as not available
                    for param_name in self.PARAMETERS.keys():
                        location_info["measurements"][param_name] = {
                            "parameter_id": self.PARAMETERS[param_name],
                            "parameter_name": param_name.upper(),
                            "available": False
                        }
                    
                    # Fill in the available measurements using sensor mapping
                    for measurement in measurements_list:
                        sensor_id = measurement.get("sensorsId")
                        
                        # Get parameter info from sensor mapping
                        sensor_info = sensor_to_param.get(sensor_id)
                        if not sensor_info:
                            continue
                            
                        param_id = sensor_info["parameter_id"]
                        param_name = param_id_to_name.get(param_id)
                        
                        if param_name:
                            location_info["measurements"][param_name] = {
                                "parameter_id": param_id,
                                "parameter_name": param_name.upper(),
                                "latest_value": measurement.get("value"),
                                "unit": sensor_info["units"],
                                "datetime": measurement.get("datetime", {}),
                                "available": True
                            }
                    
                except Exception as e:
                    # If fetching fails, mark all parameters as unavailable
                    for param_name, param_id in self.PARAMETERS.items():
                        location_info["measurements"][param_name] = {
                            "parameter_id": param_id,
                            "parameter_name": param_name.upper(),
                            "available": False,
                            "error": str(e)
                        }
                
                # Calculate summary statistics
                available_measurements = sum(
                    1 for data in location_info["measurements"].values() 
                    if data.get("available", False)
                )
                location_info["measurements_summary"] = {
                    "total_parameters": len(self.PARAMETERS),
                    "available_parameters": available_measurements,
                    "missing_parameters": len(self.PARAMETERS) - available_measurements
                }
                
                locations_with_measurements.append(location_info)
        
        return {
            "found": True,
            "bbox": bbox,
            "total_locations": len(locations_with_measurements),
            "locations": locations_with_measurements,
            "summary": {
                "total_locations_found": len(locations_with_measurements),
                "parameters_monitored": list(self.PARAMETERS.keys())
            }
        }
