"""Simple anomaly calculation algorithm."""

from typing import Any

import geopandas as gpd


def calculate(
    gdf_adjusted: gpd.GeoDataFrame,
    baseline_period: tuple[int, int],
    current_period: tuple[int, int],
    gdf_raw: gpd.GeoDataFrame | None = None,
    config: dict[str, Any] | None = None,
) -> gpd.GeoDataFrame:
    """
    Calculate simple temperature anomalies using adjusted data.

    This algorithm calculates the mean temperature difference between a current period
    and a baseline period for each station. The temperature metric (min/max/avg) is
    determined by the data loaded via the data_loader module.

    Args:
        gdf_adjusted: Adjusted USHCN temperature data (metric determined at load time)
        baseline_period: Tuple of (start_year, end_year) for baseline
        current_period: Tuple of (start_year, end_year) for current period
        gdf_raw: Optional raw USHCN temperature data (not used in this algorithm)
        config: Optional configuration parameters

    Returns:
        GeoDataFrame with columns: ['geometry', 'station_id', 'anomaly_celsius',
                                   'baseline_mean', 'current_mean', 'n_baseline', 'n_current']
    """
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

    # Calculate anomaly
    results["anomaly_celsius"] = results["current_mean"] - results["baseline_mean"]

    # Create GeoDataFrame
    return gpd.GeoDataFrame(
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
