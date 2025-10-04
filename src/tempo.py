"""
NASA TEMPO Air Quality Data Access using earthaccess (FIXED)
Monitors: O3, NO2, SO2, HCHO from TEMPO satellite

Requirements:
pip install earthaccess netCDF4 numpy matplotlib cartopy python-dotenv
"""

import earthaccess
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class TEMPOMonitor:
    """
    Access and visualize NASA TEMPO air quality data using earthaccess
    """
    
    def __init__(self, username=None, password=None):
        """
        Initialize and authenticate with NASA Earthdata
        
        Args:
            username: NASA Earthdata username (optional)
            password: NASA Earthdata password (optional)
        
        Authentication priority:
        1. Direct parameters (username/password)
        2. Environment variables (EARTHDATA_USERNAME/EARTHDATA_PASSWORD)
        3. .netrc file
        4. Interactive prompt
        """
        print("Authenticating with NASA Earthdata...")
        
        # Get credentials
        username = username or os.getenv('EARTHDATA_USERNAME')
        password = password or os.getenv('EARTHDATA_PASSWORD')
        
        # Authenticate
        try:
            if username and password:
                self.auth = earthaccess.login(strategy="environment")
                if not self.auth.authenticated:
                    # Try with explicit credentials
                    os.environ['EARTHDATA_USERNAME'] = username
                    os.environ['EARTHDATA_PASSWORD'] = password
                    self.auth = earthaccess.login(strategy="environment")
            else:
                # Will try .netrc or prompt
                self.auth = earthaccess.login(strategy="interactive")
            
            if self.auth.authenticated:
                print("✓ Authentication successful!")
            else:
                raise Exception("Authentication failed")
                
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            print("\nPlease ensure you have:")
            print("1. Created a NASA Earthdata account at https://urs.earthdata.nasa.gov/")
            print("2. Set EARTHDATA_USERNAME and EARTHDATA_PASSWORD in .env file")
            print("   OR created a ~/.netrc file with your credentials")
            raise
            
        # TEMPO product short names
        self.products = {
            'O3': 'TEMPO_O3TOT_L3',      # Total Column Ozone
            'NO2': 'TEMPO_NO2_L3',        # Nitrogen Dioxide
            'SO2': 'TEMPO_SO2_L3',        # Sulfur Dioxide
            'HCHO': 'TEMPO_HCHO_L3',      # Formaldehyde
        }
        
        self.versions = {
            'O3': 'V03',
            'NO2': 'V03',
            'SO2': 'V03',
            'HCHO': 'V03',
        }
    
    def search_data(self, product='NO2', date='2025-09-01',
        lat=38.0, lon=-96.0, daytime_only=True):
        """
        Search for TEMPO data
        
        Args:
            product: One of 'O3', 'NO2', 'SO2', 'HCHO'
            date: Date string 'YYYY-MM-DD'
            lat: Latitude of point of interest
            lon: Longitude of point of interest
            daytime_only: Filter for daytime observations only
        
        Returns:
            List of data granules
        """
        if product not in self.products:
            raise ValueError(f"Product must be one of: {list(self.products.keys())}")
        
        short_name = self.products[product]
        version = self.versions[product]
        
        date_start = f"{date} 00:00:00"
        date_end = f"{date} 23:59:59"
        
        print(f"\nSearching for {product} data on {date}...")
        print(f"Location: ({lat}, {lon})")
        print(f"Product: {short_name} {version}")
        
        try:
            results = earthaccess.search_data(
                short_name=short_name,
                version=version,
                temporal=(date_start, date_end),
                point=(lon, lat),
            )
            
            # Filter for daytime observations
            if daytime_only and results:
                daytime_results = []
                for r in results:
                    try:
                        filename = r.data_links()[0].split("/")[-1]
                        time_str = filename.split('T')[1].split('Z')[0]
                        hour = int(time_str[:2])
                        # TEMPO observes during daylight: roughly 12-22 UTC
                        if 12 <= hour <= 22:
                            daytime_results.append(r)
                    except:
                        daytime_results.append(r)
                
                print(f"Found {len(results)} total granules, {len(daytime_results)} daytime granules")
                results = daytime_results
            else:
                print(f"Found {len(results)} granules")
            
            if results:
                print("\nAvailable files (daytime observations):")
                for i, r in enumerate(results):
                    try:
                        granule_name = r.data_links()[0].split("/")[-1]
                        time_str = granule_name.split('T')[1].split('Z')[0]
                        time_formatted = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]} UTC"
                        print(f"  {i+1}. {time_formatted} - {granule_name}")
                    except:
                        print(f"  {i+1}. {r['meta']['concept-id']}")
            else:
                print("\n⚠ No data found for this date/location.")
            
            return results
            
        except Exception as e:
            print(f"Error searching data: {e}")
            return []
        
    def download_data(self, results, output_dir="tempo_data", indices=None):
        """
        Download TEMPO data files
        
        Args:
            results: Results from search_data()
            output_dir: Directory to save files
            indices: List of indices to download (e.g., [0, 1, 2]) or None for all
        
        Returns:
            List of downloaded file paths
        """
        if not results:
            print("No results to download")
            return []
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"\nOutput directory: {output_path.absolute()}")
        
        # Select specific indices or all
        if indices:
            to_download = [results[i] for i in indices if i < len(results)]
            print(f"Downloading {len(to_download)} selected file(s)...")
        else:
            to_download = results
            print(f"Downloading all {len(to_download)} file(s)...")
        
        try:
            # Download files
            files = earthaccess.download(
                to_download, 
                local_path=str(output_path),
                threads=4  # Parallel downloads
            )
            
            if files:
                print(f"\n✓ Successfully downloaded {len(files)} file(s):")
                for f in files:
                    file_path = Path(f)
                    size_mb = file_path.stat().st_size / (1024*1024)
                    print(f"  - {file_path.name} ({size_mb:.2f} MB)")
                return files
            else:
                print("✗ No files were downloaded")
                return []
                
        except Exception as e:
            print(f"✗ Error downloading files: {e}")
            print("\nTroubleshooting:")
            print("1. Check your internet connection")
            print("2. Verify NASA Earthdata authentication is working")
            print("3. Check if you have write permissions for the output directory")
            return []
    
    def read_no2_data(self, filepath):
        """
        Read NO2 data from TEMPO L3 file
        
        Returns:
            Dictionary with lat, lon, tropospheric NO2, stratospheric NO2, quality flags
        """
        print(f"Reading file: {filepath}")
        
        try:
            with nc.Dataset(filepath) as ds:
                prod = ds.groups["product"]
                
                # Read stratospheric column
                var = prod.variables["vertical_column_stratosphere"]
                strat_column = var[:]
                fv_strat = var.getncattr("_FillValue")
                
                # Read tropospheric column
                var = prod.variables["vertical_column_troposphere"]
                trop_column = var[:]
                fv_trop = var.getncattr("_FillValue")
                units = var.getncattr("units")
                
                # Read quality flag
                qf = prod.variables["main_data_quality_flag"][:]
                
                # Read coordinates
                lat = ds.variables["latitude"][:]
                lon = ds.variables["longitude"][:]
            
            print(f"✓ Successfully read data from {Path(filepath).name}")
            
            return {
                'lat': lat,
                'lon': lon,
                'trop_column': trop_column,
                'strat_column': strat_column,
                'fv_trop': fv_trop,
                'fv_strat': fv_strat,
                'quality_flag': qf,
                'units': units
            }
        except Exception as e:
            print(f"✗ Error reading file: {e}")
            raise
    
    def plot_no2(self, filepath, center_lat=38.0, center_lon=-96.0, 
                 extent=10.0, output_file=None):
        """
        Plot NO2 data from a TEMPO file
        
        Args:
            filepath: Path to downloaded TEMPO file
            center_lat: Center latitude
            center_lon: Center longitude
            extent: Map extent in degrees
            output_file: Path to save plot (optional)
        """
        print(f"\nGenerating plot...")
        data = self.read_no2_data(filepath)
        
        lat = data['lat']
        lon = data['lon']
        trop_col = data['trop_column']
        strat_col = data['strat_column']
        qf = data['quality_flag']
        units = data['units']
        
        # Subset to region of interest
        dlat = extent / 2
        dlon = extent / 2
        mask_lat = (lat > center_lat - dlat) & (lat < center_lat + dlat)
        mask_lon = (lon > center_lon - dlon) & (lon < center_lon + dlon)
        
        # Apply masks
        trop_col_roi = trop_col[0, mask_lat, :][:, mask_lon]
        strat_col_roi = strat_col[0, mask_lat, :][:, mask_lon]
        qf_roi = qf[0, mask_lat, :][:, mask_lon]
        
        # Create good data mask (high quality + positive values)
        good_mask = (qf_roi == 0) & (trop_col_roi > 0.0) & (strat_col_roi > 0.0)
        
        # Create 2D coordinate arrays
        nlat, nlon = trop_col_roi.shape
        lon_2d = np.vstack([lon[mask_lon]] * nlat)
        lat_2d = np.column_stack([lat[mask_lat]] * nlon)
        
        # Calculate total column
        total_col = trop_col_roi + strat_col_roi
        
        print(f"Valid pixels in region: {np.sum(good_mask)}")
        if np.sum(good_mask) > 0:
            print(f"NO2 range: {np.min(total_col[good_mask]):.2e} - {np.max(total_col[good_mask]):.2e} {units}")
        
        # Create plot
        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(1, 1, figsize=(10, 8), dpi=150, 
                              subplot_kw={"projection": proj})
        
        # Add map features
        ax.coastlines(linewidth=0.5)
        ax.add_feature(cfeature.STATES, linestyle=":", edgecolor="gray", linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle="-", edgecolor="gray", linewidth=0.5)
        
        # Plot data
        if np.sum(good_mask) > 0:
            scatter = ax.scatter(
                lon_2d[good_mask],
                lat_2d[good_mask],
                s=0.5,
                c=total_col[good_mask],
                vmin=0,
                vmax=5.0e16,
                cmap='jet',
                transform=proj
            )
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax, orientation='horizontal', 
                               fraction=0.046, pad=0.08)
            cbar.set_label(f'Total NO₂ Column [{units}]', fontsize=11)
        else:
            ax.text(0.5, 0.5, 'No valid data in region', 
                   transform=ax.transAxes, ha='center', va='center')
        
        # Set extent
        ax.set_extent([center_lon - dlon, center_lon + dlon, 
                      center_lat - dlat, center_lat + dlat], crs=proj)
        
        # Title
        filename = Path(filepath).name
        timestamp = filename.split('_')[3] if len(filename.split('_')) > 3 else 'Unknown'
        ax.set_title(f'TEMPO NO₂ Total Column\n{timestamp}', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"✓ Plot saved to {output_file}")
        else:
            plt.show()

    def export_to_csv(self, data, output_file='tempo_data.csv'):
        """
        Exporta los datos a un archivo CSV asegurando que todos los arrays tengan la misma longitud
        """
        import pandas as pd
        import numpy as np
        
        try:
            # Obtener las dimensiones
            trop_shape = data['trop_column'].shape
            rows = trop_shape[1]  # número de latitudes
            cols = trop_shape[2]  # número de longitudes
            
            # Crear grids de coordenadas
            lats = np.repeat(data['lat'], cols)
            lons = np.tile(data['lon'], rows)
            
            # Aplanar los arrays asegurando dimensiones consistentes
            df = pd.DataFrame({
                'latitude': lats,
                'longitude': lons,
                'tropospheric_no2': data['trop_column'][0].flatten(),
                'stratospheric_no2': data['strat_column'][0].flatten(),
                'quality_flag': data['quality_flag'][0].flatten(),
                'units': [data['units']] * len(lats)  # repetir el valor para cada fila
            })
            
            # Guardar a CSV
            df.to_csv(output_file, index=False)
            print(f"✓ Data exported successfully to {output_file}")
            print(f"  Rows: {len(df)}")
            print(f"  Columns: {len(df.columns)}")
            
        except Exception as e:
            print(f"✗ Error exporting data: {e}")
            print("Debugging info:")
            print(f"Trop shape: {data['trop_column'].shape}")
            print(f"Lat shape: {data['lat'].shape}")
            print(f"Lon shape: {data['lon'].shape}")

