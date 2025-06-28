"""Minimum observations anomaly calculation algorithm."""

from typing import Dict, Any, Optional
import geopandas as gpd


def calculate(
    gdf_adjusted: gpd.GeoDataFrame,
    baseline_period: tuple[int, int],
    current_period: tuple[int, int],
    gdf_raw: Optional[gpd.GeoDataFrame] = None,
    config: Optional[Dict[str, Any]] = None,
) -> gpd.GeoDataFrame:
    """
    Calculate temperature anomalies with minimum observation requirements.

    This algorithm is similar to simple_anomaly but requires a minimum number
    of observations in both baseline and current periods to include a station.

    Args:
        gdf_adjusted: Adjusted USHCN temperature data
        baseline_period: Tuple of (start_year, end_year) for baseline
        current_period: Tuple of (start_year, end_year) for current period
        gdf_raw: Optional raw USHCN temperature data (not used in this algorithm)
        config: Optional configuration parameters with 'min_observations' key

    Returns:
        GeoDataFrame with columns: ['geometry', 'station_id', 'anomaly_celsius',
                                   'baseline_mean', 'current_mean', 'n_baseline', 'n_current']
    """
    # Get minimum observations requirement from config
    min_obs = 240  # Default: 20 years * 12 months
    if config and "min_observations" in config:
        min_obs = config["min_observations"]

    # Extract years from periods
    baseline_start, baseline_end = baseline_period
    current_start, current_end = current_period

    # Filter data by time periods
    gdf_adjusted = gdf_adjusted.copy()
    gdf_adjusted["year"] = gdf_adjusted["timestamp"].dt.year

    baseline_data = gdf_adjusted[
        (gdf_adjusted["year"] >= baseline_start)
        & (gdf_adjusted["year"] <= baseline_end)
    ]

    current_data = gdf_adjusted[
        (gdf_adjusted["year"] >= current_start) & (gdf_adjusted["year"] <= current_end)
    ]

    # Calculate mean temperatures for each station in each period
    baseline_means = (
        baseline_data.groupby("station_id")
        .agg({"temperature_celsius": ["mean", "count"], "geometry": "first"})
        .reset_index()
    )

    current_means = (
        current_data.groupby("station_id")
        .agg({"temperature_celsius": ["mean", "count"]})
        .reset_index()
    )

    # Flatten column names
    baseline_means.columns = ["station_id", "baseline_mean", "n_baseline", "geometry"]
    current_means.columns = ["station_id", "current_mean", "n_current"]

    # Merge baseline and current data
    results = baseline_means.merge(current_means, on="station_id", how="inner")

    # Apply minimum observation filter
    results = results[
        (results["n_baseline"] >= min_obs) & (results["n_current"] >= min_obs)
    ]

    if len(results) == 0:
        # Return empty GeoDataFrame with correct structure
        return gpd.GeoDataFrame(
            columns=[
                "station_id",
                "anomaly_celsius",
                "baseline_mean",
                "current_mean",
                "n_baseline",
                "n_current",
                "geometry",
            ],
            crs=gdf_adjusted.crs,
        )

    # Calculate anomaly
    results["anomaly_celsius"] = results["current_mean"] - results["baseline_mean"]

    # Create GeoDataFrame
    result_gdf = gpd.GeoDataFrame(
        results[
            [
                "station_id",
                "anomaly_celsius",
                "baseline_mean",
                "current_mean",
                "n_baseline",
                "n_current",
                "geometry",
            ]
        ],
        crs=gdf_adjusted.crs,
    )

    return result_gdf
