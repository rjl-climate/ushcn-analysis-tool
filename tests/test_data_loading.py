"""Data loading integration tests."""

import pytest
import pandas as pd
import geopandas as gpd

from src.ushcn_heatisland.data.loaders import load_ushcn_data
from src.ushcn_heatisland.urban.context import UrbanContextManager


class TestDataLoading:
    """Test data loading functionality."""

    def test_load_ushcn_data_fls52(self, data_dir):
        """Test loading FLS52 adjusted data."""
        adjusted_data, raw_data = load_ushcn_data(
            data_dir, 
            adjusted_type="fls52", 
            load_raw=False,
            temp_metric="min"
        )
        
        assert isinstance(adjusted_data, gpd.GeoDataFrame)
        assert len(adjusted_data) > 0
        assert raw_data is None
        
        # Check required columns exist
        required_columns = ["station_id", "timestamp", "temperature_celsius", "geometry"]
        for col in required_columns:
            assert col in adjusted_data.columns, f"Missing column: {col}"
        
        # Check geometry contains coordinates
        sample_point = adjusted_data.geometry.iloc[0]
        assert hasattr(sample_point, 'x') and hasattr(sample_point, 'y')
        assert -180 <= sample_point.x <= 180  # Valid longitude
        assert -90 <= sample_point.y <= 90    # Valid latitude

    def test_load_ushcn_data_with_raw(self, data_dir):
        """Test loading both adjusted and raw data."""
        adjusted_data, raw_data = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            raw_type="raw", 
            load_raw=True,
            temp_metric="min"
        )
        
        assert isinstance(adjusted_data, gpd.GeoDataFrame)
        assert isinstance(raw_data, gpd.GeoDataFrame)
        assert len(adjusted_data) > 0
        assert len(raw_data) > 0

    def test_load_all_data_types(self, data_dir):
        """Test loading all available data types."""
        data_types = ["raw", "tob", "fls52"]
        
        for data_type in data_types:
            adjusted_data, _ = load_ushcn_data(
                data_dir,
                adjusted_type=data_type,
                load_raw=False,
                temp_metric="min"
            )
            
            assert isinstance(adjusted_data, gpd.GeoDataFrame)
            assert len(adjusted_data) > 0, f"No data loaded for type: {data_type}"

    def test_load_different_temp_metrics(self, data_dir):
        """Test loading different temperature metrics."""
        temp_metrics = ["min", "max", "avg"]
        
        for metric in temp_metrics:
            adjusted_data, _ = load_ushcn_data(
                data_dir,
                adjusted_type="fls52",
                load_raw=False,
                temp_metric=metric
            )
            
            assert isinstance(adjusted_data, gpd.GeoDataFrame)
            assert len(adjusted_data) > 0, f"No data loaded for metric: {metric}"


class TestUrbanContextLoading:
    """Test urban context data loading."""

    def test_urban_context_manager_initialization(self):
        """Test that UrbanContextManager can be initialized."""
        manager = UrbanContextManager()
        assert manager is not None

    def test_load_cities_data(self):
        """Test loading cities data."""
        manager = UrbanContextManager()
        cities_gdf = manager.load_cities_data(min_population=100000)
        
        assert isinstance(cities_gdf, gpd.GeoDataFrame)
        assert len(cities_gdf) > 0
        
        # Check required columns
        required_columns = ["city_name", "state", "population", "geometry"]
        for col in required_columns:
            assert col in cities_gdf.columns, f"Missing column: {col}"
        
        # Check population filter worked
        assert all(cities_gdf["population"] >= 100000)

    def test_load_urban_areas(self):
        """Test loading urban areas data."""
        manager = UrbanContextManager()
        urban_areas_gdf = manager.load_urban_areas()
        
        assert isinstance(urban_areas_gdf, gpd.GeoDataFrame)
        # Note: May be empty if no urban areas data is available

    def test_classify_stations_integration(self, data_dir):
        """Test station classification with real data."""
        # Load station data
        stations_gdf, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        # Initialize urban context
        manager = UrbanContextManager()
        cities_gdf = manager.load_cities_data(min_population=50000)
        urban_areas_gdf = manager.load_urban_areas()
        
        # Classify stations (take small sample for speed)
        sample_stations = stations_gdf.head(50)
        classified_stations = manager.classify_stations_urban_rural(
            sample_stations,
            cities_gdf=cities_gdf,
            urban_areas_gdf=urban_areas_gdf,
            use_4_level_hierarchy=True
        )
        
        assert isinstance(classified_stations, gpd.GeoDataFrame)
        assert len(classified_stations) == len(sample_stations)
        
        # Check classification columns were added
        classification_columns = [
            "urban_classification",
            "distance_to_nearest_city_km", 
            "nearest_city_name",
            "nearest_city_population"
        ]
        for col in classification_columns:
            assert col in classified_stations.columns, f"Missing column: {col}"
        
        # Check classification values are valid
        valid_classifications = ["urban_core", "urban_fringe", "suburban", "rural"]
        assert all(
            cls in valid_classifications 
            for cls in classified_stations["urban_classification"]
        )