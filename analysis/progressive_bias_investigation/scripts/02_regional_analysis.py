#!/usr/bin/env python3
"""
Regional analysis of progressive bias trends.

This script groups stations by climate regions and analyzes whether
bias trends show regional patterns or are uniformly distributed.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import Point

# Define US climate regions based on NOAA classifications
CLIMATE_REGIONS = {
    "Northeast": {
        "states": ["ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA"],
        "bounds": {"min_lon": -80.5, "max_lon": -66.9, "min_lat": 39.7, "max_lat": 47.5}
    },
    "Southeast": {
        "states": ["WV", "MD", "DE", "VA", "KY", "TN", "NC", "SC", "GA", "FL", "AL", "MS", "LA", "AR"],
        "bounds": {"min_lon": -94.6, "max_lon": -75.0, "min_lat": 24.5, "max_lat": 39.7}
    },
    "Midwest": {
        "states": ["OH", "IN", "IL", "MI", "WI", "MN", "IA", "MO", "ND", "SD", "NE", "KS"],
        "bounds": {"min_lon": -104.0, "max_lon": -80.5, "min_lat": 36.0, "max_lat": 49.0}
    },
    "South": {
        "states": ["OK", "TX"],
        "bounds": {"min_lon": -106.6, "max_lon": -93.5, "min_lat": 25.8, "max_lat": 37.0}
    },
    "Southwest": {
        "states": ["AZ", "NM", "NV", "UT", "CO"],
        "bounds": {"min_lon": -120.0, "max_lon": -102.0, "min_lat": 31.3, "max_lat": 42.0}
    },
    "Northwest": {
        "states": ["WA", "OR", "ID", "MT", "WY"],
        "bounds": {"min_lon": -124.7, "max_lon": -104.0, "min_lat": 42.0, "max_lat": 49.0}
    },
    "West": {
        "states": ["CA"],
        "bounds": {"min_lon": -124.4, "max_lon": -114.1, "min_lat": 32.5, "max_lat": 42.0}
    },
    "Alaska": {
        "states": ["AK"],
        "bounds": {"min_lon": -180.0, "max_lon": -130.0, "min_lat": 51.0, "max_lat": 72.0}
    },
    "Hawaii": {
        "states": ["HI"],
        "bounds": {"min_lon": -160.6, "max_lon": -154.8, "min_lat": 18.9, "max_lat": 22.2}
    }
}


def assign_climate_region(row: pd.Series) -> str:
    """Assign a station to a climate region based on state or coordinates."""
    state = row.get("state", "")
    lat = row["lat"]
    lon = row["lon"]
    
    # First try to match by state
    for region, info in CLIMATE_REGIONS.items():
        if state in info["states"]:
            return region
    
    # If state not found, use coordinates
    for region, info in CLIMATE_REGIONS.items():
        bounds = info["bounds"]
        if (bounds["min_lon"] <= lon <= bounds["max_lon"] and 
            bounds["min_lat"] <= lat <= bounds["max_lat"]):
            return region
    
    return "Unknown"


def analyze_regional_trends(
    station_results: pd.DataFrame,
    temp_metric: str,
    start_year: int = 1895
) -> pd.DataFrame:
    """Analyze bias trends by climate region."""
    # Assign regions
    station_results["region"] = station_results.apply(assign_climate_region, axis=1)
    
    # Remove unknown regions
    known_regions = station_results[station_results["region"] != "Unknown"]
    
    # Calculate regional statistics
    regional_stats = []
    
    for region in CLIMATE_REGIONS.keys():
        region_data = known_regions[known_regions["region"] == region]
        
        if len(region_data) < 5:  # Skip regions with too few stations
            continue
        
        # Filter valid trends and ensure they start from specified year
        valid_trends = region_data[
            (~region_data["trend_per_decade"].isna()) & 
            (region_data["first_year"] <= start_year + 10)  # Allow some flexibility for start year
        ]
        
        if len(valid_trends) < 3:
            continue
        
        # Calculate statistics
        trends = valid_trends["trend_per_decade"].values
        significant = valid_trends[valid_trends["p_value"] < 0.05]
        sig_positive = significant[significant["trend_per_decade"] > 0]
        
        # Perform one-sample t-test against zero
        t_stat, p_value = stats.ttest_1samp(trends, 0)
        
        regional_stats.append({
            "region": region,
            "temp_metric": temp_metric,
            "n_stations": len(region_data),
            "n_valid_trends": len(valid_trends),
            "mean_trend": np.mean(trends),
            "median_trend": np.median(trends),
            "std_trend": np.std(trends),
            "sem_trend": stats.sem(trends),
            "min_trend": np.min(trends),
            "max_trend": np.max(trends),
            "n_significant": len(significant),
            "n_sig_positive": len(sig_positive),
            "pct_sig_positive": 100 * len(sig_positive) / len(valid_trends) if len(valid_trends) > 0 else 0,
            "ttest_statistic": t_stat,
            "ttest_pvalue": p_value,
            "trend_different_from_zero": p_value < 0.05
        })
    
    return pd.DataFrame(regional_stats)


def test_regional_homogeneity(
    station_results: pd.DataFrame,
    regional_stats: pd.DataFrame
) -> Dict:
    """Test if trends are homogeneous across regions."""
    # Assign regions to stations
    station_results["region"] = station_results.apply(assign_climate_region, axis=1)
    
    # Get valid trends by region
    region_trends = {}
    for region in regional_stats["region"]:
        region_data = station_results[
            (station_results["region"] == region) & 
            (~station_results["trend_per_decade"].isna())
        ]
        if len(region_data) >= 3:
            region_trends[region] = region_data["trend_per_decade"].values
    
    if len(region_trends) < 2:
        return {"test_possible": False}
    
    # Perform ANOVA
    f_stat, p_value = stats.f_oneway(*region_trends.values())
    
    # Perform Kruskal-Wallis test (non-parametric alternative)
    h_stat, kw_p_value = stats.kruskal(*region_trends.values())
    
    # Calculate effect size (eta squared)
    all_trends = np.concatenate(list(region_trends.values()))
    grand_mean = np.mean(all_trends)
    ss_between = sum(len(trends) * (np.mean(trends) - grand_mean)**2 
                     for trends in region_trends.values())
    ss_total = np.sum((all_trends - grand_mean)**2)
    eta_squared = ss_between / ss_total if ss_total > 0 else 0
    
    return {
        "test_possible": True,
        "n_regions": len(region_trends),
        "anova_f_statistic": f_stat,
        "anova_p_value": p_value,
        "kruskal_h_statistic": h_stat,
        "kruskal_p_value": kw_p_value,
        "eta_squared": eta_squared,
        "regions_differ": p_value < 0.05,
        "interpretation": "Regions show different bias trends" if p_value < 0.05 
                         else "Bias trends are similar across regions"
    }


def create_regional_visualizations(
    station_results: pd.DataFrame,
    regional_stats: pd.DataFrame,
    output_dir: Path,
    temp_metric: str
):
    """Create regional analysis visualizations."""
    # Assign regions
    station_results["region"] = station_results.apply(assign_climate_region, axis=1)
    
    # Set up style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. Box plot of trends by region
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Prepare data for box plot
    plot_data = station_results[~station_results["trend_per_decade"].isna()]
    plot_data = plot_data[plot_data["region"] != "Unknown"]
    
    # Sort regions by mean trend
    region_order = (plot_data.groupby("region")["trend_per_decade"]
                   .mean()
                   .sort_values()
                   .index.tolist())
    
    # Create box plot
    bp = ax.boxplot([plot_data[plot_data["region"] == region]["trend_per_decade"].values
                     for region in region_order],
                    labels=region_order,
                    patch_artist=True,
                    showfliers=True)
    
    # Color boxes by mean trend
    for i, (patch, region) in enumerate(zip(bp['boxes'], region_order)):
        mean_trend = plot_data[plot_data["region"] == region]["trend_per_decade"].mean()
        if mean_trend > 0:
            patch.set_facecolor('lightcoral')
        else:
            patch.set_facecolor('lightblue')
    
    # Add zero line
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Labels and title
    ax.set_xlabel("Climate Region")
    ax.set_ylabel("Bias Trend (°C/decade)")
    ax.set_title(f"Regional Distribution of Bias Trends - {temp_metric.upper()} Temperature")
    plt.xticks(rotation=45, ha='right')
    
    # Add sample sizes
    for i, region in enumerate(region_order):
        n = len(plot_data[plot_data["region"] == region])
        ax.text(i+1, ax.get_ylim()[1]*0.95, f'n={n}', ha='center', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_dir / f"regional_boxplot_{temp_metric}.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    # 2. Bar plot of mean trends with error bars
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sort by mean trend
    regional_stats_sorted = regional_stats.sort_values("mean_trend")
    
    # Create bar plot
    bars = ax.bar(range(len(regional_stats_sorted)), 
                   regional_stats_sorted["mean_trend"],
                   yerr=regional_stats_sorted["sem_trend"],
                   capsize=5)
    
    # Color bars
    for i, (idx, row) in enumerate(regional_stats_sorted.iterrows()):
        if row["mean_trend"] > 0:
            bars[i].set_color('red' if row["trend_different_from_zero"] else 'lightcoral')
        else:
            bars[i].set_color('blue' if row["trend_different_from_zero"] else 'lightblue')
    
    # Add significance stars
    for i, (idx, row) in enumerate(regional_stats_sorted.iterrows()):
        if row["trend_different_from_zero"]:
            y = row["mean_trend"] + row["sem_trend"] + 0.001
            ax.text(i, y, '*', ha='center', fontsize=14, fontweight='bold')
    
    # Labels
    ax.set_xticks(range(len(regional_stats_sorted)))
    ax.set_xticklabels(regional_stats_sorted["region"], rotation=45, ha='right')
    ax.set_xlabel("Climate Region")
    ax.set_ylabel("Mean Bias Trend (°C/decade)")
    ax.set_title(f"Regional Mean Bias Trends - {temp_metric.upper()} Temperature")
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', label='Significant positive'),
        Patch(facecolor='lightcoral', label='Non-significant positive'),
        Patch(facecolor='blue', label='Significant negative'),
        Patch(facecolor='lightblue', label='Non-significant negative')
    ]
    ax.legend(handles=legend_elements, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(output_dir / f"regional_means_{temp_metric}.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    # 3. Spatial map of regional trends
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create a simple US map visualization
    valid_stations = station_results[~station_results["trend_per_decade"].isna()]
    
    # Plot stations colored by trend
    scatter = ax.scatter(valid_stations["lon"], 
                        valid_stations["lat"],
                        c=valid_stations["trend_per_decade"],
                        cmap='RdBu_r',
                        vmin=-0.05,
                        vmax=0.05,
                        s=30,
                        alpha=0.7,
                        edgecolors='black',
                        linewidth=0.5)
    
    # Add region boundaries (simplified)
    for region, info in CLIMATE_REGIONS.items():
        if region in ["Alaska", "Hawaii"]:
            continue
        bounds = info["bounds"]
        # Draw rectangle for each region
        from matplotlib.patches import Rectangle
        rect = Rectangle((bounds["min_lon"], bounds["min_lat"]),
                        bounds["max_lon"] - bounds["min_lon"],
                        bounds["max_lat"] - bounds["min_lat"],
                        fill=False, edgecolor='gray', linewidth=1, linestyle='--')
        ax.add_patch(rect)
        # Add region label
        ax.text((bounds["min_lon"] + bounds["max_lon"])/2,
                (bounds["min_lat"] + bounds["max_lat"])/2,
                region, ha='center', va='center', fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, label='Bias Trend (°C/decade)')
    
    # Set limits for continental US
    ax.set_xlim(-125, -65)
    ax.set_ylim(24, 50)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Spatial Distribution of Bias Trends by Region - {temp_metric.upper()} Temperature")
    
    plt.tight_layout()
    plt.savefig(output_dir / f"regional_spatial_map_{temp_metric}.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"Regional visualizations saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Analyze bias trends by climate region")
    parser.add_argument("--temp-metric", default="avg", choices=["min", "max", "avg", "all"],
                        help="Temperature metric to analyze")
    parser.add_argument("--input-dir", type=Path, 
                        default=Path("analysis/progressive_bias_investigation/outputs/data"),
                        help="Directory containing bias trend results")
    parser.add_argument("--output-dir", type=Path,
                        default=Path("analysis/progressive_bias_investigation/outputs"),
                        help="Output directory for results")
    
    args = parser.parse_args()
    
    # Determine which metrics to analyze
    if args.temp_metric == "all":
        metrics = ["min", "max", "avg"]
    else:
        metrics = [args.temp_metric]
    
    all_regional_stats = []
    
    for metric in metrics:
        print(f"\n{'='*60}")
        print(f"Analyzing regional patterns for {metric.upper()} temperature...")
        print(f"{'='*60}")
        
        # Load station results
        input_file = args.input_dir / f"station_bias_trends_{metric}.csv"
        if not input_file.exists():
            print(f"Input file not found: {input_file}")
            print("Please run 01_calculate_bias_trends.py first")
            continue
        
        station_results = pd.read_csv(input_file)
        print(f"Loaded {len(station_results)} station results")
        
        # Analyze regional trends starting from 1895
        regional_stats = analyze_regional_trends(station_results, metric, start_year=1895)
        regional_stats["temp_metric"] = metric
        all_regional_stats.append(regional_stats)
        
        # Save regional statistics
        output_file = args.output_dir / "data" / f"regional_statistics_{metric}.csv"
        regional_stats.to_csv(output_file, index=False)
        print(f"Saved regional statistics to {output_file}")
        
        # Test regional homogeneity
        homogeneity_test = test_regional_homogeneity(station_results, regional_stats)
        
        # Create visualizations
        create_regional_visualizations(
            station_results,
            regional_stats,
            args.output_dir / "plots",
            metric
        )
        
        # Print summary
        print(f"\nRegional Analysis Summary for {metric.upper()}:")
        print(f"Number of regions analyzed: {len(regional_stats)}")
        print(f"\nRegional mean trends:")
        for _, row in regional_stats.iterrows():
            sig = "*" if row["trend_different_from_zero"] else " "
            print(f"  {row['region']:12s}: {row['mean_trend']:6.3f} ± {row['sem_trend']:5.3f} °C/decade {sig}")
        
        if homogeneity_test["test_possible"]:
            print(f"\nRegional homogeneity test:")
            print(f"  ANOVA p-value: {homogeneity_test['anova_p_value']:.4f}")
            print(f"  Interpretation: {homogeneity_test['interpretation']}")
            print(f"  Effect size (η²): {homogeneity_test['eta_squared']:.3f}")
    
    # Save combined regional statistics
    if all_regional_stats:
        combined_stats = pd.concat(all_regional_stats, ignore_index=True)
        output_file = args.output_dir / "data" / "regional_statistics_all.csv"
        combined_stats.to_csv(output_file, index=False)
        print(f"\nSaved combined regional statistics to {output_file}")


if __name__ == "__main__":
    main()