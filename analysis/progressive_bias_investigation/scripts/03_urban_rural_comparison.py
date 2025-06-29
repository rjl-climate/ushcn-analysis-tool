#!/usr/bin/env python3
"""
Urban vs Rural comparison of progressive bias trends.

This script analyzes whether bias trends differ between urban and rural stations,
which would help distinguish between legitimate UHI corrections and systematic bias.
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
from src.ushcn_heatisland.urban.context import UrbanContextManager


def classify_stations_urban_rural(
    station_results: pd.DataFrame,
    data_dir: Path
) -> pd.DataFrame:
    """Classify stations as urban or rural using the existing urban context system."""
    print("Loading urban context data...")
    
    # Simple urban classification based on distance to large cities
    # Load US cities data
    cities_file = data_dir / "cities" / "us_cities_static.csv"
    if not cities_file.exists():
        # Fallback - classify all as rural for now
        print("Warning: Cities data not found, classifying all stations as rural")
        station_results["urban_rural"] = "rural"
        station_results["urban_category"] = "rural"
        return station_results
    
    cities_df = pd.read_csv(cities_file)
    
    # Filter to larger cities (population > 50,000)
    large_cities = cities_df[cities_df["population"] > 50000]
    
    # For each station, find distance to nearest large city
    from geopy.distance import geodesic
    
    def classify_station(row):
        station_coords = (row["lat"], row["lon"])
        
        # Calculate distance to nearest large city
        min_distance = float('inf')
        for _, city in large_cities.iterrows():
            city_coords = (city["latitude"], city["longitude"])
            distance = geodesic(station_coords, city_coords).kilometers
            min_distance = min(min_distance, distance)
        
        # Classify based on distance
        if min_distance <= 25:  # Within 25km of large city
            return "urban_core"
        elif min_distance <= 50:  # 25-50km from large city
            return "urban"
        elif min_distance <= 100:  # 50-100km from large city
            return "suburban" 
        else:  # >100km from large city
            return "rural"
    
    print("Classifying stations by distance to cities...")
    station_results["urban_category"] = station_results.apply(classify_station, axis=1)
    
    # Simplify to binary urban/rural classification
    def simplify_urban_category(category):
        if category in ["urban_core", "urban", "suburban"]:
            return "urban"
        else:
            return "rural"
    
    station_results["urban_rural"] = station_results["urban_category"].apply(simplify_urban_category)
    
    return station_results


def analyze_urban_rural_differences(
    classified_stations: pd.DataFrame,
    temp_metric: str,
    start_year: int = 1895
) -> Dict:
    """Analyze differences in bias trends between urban and rural stations."""
    # Filter valid trends and ensure they start from specified year
    valid_data = classified_stations[
        (~classified_stations["trend_per_decade"].isna()) & 
        (classified_stations["first_year"] <= start_year + 10)  # Allow some flexibility for start year
    ]
    
    # Separate urban and rural
    urban_data = valid_data[valid_data["urban_rural"] == "urban"]
    rural_data = valid_data[valid_data["urban_rural"] == "rural"]
    
    if len(urban_data) < 5 or len(rural_data) < 5:
        return {"analysis_possible": False, "reason": "Insufficient data"}
    
    # Extract trends
    urban_trends = urban_data["trend_per_decade"].values
    rural_trends = rural_data["trend_per_decade"].values
    
    # Basic statistics
    urban_stats = {
        "n_stations": len(urban_data),
        "mean_trend": np.mean(urban_trends),
        "median_trend": np.median(urban_trends),
        "std_trend": np.std(urban_trends),
        "sem_trend": stats.sem(urban_trends),
        "min_trend": np.min(urban_trends),
        "max_trend": np.max(urban_trends)
    }
    
    rural_stats = {
        "n_stations": len(rural_data),
        "mean_trend": np.mean(rural_trends),
        "median_trend": np.median(rural_trends),
        "std_trend": np.std(rural_trends),
        "sem_trend": stats.sem(rural_trends),
        "min_trend": np.min(rural_trends),
        "max_trend": np.max(rural_trends)
    }
    
    # Statistical tests
    # Two-sample t-test (assuming unequal variances)
    t_stat, t_p_value = stats.ttest_ind(urban_trends, rural_trends, equal_var=False)
    
    # Mann-Whitney U test (non-parametric)
    u_stat, u_p_value = stats.mannwhitneyu(urban_trends, rural_trends, alternative='two-sided')
    
    # Effect size (Cohen's d)
    pooled_std = np.sqrt(((len(urban_trends) - 1) * np.var(urban_trends, ddof=1) + 
                         (len(rural_trends) - 1) * np.var(rural_trends, ddof=1)) / 
                        (len(urban_trends) + len(rural_trends) - 2))
    cohens_d = (np.mean(urban_trends) - np.mean(rural_trends)) / pooled_std
    
    # Test each group against zero
    urban_ttest = stats.ttest_1samp(urban_trends, 0)
    rural_ttest = stats.ttest_1samp(rural_trends, 0)
    
    # Count significant stations
    urban_significant = urban_data[urban_data["p_value"] < 0.05]
    rural_significant = rural_data[rural_data["p_value"] < 0.05]
    
    urban_sig_positive = urban_significant[urban_significant["trend_per_decade"] > 0]
    rural_sig_positive = rural_significant[rural_significant["trend_per_decade"] > 0]
    
    return {
        "analysis_possible": True,
        "temp_metric": temp_metric,
        "urban": {
            **urban_stats,
            "n_significant": len(urban_significant),
            "n_sig_positive": len(urban_sig_positive),
            "pct_sig_positive": 100 * len(urban_sig_positive) / len(urban_data),
            "ttest_vs_zero_p": urban_ttest.pvalue,
            "significantly_different_from_zero": urban_ttest.pvalue < 0.05
        },
        "rural": {
            **rural_stats,
            "n_significant": len(rural_significant),
            "n_sig_positive": len(rural_sig_positive),
            "pct_sig_positive": 100 * len(rural_sig_positive) / len(rural_data),
            "ttest_vs_zero_p": rural_ttest.pvalue,
            "significantly_different_from_zero": rural_ttest.pvalue < 0.05
        },
        "comparison": {
            "mean_difference": urban_stats["mean_trend"] - rural_stats["mean_trend"],
            "ttest_statistic": t_stat,
            "ttest_p_value": t_p_value,
            "mannwhitney_statistic": u_stat,
            "mannwhitney_p_value": u_p_value,
            "cohens_d": cohens_d,
            "groups_differ": t_p_value < 0.05,
            "interpretation": interpret_comparison(t_p_value, cohens_d, urban_stats["mean_trend"], rural_stats["mean_trend"])
        }
    }


def interpret_comparison(p_value: float, cohens_d: float, urban_mean: float, rural_mean: float) -> str:
    """Interpret the urban vs rural comparison results."""
    if p_value >= 0.05:
        return "No significant difference between urban and rural bias trends"
    
    # Significant difference exists
    effect_size = "small" if abs(cohens_d) < 0.5 else "medium" if abs(cohens_d) < 0.8 else "large"
    
    if urban_mean > rural_mean:
        direction = "Urban stations show stronger positive bias trends than rural stations"
    else:
        direction = "Rural stations show stronger positive bias trends than urban stations"
    
    return f"{direction} ({effect_size} effect size)"


def analyze_detailed_urban_categories(
    classified_stations: pd.DataFrame,
    temp_metric: str,
    start_year: int = 1895
) -> pd.DataFrame:
    """Analyze bias trends across the detailed 4-level urban hierarchy."""
    # Filter valid trends and ensure they start from specified year
    valid_data = classified_stations[
        (~classified_stations["trend_per_decade"].isna()) & 
        (classified_stations["first_year"] <= start_year + 10)  # Allow some flexibility for start year
    ]
    
    # Define category order
    category_order = ["rural", "suburban", "urban", "urban_core"]
    
    detailed_stats = []
    
    for category in category_order:
        category_data = valid_data[valid_data.get("urban_category", "rural") == category]
        
        if len(category_data) < 3:
            continue
        
        trends = category_data["trend_per_decade"].values
        significant = category_data[category_data["p_value"] < 0.05]
        sig_positive = significant[significant["trend_per_decade"] > 0]
        
        # Test against zero
        t_stat, p_value = stats.ttest_1samp(trends, 0)
        
        detailed_stats.append({
            "category": category,
            "n_stations": len(category_data),
            "mean_trend": np.mean(trends),
            "median_trend": np.median(trends),
            "std_trend": np.std(trends),
            "sem_trend": stats.sem(trends),
            "n_significant": len(significant),
            "n_sig_positive": len(sig_positive),
            "pct_sig_positive": 100 * len(sig_positive) / len(category_data),
            "ttest_statistic": t_stat,
            "ttest_p_value": p_value,
            "significantly_different_from_zero": p_value < 0.05
        })
    
    return pd.DataFrame(detailed_stats)


def create_urban_rural_visualizations(
    classified_stations: pd.DataFrame,
    analysis_results: Dict,
    detailed_stats: pd.DataFrame,
    output_dir: Path,
    temp_metric: str
):
    """Create visualizations comparing urban and rural bias trends."""
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Filter valid data
    valid_data = classified_stations[~classified_stations["trend_per_decade"].isna()]
    
    # 1. Box plot comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Binary urban/rural comparison
    urban_data = valid_data[valid_data["urban_rural"] == "urban"]["trend_per_decade"]
    rural_data = valid_data[valid_data["urban_rural"] == "rural"]["trend_per_decade"]
    
    bp1 = ax1.boxplot([rural_data, urban_data], 
                      labels=["Rural", "Urban"],
                      patch_artist=True,
                      showfliers=True)
    
    # Color boxes
    bp1['boxes'][0].set_facecolor('lightgreen')
    bp1['boxes'][1].set_facecolor('lightcoral')
    
    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax1.set_ylabel("Bias Trend (°C/decade)")
    ax1.set_title(f"Urban vs Rural Bias Trends\n{temp_metric.upper()} Temperature")
    
    # Add sample sizes and means
    ax1.text(1, ax1.get_ylim()[1]*0.9, f'n={len(rural_data)}\n{np.mean(rural_data):.3f}°C/dec', 
             ha='center', fontsize=10)
    ax1.text(2, ax1.get_ylim()[1]*0.9, f'n={len(urban_data)}\n{np.mean(urban_data):.3f}°C/dec', 
             ha='center', fontsize=10)
    
    # 4-level hierarchy comparison
    if not detailed_stats.empty:
        categories = detailed_stats["category"].tolist()
        trend_data = []
        for cat in categories:
            cat_data = valid_data[valid_data.get("urban_category", "rural") == cat]["trend_per_decade"]
            trend_data.append(cat_data.values)
        
        bp2 = ax2.boxplot(trend_data,
                          labels=categories,
                          patch_artist=True,
                          showfliers=True)
        
        # Color boxes by urbanization level
        colors = ['lightgreen', 'yellow', 'orange', 'red']
        for box, color in zip(bp2['boxes'], colors[:len(categories)]):
            box.set_facecolor(color)
        
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_ylabel("Bias Trend (°C/decade)")
        ax2.set_title(f"Detailed Urban Hierarchy\n{temp_metric.upper()} Temperature")
        ax2.tick_params(axis='x', rotation=45)
        
        # Add sample sizes
        for i, (cat, row) in enumerate(detailed_stats.iterrows()):
            ax2.text(i+1, ax2.get_ylim()[1]*0.9, f'n={row["n_stations"]}', 
                     ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / f"urban_rural_boxplot_{temp_metric}.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    # 2. Bar plot of means with error bars
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if analysis_results["analysis_possible"]:
        categories = ["Rural", "Urban"]
        means = [analysis_results["rural"]["mean_trend"], 
                 analysis_results["urban"]["mean_trend"]]
        errors = [analysis_results["rural"]["sem_trend"], 
                  analysis_results["urban"]["sem_trend"]]
        colors = ['lightgreen', 'lightcoral']
        
        bars = ax.bar(categories, means, yerr=errors, capsize=5, color=colors, 
                      edgecolor='black', linewidth=1)
        
        # Add significance indicators
        if analysis_results["rural"]["significantly_different_from_zero"]:
            ax.text(0, means[0] + errors[0] + 0.002, '*', ha='center', fontsize=16, fontweight='bold')
        if analysis_results["urban"]["significantly_different_from_zero"]:
            ax.text(1, means[1] + errors[1] + 0.002, '*', ha='center', fontsize=16, fontweight='bold')
        
        # Add comparison significance
        if analysis_results["comparison"]["groups_differ"]:
            y_max = max(means[i] + errors[i] for i in range(2)) + 0.005
            ax.plot([0, 1], [y_max, y_max], 'k-', linewidth=1)
            ax.text(0.5, y_max + 0.002, '**', ha='center', fontsize=14, fontweight='bold')
        
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax.set_ylabel("Mean Bias Trend (°C/decade)")
        ax.set_title(f"Urban vs Rural Mean Bias Trends - {temp_metric.upper()} Temperature")
        
        # Add values on bars
        for i, (bar, mean, n) in enumerate(zip(bars, means, 
                                               [analysis_results["rural"]["n_stations"],
                                                analysis_results["urban"]["n_stations"]])):
            ax.text(bar.get_x() + bar.get_width()/2, mean/2, 
                    f'{mean:.3f}\n(n={n})', ha='center', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / f"urban_rural_means_{temp_metric}.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    # 3. Spatial distribution map
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot rural stations
    rural_stations = valid_data[valid_data["urban_rural"] == "rural"]
    urban_stations = valid_data[valid_data["urban_rural"] == "urban"]
    
    # Plot with different markers
    rural_scatter = ax.scatter(rural_stations["lon"], rural_stations["lat"],
                              c=rural_stations["trend_per_decade"],
                              cmap='RdBu_r', vmin=-0.05, vmax=0.05,
                              s=40, marker='o', alpha=0.7,
                              edgecolors='darkgreen', linewidth=1,
                              label=f'Rural (n={len(rural_stations)})')
    
    urban_scatter = ax.scatter(urban_stations["lon"], urban_stations["lat"],
                              c=urban_stations["trend_per_decade"],
                              cmap='RdBu_r', vmin=-0.05, vmax=0.05,
                              s=40, marker='s', alpha=0.7,
                              edgecolors='darkred', linewidth=1,
                              label=f'Urban (n={len(urban_stations)})')
    
    # Add colorbar
    cbar = plt.colorbar(rural_scatter, ax=ax, label='Bias Trend (°C/decade)')
    
    # Set limits for continental US
    ax.set_xlim(-125, -65)
    ax.set_ylim(24, 50)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Spatial Distribution: Urban vs Rural Bias Trends - {temp_metric.upper()} Temperature")
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / f"urban_rural_spatial_{temp_metric}.png", dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"Urban/rural visualizations saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Compare bias trends between urban and rural stations")
    parser.add_argument("--temp-metric", default="avg", choices=["min", "max", "avg", "all"],
                        help="Temperature metric to analyze")
    parser.add_argument("--input-dir", type=Path,
                        default=Path("analysis/progressive_bias_investigation/outputs/data"),
                        help="Directory containing bias trend results")
    parser.add_argument("--data-dir", type=Path, default=Path("data"),
                        help="Directory containing USHCN data files")
    parser.add_argument("--output-dir", type=Path,
                        default=Path("analysis/progressive_bias_investigation/outputs"),
                        help="Output directory for results")
    
    args = parser.parse_args()
    
    # Determine which metrics to analyze
    if args.temp_metric == "all":
        metrics = ["min", "max", "avg"]
    else:
        metrics = [args.temp_metric]
    
    all_results = {}
    
    for metric in metrics:
        print(f"\n{'='*60}")
        print(f"Analyzing urban vs rural patterns for {metric.upper()} temperature...")
        print(f"{'='*60}")
        
        # Load station results
        input_file = args.input_dir / f"station_bias_trends_{metric}.csv"
        if not input_file.exists():
            print(f"Input file not found: {input_file}")
            print("Please run 01_calculate_bias_trends.py first")
            continue
        
        station_results = pd.read_csv(input_file)
        print(f"Loaded {len(station_results)} station results")
        
        # Classify stations as urban/rural
        classified_stations = classify_stations_urban_rural(station_results, args.data_dir)
        print(f"Classified {len(classified_stations)} stations")
        
        # Count classifications
        urban_count = len(classified_stations[classified_stations["urban_rural"] == "urban"])
        rural_count = len(classified_stations[classified_stations["urban_rural"] == "rural"])
        print(f"Urban stations: {urban_count}, Rural stations: {rural_count}")
        
        # Analyze differences (starting from 1895)
        analysis_results = analyze_urban_rural_differences(classified_stations, metric, start_year=1895)
        
        if not analysis_results["analysis_possible"]:
            print(f"Analysis not possible: {analysis_results.get('reason', 'Unknown')}")
            continue
        
        # Detailed category analysis (starting from 1895)
        detailed_stats = analyze_detailed_urban_categories(classified_stations, metric, start_year=1895)
        
        # Save results (convert numpy types for JSON serialization)
        def convert_numpy_types(obj):
            """Convert numpy types to Python native types for JSON serialization."""
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        serializable_results = convert_numpy_types(analysis_results)
        results_file = args.output_dir / "data" / f"urban_rural_analysis_{metric}.json"
        with open(results_file, "w") as f:
            json.dump(serializable_results, f, indent=2)
        print(f"Saved analysis results to {results_file}")
        
        if not detailed_stats.empty:
            detailed_file = args.output_dir / "data" / f"detailed_urban_stats_{metric}.csv"
            detailed_stats.to_csv(detailed_file, index=False)
            print(f"Saved detailed statistics to {detailed_file}")
        
        # Create visualizations
        create_urban_rural_visualizations(
            classified_stations,
            analysis_results,
            detailed_stats,
            args.output_dir / "plots",
            metric
        )
        
        # Print summary
        print(f"\nUrban vs Rural Analysis Summary for {metric.upper()}:")
        if analysis_results["analysis_possible"]:
            urban = analysis_results["urban"]
            rural = analysis_results["rural"]
            comp = analysis_results["comparison"]
            
            print(f"\nUrban stations (n={urban['n_stations']}):")
            print(f"  Mean trend: {urban['mean_trend']:.3f} ± {urban['sem_trend']:.3f} °C/decade")
            print(f"  Significant positive: {urban['n_sig_positive']} ({urban['pct_sig_positive']:.1f}%)")
            print(f"  Different from zero: {'Yes' if urban['significantly_different_from_zero'] else 'No'}")
            
            print(f"\nRural stations (n={rural['n_stations']}):")
            print(f"  Mean trend: {rural['mean_trend']:.3f} ± {rural['sem_trend']:.3f} °C/decade")
            print(f"  Significant positive: {rural['n_sig_positive']} ({rural['pct_sig_positive']:.1f}%)")
            print(f"  Different from zero: {'Yes' if rural['significantly_different_from_zero'] else 'No'}")
            
            print(f"\nComparison:")
            print(f"  Difference (Urban - Rural): {comp['mean_difference']:.3f} °C/decade")
            print(f"  Statistical significance: p = {comp['ttest_p_value']:.4f}")
            print(f"  Effect size (Cohen's d): {comp['cohens_d']:.3f}")
            print(f"  Interpretation: {comp['interpretation']}")
        
        all_results[metric] = analysis_results
    
    # Save combined results
    if all_results:
        # Convert numpy types for JSON serialization
        def convert_numpy_types(obj):
            """Convert numpy types to Python native types for JSON serialization."""
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        serializable_all_results = convert_numpy_types(all_results)
        combined_file = args.output_dir / "data" / "urban_rural_analysis_all.json"
        with open(combined_file, "w") as f:
            json.dump(serializable_all_results, f, indent=2)
        print(f"\nSaved combined analysis results to {combined_file}")


if __name__ == "__main__":
    main()