"""Core analysis workflow integration tests."""

import pytest
import pandas as pd
import geopandas as gpd

from src.ushcn_heatisland.data.loaders import load_ushcn_data
from src.ushcn_heatisland.analysis.anomaly import get_algorithm, list_algorithms
from src.ushcn_heatisland.urban.context import UrbanContextManager
from src.ushcn_heatisland.analysis.heat_island import generate_heat_island_report


class TestAnalysisAlgorithms:
    """Test analysis algorithm functionality."""

    def test_list_algorithms(self):
        """Test that algorithms can be listed."""
        algorithms = list_algorithms()
        assert isinstance(algorithms, list)
        assert len(algorithms) > 0
        
        # Check expected algorithms exist
        expected_algorithms = ["simple", "min_obs", "adjustment_impact"]
        for algo in expected_algorithms:
            assert algo in algorithms, f"Algorithm {algo} not found"

    def test_get_algorithm(self):
        """Test getting algorithm functions."""
        algorithms = list_algorithms()
        
        for algo_name in algorithms:
            algo_func = get_algorithm(algo_name)
            assert callable(algo_func), f"Algorithm {algo_name} is not callable"

    @pytest.mark.parametrize("algorithm", ["simple", "min_obs"])
    def test_algorithm_execution(self, algorithm, data_dir, sample_baseline_period, sample_current_period):
        """Test algorithm execution with sample data."""
        # Load small sample of data for testing
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        # Take small sample for speed
        sample_data = adjusted_data.head(20)
        
        # Get algorithm function
        algo_func = get_algorithm(algorithm)
        
        # Configure for algorithm
        config = {}
        if algorithm == "min_obs":
            config["min_observations"] = 20
        
        # Run analysis
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period,
            config=config if config else None
        )
        
        assert isinstance(results, gpd.GeoDataFrame)
        assert len(results) <= len(sample_data)  # May filter out stations
        
        # Check expected result columns
        expected_columns = ["station_id", "geometry", "anomaly_celsius"]
        for col in expected_columns:
            assert col in results.columns, f"Missing column: {col}"

    def test_adjustment_impact_algorithm(self, data_dir, sample_baseline_period, sample_current_period):
        """Test adjustment impact algorithm specifically."""
        # Load both adjusted and raw data
        adjusted_data, raw_data = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            raw_type="raw",
            load_raw=True,
            temp_metric="min"
        )
        
        # Take small sample
        sample_adjusted = adjusted_data.head(20)
        sample_raw = raw_data.head(20)
        
        # Get algorithm
        algo_func = get_algorithm("adjustment_impact")
        
        # Run analysis
        results = algo_func(
            gdf_adjusted=sample_adjusted,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period,
            gdf_raw=sample_raw
        )
        
        assert isinstance(results, gpd.GeoDataFrame)
        
        # Check adjustment impact specific columns
        expected_columns = ["adjustment_impact"]  # Note: column name is "adjustment_impact", not "adjustment_impact_celsius"
        for col in expected_columns:
            assert col in results.columns, f"Missing column: {col}"


