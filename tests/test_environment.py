"""Environment and dependency tests."""

import sys
from pathlib import Path

import pytest


def test_python_version():
    """Test that Python version is compatible."""
    assert sys.version_info >= (3, 12), f"Python 3.12+ required, got {sys.version}"


def test_project_structure(project_root):
    """Test that project structure exists."""
    assert project_root.exists()
    assert (project_root / "src").exists()
    assert (project_root / "src" / "ushcn_heatisland").exists()
    assert (project_root / "pyproject.toml").exists()


def test_data_directory_exists(data_dir):
    """Test that data directory and files exist."""
    assert data_dir.exists()
    
    # Check for required data files
    fls52_file = data_dir / "ushcn-monthly-fls52-2025-06-27.parquet"
    assert fls52_file.exists(), "FLS52 data file not found"
    
    raw_file = data_dir / "ushcn-monthly-raw-2025-06-27.parquet"
    assert raw_file.exists(), "Raw data file not found"
    
    cities_file = data_dir / "cities" / "us_cities_static.csv"
    assert cities_file.exists(), "Cities data file not found"


def test_required_imports():
    """Test that all required packages can be imported."""
    # Core scientific packages
    import pandas
    import geopandas
    import matplotlib
    import numpy
    import scipy
    
    # Project-specific packages
    import contextily
    import shapely
    import typer
    import pydantic
    import pyproj
    import sklearn
    
    # Test project imports
    from src.ushcn_heatisland.data.loaders import load_ushcn_data
    from src.ushcn_heatisland.urban.context import UrbanContextManager
    from src.ushcn_heatisland.analysis.anomaly import get_algorithm
    
    assert True  # If we get here, all imports succeeded