def main():
    """Example usage"""
    
    print("="*60)
    print("NASA TEMPO Air Quality Monitor (earthaccess)")
    print("="*60)
    
    # Authentication will automatically use .env file if present
    # Make sure you have created .env with:
    #   EARTHDATA_USERNAME=your_username
    #   EARTHDATA_PASSWORD=your_password
    
    try:
        monitor = TEMPOMonitor()
    except Exception as e:
        print(f"\nFailed to initialize monitor: {e}")
        return
    
    # Search for NO2 data
    results = monitor.search_data(
        product='NO2',
        date='2024-09-01',
        lat=38.0,
        lon=-96.0
    )
    
    if not results:
        print("\nNo data found. Try a different date or location.")
        print("TEMPO operates from August 2023 onwards.")
        print("Coverage: North America (approximately 25°N-55°N, 125°W-65°W)")
        return
    
    # Download a few files (first 2)
    files = monitor.download_data(results, indices=[0, 1])
    
    if files:
        # Plot the first file
        print("Exporting data to CSV...")
        monitor.export_to_csv(
            monitor.read_no2_data(files[0])
        )
        print("\nCreating visualization...")
        monitor.plot_no2(
            files[0],
            center_lat=38.0,
            center_lon=-96.0,
            extent=15.0,
            output_file='tempo_no2_map.png'
        )
        
    else:
        print("\n⚠ No files downloaded, skipping visualization")
    
    print("\n" + "="*60)
    print("Available products:")
    for product in monitor.products.keys():
        print(f"  - {product}")
    print("\nTo monitor other pollutants:")
    print("  results = monitor.search_data(product='O3', date='2024-09-01')")
    print("="*60)


if __name__ == "__main__":
    main()