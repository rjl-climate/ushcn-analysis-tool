"""Spatial interpolation functionality for temperature data visualization."""


import numpy as np
from scipy.interpolate import griddata


def interpolate_to_grid(
    lats: np.ndarray,
    lons: np.ndarray,
    values: np.ndarray,
    grid_resolution: float = 0.1,
    method: str = "cubic",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Interpolate scattered station data to a regular grid for contour plotting.

    Args:
        lats: Array of station latitudes
        lons: Array of station longitudes
        values: Array of values to interpolate (e.g., temperature anomalies)
        grid_resolution: Grid spacing in degrees
        method: Interpolation method ('linear', 'nearest', 'cubic')

    Returns:
        Tuple of (grid_lats, grid_lons, interpolated_values)
        - grid_lats: 2D array of grid latitudes
        - grid_lons: 2D array of grid longitudes
        - interpolated_values: 2D array of interpolated values
    """
    # Define continental US bounds with some padding
    lat_min, lat_max = 24.0, 50.0
    lon_min, lon_max = -125.0, -66.0

    # Create regular grid
    lat_grid = np.arange(lat_min, lat_max + grid_resolution, grid_resolution)
    lon_grid = np.arange(lon_min, lon_max + grid_resolution, grid_resolution)
    grid_lons, grid_lats = np.meshgrid(lon_grid, lat_grid)

    # Prepare station coordinates for interpolation
    station_points = np.column_stack((lons, lats))
    grid_points = np.column_stack((grid_lons.ravel(), grid_lats.ravel()))

    # Remove any NaN values from the input data
    valid_mask = ~np.isnan(values)
    if not np.any(valid_mask):
        raise ValueError("No valid data points for interpolation")

    clean_points = station_points[valid_mask]
    clean_values = values[valid_mask]

    # Perform interpolation
    try:
        interpolated_flat = griddata(
            clean_points, clean_values, grid_points, method=method, fill_value=np.nan
        )
        interpolated_values = interpolated_flat.reshape(grid_lats.shape)
    except Exception as e:
        raise ValueError(f"Interpolation failed: {str(e)}") from e

    return grid_lats, grid_lons, interpolated_values


def create_land_mask(grid_lats: np.ndarray, grid_lons: np.ndarray) -> np.ndarray:
    """
    Create a mask for continental US land areas to exclude interpolation over oceans.

    Args:
        grid_lats: 2D array of grid latitudes
        grid_lons: 2D array of grid longitudes

    Returns:
        Boolean mask array (True for land, False for water/non-US)
    """
    # Simple rectangular continental US bounds for now
    # TODO: Replace with actual US land boundary shapefile
    lat_min, lat_max = 24.5, 49.0
    lon_min, lon_max = -124.5, -67.0

    # Create basic rectangular mask (conservative approach)
    land_mask = (
        (grid_lats >= lat_min)
        & (grid_lats <= lat_max)
        & (grid_lons >= lon_min)
        & (grid_lons <= lon_max)
    )

    # Exclude obvious ocean areas (simplified)
    # Pacific coast exclusions
    pacific_mask = (grid_lons < -120) & (grid_lats < 35)
    # Gulf of Mexico exclusions
    gulf_mask = (grid_lons > -95) & (grid_lats < 30)
    # Atlantic coast exclusions
    atlantic_mask = (grid_lons > -80) & (grid_lats < 32) & (grid_lons > -81)

    # Apply exclusions
    land_mask &= ~pacific_mask
    land_mask &= ~gulf_mask
    land_mask &= ~atlantic_mask

    return land_mask
