"""Data loading utilities for USHCN datasets."""

from pathlib import Path
from typing import Literal

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


def load_station_locations(daily_data_path: Path) -> gpd.GeoDataFrame:
    """
    Load station locations from daily data file.

    Args:
        daily_data_path: Path to daily data parquet file

    Returns:
        GeoDataFrame with unique station locations
    """
    df_daily = pd.read_parquet(daily_data_path)
    stations = df_daily[["id", "lat", "lon"]].drop_duplicates()

    geometry = [Point(xy) for xy in zip(stations["lon"], stations["lat"])]
    gdf_stations = gpd.GeoDataFrame(stations, geometry=geometry, crs="EPSG:4326")

    # Ensure we return a GeoDataFrame by explicitly casting
    result = gdf_stations.set_index("id")
    return gpd.GeoDataFrame(result, crs=gdf_stations.crs)


def load_all_ushcn_stations(data_dir: Path) -> gpd.GeoDataFrame:
    """
    Load all USHCN station locations from monthly data files.

    The monthly data files contain all 1,218 USHCN stations, whereas the daily
    data files only contain a subset (typically around 318 stations).

    Args:
        data_dir: Directory containing USHCN data files

    Returns:
        GeoDataFrame with all USHCN station locations
    """
    # Find any monthly data file (they all have the same station list)
    monthly_files = list(data_dir.glob("ushcn-monthly-*.parquet"))

    if not monthly_files:
        raise FileNotFoundError("No monthly data files found in data directory")

    # Use the first monthly file (any will work since they have the same stations)
    df_monthly = pd.read_parquet(monthly_files[0])

    # Get unique stations with their locations
    stations = df_monthly[["id", "lat", "lon"]].drop_duplicates()

    # Create GeoDataFrame
    geometry = [Point(xy) for xy in zip(stations["lon"], stations["lat"])]
    gdf_stations = gpd.GeoDataFrame(stations, geometry=geometry, crs="EPSG:4326")

    # Set station ID as index
    result = gdf_stations.set_index("id")
    return gpd.GeoDataFrame(result, crs=gdf_stations.crs)


def load_ushcn_monthly_data(
    file_path: Path,
    data_type: Literal["raw", "tob", "fls52"] = "fls52",
    temp_metric: Literal["min", "max", "avg"] = "min",
) -> gpd.GeoDataFrame:
    """
    Load USHCN monthly data from parquet file and convert to GeoDataFrame.

    Args:
        file_path: Path to the parquet file
        data_type: Type of data to extract ("raw", "tob", or "fls52")
        temp_metric: Temperature metric to use ("min", "max", or "avg")

    Returns:
        GeoDataFrame with USHCN temperature data

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the data doesn't match expected schema
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    # Load parquet file
    df = pd.read_parquet(file_path)

    # Convert date column to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Select temperature column based on metric and data_type
    temp_col = f"{temp_metric}_{data_type}"
    if temp_col not in df.columns:
        raise ValueError(f"Temperature column '{temp_col}' not found in data")

    # Create standardized DataFrame
    result_df = pd.DataFrame(
        {
            "station_id": df["id"],
            "timestamp": df["date"],
            "temperature_celsius": df[temp_col],
            "lat": df["lat"],
            "lon": df["lon"],
        }
    )

    # Remove rows with NaN temperatures
    result_df = result_df.dropna(subset=["temperature_celsius"])

    # Create geometry from lat/lon coordinates
    geometry = [Point(xy) for xy in zip(result_df["lon"], result_df["lat"])]
    return gpd.GeoDataFrame(
        result_df.drop(["lat", "lon"], axis=1), geometry=geometry, crs="EPSG:4326"
    )


def load_ushcn_data(
    data_dir: Path,
    adjusted_type: Literal["raw", "tob", "fls52"] = "fls52",
    raw_type: Literal["raw", "tob", "fls52"] = "raw",
    load_raw: bool = False,
    temp_metric: Literal["min", "max", "avg"] = "min",
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame | None]:
    """
    Load USHCN data for analysis.

    Args:
        data_dir: Directory containing USHCN data files
        adjusted_type: Type of adjusted data to load
        raw_type: Type of raw data to load (if load_raw=True)
        load_raw: Whether to also load raw data
        temp_metric: Temperature metric to use ("min", "max", or "avg")

    Returns:
        Tuple of (adjusted_data, raw_data) where raw_data is None if load_raw=False
    """
    # Find data files
    monthly_files = {}

    for file_path in data_dir.glob("*.parquet"):
        if "monthly" in file_path.name:
            if "raw" in file_path.name:
                monthly_files["raw"] = file_path
            elif "tob" in file_path.name:
                monthly_files["tob"] = file_path
            elif "fls52" in file_path.name:
                monthly_files["fls52"] = file_path

    # Load adjusted data
    if adjusted_type not in monthly_files:
        raise FileNotFoundError(f"Monthly data file for {adjusted_type} not found")

    adjusted_data = load_ushcn_monthly_data(
        monthly_files[adjusted_type], adjusted_type, temp_metric
    )

    # Load raw data if requested
    raw_data = None
    if load_raw:
        if raw_type not in monthly_files:
            raise FileNotFoundError(f"Monthly data file for {raw_type} not found")

        raw_data = load_ushcn_monthly_data(
            monthly_files[raw_type], raw_type, temp_metric
        )

    return adjusted_data, raw_data
