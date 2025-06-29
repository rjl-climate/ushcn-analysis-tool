#!/usr/bin/env python3
"""
Calculate progressive bias trends in NOAA temperature adjustments.

This script compares F52 (fully adjusted) data with TOB (time-of-observation adjusted) data
to identify any systematic, time-dependent bias in the adjustments.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.ushcn_heatisland.data.loaders import load_ushcn_data


def calculate_station_bias(
    tob_data: pd.DataFrame,
    f52_data: pd.DataFrame,
    station_id: str
) -> pd.DataFrame:
    """Calculate monthly bias (F52 - TOB) for a single station."""
    # Filter data for this station
    tob_station = tob_data[tob_data["id"] == station_id].copy()
    f52_station = f52_data[f52_data["id"] == station_id].copy()
    
    if tob_station.empty or f52_station.empty:
        return pd.DataFrame()
    
    # Merge on year and month
    merged = pd.merge(
        tob_station[["year", "month", "temperature"]],
        f52_station[["year", "month", "temperature"]],
        on=["year", "month"],
        suffixes=("_tob", "_f52")
    )
    
    # Calculate bias
    merged["bias"] = merged["temperature_f52"] - merged["temperature_tob"]
    merged["id"] = station_id
    
    # Create date column for easier plotting
    merged["date"] = pd.to_datetime(merged[["year", "month"]].assign(day=1))
    
    return merged[["id", "date", "year", "month", "bias"]]


def calculate_trend(bias_series: pd.Series, years: pd.Series, start_year: int = 1895) -> Dict:
    """Calculate linear trend in bias over time starting from specified year."""
    # Filter to start year and later
    year_mask = years >= start_year
    bias_filtered = bias_series[year_mask]
    years_filtered = years[year_mask]
    
    # Remove NaN values
    mask = ~(bias_filtered.isna() | years_filtered.isna())
    clean_bias = bias_filtered[mask]
    clean_years = years_filtered[mask]
    
    if len(clean_bias) < 30:  # Need at least 30 points for reliable trend
        return {
            "trend_per_decade": np.nan,
            "p_value": np.nan,
            "r_squared": np.nan,
            "n_points": len(clean_bias),
            "std_error": np.nan,
            "start_year": start_year
        }
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(clean_years, clean_bias)
    
    return {
        "trend_per_decade": slope * 10,  # Convert to per decade
        "p_value": p_value,
        "r_squared": r_value ** 2,
        "n_points": len(clean_bias),
        "std_error": std_err * 10,
        "start_year": start_year
    }


def analyze_network_bias(
    tob_data: pd.DataFrame,
    f52_data: pd.DataFrame,
    stations_gdf: pd.DataFrame,
    start_year: int = 1895
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Analyze bias trends across the entire network."""
    station_results = []
    all_bias_data = []
    
    print(f"Analyzing {len(stations_gdf)} stations...")
    
    for idx, station in stations_gdf.iterrows():
        station_id = station["id"]
        
        # Calculate bias for this station
        bias_data = calculate_station_bias(tob_data, f52_data, station_id)
        
        if bias_data.empty:
            continue
            
        all_bias_data.append(bias_data)
        
        # Calculate annual means for trend analysis
        annual_bias = bias_data.groupby("year")["bias"].agg(["mean", "count"])
        annual_bias = annual_bias[annual_bias["count"] >= 6]  # Require at least 6 months
        
        # Filter to start year and later
        annual_bias = annual_bias[annual_bias.index >= start_year]
        
        if len(annual_bias) < 10:  # Skip if less than 10 years of data after filtering
            continue
        
        # Calculate trend
        trend_stats = calculate_trend(annual_bias["mean"], annual_bias.index, start_year)
        
        # Store results
        station_results.append({
            "id": station_id,
            "name": station.get("name", "Unknown"),
            "lat": station.geometry.y,
            "lon": station.geometry.x,
            "state": station.get("state", "Unknown"),
            **trend_stats,
            "mean_bias": annual_bias["mean"].mean(),
            "bias_std": annual_bias["mean"].std(),
            "first_year": annual_bias.index.min(),
            "last_year": annual_bias.index.max(),
            "n_years": len(annual_bias)
        })
    
    # Combine all bias data
    if all_bias_data:
        combined_bias = pd.concat(all_bias_data, ignore_index=True)
    else:
        combined_bias = pd.DataFrame()
    
    return pd.DataFrame(station_results), combined_bias


