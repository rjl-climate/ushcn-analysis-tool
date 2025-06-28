"""Adjustment impact analysis algorithm for skeptical verification."""

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
    Calculate the impact of NOAA adjustments on temperature anomalies.

    This algorithm computes anomalies using both raw and adjusted data,
    then calculates the difference to isolate the effect of adjustments.
    The temperature metric (min/max/avg) is determined by the data loaded via 
    the data_loader module and applies to both raw and adjusted datasets.

    Args:
        gdf_adjusted: Adjusted USHCN temperature data (metric determined at load time)
        baseline_period: Tuple of (start_year, end_year) for baseline
        current_period: Tuple of (start_year, end_year) for current period
        gdf_raw: Raw USHCN temperature data (REQUIRED, same metric as adjusted)
        config: Optional configuration parameters

    Returns:
        GeoDataFrame with columns: ['geometry', 'station_id', 'anomaly_raw',
                                   'anomaly_adjusted', 'adjustment_impact']
    """
    if gdf_raw is None:
        raise ValueError("Raw data is required for adjustment impact analysis")

    # Calculate anomaly using adjusted data
    anomaly_adjusted = _calculate_single_anomaly(
        gdf_adjusted, baseline_period, current_period
    )

    # Calculate anomaly using raw data
    anomaly_raw = _calculate_single_anomaly(gdf_raw, baseline_period, current_period)

    # Merge results on station_id
    results = anomaly_adjusted.merge(
        anomaly_raw[["station_id", "anomaly_celsius"]],
        on="station_id",
        how="inner",
        suffixes=("_adjusted", "_raw"),
    )

    # Calculate adjustment impact
    results["adjustment_impact"] = (
        results["anomaly_celsius_adjusted"] - results["anomaly_celsius_raw"]
    )

    # Rename columns for clarity
    results = results.rename(
        columns={
            "anomaly_celsius_adjusted": "anomaly_adjusted",
            "anomaly_celsius_raw": "anomaly_raw",
        }
    )

    # Create final GeoDataFrame
    result_gdf = gpd.GeoDataFrame(
        results[
            [
                "station_id",
                "anomaly_raw",
                "anomaly_adjusted",
                "adjustment_impact",
                "geometry",
            ]
        ],
        crs=gdf_adjusted.crs,
    )

    return result_gdf


def _calculate_single_anomaly(
    gdf: gpd.GeoDataFrame,
    baseline_period: tuple[int, int],
    current_period: tuple[int, int],
) -> gpd.GeoDataFrame:
    """
    Helper function to calculate anomaly for a single dataset.

    Args:
        gdf: Temperature data
        baseline_period: Tuple of (start_year, end_year) for baseline
        current_period: Tuple of (start_year, end_year) for current period

    Returns:
        GeoDataFrame with anomaly results
    """
    # Extract years from periods
    baseline_start, baseline_end = baseline_period
    current_start, current_end = current_period

    # Filter data by time periods
    gdf = gdf.copy()
    gdf["year"] = gdf["timestamp"].dt.year

    baseline_data = gdf[(gdf["year"] >= baseline_start) & (gdf["year"] <= baseline_end)]

    current_data = gdf[(gdf["year"] >= current_start) & (gdf["year"] <= current_end)]

    # Calculate mean temperatures for each station in each period
    baseline_means = (
        baseline_data.groupby("station_id")
        .agg({"temperature_celsius": "mean", "geometry": "first"})
        .reset_index()
    )

    current_means = (
        current_data.groupby("station_id")
        .agg({"temperature_celsius": "mean"})
        .reset_index()
    )

    # Rename columns
    baseline_means.columns = ["station_id", "baseline_mean", "geometry"]
    current_means.columns = ["station_id", "current_mean"]

    # Merge baseline and current data
    results = baseline_means.merge(current_means, on="station_id", how="inner")

    # Calculate anomaly
    results["anomaly_celsius"] = results["current_mean"] - results["baseline_mean"]

    return results
