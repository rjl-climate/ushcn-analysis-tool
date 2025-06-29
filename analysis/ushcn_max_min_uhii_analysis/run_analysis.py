#!/usr/bin/env python3
"""
Master script to run both maximum and minimum temperature UHII analyses.

This script executes both the summer maximum temperature analysis and 
year-round minimum temperature analysis in sequence, providing comprehensive
Urban Heat Island assessment of the USHCN network.

Author: Richard Lyon (richlyon@fastmail.com)
Date: 2025-06-29
Version: 1.0
"""

import sys
import subprocess
from pathlib import Path


def run_analysis(script_name: str, analysis_type: str):
    """Run an analysis script and report results."""
    
    script_path = Path(__file__).parent / script_name
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting {analysis_type} Analysis")
    print(f"{'='*60}")
    
    try:
        # Run the analysis script
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {analysis_type} Analysis Completed Successfully!")
            print("\nOutput:")
            print(result.stdout)
        else:
            print(f"❌ {analysis_type} Analysis Failed!")
            print(f"Return code: {result.returncode}")
            print("\nError output:")
            print(result.stderr)
            print("\nStandard output:")
            print(result.stdout)
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {analysis_type} Analysis timed out after 5 minutes")
    except Exception as e:
        print(f"💥 Error running {analysis_type} Analysis: {e}")


def main():
    """Execute both UHII analyses."""
    
    print("🌡️ USHCN Urban Heat Island Analysis Suite")
    print("=========================================")
    
    # Run maximum temperature analysis (summer focus)
    run_analysis("create_max_temp_uhii_plot.py", "Summer Maximum Temperature")
    
    # Run minimum temperature analysis (year-round)
    run_analysis("create_min_temp_uhii_plot.py", "Minimum Temperature")
    
    print(f"\n{'='*60}")
    print("📊 Analysis Suite Complete!")
    print("📁 Check output directory for results:")
    print(f"   - max_temp_uhii_plot.png")
    print(f"   - min_temp_uhii_plot.png")
    print(f"   - Validation logs and statistics")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()