def create_visualizations(
    station_results: pd.DataFrame,
    bias_data: pd.DataFrame,
    output_dir: Path,
    temp_metric: str
):
    """Create visualizations of bias trends."""
    # Set up style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. Time series of network-wide mean bias
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Calculate annual means across all stations (from 1895 onwards)
    annual_network_bias = bias_data[bias_data["year"] >= 1895].groupby("year")["bias"].agg(["mean", "std", "count"])
    
    # Plot with confidence interval
    ax.plot(annual_network_bias.index, annual_network_bias["mean"], 
            color="red", linewidth=2, label="Mean bias (F52 - TOB)")
    ax.fill_between(
        annual_network_bias.index,
        annual_network_bias["mean"] - annual_network_bias["std"] / np.sqrt(annual_network_bias["count"]),
        annual_network_bias["mean"] + annual_network_bias["std"] / np.sqrt(annual_network_bias["count"]),
        alpha=0.3, color="red", label="95% CI"
    )
    
    # Add trend line
    valid_years = annual_network_bias.index[~annual_network_bias["mean"].isna()]
    valid_bias = annual_network_bias.loc[valid_years, "mean"]
    if len(valid_years) > 10:
        z = np.polyfit(valid_years, valid_bias, 1)
        p = np.poly1d(z)
        ax.plot(valid_years, p(valid_years), "--", color="darkred", 
                label=f"Trend: {z[0]*10:.3f}°C/decade")
    
    ax.axhline(y=0, color="black", linestyle="-", alpha=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Adjustment Bias (°C)")
    ax.set_title(f"Network-Wide F52 vs TOB Adjustment Bias (1895+) - {temp_metric.upper()} Temperature")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f"bias_timeseries_{temp_metric}.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    # 2. Histogram of station trends
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Filter valid trends
    valid_trends = station_results[~station_results["trend_per_decade"].isna()]
    
    # Histogram
    ax1.hist(valid_trends["trend_per_decade"], bins=30, edgecolor="black", alpha=0.7)
    ax1.axvline(x=0, color="black", linestyle="--", alpha=0.5)
    ax1.axvline(x=valid_trends["trend_per_decade"].mean(), color="red", 
                linestyle="-", linewidth=2, label=f"Mean: {valid_trends['trend_per_decade'].mean():.3f}")
    ax1.set_xlabel("Bias Trend (°C/decade)")
    ax1.set_ylabel("Number of Stations")
    ax1.set_title("Distribution of Station Bias Trends")
    ax1.legend()
    
    # Significance plot
    significant = valid_trends[valid_trends["p_value"] < 0.05]
    sig_positive = significant[significant["trend_per_decade"] > 0]
    sig_negative = significant[significant["trend_per_decade"] < 0]
    
    ax2.bar(["Positive\n(warming)", "Negative\n(cooling)", "Not significant"], 
            [len(sig_positive), len(sig_negative), len(valid_trends) - len(significant)],
            color=["red", "blue", "gray"])
    ax2.set_ylabel("Number of Stations")
    ax2.set_title("Statistical Significance of Trends (p < 0.05)")
    
    # Add percentages
    for i, (label, count) in enumerate([
        ("Positive\n(warming)", len(sig_positive)),
        ("Negative\n(cooling)", len(sig_negative)),
        ("Not significant", len(valid_trends) - len(significant))
    ]):
        pct = 100 * count / len(valid_trends)
        ax2.text(i, count + 5, f"{pct:.1f}%", ha="center")
    
    plt.tight_layout()
    plt.savefig(output_dir / f"trend_distribution_{temp_metric}.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    # 3. Cumulative bias plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Calculate cumulative bias
    annual_mean = annual_network_bias["mean"].fillna(0)
    cumulative_bias = annual_mean.cumsum()
    
    ax.plot(cumulative_bias.index, cumulative_bias.values, 
            color="red", linewidth=3, label="Cumulative bias")
    ax.fill_between(cumulative_bias.index, 0, cumulative_bias.values, 
                    alpha=0.3, color="red")
    
    ax.axhline(y=0, color="black", linestyle="-", alpha=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative Bias (°C)")
    ax.set_title(f"Cumulative F52 Adjustment Bias (1895+) - {temp_metric.upper()} Temperature")
    ax.grid(True, alpha=0.3)
    
    # Add final value annotation
    final_year = cumulative_bias.index[-1]
    final_value = cumulative_bias.iloc[-1]
    ax.annotate(f"Total: {final_value:.2f}°C", 
                xy=(final_year, final_value),
                xytext=(final_year - 20, final_value + 0.5),
                arrowprops=dict(arrowstyle="->", color="black"),
                fontsize=12, fontweight="bold")
    
    plt.tight_layout()
    plt.savefig(output_dir / f"cumulative_bias_{temp_metric}.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"Visualizations saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Calculate progressive bias in temperature adjustments")
    parser.add_argument("--temp-metric", default="avg", choices=["min", "max", "avg", "all"],
                        help="Temperature metric to analyze")
    parser.add_argument("--data-dir", type=Path, default=Path("data"),
                        help="Directory containing USHCN data files")
    parser.add_argument("--output-dir", type=Path, 
                        default=Path("analysis/progressive_bias_investigation/outputs"),
                        help="Output directory for results")
    
    args = parser.parse_args()
    
    # Create output directories
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "plots").mkdir(exist_ok=True)
    (args.output_dir / "data").mkdir(exist_ok=True)
    
    # Determine which metrics to analyze
    if args.temp_metric == "all":
        metrics = ["min", "max", "avg"]
    else:
        metrics = [args.temp_metric]
    
    # Store results for all metrics
    all_results = {}
    
    for metric in metrics:
        print(f"\n{'='*60}")
        print(f"Analyzing {metric.upper()} temperature...")
        print(f"{'='*60}")
        
        # Load data
        print("Loading TOB adjusted data...")
        tob_data, _ = load_ushcn_data(
            args.data_dir,
            adjusted_type="tob",
            raw_type="raw",
            load_raw=False,
            temp_metric=metric
        )
        
        print("Loading F52 adjusted data...")
        f52_data, _ = load_ushcn_data(
            args.data_dir,
            adjusted_type="fls52",
            raw_type="raw",
            load_raw=False,
            temp_metric=metric
        )
        
        # Get station metadata - extract unique stations with coordinates from geometry
        station_info = tob_data[["station_id", "geometry"]].drop_duplicates()
        station_info["lat"] = station_info.geometry.y
        station_info["lon"] = station_info.geometry.x
        station_info = station_info.rename(columns={"station_id": "id"})
        stations_gdf = station_info.copy()
        
        # Convert to proper format for bias calculation
        tob_temps = pd.DataFrame({
            "id": tob_data["station_id"],
            "year": tob_data["timestamp"].dt.year,
            "month": tob_data["timestamp"].dt.month,
            "temperature": tob_data["temperature_celsius"]
        })
        
        f52_temps = pd.DataFrame({
            "id": f52_data["station_id"],
            "year": f52_data["timestamp"].dt.year,
            "month": f52_data["timestamp"].dt.month,
            "temperature": f52_data["temperature_celsius"]
        })
        
        print(f"Loaded {len(tob_temps)} TOB records and {len(f52_temps)} F52 records")
        
        # Analyze bias trends starting from 1895
        station_results, bias_data = analyze_network_bias(tob_temps, f52_temps, stations_gdf, start_year=1895)
        
        if station_results.empty:
            print(f"No valid results for {metric} temperature")
            continue
        
        # Save results
        output_file = args.output_dir / "data" / f"station_bias_trends_{metric}.csv"
        station_results.to_csv(output_file, index=False)
        print(f"Saved station results to {output_file}")
        
        # Create visualizations
        create_visualizations(
            station_results,
            bias_data,
            args.output_dir / "plots",
            metric
        )
        
        # Calculate summary statistics
        valid_trends = station_results[~station_results["trend_per_decade"].isna()]
        significant = valid_trends[valid_trends["p_value"] < 0.05]
        sig_positive = significant[significant["trend_per_decade"] > 0]
        
        summary = {
            "metric": metric,
            "total_stations": len(stations_gdf),
            "stations_analyzed": len(station_results),
            "stations_with_valid_trends": len(valid_trends),
            "mean_trend_per_decade": valid_trends["trend_per_decade"].mean(),
            "median_trend_per_decade": valid_trends["trend_per_decade"].median(),
            "std_trend_per_decade": valid_trends["trend_per_decade"].std(),
            "stations_significant_positive": len(sig_positive),
            "stations_significant_negative": len(significant) - len(sig_positive),
            "percent_significant_positive": 100 * len(sig_positive) / len(valid_trends),
            "network_trend_significance": "TBD",  # Will calculate separately
            "analysis_date": datetime.now().isoformat()
        }
        
        all_results[metric] = summary
        
        # Print summary
        print(f"\n{metric.upper()} Temperature Summary:")
        print(f"  Stations analyzed: {summary['stations_analyzed']}")
        print(f"  Mean bias trend: {summary['mean_trend_per_decade']:.3f} °C/decade")
        print(f"  Stations with significant positive trend: {summary['stations_significant_positive']} ({summary['percent_significant_positive']:.1f}%)")
    
    # Save combined summary
    summary_file = args.output_dir / "data" / "analysis_summary.json"
    with open(summary_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved analysis summary to {summary_file}")


if __name__ == "__main__":
    main()