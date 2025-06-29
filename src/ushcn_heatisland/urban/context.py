"""Simplified urban context management with static database."""

from pathlib import Path
from typing import Any
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from shapely.geometry import Point


class UrbanContextManager:
    """Manages urban context data for heat island analysis using static database."""

    def __init__(self, static_cities_path: Path | None = None):
        """
        Initialize urban context manager with static cities database.

        Args:
            static_cities_path: Path to static cities CSV file
        """
        if static_cities_path is None:
            static_cities_path = (
                Path(__file__).parent.parent.parent.parent
                / "data"
                / "cities"
                / "us_cities_static.csv"
            )

        self.static_cities_path = Path(static_cities_path)

        # Define 4-level classification thresholds and population criteria
        self.classification_config = {
            "urban_core": {
                "max_distance_km": 25.0,
                "min_city_population": 250000,
                "description": "Major city centers (<25km from 250k+ cities)",
            },
            "urban_fringe": {
                "max_distance_km": 50.0,
                "min_city_population": 100000,
                "description": "Urban fringes (25-50km from 100k+ cities)",
            },
            "suburban": {
                "max_distance_km": 100.0,
                "min_city_population": 50000,
                "description": "Suburban areas (50-100km from 50k+ cities)",
            },
            # rural: >100km from any city with 50k+ population
        }

    def load_cities_data(self, min_population: int = 50000) -> gpd.GeoDataFrame:
        """
        Load US cities data from static database.

        Args:
            min_population: Minimum city population to include

        Returns:
            GeoDataFrame with city points, names, and population
        """
        if not self.static_cities_path.exists():
            raise FileNotFoundError(
                f"Static cities database not found: {self.static_cities_path}"
            )

        # Load static cities database
        cities_df = pd.read_csv(self.static_cities_path)

        # Filter by minimum population
        cities_df = cities_df[cities_df["population"] >= min_population].copy()

        if len(cities_df) == 0:
            raise ValueError(f"No cities found with population >= {min_population:,}")

        # Create geometry from coordinates
        geometry = [
            Point(lon, lat)
            for lon, lat in zip(cities_df["longitude"], cities_df["latitude"])
        ]
        return gpd.GeoDataFrame(cities_df, geometry=geometry, crs="EPSG:4326")

    def load_urban_areas(self, min_population: int = 100000) -> gpd.GeoDataFrame:
        """
        Create simplified urban areas as buffers around major cities.

        Args:
            min_population: Minimum population for urban area creation

        Returns:
            GeoDataFrame with urban area boundaries
        """
        cities = self.load_cities_data(min_population=min_population)

        if len(cities) == 0:
            return gpd.GeoDataFrame(
                {"urban_area_name": [], "geometry": []}, crs="EPSG:4326"
            )

        # Create approximate urban areas as buffers around major cities
        # Buffer size based on city population (roughly)
        cities["buffer_km"] = np.sqrt(cities["population"] / 1000) * 2  # Rough scaling

        # Convert to projected CRS for buffering (Albers Equal Area for CONUS)
        cities_proj = cities.to_crs("EPSG:5070")  # Albers Equal Area Conic

        # Create buffers (buffer_km converted to meters)
        cities_proj["geometry"] = cities_proj.apply(
            lambda row: row["geometry"].buffer(row["buffer_km"] * 1000), axis=1
        )

        # Convert back to WGS84
        urban_areas = cities_proj.to_crs("EPSG:4326")

        # Rename and select columns
        urban_areas = urban_areas.rename(columns={"city_name": "urban_area_name"})
        return urban_areas[["urban_area_name", "geometry"]].copy()

    def classify_stations_urban_rural(
        self,
        stations_gdf: gpd.GeoDataFrame,
        cities_gdf: gpd.GeoDataFrame | None = None,
        urban_areas_gdf: gpd.GeoDataFrame | None = None,
        use_4_level_hierarchy: bool = True,
    ) -> gpd.GeoDataFrame:
        """
        Classify weather stations using 4-level urban hierarchy.

        Classification levels:
        - urban_core: <25km from cities with 250k+ population
        - urban_fringe: 25-50km from cities with 100k+ population
        - suburban: 50-100km from cities with 50k+ population
        - rural: >100km from any significant city

        Args:
            stations_gdf: GeoDataFrame with weather station locations
            cities_gdf: GeoDataFrame with city locations (loaded if None)
            urban_areas_gdf: GeoDataFrame with urban areas (loaded if None)
            use_4_level_hierarchy: Use 4-level vs simplified 3-level classification

        Returns:
            Enhanced GeoDataFrame with urban classification columns
        """
        # Load urban context data if not provided
        if cities_gdf is None:
            # Load comprehensive cities data with lower threshold for better classification
            cities_gdf = self.load_cities_data(min_population=50000)
        if urban_areas_gdf is None:
            urban_areas_gdf = self.load_urban_areas()

        # Make a copy to avoid modifying original
        classified_stations = stations_gdf.copy()

        # Initialize classification columns
        classified_stations["urban_classification"] = "rural"
        classified_stations["distance_to_nearest_city_km"] = np.nan
        classified_stations["nearest_city_name"] = ""
        classified_stations["nearest_city_population"] = np.nan
        classified_stations["within_urban_area"] = False

        if len(cities_gdf) == 0:
            warnings.warn("No cities data available for classification", stacklevel=2)
            return classified_stations

        # Ensure both datasets are in WGS84
        if stations_gdf.crs is None:
            stations_gdf = stations_gdf.set_crs("EPSG:4326")
        elif stations_gdf.crs != "EPSG:4326":
            stations_gdf = stations_gdf.to_crs("EPSG:4326")

        if cities_gdf.crs is None:
            cities_gdf = cities_gdf.set_crs("EPSG:4326")
        elif cities_gdf.crs != "EPSG:4326":
            cities_gdf = cities_gdf.to_crs("EPSG:4326")

        # Calculate distances to all cities for each station
        station_coords = np.array([[pt.x, pt.y] for pt in stations_gdf.geometry])
        city_coords = np.array([[pt.x, pt.y] for pt in cities_gdf.geometry])

        # Check if we have valid coordinates for both stations and cities
        if len(station_coords) == 0 or len(city_coords) == 0:
            warnings.warn("No valid stations or cities for classification", stacklevel=2)
            return classified_stations

        if len(city_coords) > 0:
            # Calculate distance matrix (in degrees, then convert to km)
            distances_deg = cdist(station_coords, city_coords)
            distances_km = distances_deg * 111  # Rough conversion

            # Find nearest city for each station
            nearest_city_indices = np.argmin(distances_km, axis=1)
            nearest_distances = np.min(distances_km, axis=1)

            # Populate nearest city information
            classified_stations["distance_to_nearest_city_km"] = nearest_distances
            classified_stations["nearest_city_name"] = cities_gdf.iloc[
                nearest_city_indices
            ]["city_name"].values
            classified_stations["nearest_city_population"] = cities_gdf.iloc[
                nearest_city_indices
            ]["population"].values

            # Apply classification logic
            if use_4_level_hierarchy:
                self._apply_4_level_classification(
                    classified_stations, cities_gdf, distances_km, nearest_city_indices
                )
            else:
                # Legacy 3-level classification
                urban_mask = nearest_distances <= 50.0
                suburban_mask = (nearest_distances > 50.0) & (
                    nearest_distances <= 100.0
                )

                classified_stations.loc[urban_mask, "urban_classification"] = "urban"
                classified_stations.loc[suburban_mask, "urban_classification"] = (
                    "suburban"
                )

        # Check containment within urban areas
        if len(urban_areas_gdf) > 0:
            try:
                # Spatial join to check if stations are within urban areas
                stations_with_urban = gpd.sjoin(
                    classified_stations, urban_areas_gdf, how="left", predicate="within"
                )

                # Mark stations within urban areas
                within_urban = ~stations_with_urban["urban_area_name"].isna()
                classified_stations["within_urban_area"] = within_urban.values

                # For 4-level classification, urban areas can upgrade suburban to urban_fringe
                if use_4_level_hierarchy:
                    urban_area_mask = classified_stations["within_urban_area"]
                    suburban_in_urban = (
                        classified_stations["urban_classification"] == "suburban"
                    ) & urban_area_mask
                    classified_stations.loc[
                        suburban_in_urban, "urban_classification"
                    ] = "urban_fringe"
                else:
                    # Legacy behavior: upgrade to urban_core
                    urban_area_mask = classified_stations["within_urban_area"]
                    classified_stations.loc[urban_area_mask, "urban_classification"] = (
                        "urban_core"
                    )

            except Exception as e:
                warnings.warn(f"Could not perform urban area classification: {str(e)}", stacklevel=2)

        return classified_stations

    def _apply_4_level_classification(
        self,
        classified_stations: gpd.GeoDataFrame,
        cities_gdf: gpd.GeoDataFrame,
        distances_km: np.ndarray,
        nearest_city_indices: np.ndarray,
    ) -> None:
        """
        Apply 4-level urban classification hierarchy.

        Args:
            classified_stations: Stations dataframe to modify
            cities_gdf: Cities data with population information
            distances_km: Distance matrix (stations x cities)
            nearest_city_indices: Index of nearest city for each station
        """
        n_stations = len(classified_stations)

        for i in range(n_stations):
            station_distances = distances_km[
                i, :
            ]  # Distances from this station to all cities

            # Check each classification level in order of precedence
            classification = "rural"  # Default

            # 1. Urban Core: <25km from 250k+ population cities
            major_cities_mask = cities_gdf["population"] >= 250000
            if np.any(major_cities_mask):
                major_cities_distances = station_distances[major_cities_mask]
                if np.min(major_cities_distances) <= 25.0:
                    classification = "urban_core"

            # 2. Urban Fringe: 25-50km from 100k+ population cities
            if classification == "rural":
                large_cities_mask = cities_gdf["population"] >= 100000
                if np.any(large_cities_mask):
                    large_cities_distances = station_distances[large_cities_mask]
                    min_distance = np.min(large_cities_distances)
                    if 25.0 < min_distance <= 50.0:
                        classification = "urban_fringe"

            # 3. Suburban: 50-100km from 50k+ population cities
            if classification == "rural":
                medium_cities_mask = cities_gdf["population"] >= 50000
                if np.any(medium_cities_mask):
                    medium_cities_distances = station_distances[medium_cities_mask]
                    min_distance = np.min(medium_cities_distances)
                    if 50.0 < min_distance <= 100.0:
                        classification = "suburban"

            # 4. Rural: >100km from any 50k+ city (default)

            classified_stations.iloc[
                i, classified_stations.columns.get_loc("urban_classification")
            ] = classification

    def calculate_urban_proximity_metrics(
        self,
        stations_gdf: gpd.GeoDataFrame,
        cities_gdf: gpd.GeoDataFrame | None = None,
    ) -> gpd.GeoDataFrame:
        """
        Calculate urban proximity metrics for weather stations.

        Args:
            stations_gdf: GeoDataFrame with weather station locations
            cities_gdf: GeoDataFrame with city locations (loaded if None)

        Returns:
            Enhanced GeoDataFrame with proximity metrics
        """
        if cities_gdf is None:
            cities_gdf = self.load_cities_data()

        # Use the classification function which includes proximity calculations
        return self.classify_stations_urban_rural(stations_gdf, cities_gdf)

    def get_urban_context_summary(
        self,
        classified_stations_gdf: gpd.GeoDataFrame,
        cities_gdf: gpd.GeoDataFrame | None = None,
        urban_areas_gdf: gpd.GeoDataFrame | None = None,
    ) -> dict[str, Any]:
        """
        Generate summary statistics for urban context analysis.

        Args:
            classified_stations_gdf: Stations with urban classification
            cities_gdf: Cities data (loaded if None)
            urban_areas_gdf: Urban areas data (loaded if None)

        Returns:
            Dictionary with summary statistics
        """
        if cities_gdf is None:
            cities_gdf = self.load_cities_data()
        if urban_areas_gdf is None:
            urban_areas_gdf = self.load_urban_areas()

        # Count stations by classification
        classification_counts = classified_stations_gdf[
            "urban_classification"
        ].value_counts()

        # Calculate proximity statistics
        valid_distances = classified_stations_gdf[
            "distance_to_nearest_city_km"
        ].dropna()

        summary = {
            "total_stations": int(len(classified_stations_gdf)),
            "total_cities": int(len(cities_gdf)),
            "total_urban_areas": int(len(urban_areas_gdf)),
            # Station counts by classification
            "urban_core_stations": int(classification_counts.get("urban_core", 0)),
            "urban_fringe_stations": int(classification_counts.get("urban_fringe", 0)),
            "urban_stations": int(classification_counts.get("urban", 0)),
            "suburban_stations": int(classification_counts.get("suburban", 0)),
            "rural_stations": int(classification_counts.get("rural", 0)),
            # Distance statistics
            "mean_distance_to_city_km": float(valid_distances.mean())
            if len(valid_distances) > 0
            else np.nan,
            "median_distance_to_city_km": float(valid_distances.median())
            if len(valid_distances) > 0
            else np.nan,
            "min_distance_to_city_km": float(valid_distances.min())
            if len(valid_distances) > 0
            else np.nan,
            "max_distance_to_city_km": float(valid_distances.max())
            if len(valid_distances) > 0
            else np.nan,
            # Population statistics
            "city_population_range": {
                "min": int(cities_gdf["population"].min())
                if len(cities_gdf) > 0
                else 0,
                "max": int(cities_gdf["population"].max())
                if len(cities_gdf) > 0
                else 0,
                "mean": int(cities_gdf["population"].mean())
                if len(cities_gdf) > 0
                else 0,
            },
            # Coverage statistics
            "classification_distribution": {
                str(category): float(int(count) / len(classified_stations_gdf) * 100)
                for category, count in classification_counts.items()
            },
        }

        return summary
