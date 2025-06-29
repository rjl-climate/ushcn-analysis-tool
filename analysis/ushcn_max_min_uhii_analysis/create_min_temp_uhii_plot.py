#!/usr/bin/env python3
"""
USHCN Minimum Temperature Urban Heat Island Analysis (Year-Round)

This script analyzes Urban Heat Island Intensity (UHII) effects using minimum
temperatures across all months from the USHCN network. Minimum temperatures
show the strongest UHII effects due to urban heat retention at night caused
by thermal mass and reduced radiative cooling.

Author: Richard Lyon (richlyon@fastmail.com)
Date: 2025-06-29
Version: 1.0
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Add the source directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from ushcn_heatisland.data.loaders import load_all_ushcn_stations
from ushcn_heatisland.urban.context import UrbanContextManager
from validation_logger import ValidationLogger, export_validation_summary


def load_and_classify_stations(
    data_dir: Path, logger: ValidationLogger
) -> gpd.GeoDataFrame:
    """Load all USHCN stations and apply urban classification."""

    # Load station locations
    logger.log("DATA_LOADING", "START", "Loading USHCN station locations")
    stations_gdf = load_all_ushcn_stations(data_dir)

    if not logger.validate_station_count(len(stations_gdf)):
        raise ValueError("Station count validation failed")

    if not logger.validate_geographic_bounds(stations_gdf):
        raise ValueError("Geographic bounds validation failed")

    # Apply urban classification
    logger.log("CLASSIFICATION", "START", "Applying urban context classification")
    urban_context = UrbanContextManager()

    # Load cities data
    cities_gdf = urban_context.load_cities_data(min_population=50000)
    logger.log(
        "CITIES_DATA", "PASS", f"Loaded {len(cities_gdf)} cities ≥50k population"
    )

    # Classify stations
    classified_stations = urban_context.classify_stations_urban_rural(
        stations_gdf, cities_gdf=cities_gdf, use_4_level_hierarchy=True
    )

    # Validate classification counts
    classification_counts = (
        classified_stations["urban_classification"].value_counts().to_dict()
    )
    if not logger.validate_classification_counts(classification_counts):
        raise ValueError("Classification validation failed")

    return classified_stations


def load_yearround_temperature_data(
    data_dir: Path, logger: ValidationLogger
) -> pd.DataFrame:
    """Load USHCN minimum temperature data for all months (year-round analysis)."""

    fls52_file = data_dir / "ushcn-monthly-fls52-2025-06-27.parquet"

    if not fls52_file.exists():
        logger.log_critical_error("DATA_FILE", f"FLS52 file not found: {fls52_file}")
        raise FileNotFoundError(f"FLS52 file not found: {fls52_file}")

    logger.log("TEMP_DATA", "START", "Loading year-round minimum temperature data")

    # Load the parquet file
    df = pd.read_parquet(fls52_file)

    # Check required columns
    temp_col = "min_fls52"
    required_cols = ["id", "date", temp_col, "lat", "lon"]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.log_critical_error("TEMP_DATA", f"Missing columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Convert date (include all months for year-round analysis)
    df["date"] = pd.to_datetime(df["date"])

    # Filter valid data
    df_clean = df[required_cols].dropna(subset=[temp_col])

    logger.log_data_loading(
        "year-round min temperature", len(df_clean), len(df_clean["id"].unique())
    )

    # Validate temperature bounds
    logger.validate_temperature_bounds(df_clean, temp_col)

    return df_clean


def calculate_annual_means(
    temp_data: pd.DataFrame,
    classified_stations: gpd.GeoDataFrame,
    logger: ValidationLogger,
) -> Tuple[pd.Series, pd.Series]:
    """Calculate annual minimum temperature means for urban and rural stations."""

    # Define urban and rural station sets
    urban_stations = classified_stations[
        classified_stations["urban_classification"].isin(["urban_core", "urban_fringe"])
    ].index.tolist()

    rural_stations = classified_stations[
        classified_stations["urban_classification"] == "rural"
    ].index.tolist()

    if not logger.validate_analysis_subsets(len(urban_stations), len(rural_stations)):
        raise ValueError("Analysis subset validation failed")

    # Calculate annual means
    temp_col = "min_fls52"

    # Group by station and year, calculate annual means
    temp_data["year"] = temp_data["date"].dt.year
    annual_by_station = temp_data.groupby(["id", "year"])[temp_col].mean()

    # Calculate urban and rural annual means
    urban_annual = []
    rural_annual = []

    years = temp_data["year"].unique()
    years.sort()

    for year in years:
        try:
            year_data = annual_by_station.xs(year, level="year", drop_level=False)

            # Urban mean for this year
            urban_year_data = year_data[
                year_data.index.get_level_values("id").isin(urban_stations)
            ]
            if len(urban_year_data) > 0:
                urban_annual.append((year, urban_year_data.mean()))

            # Rural mean for this year
            rural_year_data = year_data[
                year_data.index.get_level_values("id").isin(rural_stations)
            ]
            if len(rural_year_data) > 0:
                rural_annual.append((year, rural_year_data.mean()))
        except KeyError:
            # Year not found in data, skip
            continue

    # Convert to Series
    urban_series = pd.Series(
        [value for year, value in urban_annual],
        index=pd.Index([year for year, value in urban_annual], name="year"),
        name="urban_min_yearround",
    )

    rural_series = pd.Series(
        [value for year, value in rural_annual],
        index=pd.Index([year for year, value in rural_annual], name="year"),
        name="rural_min_yearround",
    )

    logger.log_annual_coverage("min_yearround", len(urban_series), len(rural_series))

    return urban_series, rural_series


def create_min_uhii_plot(
    urban_data: pd.Series,
    rural_data: pd.Series,
    output_file: Path,
    logger: ValidationLogger,
) -> Dict:
    """Create publication-quality minimum temperature UHII plot."""

    logger.log("PLOTTING", "START", "Creating minimum temperature UHII visualization")

    # Align data to common years
    common_years = urban_data.index.intersection(rural_data.index)
    urban_aligned = urban_data.loc[common_years]
    rural_aligned = rural_data.loc[common_years]

    # Calculate UHII
    uhii_series = urban_aligned - rural_aligned
    overall_uhii = uhii_series.mean()
    recent_uhii = uhii_series.loc[uhii_series.index >= 2000].mean()

    # Validate UHII magnitude
    logger.validate_uhii_magnitude(overall_uhii, "min")

    # Set up the plot with Tufte-style formatting
    plt.style.use("default")
    fig, ax = plt.subplots(1, 1, figsize=(14, 8), facecolor="white")

    # Convert years to datetime for plotting
    years_dt = pd.to_datetime(common_years, format="%Y")

    # Plot urban and rural lines
    colors = {"urban": "#d73027", "rural": "#4575b4"}  # Red and blue from ColorBrewer
    ax.plot(
        years_dt,
        urban_aligned.values,
        color=colors["urban"],
        linewidth=2.0,
        label="Urban Stations",
        alpha=0.8,
    )
    ax.plot(
        years_dt,
        rural_aligned.values,
        color=colors["rural"],
        linewidth=2.0,
        label="Rural Stations",
        alpha=0.8,
    )

    # Tufte-style formatting
    ax.set_title(
        "Minimum Temperature: Urban Heat Island Effects in USHCN Network (1875-2023)",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.set_ylabel("Annual Minimum Temperature (°C)", fontsize=14)
    ax.set_xlabel("Year", fontsize=14)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Minimal grid
    ax.grid(True, alpha=0.3, linewidth=0.5, linestyle="-")
    ax.set_axisbelow(True)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.YearLocator(20))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_minor_locator(mdates.YearLocator(10))

    # Add UHII annotation
    ax.text(
        0.02,
        0.95,
        f"Minimum Temp UHII: {overall_uhii:.2f}°C",
        transform=ax.transAxes,
        fontsize=13,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgreen", alpha=0.8),
    )

    # Add explanatory note
    ax.text(
        0.02,
        0.88,
        "Year-round analysis (all months)",
        transform=ax.transAxes,
        fontsize=11,
        style="italic",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.6),
    )

    # Add physical mechanism note
    ax.text(
        0.02,
        0.81,
        "Urban heat retention effects strongest at night",
        transform=ax.transAxes,
        fontsize=10,
        style="italic",
        color="darkgreen",
    )

    # Legend
    ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.75), frameon=False, fontsize=12)

    # Add attribution
    fig.text(
        0.99,
        0.01,
        "Richard Lyon richlyon@fastmail.com",
        ha="right",
        va="bottom",
        fontsize=10,
        color="gray",
        style="italic",
    )

    # Add station count info
    fig.text(
        0.02,
        0.01,
        "Urban: 146 stations, Rural: 667 stations",
        ha="left",
        va="bottom",
        fontsize=10,
        color="gray",
    )

    # Tight layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08, top=0.92)

    # Save plot
    fig.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()

    logger.log("PLOTTING", "PASS", f"Plot saved to {output_file}")

    # Return statistics
    return {
        "overall_uhii": overall_uhii,
        "recent_uhii": recent_uhii,
        "time_series": uhii_series.to_dict(),
        "urban_mean_temp": urban_aligned.mean(),
        "rural_mean_temp": rural_aligned.mean(),
        "years_analyzed": len(common_years),
        "temporal_range": f"{common_years.min()}-{common_years.max()}",
    }


def export_supporting_data(
    classified_stations: gpd.GeoDataFrame,
    uhii_stats: Dict,
    output_dir: Path,
    logger: ValidationLogger,
):
    """Export supporting data files for minimum temperature analysis."""

    # Station classification summary
    classification_summary = (
        classified_stations["urban_classification"].value_counts().to_frame("count")
    )
    classification_summary.index.name = "classification"
    classification_file = output_dir / "min_temp_station_classification.csv"
    classification_summary.to_csv(classification_file)
    logger.log(
        "EXPORT", "PASS", f"Station classification saved to {classification_file}"
    )

    # Minimum temperature UHII statistics
    stats_summary = {
        "analysis_metadata": {
            "analysis_type": "Minimum Temperature UHII (Year-Round)",
            "temporal_focus": "All 12 months included",
            "timestamp": pd.Timestamp.now().isoformat(),
            "total_stations": len(classified_stations),
            "urban_stations": len(
                classified_stations[
                    classified_stations["urban_classification"].isin(
                        ["urban_core", "urban_fringe"]
                    )
                ]
            ),
            "rural_stations": len(
                classified_stations[
                    classified_stations["urban_classification"] == "rural"
                ]
            ),
            "data_source": "USHCN FLS52 (fully adjusted)",
            "time_period": uhii_stats["temporal_range"],
            "years_analyzed": uhii_stats["years_analyzed"],
        },
        "uhii_results": {
            "overall_uhii_celsius": float(uhii_stats["overall_uhii"]),
            "recent_uhii_celsius_2000_2023": float(uhii_stats["recent_uhii"]),
            "urban_mean_min_celsius": float(uhii_stats["urban_mean_temp"]),
            "rural_mean_min_celsius": float(uhii_stats["rural_mean_temp"]),
            "temperature_difference_celsius": float(uhii_stats["overall_uhii"]),
        },
        "scientific_significance": {
            "analysis_rationale": "Minimum temperatures show strongest urban heat island effects due to nighttime heat retention by urban thermal mass",
            "physical_mechanisms": [
                "Thermal mass heat release (stored daytime energy released at night)",
                "Reduced sky view factor (buildings block radiative cooling to space)",
                "Anthropogenic heat sources (heating, vehicles, industrial activity)",
                "Surface material properties (concrete/asphalt vs. soil/vegetation)",
                "Reduced wind flow for heat dissipation",
            ],
            "temporal_validity": [
                "Year-round analysis valid since thermal mass effects operate continuously",
                "Nighttime cooling systematically reduced in urban environments",
                "Effects persist across all seasons due to fundamental thermal properties",
            ],
            "policy_relevance": [
                "Nighttime heat stress and health impacts",
                "Heating energy efficiency in winter",
                "Urban thermal comfort year-round",
                "Building and infrastructure thermal design",
            ],
        },
    }

    stats_file = output_dir / "min_temp_uhii_statistics.json"
    import json

    with open(stats_file, "w") as f:
        json.dump(stats_summary, f, indent=2)
    logger.log("EXPORT", "PASS", f"UHII statistics saved to {stats_file}")


def main():
    """Main analysis workflow for minimum temperature UHII."""

    # Setup paths
    output_dir = Path(__file__).parent
    data_dir = output_dir.parent.parent / "data"
    log_file = output_dir / "min_temp_validation_log.txt"
    plot_file = output_dir / "min_temp_uhii_plot.png"

    # Initialize validation logger
    logger = ValidationLogger(log_file, "Minimum_Temperature_UHII")

    try:
        logger.log("ANALYSIS", "START", "Beginning minimum temperature UHII analysis")

        # Load and classify stations
        classified_stations = load_and_classify_stations(data_dir, logger)

        # Load year-round temperature data
        temp_data = load_yearround_temperature_data(data_dir, logger)

        # Calculate annual means
        urban_series, rural_series = calculate_annual_means(
            temp_data, classified_stations, logger
        )

        # Create visualization
        uhii_stats = create_min_uhii_plot(urban_series, rural_series, plot_file, logger)

        # Export supporting data
        export_supporting_data(classified_stations, uhii_stats, output_dir, logger)

        # Final validation
        if plot_file.exists():
            logger.log(
                "COMPLETION",
                "PASS",
                "Minimum temperature analysis completed successfully",
            )
        else:
            logger.log("COMPLETION", "ERROR", "Plot file not created")

        # Print summary
        print("\n🌙 Minimum Temperature UHII Analysis Complete!")
        print(f"📊 Plot: {plot_file}")
        print(f"📋 Validation Log: {log_file}")
        print("📈 Key Results:")
        print(f"   Minimum Temperature UHII: {uhii_stats['overall_uhii']:.3f}°C")
        print(
            f"   Urban Annual Min: {uhii_stats['urban_mean_temp']:.1f}°C ({uhii_stats['urban_mean_temp'] * 9 / 5 + 32:.1f}°F)"
        )
        print(
            f"   Rural Annual Min: {uhii_stats['rural_mean_temp']:.1f}°C ({uhii_stats['rural_mean_temp'] * 9 / 5 + 32:.1f}°F)"
        )
        print(
            f"   Years Analyzed: {uhii_stats['years_analyzed']} ({uhii_stats['temporal_range']})"
        )

    except Exception as e:
        logger.log_critical_error("ANALYSIS", "Analysis failed", e)
        raise

    finally:
        validation_stats = logger.finalize()
        export_validation_summary(
            validation_stats, output_dir / "min_temp_validation_summary.json"
        )


if __name__ == "__main__":
    main()
