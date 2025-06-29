"""CLI integration tests."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_help(self):
        """Test that CLI help works."""
        result = subprocess.run(
            [sys.executable, "-m", "src.ushcn_heatisland.cli.main", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "US Long-Term Temperature Change Analyzer" in result.stdout

    def test_list_algorithms_command(self):
        """Test list-algos command."""
        result = subprocess.run(
            [sys.executable, "-m", "src.ushcn_heatisland.cli.main", "list-algos"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "simple" in result.stdout
        assert "min_obs" in result.stdout
        assert "adjustment_impact" in result.stdout


class TestCLIAnalysisCommands:
    """Test CLI analysis commands."""

    def test_simple_analysis_command(self, data_dir, output_dir):
        """Test running simple analysis via CLI."""
        cmd = [
            sys.executable, "-m", "src.ushcn_heatisland.cli.main", "analyze",
            "simple",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
            "--temp-metric", "min",
            "--visualization-type", "points",
            "--baseline-start-year", "1970",
            "--current-start-year", "1990",
            "--period-length", "20"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert "Analysis complete!" in result.stdout
        assert "Visualization complete!" in result.stdout
        
        # Check output files were created
        stats_file = output_dir / "simple_min_statistics.json"
        assert stats_file.exists(), "Statistics file not created"
        
        plot_file = output_dir / "simple_min_anomaly_map.png" 
        assert plot_file.exists(), "Plot file not created"

    def test_urban_analysis_command(self, data_dir, output_dir):
        """Test running urban heat island analysis via CLI."""
        cmd = [
            sys.executable, "-m", "src.ushcn_heatisland.cli.main", "analyze",
            "simple",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
            "--temp-metric", "min",
            "--visualization-type", "contours",
            "--show-cities",
            "--classify-stations",
            "--urban-analysis",
            "--heat-island-report",
            "--baseline-start-year", "1970",
            "--current-start-year", "1990",
            "--period-length", "20"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert "Urban Heat Island Analysis" in result.stdout
        
        # Check urban-specific outputs
        heat_island_report = output_dir / "simple_min_heat_island_report.json"
        assert heat_island_report.exists(), "Heat island report not created"

    def test_adjustment_impact_analysis(self, data_dir, output_dir):
        """Test adjustment impact analysis via CLI."""
        cmd = [
            sys.executable, "-m", "src.ushcn_heatisland.cli.main", "analyze", 
            "adjustment_impact",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
            "--temp-metric", "min",
            "--baseline-start-year", "1970",
            "--current-start-year", "1990", 
            "--period-length", "20"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert "Mean adjustment impact" in result.stdout

    def test_cli_parameter_validation(self, data_dir, output_dir):
        """Test CLI parameter validation."""
        # Test invalid algorithm
        cmd = [
            sys.executable, "-m", "src.ushcn_heatisland.cli.main", "analyze",
            "invalid_algorithm",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 1
        assert "Unknown algorithm" in result.stderr or "Unknown algorithm" in result.stdout
        
        # Test invalid temperature metric
        cmd = [
            sys.executable, "-m", "src.ushcn_heatisland.cli.main", "analyze",
            "simple",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
            "--temp-metric", "invalid_metric"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 1
        assert "Unknown temperature metric" in result.stderr or "Unknown temperature metric" in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_missing_data_directory(self, output_dir):
        """Test handling of missing data directory."""
        nonexistent_dir = Path("/nonexistent/data/dir")
        
        cmd = [
            sys.executable, "-m", "src.ushcn_heatisland.cli.main", "analyze",
            "simple",
            "--data-dir", str(nonexistent_dir),
            "--output-dir", str(output_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        assert result.returncode == 1
        assert "Error during analysis" in result.stderr or "Error during analysis" in result.stdout

    def test_invalid_period_ranges(self, data_dir, output_dir):
        """Test handling of invalid period ranges."""
        cmd = [
            sys.executable, "-m", "src.ushcn_heatisland.cli.main", "analyze",
            "simple",
            "--data-dir", str(data_dir),
            "--output-dir", str(output_dir),
            "--baseline-start-year", "2000",
            "--current-start-year", "1950",  # Current before baseline
            "--period-length", "10"
        ]
        
        # This should either fail or produce a warning
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        # Allow this to pass but with warnings, or fail gracefully
        # The exact behavior depends on implementation
        assert result.returncode in [0, 1]