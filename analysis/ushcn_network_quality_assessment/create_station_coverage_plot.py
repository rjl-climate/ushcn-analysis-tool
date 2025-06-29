#!/usr/bin/env python3
"""
USHCN Station Coverage Timeline Analysis

This script analyzes and visualizes the evolution of USHCN station network coverage
over time to assess the impact of network sparseness on temperature trend reliability.
Focus on the dramatic expansion around 1890-1910 and its implications for climate analysis.

Author: Richard Lyon (richlyon@fastmail.com)
Date: 2025-06-29
Version: 1.0
"""

import sys
from pathlib import Path
from typing import Dict

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import json

# Add the source directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from network_quality_logger import NetworkQualityLogger


def load_ushcn_coverage_data(
    data_file: Path, logger: NetworkQualityLogger
) -> pd.DataFrame:
    """Load USHCN data and calculate station coverage by year."""

    logger.log("DATA_LOADING", "INFO", "Loading USHCN monthly temperature data")

    if not data_file.exists():
        logger.log("DATA_FILE", "ERROR", f"Data file not found: {data_file}")
        raise FileNotFoundError(f"Data file not found: {data_file}")

    # Load the parquet file
    df = pd.read_parquet(data_file)

    # Convert date and extract year
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    logger.log(
        "DATA_LOADING",
        "PASS",
        f"Loaded {len(df)} records from {df['id'].nunique()} stations",
    )

    # Validate data completeness
    temp_columns = ["max_fls52", "min_fls52", "avg_fls52"]
    logger.validate_data_completeness(df, temp_columns)

    return df


def calculate_annual_coverage(
    df: pd.DataFrame, logger: NetworkQualityLogger
) -> pd.DataFrame:
    """Calculate annual station coverage for each temperature metric."""

    logger.log("COVERAGE_CALC", "INFO", "Calculating annual station coverage")

    # Calculate station counts by year for each temperature metric
    coverage_stats = []

    years = sorted(df["year"].unique())

    for year in years:
        year_data = df[df["year"] == year]

        # Count stations with data for each metric
        max_stations = year_data[year_data["max_fls52"].notna()]["id"].nunique()
        min_stations = year_data[year_data["min_fls52"].notna()]["id"].nunique()
        avg_stations = year_data[year_data["avg_fls52"].notna()]["id"].nunique()

        # Calculate data completeness
        total_possible = len(year_data)
        max_available = year_data["max_fls52"].notna().sum()
        min_available = year_data["min_fls52"].notna().sum()
        avg_available = year_data["avg_fls52"].notna().sum()

        max_completeness = max_available / total_possible if total_possible > 0 else 0
        min_completeness = min_available / total_possible if total_possible > 0 else 0
        avg_completeness = avg_available / total_possible if total_possible > 0 else 0

        coverage_stats.append(
            {
                "year": year,
                "max_stations": max_stations,
                "min_stations": min_stations,
                "avg_stations": avg_stations,
                "max_completeness": max_completeness,
                "min_completeness": min_completeness,
                "avg_completeness": avg_completeness,
                "total_records": total_possible,
            }
        )

        # Log network transitions for major changes
        if len(coverage_stats) > 1:
            prev_max = coverage_stats[-2]["max_stations"]
            logger.log_network_transition(year, max_stations, prev_max)

        # Validate coverage adequacy for key periods
        if year >= 1900:
            logger.validate_coverage_adequacy(year, max_stations, "continental")

    coverage_df = pd.DataFrame(coverage_stats)

    # Validate coverage evolution patterns
    logger.validate_station_coverage_evolution(
        coverage_df[["year", "max_stations"]].rename(
            columns={"max_stations": "station_count"}
        )
    )

    logger.log(
        "COVERAGE_CALC",
        "PASS",
        f"Calculated coverage for {len(coverage_df)} years ({years[0]}-{years[-1]})",
    )

    return coverage_df


