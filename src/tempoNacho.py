#!/usr/bin/env python3
"""
TEMPO O3 & SO2 Data Analysis - Full Script
Requirements: earthaccess>=0.15, xarray, dask, numpy, matplotlib, cartopy, python-dotenv
"""

import earthaccess
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from matplotlib import rcParams
from dotenv import load_dotenv

load_dotenv()  # Load Earthdata token from .env
rcParams["figure.dpi"] = 80

# ===============================
# 1️⃣ Login to Earthdata
# ===============================
auth = earthaccess.login(strategy="environment")  # fixed typo
if not auth.authenticated:
    raise RuntimeError("Failed to authenticate with Earthdata token")

# ===============================
# 2️⃣ Search for TEMPO granules
# ===============================
DATE = "2025-04-10"
results = earthaccess.search_data(
    short_name="TEMPO_O3TOT_L3",  # TEMPO O3 Level-3 product
    version="V03",
    temporal=(f"{DATE} 00:00", f"{DATE} 23:59"),
    count=12  # limit for quick testing
)
print(f"Found {len(results)} granules")

# ===============================
# 3️⃣ Open as virtual multi-file dataset
# ===============================
open_options = {
    "access": "indirect",
    "load": True,
    "concat_dim": "time",
    "data_vars": "minimal",
    "coords": "minimal",
    "compat": "override",
    "combine_attrs": "override",
}

ds_root = earthaccess.open_virtual_mfdataset(granules=results, **open_options)
ds_product = earthaccess.open_virtual_mfdataset(granules=results, group="product", **open_options)
ds_geo = earthaccess.open_virtual_mfdataset(granules=results, group="geolocation", **open_options)

# Merge groups
ds_merged = xr.merge([ds_root, ds_product, ds_geo])
print(ds_merged)

# ===============================
# 4️⃣ Subset region: CONUS
# ===============================
lon_bounds = (-125, -66)
lat_bounds = (24, 50)

ds_subset = ds_merged.sel(
    longitude=slice(lon_bounds[0], lon_bounds[1]),
    latitude=slice(lat_bounds[0], lat_bounds[1])
)

# ===============================
# 5️⃣ Variables to plot
# ===============================
variables = {
    "O3": "column_amount_o3",
    "SO2": "so2_index"
}

# ===============================
# 6️⃣ Compute temporal mean and plot maps
# ===============================
for name, var in variables.items():
    if var not in ds_subset:
        print(f"Variable {var} not found in dataset, skipping {name}")
        continue
    
    temporal_mean = ds_subset[var].mean(dim="time").compute()
    
    fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
    temporal_mean.plot.contourf(ax=ax)
    ax.coastlines()
    ax.gridlines(draw_labels=True, dms=True)
    ax.set_title(f"TEMPO {name} Temporal Mean - {DATE}")
    plt.show()

# ===============================
# 7️⃣ Optional: Spatial mean (time series)
# ===============================
for name, var in variables.items():
    if var not in ds_subset:
        continue
    spatial_mean = ds_subset[var].mean(dim=("latitude", "longitude")).compute()
    plt.figure()
    spatial_mean.plot(marker="o")
    plt.title(f"TEMPO {name} Spatial Mean Time Series - {DATE}")
    plt.xlabel("Time")
    plt.ylabel(f"{name} column")
    plt.grid(True)
    plt.show()

print("Script completed successfully!")
