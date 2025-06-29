"""Visualization module for USHCN temperature anomaly results."""

from pathlib import Path
from typing import Any

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial.distance import cdist
from sklearn.metrics import mean_absolute_error, mean_squared_error


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
    land_mask = land_mask & ~pacific_mask & ~gulf_mask & ~atlantic_mask

    return land_mask


def analyze_station_coverage(station_coords: np.ndarray) -> dict[str, Any]:
    """
    Analyze station coverage patterns and density.

    Args:
        station_coords: Array of [lon, lat] coordinates for stations

    Returns:
        Dictionary with coverage statistics
    """
    n_stations = len(station_coords)

    # Calculate nearest neighbor distances
    distances = cdist(station_coords, station_coords)
    # Set diagonal to infinity to exclude self-distances
    np.fill_diagonal(distances, np.inf)
    nearest_distances = np.min(distances, axis=1)

    # Calculate domain area (approximate continental US)
    lat_range = np.ptp(station_coords[:, 1])
    lon_range = np.ptp(station_coords[:, 0])
    # Rough conversion to km² (111 km per degree latitude)
    domain_area_km2 = lat_range * lon_range * (111 * 111)

    coverage_stats = {
        "total_stations": int(n_stations),
        "domain_area_km2": float(domain_area_km2),
        "station_density_per_km2": float(n_stations / domain_area_km2),
        "mean_nearest_distance_km": float(np.mean(nearest_distances) * 111),
        "median_nearest_distance_km": float(np.median(nearest_distances) * 111),
        "max_nearest_distance_km": float(np.max(nearest_distances) * 111),
        "min_nearest_distance_km": float(np.min(nearest_distances) * 111),
        "lat_range": float(lat_range),
        "lon_range": float(lon_range),
        "lat_bounds": [
            float(np.min(station_coords[:, 1])),
            float(np.max(station_coords[:, 1])),
        ],
        "lon_bounds": [
            float(np.min(station_coords[:, 0])),
            float(np.max(station_coords[:, 0])),
        ],
    }

    return coverage_stats


def create_confidence_mask(
    grid_lats: np.ndarray,
    grid_lons: np.ndarray,
    station_coords: np.ndarray,
    max_distance_km: float = 100.0,
    min_station_count: int = 2,
    confidence_radius_km: float = 100.0,
) -> np.ndarray:
    """
    Create confidence-based mask for interpolation based on station coverage.

    Args:
        grid_lats: 2D array of grid latitudes
        grid_lons: 2D array of grid longitudes
        station_coords: Array of [lon, lat] station coordinates
        max_distance_km: Maximum distance to nearest station
        min_station_count: Minimum stations within radius
        confidence_radius_km: Radius for counting nearby stations

    Returns:
        Confidence mask (0=masked, 1=low, 2=medium, 3=high confidence)
    """
    # Convert grid to coordinate pairs
    grid_points = np.column_stack([grid_lons.ravel(), grid_lats.ravel()])

    # Calculate distances to all stations (in degrees, convert to km later)
    distances_deg = cdist(grid_points, station_coords)
    distances_km = distances_deg * 111  # Rough conversion to km

    # Find nearest station distance for each grid point
    nearest_distances = np.min(distances_km, axis=1)

    # Count stations within confidence radius
    within_radius = distances_km <= confidence_radius_km
    station_counts = np.sum(within_radius, axis=1)

    # Initialize confidence mask
    confidence = np.zeros(len(grid_points), dtype=int)

    # Apply confidence criteria
    valid_distance = nearest_distances <= max_distance_km
    enough_stations = station_counts >= min_station_count

    # High confidence: close to stations with good coverage
    high_conf = valid_distance & (station_counts >= 3) & (nearest_distances <= 50)

    # Medium confidence: adequate coverage
    medium_conf = valid_distance & enough_stations & ~high_conf

    # Low confidence: minimal coverage but within distance limit
    low_conf = valid_distance & ~enough_stations

    confidence[high_conf] = 3
    confidence[medium_conf] = 2
    confidence[low_conf] = 1

    return confidence.reshape(grid_lats.shape)


def validate_interpolation(
    station_coords: np.ndarray, values: np.ndarray, method: str = "cubic"
) -> dict[str, float]:
    """
    Perform leave-one-out cross-validation for interpolation quality assessment.

    Args:
        station_coords: Array of [lon, lat] station coordinates
        values: Array of values at stations
        method: Interpolation method

    Returns:
        Dictionary with validation metrics
    """
    n_stations = len(station_coords)
    predictions = np.full(n_stations, np.nan)

    # Leave-one-out cross-validation
    for i in range(n_stations):
        # Remove one station
        train_coords = np.delete(station_coords, i, axis=0)
        train_values = np.delete(values, i)
        test_coord = station_coords[i : i + 1]

        # Skip if not enough training points
        if len(train_coords) < 4:
            continue

        try:
            # Interpolate to test point
            pred = griddata(train_coords, train_values, test_coord, method=method)
            predictions[i] = pred[0]
        except Exception:
            continue

    # Calculate metrics for valid predictions
    valid_mask = ~np.isnan(predictions)
    if np.sum(valid_mask) < 10:
        return {"error": "Insufficient valid predictions for validation", "rmse": float("nan"), "mae": float("nan"), "r2": float("nan")}

    valid_obs = values[valid_mask]
    valid_pred = predictions[valid_mask]

    rmse = np.sqrt(mean_squared_error(valid_obs, valid_pred))
    mae = mean_absolute_error(valid_obs, valid_pred)
    bias = np.mean(valid_pred - valid_obs)
    correlation = np.corrcoef(valid_obs, valid_pred)[0, 1]

    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "bias": float(bias),
        "correlation": float(correlation),
        "n_validated": int(np.sum(valid_mask)),
        "validation_fraction": float(np.sum(valid_mask) / len(values)),
    }