def create_coverage_timeline_plot(
    coverage_df: pd.DataFrame, output_file: Path, logger: NetworkQualityLogger
) -> Dict:
    """Create comprehensive station coverage timeline visualization."""

    logger.log("PLOTTING", "INFO", "Creating station coverage timeline visualization")

    # Set up the plot with subplots for station count and data completeness
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), facecolor="white")

    # Color scheme
    colors = {
        "max": "#d73027",  # Red
        "min": "#4575b4",  # Blue
        "avg": "#74add1",  # Light blue
        "critical": "#fee08b",  # Yellow highlight
        "transition": "#f46d43",  # Orange
    }

    # === SUBPLOT 1: Station Count Timeline ===
    ax1.plot(
        coverage_df["year"],
        coverage_df["max_stations"],
        color=colors["max"],
        linewidth=2.5,
        label="Maximum Temperature",
        alpha=0.9,
    )
    ax1.plot(
        coverage_df["year"],
        coverage_df["min_stations"],
        color=colors["min"],
        linewidth=2.5,
        label="Minimum Temperature",
        alpha=0.9,
    )
    ax1.plot(
        coverage_df["year"],
        coverage_df["avg_stations"],
        color=colors["avg"],
        linewidth=2.0,
        label="Average Temperature",
        alpha=0.8,
    )

    # Highlight critical transition period (1890-1910)
    transition_rect = Rectangle(
        (1890, 0),
        20,
        coverage_df["max_stations"].max() * 1.1,
        facecolor=colors["critical"],
        alpha=0.2,
        edgecolor=colors["transition"],
        linewidth=2,
    )
    ax1.add_patch(transition_rect)

    # Add coverage adequacy threshold line
    adequacy_threshold = 500
    ax1.axhline(
        y=adequacy_threshold, color="red", linestyle="--", alpha=0.7, linewidth=2
    )
    ax1.text(
        1980,
        adequacy_threshold + 30,
        "Continental Analysis Threshold (500 stations)",
        fontsize=11,
        color="red",
        fontweight="bold",
    )

    # Formatting for subplot 1
    ax1.set_title(
        "USHCN Network Coverage Evolution: Station Count Timeline (1865-2025)",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax1.set_ylabel("Active Stations", fontsize=14, fontweight="bold")
    ax1.set_ylim(0, coverage_df["max_stations"].max() * 1.1)

    # Remove top and right spines
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Grid and legend
    ax1.grid(True, alpha=0.3, linewidth=0.5)
    ax1.legend(loc="upper left", fontsize=12, frameon=False)

    # Annotate critical periods
    ax1.annotate(
        "Network Sparseness Crisis\n(17-237 stations)",
        xy=(1885, 200),
        xytext=(1920, 800),
        arrowprops=dict(arrowstyle="->", color="red", lw=2),
        fontsize=12,
        fontweight="bold",
        color="red",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.8),
    )

    ax1.annotate(
        "Rapid Network Expansion\n(4.4x growth 1890-1893)",
        xy=(1893, 1000),
        xytext=(1930, 400),
        arrowprops=dict(arrowstyle="->", color="orange", lw=2),
        fontsize=12,
        fontweight="bold",
        color="orange",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8),
    )

    ax1.annotate(
        "Modern Network Achieved\n(1,218 stations)",
        xy=(1908, 1218),
        xytext=(1950, 1100),
        arrowprops=dict(arrowstyle="->", color="green", lw=2),
        fontsize=12,
        fontweight="bold",
        color="green",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgreen", alpha=0.8),
    )

    # === SUBPLOT 2: Data Completeness ===
    ax2.plot(
        coverage_df["year"],
        coverage_df["max_completeness"] * 100,
        color=colors["max"],
        linewidth=2.5,
        label="Maximum Temperature",
        alpha=0.9,
    )
    ax2.plot(
        coverage_df["year"],
        coverage_df["min_completeness"] * 100,
        color=colors["min"],
        linewidth=2.5,
        label="Minimum Temperature",
        alpha=0.9,
    )
    ax2.plot(
        coverage_df["year"],
        coverage_df["avg_completeness"] * 100,
        color=colors["avg"],
        linewidth=2.0,
        label="Average Temperature",
        alpha=0.8,
    )

    # Add completeness threshold line
    completeness_threshold = 80
    ax2.axhline(
        y=completeness_threshold, color="red", linestyle="--", alpha=0.7, linewidth=2
    )
    ax2.text(
        1980,
        completeness_threshold + 2,
        "Reliability Threshold (80%)",
        fontsize=11,
        color="red",
        fontweight="bold",
    )

    # Formatting for subplot 2
    ax2.set_title(
        "Data Completeness: Percentage of Available Temperature Records",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax2.set_xlabel("Year", fontsize=14, fontweight="bold")
    ax2.set_ylabel("Data Completeness (%)", fontsize=14, fontweight="bold")
    ax2.set_ylim(0, 100)

    # Remove top and right spines
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    # Grid and legend
    ax2.grid(True, alpha=0.3, linewidth=0.5)
    ax2.legend(loc="upper left", fontsize=12, frameon=False)

    # Format x-axis for both subplots
    for ax in [ax1, ax2]:
        ax.set_xlim(1860, 2030)
        ax.tick_params(axis="both", labelsize=12)

    # Add key statistics box
    stats_text = """Network Coverage Statistics:
• Early Period (1860s): 17 stations
• Pre-expansion (1890): 237 stations  
• Post-expansion (1900): 1,194 stations
• Modern Network (1908+): 1,218 stations
• Expansion Factor: 5.1x (1890-1900)
• Current Adequacy: Full continental coverage"""

    fig.text(
        0.02,
        0.02,
        stats_text,
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.8", facecolor="lightblue", alpha=0.8),
    )

    # Add attribution
    fig.text(
        0.98,
        0.02,
        "Richard Lyon richlyon@fastmail.com",
        ha="right",
        va="bottom",
        fontsize=10,
        color="gray",
        style="italic",
    )

    # Tight layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15, top=0.93)

    # Save plot
    fig.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()

    logger.log("PLOTTING", "PASS", f"Coverage timeline plot saved to {output_file}")

    # Calculate key statistics for return
    early_period = coverage_df[coverage_df["year"] < 1890]
    expansion_period = coverage_df[
        (coverage_df["year"] >= 1890) & (coverage_df["year"] <= 1910)
    ]
    modern_period = coverage_df[coverage_df["year"] > 1910]

    stats = {
        "early_period_avg_stations": early_period["max_stations"].mean(),
        "expansion_period_growth": (
            expansion_period["max_stations"].max()
            / expansion_period["max_stations"].min()
        ),
        "modern_period_avg_stations": modern_period["max_stations"].mean(),
        "max_annual_growth_rate": coverage_df["max_stations"].pct_change().max(),
        "years_analyzed": len(coverage_df),
        "temporal_range": f"{coverage_df['year'].min()}-{coverage_df['year'].max()}",
    }

    return stats


def export_coverage_statistics(
    coverage_df: pd.DataFrame,
    stats: Dict,
    output_dir: Path,
    logger: NetworkQualityLogger,
):
    """Export detailed coverage statistics and supporting data."""

    # Coverage statistics CSV
    coverage_file = output_dir / "station_coverage_statistics.csv"
    coverage_df.to_csv(coverage_file, index=False)
    logger.log("EXPORT", "PASS", f"Coverage statistics saved to {coverage_file}")

    # Detailed JSON statistics
    detailed_stats = {
        "analysis_metadata": {
            "analysis_type": "USHCN Station Coverage Timeline",
            "timestamp": pd.Timestamp.now().isoformat(),
            "data_source": "USHCN FLS52 (fully adjusted monthly data)",
            "temporal_range": stats["temporal_range"],
            "total_years": stats["years_analyzed"],
        },
        "network_evolution": {
            "early_period_average_stations": float(stats["early_period_avg_stations"]),
            "expansion_growth_factor": float(stats["expansion_period_growth"]),
            "modern_period_average_stations": float(
                stats["modern_period_avg_stations"]
            ),
            "maximum_annual_growth_rate": float(stats["max_annual_growth_rate"]),
        },
        "critical_findings": {
            "network_sparseness_crisis": "Pre-1900 period severely under-sampled",
            "rapid_expansion_artifact": "1890-1910 expansion creates trend artifacts",
            "adequacy_achievement": "Continental coverage adequate from ~1900",
            "modern_stability": "Post-1908 network provides reliable coverage",
        },
        "coverage_thresholds": {
            "continental_analysis_minimum": 500,
            "early_period_maximum": int(
                coverage_df[coverage_df["year"] < 1890]["max_stations"].max()
            ),
            "expansion_period_range": [
                int(
                    coverage_df[
                        (coverage_df["year"] >= 1890) & (coverage_df["year"] <= 1910)
                    ]["max_stations"].min()
                ),
                int(
                    coverage_df[
                        (coverage_df["year"] >= 1890) & (coverage_df["year"] <= 1910)
                    ]["max_stations"].max()
                ),
            ],
            "modern_network_size": 1218,
        },
        "climate_implications": {
            "pre_1900_trend_reliability": "Questionable due to severe under-sampling",
            "transition_period_artifacts": "Apparent trends 1890-1910 may be network artifacts",
            "reliable_analysis_period": "Post-1900 for continental analysis",
            "recommendation": "Network coverage assessment required before trend analysis",
        },
    }

    stats_file = output_dir / "detailed_coverage_analysis.json"
    with open(stats_file, "w") as f:
        json.dump(detailed_stats, f, indent=2)

    logger.log("EXPORT", "PASS", f"Detailed statistics saved to {stats_file}")


def main():
    """Main analysis workflow for USHCN station coverage timeline."""

    # Setup paths
    output_dir = Path(__file__).parent
    data_dir = output_dir.parent.parent / "data"
    data_file = data_dir / "ushcn-monthly-fls52-2025-06-27.parquet"
    log_file = output_dir / "station_coverage_validation_log.txt"
    plot_file = output_dir / "ushcn_station_coverage_timeline.png"

    # Initialize validation logger
    logger = NetworkQualityLogger(log_file, "Station_Coverage_Analysis")

    try:
        logger.log(
            "ANALYSIS", "INFO", "Beginning USHCN station coverage timeline analysis"
        )

        # Load USHCN data
        df = load_ushcn_coverage_data(data_file, logger)

        # Calculate annual coverage statistics
        coverage_df = calculate_annual_coverage(df, logger)

        # Create visualization
        stats = create_coverage_timeline_plot(coverage_df, plot_file, logger)

        # Export supporting data
        export_coverage_statistics(coverage_df, stats, output_dir, logger)

        # Final validation
        if plot_file.exists():
            logger.log(
                "COMPLETION", "PASS", "Station coverage analysis completed successfully"
            )
        else:
            logger.log("COMPLETION", "ERROR", "Plot file not created")

        # Print summary
        print("\n📈 USHCN Station Coverage Analysis Complete!")
        print(f"📊 Plot: {plot_file}")
        print(f"📋 Validation Log: {log_file}")
        print("📊 Key Findings:")
        print(f"   Early Period Avg: {stats['early_period_avg_stations']:.0f} stations")
        print(f"   Expansion Growth: {stats['expansion_period_growth']:.1f}x increase")
        print(
            f"   Modern Period Avg: {stats['modern_period_avg_stations']:.0f} stations"
        )
        print(f"   Max Annual Growth: {stats['max_annual_growth_rate']:.1%}")
        print(
            f"   Analysis Period: {stats['temporal_range']} ({stats['years_analyzed']} years)"
        )

        print("\n🚨 Critical Implications:")
        print("   • Pre-1900 data inadequate for continental climate analysis")
        print(
            "   • Network expansion 1890-1910 may create artificial temperature trends"
        )
        print("   • Reliable climate analysis requires post-1900 data")
        print("   • Network coverage assessment essential before trend calculation")

    except Exception as e:
        logger.log("ANALYSIS", "ERROR", f"Analysis failed: {str(e)}")
        raise

    finally:
        validation_stats = logger.finalize()

        # Export validation summary
        validation_file = output_dir / "coverage_analysis_validation_summary.json"
        with open(validation_file, "w") as f:
            json.dump(validation_stats, f, indent=2)


if __name__ == "__main__":
    main()
