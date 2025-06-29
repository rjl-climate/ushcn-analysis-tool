"""Output validation tests."""

import json
from pathlib import Path

import pytest
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from src.ushcn_heatisland.data.loaders import load_ushcn_data
from src.ushcn_heatisland.analysis.anomaly import get_algorithm
from src.ushcn_heatisland.plotting import create_summary_statistics, plot_anomaly_map
from src.ushcn_heatisland.urban.context import UrbanContextManager
from src.ushcn_heatisland.analysis.heat_island import generate_heat_island_report


class TestStatisticsOutput:
    """Test statistics output validation."""

    def test_summary_statistics_structure(self, data_dir, sample_baseline_period, sample_current_period):
        """Test that summary statistics have correct structure."""
        # Load and analyze data
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        sample_data = adjusted_data.head(50)
        algo_func = get_algorithm("simple")
        
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        # Generate statistics
        stats = create_summary_statistics(results)
        
        assert isinstance(stats, dict)
        
        # Check required keys
        required_keys = [
            "total_stations",
            "stations_with_data",
            "anomaly_celsius_mean",
            "anomaly_celsius_std",
            "anomaly_celsius_min",
            "anomaly_celsius_max"
        ]
        
        for key in required_keys:
            assert key in stats, f"Missing statistics key: {key}"
        
        # Validate data types and ranges
        assert isinstance(stats["total_stations"], int)
        assert isinstance(stats["stations_with_data"], int)
        assert stats["stations_with_data"] <= stats["total_stations"]
        
        # Temperature anomalies should be reasonable
        assert -15.0 < stats["anomaly_celsius_mean"] < 15.0
        assert stats["anomaly_celsius_std"] >= 0
        assert stats["anomaly_celsius_min"] <= stats["anomaly_celsius_max"]

    def test_statistics_json_serialization(self, data_dir, output_dir, sample_baseline_period, sample_current_period):
        """Test that statistics can be serialized to JSON."""
        # Generate statistics
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52", 
            load_raw=False,
            temp_metric="min"
        )
        
        sample_data = adjusted_data.head(30)
        algo_func = get_algorithm("simple")
        
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        stats = create_summary_statistics(results)
        
        # Test JSON serialization
        stats_file = output_dir / "test_statistics.json"
        
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
        
        assert stats_file.exists()
        
        # Test JSON deserialization
        with open(stats_file, "r") as f:
            loaded_stats = json.load(f)
        
        assert loaded_stats == stats


class TestPlotOutput:
    """Test plot output validation."""

    def test_plot_file_creation(self, data_dir, output_dir, sample_baseline_period, sample_current_period):
        """Test that plot files are created successfully."""
        # Generate data for plotting
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False, 
            temp_metric="min"
        )
        
        sample_data = adjusted_data.head(30)
        algo_func = get_algorithm("simple")
        
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        # Create plot
        plot_file = output_dir / "test_anomaly_map.png"
        title = "Test Anomaly Map"
        
        fig = plot_anomaly_map(results, title, plot_file, temp_metric="Min")
        
        assert plot_file.exists()
        assert plot_file.stat().st_size > 0  # File has content
        
        # Clean up matplotlib
        plt.close(fig)

    def test_plot_file_format(self, data_dir, output_dir, sample_baseline_period, sample_current_period):
        """Test that plot files have correct format."""
        # Generate minimal plot
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        sample_data = adjusted_data.head(20)
        algo_func = get_algorithm("simple")
        
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        # Test different output formats
        formats = ["png", "jpg", "pdf"]
        
        for fmt in formats:
            plot_file = output_dir / f"test_plot.{fmt}"
            title = f"Test Plot ({fmt.upper()})"
            
            # Change extension to test format
            fig = plot_anomaly_map(results, title, plot_file, temp_metric="Min")
            
            assert plot_file.exists(), f"Plot file not created for format: {fmt}"
            assert plot_file.stat().st_size > 0, f"Empty plot file for format: {fmt}"
            
            plt.close(fig)


