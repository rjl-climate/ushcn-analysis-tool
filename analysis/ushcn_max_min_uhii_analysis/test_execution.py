#!/usr/bin/env python3
"""
Simple test to verify Python execution works and diagnose environment issues.
"""

import sys
import os
from pathlib import Path

def main():
    print("🔍 Python Execution Test")
    print("=" * 40)
    
    # Test basic Python functionality
    print(f"✓ Python version: {sys.version}")
    print(f"✓ Current working directory: {os.getcwd()}")
    print(f"✓ Script location: {Path(__file__).absolute()}")
    
    # Test path to project root
    project_root = Path(__file__).parent.parent.parent
    print(f"✓ Project root: {project_root.absolute()}")
    print(f"✓ Project root exists: {project_root.exists()}")
    
    # Test path to data directory
    data_dir = project_root / "data"
    print(f"✓ Data directory: {data_dir.absolute()}")
    print(f"✓ Data directory exists: {data_dir.exists()}")
    
    # Test for USHCN data file
    if data_dir.exists():
        fls52_file = data_dir / "ushcn-monthly-fls52-2025-06-27.parquet"
        print(f"✓ FLS52 file exists: {fls52_file.exists()}")
        if fls52_file.exists():
            print(f"✓ FLS52 file size: {fls52_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Test importing required modules
    try:
        import pandas as pd
        print(f"✓ pandas version: {pd.__version__}")
    except ImportError as e:
        print(f"✗ pandas import failed: {e}")
    
    try:
        import geopandas as gpd
        print(f"✓ geopandas version: {gpd.__version__}")
    except ImportError as e:
        print(f"✗ geopandas import failed: {e}")
    
    try:
        import matplotlib
        print(f"✓ matplotlib version: {matplotlib.__version__}")
    except ImportError as e:
        print(f"✗ matplotlib import failed: {e}")
    
    # Test importing project modules
    try:
        src_path = project_root / "src"
        sys.path.insert(0, str(src_path))
        
        from ushcn_heatisland.data_loader import load_all_ushcn_stations
        print("✓ Successfully imported ushcn_heatisland.data_loader")
        
        from ushcn_heatisland.urban_context import UrbanContextManager
        print("✓ Successfully imported ushcn_heatisland.urban_context")
        
    except ImportError as e:
        print(f"✗ Project module import failed: {e}")
    except Exception as e:
        print(f"✗ Unexpected error importing modules: {e}")
    
    print("\n🎯 Environment Test Complete!")
    print("If all items show ✓, the environment is ready for analysis.")

if __name__ == "__main__":
    main()