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
    
    # Check for required data files (with flexible date patterns)
    fls52_files = list(data_dir.glob("ushcn-monthly-fls52-*.parquet"))
    assert len(fls52_files) > 0, "FLS52 data file not found (pattern: ushcn-monthly-fls52-*.parquet)"
    print(f"Found FLS52 file: {fls52_files[0].name}")
    
    raw_files = list(data_dir.glob("ushcn-monthly-raw-*.parquet"))
    assert len(raw_files) > 0, "Raw data file not found (pattern: ushcn-monthly-raw-*.parquet)"
    print(f"Found Raw file: {raw_files[0].name}")
    
    tob_files = list(data_dir.glob("ushcn-monthly-tob-*.parquet"))
    assert len(tob_files) > 0, "TOBs data file not found (pattern: ushcn-monthly-tob-*.parquet)"
    print(f"Found TOBs file: {tob_files[0].name}")
    
    # Optional daily file
    daily_files = list(data_dir.glob("ushcn-daily-*.parquet"))
    if daily_files:
        print(f"Found Daily file: {daily_files[0].name}")
    else:
        print("Daily file not found (optional)")
    
    cities_file = data_dir / "cities" / "us_cities_static.csv"
    assert cities_file.exists(), "Cities data file not found"
    print(f"Found Cities file: {cities_file.name}")


def test_data_file_naming_patterns(data_dir):
    """Test that data files follow expected naming patterns."""
    import re
    
    # Expected patterns
    patterns = {
        "fls52": r"ushcn-monthly-fls52-\d{4}-\d{2}-\d{2}\.parquet",
        "raw": r"ushcn-monthly-raw-\d{4}-\d{2}-\d{2}\.parquet", 
        "tob": r"ushcn-monthly-tob-\d{4}-\d{2}-\d{2}\.parquet",
        "daily": r"ushcn-daily-\d{4}-\d{2}-\d{2}\.parquet"
    }
    
    for data_type, pattern in patterns.items():
        files = list(data_dir.glob(f"*{data_type}*.parquet"))
        if files:  # Check pattern if file exists
            filename = files[0].name
            assert re.match(pattern, filename), f"{data_type} file '{filename}' doesn't match expected pattern '{pattern}'"
            print(f"✓ {data_type}: {filename}")
        elif data_type != "daily":  # Daily is optional
            print(f"⚠ {data_type}: No file found (pattern: {pattern})")


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