class TestHeatIslandReportOutput:
    """Test heat island report output validation."""

    def test_heat_island_report_structure(self, data_dir, sample_baseline_period, sample_current_period):
        """Test heat island report has correct structure."""
        # Generate data with urban classification
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        sample_data = adjusted_data.head(50)
        algo_func = get_algorithm("simple")
        
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        # Add urban classification
        manager = UrbanContextManager()
        cities_gdf = manager.load_cities_data(min_population=100000)
        urban_areas_gdf = manager.load_urban_areas()
        
        classified_results = manager.classify_stations_urban_rural(
            results,
            cities_gdf=cities_gdf,
            urban_areas_gdf=urban_areas_gdf,
            use_4_level_hierarchy=True
        )
        
        summary = manager.get_urban_context_summary(
            classified_results, cities_gdf, urban_areas_gdf
        )
        
        # Generate report
        report = generate_heat_island_report(classified_results, summary, cities_gdf)
        
        assert isinstance(report, dict)
        
        # Check main sections
        required_sections = ["metadata", "urban_context_summary", "station_analysis"]
        for section in required_sections:
            assert section in report, f"Missing section: {section}"
        
        # Check metadata structure
        metadata = report["metadata"]
        assert "analysis_date" in metadata
        assert "total_stations_analyzed" in metadata
        
        # Check urban context summary
        urban_summary = report["urban_context_summary"]
        assert "total_cities" in urban_summary
        assert "station_classification_counts" in urban_summary

    def test_heat_island_report_json_serialization(self, data_dir, output_dir, sample_baseline_period, sample_current_period):
        """Test that heat island report can be serialized to JSON."""
        # Generate minimal report
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        sample_data = adjusted_data.head(30)
        algo_func = get_algorithm("simple")
        
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        # Add classification
        manager = UrbanContextManager()
        cities_gdf = manager.load_cities_data(min_population=100000)
        urban_areas_gdf = manager.load_urban_areas()
        
        classified_results = manager.classify_stations_urban_rural(
            results,
            cities_gdf=cities_gdf,
            urban_areas_gdf=urban_areas_gdf,
            use_4_level_hierarchy=True
        )
        
        summary = manager.get_urban_context_summary(
            classified_results, cities_gdf, urban_areas_gdf
        )
        
        report = generate_heat_island_report(classified_results, summary, cities_gdf)
        
        # Test JSON serialization
        report_file = output_dir / "test_heat_island_report.json"
        
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        assert report_file.exists()
        
        # Test JSON deserialization
        with open(report_file, "r") as f:
            loaded_report = json.load(f)
        
        assert loaded_report == report


class TestDataOutputConsistency:
    """Test consistency of output data."""

    def test_station_id_consistency(self, data_dir, sample_baseline_period, sample_current_period):
        """Test that station IDs are consistent across outputs."""
        # Load data
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        sample_data = adjusted_data.head(30)
        
        # Run analysis
        algo_func = get_algorithm("simple")
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        # Check that station IDs in results are subset of input
        input_station_ids = set(sample_data["station_id"])
        output_station_ids = set(results["station_id"])
        
        assert output_station_ids.issubset(input_station_ids)
        
        # Check for duplicates
        assert len(results["station_id"]) == len(results["station_id"].unique())

    def test_coordinate_preservation(self, data_dir, sample_baseline_period, sample_current_period):
        """Test that coordinates are preserved through analysis."""
        # Load data
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        sample_data = adjusted_data.head(20)
        
        # Run analysis
        algo_func = get_algorithm("simple")
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        # Check coordinates for stations that appear in both
        for _, result_row in results.iterrows():
            station_id = result_row["station_id"]
            input_row = sample_data[sample_data["station_id"] == station_id].iloc[0]
            
            # Coordinates should match exactly
            assert abs(result_row["latitude"] - input_row["latitude"]) < 1e-6
            assert abs(result_row["longitude"] - input_row["longitude"]) < 1e-6

    def test_output_file_sizes(self, data_dir, output_dir, sample_baseline_period, sample_current_period):
        """Test that output files have reasonable sizes."""
        # Generate various outputs
        adjusted_data, _ = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",
            load_raw=False,
            temp_metric="min"
        )
        
        sample_data = adjusted_data.head(40)
        algo_func = get_algorithm("simple")
        
        results = algo_func(
            gdf_adjusted=sample_data,
            baseline_period=sample_baseline_period,
            current_period=sample_current_period
        )
        
        # Generate outputs
        stats = create_summary_statistics(results)
        stats_file = output_dir / "size_test_stats.json"
        
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
        
        plot_file = output_dir / "size_test_plot.png"
        fig = plot_anomaly_map(results, "Size Test", plot_file, temp_metric="Min")
        plt.close(fig)
        
        # Check file sizes are reasonable
        assert stats_file.stat().st_size > 100  # At least 100 bytes
        assert stats_file.stat().st_size < 10000  # Less than 10KB
        
        assert plot_file.stat().st_size > 1000  # At least 1KB
        assert plot_file.stat().st_size < 5000000  # Less than 5MB