def generate_coverage_report(
    station_coords: np.ndarray,
    confidence_mask: np.ndarray,
    validation_metrics: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate comprehensive coverage and quality report.

    Args:
        station_coords: Array of station coordinates
        confidence_mask: Confidence mask from create_confidence_mask()
        validation_metrics: Validation results from validate_interpolation()

    Returns:
        Comprehensive coverage report
    """
    coverage_stats = analyze_station_coverage(station_coords)

    # Calculate confidence level statistics
    total_points = confidence_mask.size
    high_conf_points = np.sum(confidence_mask == 3)
    medium_conf_points = np.sum(confidence_mask == 2)
    low_conf_points = np.sum(confidence_mask == 1)
    masked_points = np.sum(confidence_mask == 0)

    confidence_stats = {
        "total_grid_points": int(total_points),
        "high_confidence_points": int(high_conf_points),
        "medium_confidence_points": int(medium_conf_points),
        "low_confidence_points": int(low_conf_points),
        "masked_points": int(masked_points),
        "high_confidence_fraction": float(high_conf_points / total_points),
        "medium_confidence_fraction": float(medium_conf_points / total_points),
        "low_confidence_fraction": float(low_conf_points / total_points),
        "valid_interpolation_fraction": float(
            (total_points - masked_points) / total_points
        ),
    }

    return {
        "station_coverage": coverage_stats,
        "confidence_levels": confidence_stats,
        "validation_metrics": validation_metrics,
        "methodology": {
            "interpolation_method": "scipy.interpolate.griddata",
            "masking_approach": "distance_and_density_based",
            "validation_method": "leave_one_out_cross_validation",
        },
    }


def plot_contour_map(
    results_gdf: gpd.GeoDataFrame,
    title: str,
    output_path: Path | None = None,
    figsize: tuple[int, int] = (12, 8),
    colormap: str = "RdBu_r",
    vmin: float | None = None,
    vmax: float | None = None,
    temp_metric: str = "Temperature",
    grid_resolution: float = 0.1,
    interpolation_method: str = "cubic",
    show_stations: bool = False,
    contour_levels: int | None = None,
) -> plt.Figure:
    """
    Create an isothermal heat contour map from temperature anomaly data.

    Args:
        results_gdf: GeoDataFrame with anomaly results
        title: Title for the plot
        output_path: Optional path to save the plot
        figsize: Figure size as (width, height)
        colormap: Matplotlib colormap name
        vmin: Minimum value for color scale
        vmax: Maximum value for color scale
        temp_metric: Temperature metric name for labeling
        grid_resolution: Grid spacing in degrees for interpolation
        interpolation_method: Interpolation method ('linear', 'nearest', 'cubic')
        show_stations: Whether to overlay station points
        contour_levels: Number of contour levels (auto if None)

    Returns:
        Matplotlib Figure object
    """
    # Determine the value column to plot
    value_col = None
    if "anomaly_celsius" in results_gdf.columns:
        value_col = "anomaly_celsius"
    elif "adjustment_impact" in results_gdf.columns:
        value_col = "adjustment_impact"
    else:
        raise ValueError("No suitable anomaly column found in results")

    # Remove stations with missing data
    clean_gdf = results_gdf.dropna(subset=[value_col]).copy()
    if len(clean_gdf) == 0:
        raise ValueError(f"No valid data found in column {value_col}")

    # Extract coordinates and values
    lats = clean_gdf.geometry.y.values
    lons = clean_gdf.geometry.x.values
    values = clean_gdf[value_col].values

    # Set color scale limits if not provided
    if vmin is None or vmax is None:
        abs_max = max(abs(values.min()), abs(values.max()))
        if vmin is None:
            vmin = -abs_max
        if vmax is None:
            vmax = abs_max

    # Interpolate to grid
    try:
        grid_lats, grid_lons, interpolated_values = interpolate_to_grid(
            lats,
            lons,
            values,
            grid_resolution=grid_resolution,
            method=interpolation_method,
        )
    except ValueError as e:
        raise ValueError(f"Interpolation failed: {str(e)}") from e

    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Convert grid to Web Mercator for basemap compatibility
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    grid_lons_web, grid_lats_web = transformer.transform(grid_lons, grid_lats)

    # Set contour levels
    if contour_levels is None:
        contour_levels = 15

    levels = np.linspace(vmin, vmax, contour_levels)

    # Create filled contours
    contourf_plot = ax.contourf(
        grid_lons_web,
        grid_lats_web,
        interpolated_values,
        levels=levels,
        cmap=colormap,
        vmin=vmin,
        vmax=vmax,
        alpha=0.8,
    )

    # Add contour lines for clarity
    ax.contour(
        grid_lons_web,
        grid_lats_web,
        interpolated_values,
        levels=levels,
        colors="black",
        linewidths=0.3,
        alpha=0.4,
    )

    # Overlay station points if requested
    if show_stations:
        # Convert station coordinates to Web Mercator
        clean_gdf_web = clean_gdf.to_crs("EPSG:3857")
        clean_gdf_web.plot(
            ax=ax,
            markersize=8,
            color="white",
            edgecolors="black",
            linewidth=0.5,
            alpha=0.7,
        )

    # Add basemap
    try:
        ctx.add_basemap(
            ax,
            crs="EPSG:3857",
            source=ctx.providers.CartoDB.Positron,
            alpha=0.7,
        )
    except Exception:
        # Fallback if basemap fails
        ax.set_facecolor("lightgray")

    # Set title and labels
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)

    # Add colorbar
    cbar = plt.colorbar(contourf_plot, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label(
        f"{temp_metric} Temperature Anomaly (°C)",
        rotation=270,
        labelpad=20,
        fontsize=12,
    )

    # Remove axis ticks for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])

    # Adjust layout
    plt.tight_layout()

    # Save if output path provided
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Contour plot saved to: {output_path}")

    return fig


def plot_enhanced_contour_map(
    results_gdf: gpd.GeoDataFrame,
    title: str,
    output_path: Path | None = None,
    figsize: tuple[int, int] = (12, 8),
    colormap: str = "RdBu_r",
    vmin: float | None = None,
    vmax: float | None = None,
    temp_metric: str = "Temperature",
    grid_resolution: float = 0.1,
    interpolation_method: str = "cubic",
    show_stations: bool = False,
    contour_levels: int | None = None,
    mask_type: str = "land",
    confidence_levels: bool = False,
    max_interpolation_distance: float = 100.0,
    min_station_count: int = 2,
    confidence_radius: float = 100.0,
    alpha_high: float = 0.8,
    alpha_medium: float = 0.6,
    show_coverage_report: bool = False,
) -> tuple[plt.Figure, dict[str, Any]]:
    """
    Create an enhanced isothermal heat contour map with scientific masking and validation.

    Args:
        results_gdf: GeoDataFrame with anomaly results
        title: Title for the plot
        output_path: Optional path to save the plot
        figsize: Figure size as (width, height)
        colormap: Matplotlib colormap name
        vmin: Minimum value for color scale
        vmax: Maximum value for color scale
        temp_metric: Temperature metric name for labeling
        grid_resolution: Grid spacing in degrees for interpolation
        interpolation_method: Interpolation method ('linear', 'nearest', 'cubic')
        show_stations: Whether to overlay station points
        contour_levels: Number of contour levels (auto if None)
        mask_type: Masking approach ('none', 'land', 'confidence')
        confidence_levels: Show confidence level variations
        max_interpolation_distance: Maximum distance from station (km)
        min_station_count: Minimum stations for interpolation
        confidence_radius: Radius for station counting (km)
        alpha_high: Opacity for high confidence areas
        alpha_medium: Opacity for medium confidence areas
        show_coverage_report: Generate station coverage statistics

    Returns:
        Tuple of (Matplotlib Figure, coverage report dict)
    """
    # Determine the value column to plot
    value_col = None
    if "anomaly_celsius" in results_gdf.columns:
        value_col = "anomaly_celsius"
    elif "adjustment_impact" in results_gdf.columns:
        value_col = "adjustment_impact"
    else:
        raise ValueError("No suitable anomaly column found in results")

    # Remove stations with missing data
    clean_gdf = results_gdf.dropna(subset=[value_col]).copy()
    if len(clean_gdf) == 0:
        raise ValueError(f"No valid data found in column {value_col}")

    # Extract coordinates and values
    lats = clean_gdf.geometry.y.values
    lons = clean_gdf.geometry.x.values
    values = clean_gdf[value_col].values
    station_coords = np.column_stack([lons, lats])

    # Set color scale limits if not provided
    if vmin is None or vmax is None:
        abs_max = max(abs(values.min()), abs(values.max()))
        if vmin is None:
            vmin = -abs_max
        if vmax is None:
            vmax = abs_max

    # Interpolate to grid
    try:
        grid_lats, grid_lons, interpolated_values = interpolate_to_grid(
            lats,
            lons,
            values,
            grid_resolution=grid_resolution,
            method=interpolation_method,
        )
    except ValueError as e:
        raise ValueError(f"Interpolation failed: {str(e)}") from e

    # Apply masking based on type
    coverage_report = {}

    if mask_type == "land":
        # Apply simple land masking
        land_mask = create_land_mask(grid_lats, grid_lons)
        interpolated_values = np.where(land_mask, interpolated_values, np.nan)

    elif mask_type == "confidence":
        # Apply confidence-based masking
        confidence_mask = create_confidence_mask(
            grid_lats,
            grid_lons,
            station_coords,
            max_distance_km=max_interpolation_distance,
            min_station_count=min_station_count,
            confidence_radius_km=confidence_radius,
        )

        # Mask out zero-confidence areas
        interpolated_values = np.where(confidence_mask > 0, interpolated_values, np.nan)

        # Generate validation and coverage report
        if show_coverage_report:
            validation_metrics = validate_interpolation(
                station_coords, values, interpolation_method
            )
            coverage_report = generate_coverage_report(
                station_coords, confidence_mask, validation_metrics
            )

    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Convert grid to Web Mercator for basemap compatibility
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    grid_lons_web, grid_lats_web = transformer.transform(grid_lons, grid_lats)

    # Set contour levels
    if contour_levels is None:
        contour_levels = 15

    levels = np.linspace(vmin, vmax, contour_levels)

    # Create contours with confidence-based alpha if applicable
    if mask_type == "confidence" and confidence_levels:
        # Plot different confidence levels with different alpha values
        high_conf_data = np.where(confidence_mask == 3, interpolated_values, np.nan)
        medium_conf_data = np.where(confidence_mask == 2, interpolated_values, np.nan)
        low_conf_data = np.where(confidence_mask == 1, interpolated_values, np.nan)

        # High confidence areas
        if not np.all(np.isnan(high_conf_data)):
            contourf_high = ax.contourf(
                grid_lons_web,
                grid_lats_web,
                high_conf_data,
                levels=levels,
                cmap=colormap,
                vmin=vmin,
                vmax=vmax,
                alpha=alpha_high,
            )

        # Medium confidence areas
        if not np.all(np.isnan(medium_conf_data)):
            ax.contourf(
                grid_lons_web,
                grid_lats_web,
                medium_conf_data,
                levels=levels,
                cmap=colormap,
                vmin=vmin,
                vmax=vmax,
                alpha=alpha_medium,
            )

        # Low confidence areas
        if not np.all(np.isnan(low_conf_data)):
            ax.contourf(
                grid_lons_web,
                grid_lats_web,
                low_conf_data,
                levels=levels,
                cmap=colormap,
                vmin=vmin,
                vmax=vmax,
                alpha=alpha_medium * 0.7,
            )

        # Use high confidence for colorbar reference
        contourf_plot = contourf_high if "contourf_high" in locals() else None
    else:
        # Standard contour plot
        contourf_plot = ax.contourf(
            grid_lons_web,
            grid_lats_web,
            interpolated_values,
            levels=levels,
            cmap=colormap,
            vmin=vmin,
            vmax=vmax,
            alpha=alpha_high,
        )

    # Add subtle contour lines
    if not np.all(np.isnan(interpolated_values)):
        ax.contour(
            grid_lons_web,
            grid_lats_web,
            interpolated_values,
            levels=levels,
            colors="black",
            linewidths=0.2,
            alpha=0.3,
        )

    # Overlay station points if requested
    if show_stations:
        clean_gdf_web = clean_gdf.to_crs("EPSG:3857")
        clean_gdf_web.plot(
            ax=ax,
            markersize=6,
            color="white",
            edgecolors="black",
            linewidth=0.4,
            alpha=0.8,
        )

    # Add basemap
    try:
        ctx.add_basemap(
            ax,
            crs="EPSG:3857",
            source=ctx.providers.CartoDB.Positron,
            alpha=0.7,
        )
    except Exception:
        ax.set_facecolor("lightgray")

    # Set title and labels
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)

    # Add colorbar
    if contourf_plot is not None:
        cbar = plt.colorbar(contourf_plot, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label(
            f"{temp_metric} Temperature Anomaly (°C)",
            rotation=270,
            labelpad=20,
            fontsize=12,
        )

    # Remove axis ticks for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])

    # Adjust layout
    plt.tight_layout()

    # Save if output path provided
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Enhanced contour plot saved to: {output_path}")

    return fig, coverage_report


def plot_heat_island_map(
    results_gdf: gpd.GeoDataFrame,
    title: str,
    output_path: Path | None = None,
    figsize: tuple[int, int] = (12, 8),
    colormap: str = "RdBu_r",
    vmin: float | None = None,
    vmax: float | None = None,
    temp_metric: str = "Temperature",
    grid_resolution: float = 0.1,
    interpolation_method: str = "cubic",
    show_stations: bool = False,
    contour_levels: int | None = None,
    mask_type: str = "land",
    confidence_levels: bool = False,
    max_interpolation_distance: float = 100.0,
    min_station_count: int = 2,
    confidence_radius: float = 100.0,
    alpha_high: float = 0.8,
    alpha_medium: float = 0.6,
    show_coverage_report: bool = False,
    # Urban heat island specific options
    show_cities: bool = True,
    city_population_threshold: int = 100000,
    show_urban_areas: bool = False,
    classify_stations: bool = True,
    urban_analysis: bool = True,
    cities_gdf: gpd.GeoDataFrame | None = None,
    urban_areas_gdf: gpd.GeoDataFrame | None = None,
) -> tuple[plt.Figure, dict[str, Any]]:
    """
    Create heat island investigation map with urban context overlays.

    Args:
        results_gdf: GeoDataFrame with anomaly results and urban classification
        title: Title for the plot
        output_path: Optional path to save the plot
        figsize: Figure size as (width, height)
        colormap: Matplotlib colormap name
        vmin: Minimum value for color scale
        vmax: Maximum value for color scale
        temp_metric: Temperature metric name for labeling
        grid_resolution: Grid spacing in degrees for interpolation
        interpolation_method: Interpolation method ('linear', 'nearest', 'cubic')
        show_stations: Whether to overlay station points
        contour_levels: Number of contour levels (auto if None)
        mask_type: Masking approach ('none', 'land', 'confidence')
        confidence_levels: Show confidence level variations
        max_interpolation_distance: Maximum distance from station (km)
        min_station_count: Minimum stations for interpolation
        confidence_radius: Radius for station counting (km)
        alpha_high: Opacity for high confidence areas
        alpha_medium: Opacity for medium confidence areas
        show_coverage_report: Generate station coverage statistics
        show_cities: Show major cities overlay
        city_population_threshold: Minimum city population to display
        show_urban_areas: Show urban area boundaries
        classify_stations: Color-code stations by urban/rural classification
        urban_analysis: Generate urban heat island statistics
        cities_gdf: GeoDataFrame with city locations (optional)
        urban_areas_gdf: GeoDataFrame with urban areas (optional)

    Returns:
        Tuple of (Matplotlib Figure, enhanced coverage report with urban analysis)
    """
    # Start with enhanced contour map
    fig, coverage_report = plot_enhanced_contour_map(
        results_gdf,
        title,
        None,  # Don't save yet, we'll add urban overlays first
        figsize,
        colormap,
        vmin,
        vmax,
        temp_metric,
        grid_resolution,
        interpolation_method,
        False,  # Don't show stations yet
        contour_levels,
        mask_type,
        confidence_levels,
        max_interpolation_distance,
        min_station_count,
        confidence_radius,
        alpha_high,
        alpha_medium,
        show_coverage_report,
    )

    ax = fig.gca()

    # Urban context overlays
    urban_analysis_results = {}

    # Show urban areas if requested
    if show_urban_areas and urban_areas_gdf is not None and len(urban_areas_gdf) > 0:
        try:
            urban_areas_web = urban_areas_gdf.to_crs("EPSG:3857")
            urban_areas_web.plot(
                ax=ax,
                facecolor="none",
                edgecolor="gray",
                linewidth=1.0,
                alpha=0.6,
                linestyle="--",
            )
        except Exception as e:
            print(f"Warning: Could not display urban areas: {e}")

    # Show cities if requested
    if show_cities and cities_gdf is not None and len(cities_gdf) > 0:
        try:
            # Filter cities by population threshold
            large_cities = cities_gdf[
                cities_gdf["population"] >= city_population_threshold
            ].copy()

            if len(large_cities) > 0:
                cities_web = large_cities.to_crs("EPSG:3857")

                # Scale marker size by population
                max_pop = large_cities["population"].max()
                min_pop = large_cities["population"].min()

                # Normalize to marker size range (20-200)
                if max_pop > min_pop:
                    normalized_pop = (large_cities["population"] - min_pop) / (
                        max_pop - min_pop
                    )
                    marker_sizes = 20 + normalized_pop * 180
                else:
                    marker_sizes = [50] * len(large_cities)

                # Plot cities
                cities_web.plot(
                    ax=ax,
                    markersize=marker_sizes,
                    color="green",
                    edgecolors="darkgreen",
                    linewidth=1.0,
                    alpha=0.8,
                    marker="o",
                )

                # Add city labels for largest cities (top 10)
                if len(large_cities) <= 20:  # Only label if not too many cities
                    for _, city in large_cities.iterrows():
                        city_web = cities_web[cities_web.index == city.name]
                        if len(city_web) > 0:
                            point = city_web.geometry.iloc[0]
                            ax.annotate(
                                city["city_name"],
                                xy=(point.x, point.y),
                                xytext=(5, 5),
                                textcoords="offset points",
                                fontsize=8,
                                color="darkgreen",
                                weight="bold",
                                bbox=dict(
                                    boxstyle="round,pad=0.2",
                                    facecolor="white",
                                    alpha=0.7,
                                ),
                            )
        except Exception as e:
            print(f"Warning: Could not display cities: {e}")

    # Show stations with urban classification if requested
    if show_stations or classify_stations:
        try:
            clean_gdf = results_gdf.dropna(subset=["geometry"]).copy()

            if classify_stations and "urban_classification" in clean_gdf.columns:
                # Color-code stations by classification
                classification_colors = {
                    "urban_core": "red",
                    "urban": "orange",
                    "suburban": "yellow",
                    "rural": "blue",
                }

                clean_gdf_web = clean_gdf.to_crs("EPSG:3857")

                for classification, color in classification_colors.items():
                    class_stations = clean_gdf_web[
                        clean_gdf_web["urban_classification"] == classification
                    ]
                    if len(class_stations) > 0:
                        class_stations.plot(
                            ax=ax,
                            markersize=15,
                            color=color,
                            edgecolors="black",
                            linewidth=0.5,
                            alpha=0.8,
                            label=f"{classification.replace('_', ' ').title()} ({len(class_stations)})",
                        )

                # Add legend for station classification
                ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.0), fontsize=9)

            elif show_stations:
                # Standard station display
                clean_gdf_web = clean_gdf.to_crs("EPSG:3857")
                clean_gdf_web.plot(
                    ax=ax,
                    markersize=8,
                    color="white",
                    edgecolors="black",
                    linewidth=0.4,
                    alpha=0.8,
                )
        except Exception as e:
            print(f"Warning: Could not display stations: {e}")

    # Perform urban heat island analysis if requested
    if urban_analysis and "urban_classification" in results_gdf.columns:
        try:
            from .analysis.heat_island import calculate_urban_rural_statistics

            urban_stats = calculate_urban_rural_statistics(results_gdf)
            urban_analysis_results = urban_stats

            # Add UHII annotation to plot if significant
            if "urban_vs_rural_comparison" in urban_stats:
                comparison = urban_stats["urban_vs_rural_comparison"]
                if "urban_heat_island_intensity" in comparison:
                    uhii = comparison["urban_heat_island_intensity"]
                    significance = comparison.get("statistical_significance", "unknown")

                    # Add text box with UHII information
                    uhii_text = (
                        f"Urban Heat Island Intensity: {uhii:.2f}°C\n({significance})"
                    )
                    ax.text(
                        0.02,
                        0.98,
                        uhii_text,
                        transform=ax.transAxes,
                        verticalalignment="top",
                        bbox=dict(
                            boxstyle="round,pad=0.5", facecolor="white", alpha=0.8
                        ),
                        fontsize=10,
                        weight="bold",
                    )
        except Exception as e:
            print(f"Warning: Could not perform urban analysis: {e}")
            urban_analysis_results = {"error": str(e)}

    # Enhanced coverage report with urban analysis
    if urban_analysis_results:
        coverage_report["urban_heat_island_analysis"] = urban_analysis_results

    # Save if output path provided
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Heat island map saved to: {output_path}")

    return fig, coverage_report


def plot_clean_ushcn_network(
    stations_gdf: gpd.GeoDataFrame,
    cities_gdf: gpd.GeoDataFrame | None = None,
    title: str = "USHCN Station Network and Urban Context",
    output_path: Path | None = None,
    figsize: tuple[int, int] = (14, 9),
    city_population_threshold: int = 100000,
    attribution: str = "Richard Lyon richlyon@fastmail.com",
) -> plt.Figure:
    """
    Create a clean academic visualization of the USHCN station network.

    Following Tufte quantitative display principles:
    - Maximize data-ink ratio
    - Remove chartjunk
    - Clear, informative visualization
    - Appropriate use of color and symbols

    Args:
        stations_gdf: GeoDataFrame with USHCN stations and urban classification
        cities_gdf: Optional GeoDataFrame with major US cities
        title: Plot title
        output_path: Optional path to save the plot
        figsize: Figure size as (width, height)
        city_population_threshold: Minimum city population to display
        attribution: Attribution text for the plot

    Returns:
        Matplotlib Figure object
    """
    # Create figure with clean aesthetics
    fig, ax = plt.subplots(1, 1, figsize=figsize, facecolor="white")
    ax.set_facecolor("white")

    # Remove stations with missing data
    clean_stations = stations_gdf.dropna(subset=["geometry"]).copy()

    # Convert to Web Mercator for display
    stations_web = clean_stations.to_crs("EPSG:3857")

    # Define station colors and labels
    station_colors = {
        "urban_core": {"color": "red", "label": "Urban Core", "size": 20},
        "urban": {
            "color": "red",
            "label": "Urban Core",
            "size": 20,
        },  # Combine with urban_core
        "urban_fringe": {
            "color": "red",
            "label": "Urban Core",
            "size": 20,
        },  # Combine with urban_core
        "suburban": {"color": "gold", "label": "Suburban", "size": 15},
        "rural": {"color": "blue", "label": "Rural", "size": 12},
    }

    # Plot stations by classification
    station_counts: dict[str, int] = {}
    total_plotted = 0

    if "urban_classification" in clean_stations.columns:
        for classification, style in station_colors.items():
            class_stations = stations_web[
                stations_web["urban_classification"] == classification
            ]
            if len(class_stations) > 0:
                # Combine urban, urban_core, and urban_fringe into one category
                if classification in ["urban", "urban_core", "urban_fringe"]:
                    if "Urban Core" not in station_counts:
                        station_counts["Urban Core"] = 0
                    station_counts["Urban Core"] += len(class_stations)
                    label_name = "Urban Core"
                else:
                    station_counts[str(style["label"])] = len(class_stations)

                class_stations.plot(
                    ax=ax,
                    markersize=style["size"],
                    color=style["color"],
                    edgecolors="white",
                    linewidth=0.5,
                    alpha=0.8,
                    zorder=3,
                )
                total_plotted += len(class_stations)
    else:
        # Plot all stations uniformly if no classification
        stations_web.plot(
            ax=ax,
            markersize=12,
            color="darkblue",
            edgecolors="white",
            linewidth=0.5,
            alpha=0.8,
            zorder=3,
        )
        station_counts["USHCN Stations"] = len(stations_web)
        total_plotted = len(stations_web)

    # Plot cities if provided
    if cities_gdf is not None and len(cities_gdf) > 0:
        try:
            # Filter cities by population threshold
            large_cities = cities_gdf[
                cities_gdf["population"] >= city_population_threshold
            ].copy()

            if len(large_cities) > 0:
                cities_web = large_cities.to_crs("EPSG:3857")

                # Scale marker size by population (subtle scaling)
                max_pop = large_cities["population"].max()
                min_pop = large_cities["population"].min()

                if max_pop > min_pop:
                    normalized_pop = (large_cities["population"] - min_pop) / (
                        max_pop - min_pop
                    )
                    marker_sizes = 30 + normalized_pop * 50  # Size range 30-80
                else:
                    marker_sizes = [40] * len(large_cities)

                # Plot cities
                cities_web.plot(
                    ax=ax,
                    markersize=marker_sizes,
                    color="green",
                    edgecolors="darkgreen",
                    linewidth=0.8,
                    alpha=0.7,
                    marker="o",
                    zorder=2,
                )

                station_counts[
                    f"Major Cities (≥{city_population_threshold // 1000}k)"
                ] = len(large_cities)
        except Exception as e:
            print(f"Warning: Could not display cities: {e}")

    # Add subtle basemap (state boundaries)
    try:
        ctx.add_basemap(
            ax,
            crs="EPSG:3857",
            source=ctx.providers.CartoDB.PositronNoLabels,
            alpha=0.5,
            zorder=1,
        )
    except Exception:
        # Fallback: simple background
        ax.set_facecolor("#f8f8f8")

    # Set geographic extent to continental US
    # Convert bounds to Web Mercator
    from pyproj import Transformer

    # Use actual data bounds with some padding
    station_bounds = stations_web.total_bounds  # [minx, miny, maxx, maxy]
    padding = 200000  # 200km padding in meters

    ax.set_xlim(station_bounds[0] - padding, station_bounds[2] + padding)
    ax.set_ylim(station_bounds[1] - padding, station_bounds[3] + padding)

    # Clean title
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)

    # Create legend with counts
    legend_labels = []
    legend_colors = []
    legend_sizes = []

    if "urban_classification" in clean_stations.columns:
        # Add station classifications
        for classification in ["Urban Core", "Suburban", "Rural"]:
            if classification in station_counts:
                count = station_counts[classification]
                legend_labels.append(f"{classification} ({count})")
                if classification == "Urban Core":
                    legend_colors.append("red")
                    legend_sizes.append(20)
                elif classification == "Suburban":
                    legend_colors.append("gold")
                    legend_sizes.append(15)
                else:  # Rural
                    legend_colors.append("blue")
                    legend_sizes.append(12)

    # Add cities to legend
    if (
        cities_gdf is not None
        and f"Major Cities (≥{city_population_threshold // 1000}k)" in station_counts
    ):
        count = station_counts[f"Major Cities (≥{city_population_threshold // 1000}k)"]
        legend_labels.append(
            f"Major Cities (≥{city_population_threshold // 1000}k) ({count})"
        )
        legend_colors.append("green")
        legend_sizes.append(40)

    # Create custom legend
    legend_elements = []
    for label, color, size in zip(legend_labels, legend_colors, legend_sizes):
        legend_elements.append(
            plt.scatter(
                [],
                [],
                s=size,
                c=color,
                edgecolors="white",
                linewidth=0.5,
                alpha=0.8,
                label=label,
            )
        )

    if legend_elements:
        legend = ax.legend(
            handles=legend_elements,
            loc="upper right",
            bbox_to_anchor=(0.98, 0.98),
            fontsize=11,
            frameon=True,
            fancybox=False,
            shadow=False,
            framealpha=0.9,
            edgecolor="gray",
            facecolor="white",
        )
        legend.get_frame().set_linewidth(0.5)

    # Remove axis ticks and labels for clean look
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")

    # Remove axis spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Add attribution in light gray at bottom right
    ax.text(
        0.99,
        0.01,
        attribution,
        transform=ax.transAxes,
        fontsize=9,
        color="lightgray",
        ha="right",
        va="bottom",
        style="italic",
    )

    # Tight layout
    plt.tight_layout()

    # Print debugging info
    print(
        f"Debug: Total stations plotted: {total_plotted} out of {len(clean_stations)} loaded"
    )

    # Save if output path provided
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
        print(f"Clean USHCN network plot saved to: {output_path}")

    return fig


def plot_urban_rural_comparison(
    results_gdf: gpd.GeoDataFrame,
    heat_island_stats: dict[str, Any],
    output_path: Path | None = None,
    figsize: tuple[int, int] = (10, 6),
) -> plt.Figure:
    """
    Create urban vs rural temperature comparison plots.

    Args:
        results_gdf: GeoDataFrame with anomaly results and urban classification
        heat_island_stats: Results from calculate_urban_rural_statistics
        output_path: Optional path to save the plot
        figsize: Figure size as (width, height)

    Returns:
        Matplotlib Figure object
    """
    # Determine anomaly column
    anomaly_col = None
    if "anomaly_celsius" in results_gdf.columns:
        anomaly_col = "anomaly_celsius"
    elif "adjustment_impact" in results_gdf.columns:
        anomaly_col = "adjustment_impact"
    else:
        raise ValueError("No suitable anomaly column found")

    # Clean data
    clean_data = results_gdf.dropna(subset=[anomaly_col, "urban_classification"]).copy()

    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Box plot comparison
    urban_categories = ["urban_core", "urban", "suburban", "rural"]
    plot_data = []
    plot_labels = []

    for category in urban_categories:
        category_data = clean_data[clean_data["urban_classification"] == category][
            anomaly_col
        ]
        if len(category_data) > 0:
            plot_data.append(category_data.values)
            plot_labels.append(
                f"{category.replace('_', ' ').title()}\n(n={len(category_data)})"
            )

    if plot_data:
        bp = ax1.boxplot(plot_data, labels=plot_labels, patch_artist=True)

        # Color the boxes
        colors = ["red", "orange", "yellow", "blue"]
        for patch, color in zip(bp["boxes"], colors[: len(bp["boxes"])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

    ax1.set_title("Temperature Anomalies by Urban Classification")
    ax1.set_ylabel("Temperature Anomaly (°C)")
    ax1.grid(True, alpha=0.3)

    # Histogram comparison (urban vs rural)
    urban_data = clean_data[
        clean_data["urban_classification"].isin(["urban_core", "urban"])
    ][anomaly_col]
    rural_data = clean_data[clean_data["urban_classification"] == "rural"][anomaly_col]

    if len(urban_data) > 0 and len(rural_data) > 0:
        bins = np.linspace(
            min(urban_data.min(), rural_data.min()),
            max(urban_data.max(), rural_data.max()),
            20,
        )

        ax2.hist(
            urban_data,
            bins=bins,
            alpha=0.7,
            label=f"Urban (n={len(urban_data)})",
            color="red",
            density=True,
        )
        ax2.hist(
            rural_data,
            bins=bins,
            alpha=0.7,
            label=f"Rural (n={len(rural_data)})",
            color="blue",
            density=True,
        )

        # Add vertical lines for means
        ax2.axvline(
            urban_data.mean(),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Urban mean: {urban_data.mean():.2f}°C",
        )
        ax2.axvline(
            rural_data.mean(),
            color="blue",
            linestyle="--",
            linewidth=2,
            label=f"Rural mean: {rural_data.mean():.2f}°C",
        )

    ax2.set_title("Urban vs Rural Temperature Distribution")
    ax2.set_xlabel("Temperature Anomaly (°C)")
    ax2.set_ylabel("Density")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Add statistics text
    if "urban_vs_rural_comparison" in heat_island_stats:
        comparison = heat_island_stats["urban_vs_rural_comparison"]
        if "urban_heat_island_intensity" in comparison:
            uhii = comparison["urban_heat_island_intensity"]
            significance = comparison.get("statistical_significance", "unknown")
            p_value = comparison.get("t_test_p_value", np.nan)

            stats_text = f"UHII: {uhii:.2f}°C\np-value: {p_value:.3f}\n{significance}"
            fig.text(
                0.02,
                0.98,
                stats_text,
                verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8),
                fontsize=10,
            )

    plt.tight_layout()

    # Save if output path provided
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Urban/rural comparison plot saved to: {output_path}")

    return fig


def plot_anomaly_map(
    results_gdf: gpd.GeoDataFrame,
    title: str,
    output_path: Path | None = None,
    figsize: tuple[int, int] = (12, 8),
    colormap: str = "RdBu_r",
    vmin: float | None = None,
    vmax: float | None = None,
    temp_metric: str = "Temperature",
) -> plt.Figure:
    """
    Create a map visualization of temperature anomalies.

    Args:
        results_gdf: GeoDataFrame with anomaly results
        title: Title for the plot
        output_path: Optional path to save the plot
        figsize: Figure size as (width, height)
        colormap: Matplotlib colormap name
        vmin: Minimum value for color scale
        vmax: Maximum value for color scale

    Returns:
        Matplotlib Figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Determine the value column to plot
    value_col = None
    if "anomaly_celsius" in results_gdf.columns:
        value_col = "anomaly_celsius"
    elif "adjustment_impact" in results_gdf.columns:
        value_col = "adjustment_impact"
    else:
        raise ValueError("No suitable anomaly column found in results")

    # Set color scale limits if not provided
    if vmin is None or vmax is None:
        values = results_gdf[value_col].dropna()
        if len(values) > 0:
            abs_max = max(abs(values.min()), abs(values.max()))
            if vmin is None:
                vmin = -abs_max
            if vmax is None:
                vmax = abs_max
        else:
            vmin, vmax = -1, 1

    # Convert to Web Mercator for basemap compatibility
    results_web_mercator = results_gdf.to_crs("EPSG:3857")

    # Plot the points
    results_web_mercator.plot(
        column=value_col,
        ax=ax,
        cmap=colormap,
        vmin=vmin,
        vmax=vmax,
        markersize=50,
        alpha=0.8,
        edgecolors="black",
        linewidth=0.5,
    )

    # Add basemap
    try:
        ctx.add_basemap(
            ax,
            crs=results_web_mercator.crs,
            source=ctx.providers.CartoDB.Positron,
            alpha=0.7,
        )
    except Exception:
        # Fallback if basemap fails
        ax.set_facecolor("lightgray")

    # Set title and labels
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)

    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label(
        f"{temp_metric} Temperature Anomaly (°C)",
        rotation=270,
        labelpad=20,
        fontsize=12,
    )

    # Remove axis ticks for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])

    # Adjust layout
    plt.tight_layout()

    # Save if output path provided
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {output_path}")

    return fig


