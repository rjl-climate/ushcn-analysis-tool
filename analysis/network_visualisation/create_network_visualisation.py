#!/usr/bin/env python3
"""
Create clean academic plot of USHCN station network for publication.

This script generates a publication-quality visualization following Tufte principles,
showing USHCN weather stations classified by urban context alongside major US cities.
"""

import sys
from pathlib import Path

# Add the source directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from ushcn_heatisland.plotting import plot_clean_ushcn_network
from ushcn_heatisland.urban.context import UrbanContextManager
from ushcn_heatisland.data.loaders import load_station_locations, load_all_ushcn_stations


def main():
    """Generate clean academic plot of USHCN station network."""

    # Define paths
    data_dir = Path("data")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Load station data
    print("Loading USHCN station data...")

    # Use the new function to load all 1,218 USHCN stations from monthly data
    try:
        stations_gdf = load_all_ushcn_stations(data_dir)
        print(f"Loaded {len(stations_gdf)} USHCN stations (full network)")
    except FileNotFoundError:
        # Fallback to daily data if monthly files not found
        print("Monthly data files not found, falling back to daily data...")
        daily_data_path = data_dir / "ushcn-daily-2025-06-27.parquet"

        if not daily_data_path.exists():
            print(f"Error: Could not find daily data file at {daily_data_path}")
            return 1

        stations_gdf = load_station_locations(daily_data_path)
        print(f"Loaded {len(stations_gdf)} stations from daily data (subset)")

    # Load urban context
    print("Loading urban context...")
    urban_context = UrbanContextManager()

    # Load cities and urban areas
    try:
        cities_gdf = urban_context.load_cities_data(min_population=50000)
        print(f"Loaded {len(cities_gdf)} cities")
        urban_areas_gdf = None  # Not using urban areas for this plot
    except Exception as e:
        print(f"Warning: Could not load urban context: {e}")
        cities_gdf = None
        urban_areas_gdf = None

    # Classify stations by urban context
    print("Classifying stations by urban context...")
    try:
        classified_stations = urban_context.classify_stations_urban_rural(
            stations_gdf,
            cities_gdf=cities_gdf,
            urban_areas_gdf=urban_areas_gdf,
            use_4_level_hierarchy=True,
        )
        print("Station classification completed")

        # Print classification summary
        if "urban_classification" in classified_stations.columns:
            classification_counts = classified_stations[
                "urban_classification"
            ].value_counts()
            print("\nStation classification summary:")
            for classification, count in classification_counts.items():
                print(f"  {classification}: {count}")

    except Exception as e:
        print(f"Warning: Could not classify stations: {e}")
        classified_stations = stations_gdf

    # Create the academic plot
    print("\nGenerating clean academic plot...")

    title = "USHCN Temperature Station Network and Urban Context"
    output_path = output_dir / "ushcn_academic_network_map.png"

    try:
        fig = plot_clean_ushcn_network(
            stations_gdf=classified_stations,
            cities_gdf=cities_gdf,
            title=title,
            output_path=output_path,
            figsize=(16, 10),  # Larger for publication quality
            city_population_threshold=250000,  # Show major cities only
            attribution="Richard Lyon richlyon@fastmail.com",
        )

        print(f"✓ Academic plot saved to: {output_path}")
        print("  Figure size: 16×10 inches at 300 DPI")
        print("  Clean Tufte-style design with attribution")

        # Also create a version with all cities used in rural classification
        output_path_detailed = output_dir / "ushcn_academic_network_map_detailed.png"
        fig_detailed = plot_clean_ushcn_network(
            stations_gdf=classified_stations,
            cities_gdf=cities_gdf,
            title=title,
            output_path=output_path_detailed,
            figsize=(16, 10),
            city_population_threshold=50000,  # Show all cities used in rural classification
            attribution="Richard Lyon richlyon@fastmail.com",
        )

        print(f"✓ Detailed version saved to: {output_path_detailed}")

    except Exception as e:
        print(f"Error creating plot: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print("\n🎯 Academic plots created successfully for publication!")
    print(f"   Main plot: {output_path}")
    print(f"   Detailed plot: {output_path_detailed}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