class TestUrbanHeatIslandAnalysis:
    """Test urban heat island analysis workflow."""

    def test_station_classification_workflow(self, data_dir):
        """Test complete station classification workflow."""
        # Load data
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        # Take sample
        sample_data = adjusted_data.head(30)
        
        # Initialize urban context
        manager = UrbanContextManager()
        cities_gdf = manager.load_cities_data(min_population=100000)
        urban_areas_gdf = manager.load_urban_areas()
        
        # Classify stations
        classified_data = manager.classify_stations_urban_rural(
            sample_data,
            cities_gdf=cities_gdf,
            urban_areas_gdf=urban_areas_gdf,
            use_4_level_hierarchy=True
        )
        
        # Get summary
        summary = manager.get_urban_context_summary(
            classified_data, cities_gdf, urban_areas_gdf
        )
        
        assert isinstance(summary, dict)
        
        # Check summary keys
        expected_keys = [
            "total_stations",
            "urban_core_stations", 
            "urban_stations",
            "suburban_stations",
            "rural_stations",
            "total_cities"
        ]
        for key in expected_keys:
            assert key in summary, f"Missing summary key: {key}"

    def test_heat_island_report_generation(self, data_dir, sample_baseline_period, sample_current_period):
        """Test heat island report generation."""
        # Load and process data
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        # Get sample of unique stations (not just first 50 records)
        unique_stations = adjusted_data['station_id'].unique()[:10]  # Get 10 stations
        sample_data = adjusted_data[adjusted_data['station_id'].isin(unique_stations)]
        
        # Run analysis
        algo_func = get_algorithm("simple")
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        # Verify we have results with geometry
        assert len(results) > 0, "No results from algorithm"
        assert 'geometry' in results.columns, "Results missing geometry column"
        print(f"Algorithm produced {len(results)} station results")
        
        # Add urban classification
        manager = UrbanContextManager()
        cities_gdf = manager.load_cities_data(min_population=100000)
        urban_areas_gdf = manager.load_urban_areas()
        
        print(f"Loaded {len(cities_gdf)} cities for classification")
        print(f"Loaded {len(urban_areas_gdf)} urban areas for classification")
        
        classified_results = manager.classify_stations_urban_rural(
            results,
            cities_gdf=cities_gdf,
            urban_areas_gdf=urban_areas_gdf,
            use_4_level_hierarchy=True
        )
        
        # Verify classification worked
        assert len(classified_results) > 0, "No classified results"
        print(f"Classified {len(classified_results)} stations")
        
        summary = manager.get_urban_context_summary(
            classified_results, cities_gdf, urban_areas_gdf
        )
        
        # Generate heat island report
        report = generate_heat_island_report(
            classified_results, summary, cities_gdf
        )
        
        assert isinstance(report, dict)
        
        # Check report structure (based on actual heat island report structure)
        expected_sections = [
            "analysis_metadata",
            "urban_rural_analysis",
            "distance_gradient_analysis",
            "scientific_interpretation"
        ]
        for section in expected_sections:
            assert section in report, f"Missing report section: {section}"
            
        # Verify key metadata
        assert "total_stations" in report["analysis_metadata"]
        assert report["analysis_metadata"]["total_stations"] == len(classified_results)
        
        # Verify urban/rural analysis has expected structure
        urban_rural = report["urban_rural_analysis"]
        assert "total_stations_analyzed" in urban_rural
        assert "statistics_by_classification" in urban_rural
        print(f"Report generated successfully with {urban_rural['total_stations_analyzed']} stations")


class TestDataIntegrity:
    """Test data integrity and consistency."""

    def test_coordinate_consistency(self, data_dir):
        """Test that coordinates are consistent across data types."""
        data_types = ["raw", "tob", "fls52"]
        coordinates = {}
        
        for data_type in data_types:
            data, _ = load_ushcn_data(
                data_dir,
                adjusted_type=data_type,
                load_raw=False,
                temp_metric="min"
            )
            
            # Store coordinates for comparison (extract from geometry column)
            coords = data[["station_id"]].copy()
            coords["latitude"] = data.geometry.y
            coords["longitude"] = data.geometry.x
            coords = coords.drop_duplicates()
            coordinates[data_type] = coords.set_index("station_id")
        
        # Check that coordinates match across data types for same stations
        common_stations = set(coordinates["raw"].index)
        for data_type in ["tob", "fls52"]:
            common_stations &= set(coordinates[data_type].index)
        
        # Test a sample of common stations
        sample_stations = list(common_stations)[:10]
        
        for station_id in sample_stations:
            raw_coords = coordinates["raw"].loc[station_id]
            for data_type in ["tob", "fls52"]:
                if station_id in coordinates[data_type].index:
                    coords = coordinates[data_type].loc[station_id]
                    assert abs(raw_coords["latitude"] - coords["latitude"]) < 0.001
                    assert abs(raw_coords["longitude"] - coords["longitude"]) < 0.001

    def test_temperature_data_ranges(self, data_dir):
        """Test that temperature data is within reasonable ranges."""
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52", 
            load_raw=False,
            temp_metric="min"
        )
        
        # Take sample and run analysis
        sample_data = adjusted_data.head(100)
        algo_func = get_algorithm("simple")
        
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=(1951, 1980),
            current_period=(1981, 2010)
        )
        
        if len(results) > 0:
            anomalies = results["anomaly_celsius"]
            
            # Check for reasonable anomaly ranges (-10°C to +10°C)
            assert anomalies.min() > -15.0, f"Anomaly too cold: {anomalies.min()}"
            assert anomalies.max() < 15.0, f"Anomaly too hot: {anomalies.max()}"
            
            # Check for no extreme outliers (3 standard deviations)
            std_dev = anomalies.std()
            mean_anomaly = anomalies.mean()
            outlier_threshold = 3 * std_dev
            
            extreme_outliers = anomalies[
                abs(anomalies - mean_anomaly) > outlier_threshold
            ]
            
            # Allow some outliers but not too many
            outlier_percentage = len(extreme_outliers) / len(anomalies) * 100
            assert outlier_percentage < 5.0, f"Too many outliers: {outlier_percentage}%"