def plot_comparison_maps(
    results_gdf: gpd.GeoDataFrame,
    title_prefix: str,
    output_dir: Path | None = None,
    figsize: tuple[int, int] = (18, 6),
    temp_metric: str = "Temperature",
) -> plt.Figure:
    """
    Create side-by-side comparison maps for adjustment impact analysis.

    Args:
        results_gdf: GeoDataFrame with adjustment impact results
        title_prefix: Prefix for plot titles
        output_dir: Optional directory to save plots
        figsize: Figure size as (width, height)

    Returns:
        Matplotlib Figure object
    """
    # Verify required columns exist
    required_cols = ["anomaly_raw", "anomaly_adjusted", "adjustment_impact"]
    missing_cols = [col for col in required_cols if col not in results_gdf.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Create figure with three subplots
    fig, axes = plt.subplots(1, 3, figsize=figsize)

    # Convert to Web Mercator for basemap compatibility
    results_web_mercator = results_gdf.to_crs("EPSG:3857")

    # Determine common color scale for anomaly plots
    all_anomalies = np.concatenate(
        [results_gdf["anomaly_raw"].dropna(), results_gdf["anomaly_adjusted"].dropna()]
    )
    if len(all_anomalies) > 0:
        abs_max_anomaly = max(abs(all_anomalies.min()), abs(all_anomalies.max()))
        anomaly_vmin, anomaly_vmax = -abs_max_anomaly, abs_max_anomaly
    else:
        anomaly_vmin, anomaly_vmax = -1, 1

    # Determine color scale for adjustment impact
    impacts = results_gdf["adjustment_impact"].dropna()
    if len(impacts) > 0:
        abs_max_impact = max(abs(impacts.min()), abs(impacts.max()))
        impact_vmin, impact_vmax = -abs_max_impact, abs_max_impact
    else:
        impact_vmin, impact_vmax = -0.5, 0.5

    # Plot configurations
    plot_configs = [
        {
            "column": "anomaly_raw",
            "title": f"{title_prefix} - Raw Data Anomaly",
            "vmin": anomaly_vmin,
            "vmax": anomaly_vmax,
            "cmap": "RdBu_r",
        },
        {
            "column": "anomaly_adjusted",
            "title": f"{title_prefix} - Adjusted Data Anomaly",
            "vmin": anomaly_vmin,
            "vmax": anomaly_vmax,
            "cmap": "RdBu_r",
        },
        {
            "column": "adjustment_impact",
            "title": f"{title_prefix} - Adjustment Impact",
            "vmin": impact_vmin,
            "vmax": impact_vmax,
            "cmap": "RdYlBu_r",
        },
    ]

    # Create each subplot
    for i, config in enumerate(plot_configs):
        ax = axes[i]

        # Plot the points
        results_web_mercator.plot(
            column=config["column"],
            ax=ax,
            cmap=config["cmap"],
            vmin=config["vmin"],
            vmax=config["vmax"],
            markersize=30,
            alpha=0.8,
            edgecolors="black",
            linewidth=0.3,
        )

        # Add basemap
        try:
            ctx.add_basemap(
                ax,
                crs=results_web_mercator.crs,
                source=ctx.providers.CartoDB.Positron,
                alpha=0.7,
            )
        except Exception:
            ax.set_facecolor("lightgray")

        # Set title and remove ticks
        ax.set_title(config["title"], fontsize=12, fontweight="bold", pad=10)
        ax.set_xticks([])
        ax.set_yticks([])

        # Add colorbar
        sm = plt.cm.ScalarMappable(
            cmap=config["cmap"],
            norm=plt.Normalize(vmin=config["vmin"], vmax=config["vmax"]),
        )
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
        cbar.set_label("°C", rotation=0, labelpad=10, fontsize=10)

    # Adjust layout
    plt.tight_layout()

    # Save if output directory provided
    if output_dir:
        output_path = (
            output_dir / f"{title_prefix.lower().replace(' ', '_')}_comparison.png"
        )
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Comparison plot saved to: {output_path}")

    return fig


def create_summary_statistics(results_gdf: gpd.GeoDataFrame) -> dict:
    """
    Generate summary statistics for anomaly results.

    Args:
        results_gdf: GeoDataFrame with anomaly results

    Returns:
        Dictionary with summary statistics
    """
    stats = {
        "total_stations": len(results_gdf),
        "stations_with_data": results_gdf.dropna().shape[0],
    }

    # Add statistics for each numeric column
    numeric_cols = results_gdf.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in results_gdf.columns:
            values = results_gdf[col].dropna()
            if len(values) > 0:
                stats[f"{col}_mean"] = float(values.mean())
                stats[f"{col}_std"] = float(values.std())
                stats[f"{col}_min"] = float(values.min())
                stats[f"{col}_max"] = float(values.max())
                stats[f"{col}_median"] = float(values.median())

    return stats
