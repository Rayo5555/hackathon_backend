#!/usr/bin/env python3
"""
TEMPO O3 & SO2 Data Extraction to JSON
Requirements: earthaccess>=0.15, xarray, dask, numpy, python-dotenv
"""

import earthaccess
import xarray as xr
import numpy as np
import json
import time
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()  # Load Earthdata token from .env

class ProgressTracker:
    """Track progress and estimate remaining time"""
    
    def __init__(self, total_steps, description="Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        self.description = description
        self.step_times = []
        
    def update(self, message=""):
        """Update progress and show ETA"""
        self.current_step += 1
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Calculate average time per step
        if self.step_times:
            avg_time_per_step = np.mean(self.step_times)
        else:
            avg_time_per_step = elapsed / self.current_step
        
        # Store this step's time (for better averaging)
        if len(self.step_times) < 10:  # Keep last 10 steps for average
            self.step_times.append(elapsed - sum(self.step_times))
        else:
            self.step_times.pop(0)
            self.step_times.append(elapsed - sum(self.step_times))
        
        # Calculate remaining time
        remaining_steps = self.total_steps - self.current_step
        remaining_time = avg_time_per_step * remaining_steps
        
        # Format time strings
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        remaining_str = str(timedelta(seconds=int(remaining_time)))
        
        # Progress percentage
        percentage = (self.current_step / self.total_steps) * 100
        
        # Progress bar (simplified)
        bar_length = 20
        filled_length = int(bar_length * self.current_step // self.total_steps)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r[{bar}] {percentage:5.1f}% | {self.description} | "
              f"Step {self.current_step}/{self.total_steps} | "
              f"Elapsed: {elapsed_str} | ETA: {remaining_str} {message}", 
              end="", flush=True)
        
        if self.current_step >= self.total_steps:
            print()  # New line when complete

# ===============================
# 1️⃣ Login to Earthdata
# ===============================
print("🔐 Authenticating with Earthdata...")
auth = earthaccess.login(strategy="environment")
if not auth.authenticated:
    raise RuntimeError("Failed to authenticate with Earthdata token")
print("✅ Authentication successful")

# ===============================
# 2️⃣ Search for TEMPO granules
# ===============================
DATE = "2025-04-10"
print(f"🔍 Searching for TEMPO data on {DATE}...")
results = earthaccess.search_data(
    short_name="TEMPO_HCHO_L3",  # TEMPO O3 Level-3 product
    version="V03",
    temporal=(f"{DATE} 00:00", f"{DATE} 23:59"),
    count=3
)
print(f"✅ Found {len(results)} granules")

# ===============================
# 3️⃣ Open as virtual multi-file dataset
# ===============================
print("📂 Opening dataset...")
progress = ProgressTracker(4, "Opening dataset")

open_options = {
    "access": "indirect",
    "load": True,
    "concat_dim": "time",
    "data_vars": "minimal",
    "coords": "minimal",
    "compat": "override",
    "combine_attrs": "override",
}

progress.update("Loading root group")
ds_root = earthaccess.open_virtual_mfdataset(granules=results, **open_options)

progress.update("Loading product group")
ds_product = earthaccess.open_virtual_mfdataset(granules=results, group="product", **open_options)

progress.update("Loading geolocation group")
ds_geo = earthaccess.open_virtual_mfdataset(granules=results, group="geolocation", **open_options)

progress.update("Merging groups")
ds_merged = xr.merge([ds_root, ds_product, ds_geo])
print("✅ Dataset merged successfully")

# ===============================
# 4️⃣ Subset region: CONUS (or change to NYC etc.)
# ===============================
print("🗺️ Subsetting region...")
# NYC region
# CONUS region
lon_bounds = (-125, -66)  # Western to Eastern US
lat_bounds = (24, 50)     # Southern to Northern US


ds_subset = ds_merged.sel(
    longitude=slice(lon_bounds[0], lon_bounds[1]),
    latitude=slice(lat_bounds[0], lat_bounds[1])
)
print(f"✅ Subset shape: {ds_subset.dims}")

# ===============================
# 5️⃣ Variables to export
# ===============================
variables = {
    "HCHO": "vertical_column",
}

# ===============================
# 6️⃣ Convert to JSON with progress tracking
# ===============================
def dataset_to_json(ds, var_name, coarsen_factor=300):
    """
    Faster downsample and convert to JSON list of {lat, lon, value}.
    Vectorized using xarray operations.
    """
    if var_name not in ds:
        print(f"⚠️ Variable {var_name} not found")
        return []

    print(f"📊 Processing {var_name}...")

    # Mean over time, then coarsen
    ds_down = ds[var_name].mean(dim="time").coarsen(
        latitude=coarsen_factor, longitude=coarsen_factor, boundary='trim'
    ).mean()

    # Stack lat/lon to 1D
    stacked = ds_down.stack(points=("latitude", "longitude"))

    # Drop NaNs
    stacked = stacked.dropna("points", how="any")

    # Convert to list of dicts
    data_list = [
        {"lat": float(lat), "lon": float(lon), "value": float(val)}
        for (lat, lon), val in zip(zip(stacked.latitude.values, stacked.longitude.values), stacked.values)
    ]

    print(f"✅ {var_name}: {len(data_list)} points exported")
    return data_list

# Build final JSON object with overall progress tracking
print("🚀 Starting JSON export...")
overall_progress = ProgressTracker(len(variables), "Overall progress")

output_json = {}
for name, var in variables.items():
    output_json[name] = dataset_to_json(ds_subset, var)
    overall_progress.update(f"Completed {name}")

# Save to files with progress
print("💾 Saving to files...")
file_progress = ProgressTracker(len(output_json), "Saving files")

for name, data in output_json.items():
    filename = f"{name.lower()}_heatmap.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    file_progress.update(f"Saved {filename}")

# Return JSON object for programmatic use
total_time = time.time() - overall_progress.start_time
print(f"✅ JSON generation complete! Total time: {timedelta(seconds=int(total_time))}")
print("📊 Summary:")
for name, data in output_json.items():
    print(f"   {name}: {len(data)} data points")


print(output_json)