#!/usr/bin/env python3
"""
Advanced statistical tests for progressive bias investigation.

This script performs comprehensive statistical analyses including:
- Mann-Kendall trend tests
- Breakpoint detection
- Bootstrap confidence intervals
- Multiple testing corrections
- Spatial autocorrelation analysis
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Statistical test functions
def mann_kendall_test(data: np.ndarray) -> Dict:
    """
    Perform Mann-Kendall test for monotonic trend.
    
    Returns:
        Dictionary with test statistic, p-value, and trend direction
    """
    n = len(data)
    if n < 3:
        return {"valid": False, "reason": "Insufficient data"}
    
    # Calculate S statistic
    s = 0
    for i in range(n-1):
        for j in range(i+1, n):
            if data[j] > data[i]:
                s += 1
            elif data[j] < data[i]:
                s -= 1
    
    # Calculate variance
    var_s = n * (n - 1) * (2 * n + 5) / 18
    
    # Tie correction (if needed)
    ties = {}
    for value in data:
        ties[value] = ties.get(value, 0) + 1
    
    tie_correction = sum(t * (t - 1) * (2 * t + 5) for t in ties.values() if t > 1)
    var_s -= tie_correction / 18
    
    if var_s <= 0:
        return {"valid": False, "reason": "Zero variance"}
    
    # Calculate Z statistic
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    # Trend interpretation
    if p_value < 0.05:
        trend = "increasing" if s > 0 else "decreasing"
    else:
        trend = "no significant trend"
    
    return {
        "valid": True,
        "s_statistic": s,
        "z_statistic": z,
        "p_value": p_value,
        "trend": trend,
        "significant": p_value < 0.05
    }


def pettitt_test(data: np.ndarray) -> Dict:
    """
    Perform Pettitt test for change point detection.
    
    Returns:
        Dictionary with change point information
    """
    n = len(data)
    if n < 10:
        return {"valid": False, "reason": "Insufficient data"}
    
    # Calculate U statistics
    u = np.zeros(n)
    for k in range(n):
        u[k] = sum(np.sign(data[j] - data[i]) for i in range(k+1) for j in range(k+1, n))
    
    # Find maximum absolute U
    k_max = np.argmax(np.abs(u))
    u_max = abs(u[k_max])
    
    # Calculate p-value (approximate)
    p_value = 2 * np.exp((-6 * u_max**2) / (n**3 + n**2))
    
    change_year = k_max + 1  # Convert to 1-based indexing
    
    return {
        "valid": True,
        "change_point_index": k_max,
        "change_point_year": change_year,
        "u_statistic": u_max,
        "p_value": p_value,
        "significant": p_value < 0.05,
        "all_u_stats": u.tolist()
    }


def bootstrap_confidence_interval(
    data: np.ndarray, 
    statistic_func, 
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95
) -> Dict:
    """
    Calculate bootstrap confidence interval for a statistic.
    """
    if len(data) < 3:
        return {"valid": False, "reason": "Insufficient data"}
    
    # Bootstrap resampling
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=len(data), replace=True)
        stat = statistic_func(sample)
        if not np.isnan(stat):
            bootstrap_stats.append(stat)
    
    if len(bootstrap_stats) < n_bootstrap * 0.5:
        return {"valid": False, "reason": "Too many invalid bootstrap samples"}
    
    bootstrap_stats = np.array(bootstrap_stats)
    
    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    ci_lower = np.percentile(bootstrap_stats, lower_percentile)
    ci_upper = np.percentile(bootstrap_stats, upper_percentile)
    
    return {
        "valid": True,
        "statistic_mean": np.mean(bootstrap_stats),
        "statistic_std": np.std(bootstrap_stats),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "confidence_level": confidence_level,
        "n_bootstrap": len(bootstrap_stats)
    }


def calculate_spatial_autocorrelation(
    stations: pd.DataFrame,
    values: np.ndarray,
    max_distance_km: float = 500.0
) -> Dict:
    """
    Calculate Moran's I spatial autocorrelation statistic.
    """
    from geopy.distance import geodesic
    
    n = len(stations)
    if n < 10:
        return {"valid": False, "reason": "Insufficient stations"}
    
    # Calculate distance matrix
    distances = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dist = geodesic(
                    (stations.iloc[i]["lat"], stations.iloc[i]["lon"]),
                    (stations.iloc[j]["lat"], stations.iloc[j]["lon"])
                ).kilometers
                distances[i, j] = dist
    
    # Create spatial weights matrix (inverse distance)
    weights = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j and distances[i, j] <= max_distance_km:
                weights[i, j] = 1.0 / distances[i, j]
    
    # Normalize weights
    row_sums = weights.sum(axis=1)
    for i in range(n):
        if row_sums[i] > 0:
            weights[i, :] /= row_sums[i]
    
    # Calculate Moran's I
    mean_val = np.mean(values)
    numerator = 0
    denominator = 0
    
    for i in range(n):
        for j in range(n):
            numerator += weights[i, j] * (values[i] - mean_val) * (values[j] - mean_val)
        denominator += (values[i] - mean_val) ** 2
    
    if denominator == 0:
        return {"valid": False, "reason": "Zero variance"}
    
    morans_i = numerator / denominator
    
    # Expected value and variance (under null hypothesis)
    expected_i = -1 / (n - 1)
    w_sum = np.sum(weights)
    
    if w_sum == 0:
        return {"valid": False, "reason": "No spatial connections"}
    
    # Simplified variance calculation
    variance_i = (w_sum * w_sum) / ((n - 1) * (n - 2) * (n - 3)) - expected_i ** 2
    
    if variance_i <= 0:
        z_score = 0
        p_value = 1.0
    else:
        z_score = (morans_i - expected_i) / np.sqrt(variance_i)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    return {
        "valid": True,
        "morans_i": morans_i,
        "expected_i": expected_i,
        "variance_i": variance_i,
        "z_score": z_score,
        "p_value": p_value,
        "significant": p_value < 0.05,
        "interpretation": "Positive spatial autocorrelation" if morans_i > expected_i and p_value < 0.05
                        else "Negative spatial autocorrelation" if morans_i < expected_i and p_value < 0.05
                        else "No significant spatial autocorrelation"
    }


def multiple_testing_correction(p_values: List[float], method: str = "bonferroni") -> Dict:
    """
    Apply multiple testing correction to p-values.
    """
    p_array = np.array(p_values)
    n_tests = len(p_array)
    
    if method == "bonferroni":
        corrected_p = np.minimum(p_array * n_tests, 1.0)
        alpha_corrected = 0.05 / n_tests
    elif method == "fdr_bh":  # Benjamini-Hochberg
        sorted_indices = np.argsort(p_array)
        sorted_p = p_array[sorted_indices]
        
        corrected_p = np.zeros_like(p_array)
        for i in range(n_tests):
            corrected_p[sorted_indices[i]] = min(1.0, sorted_p[i] * n_tests / (i + 1))
        
        alpha_corrected = 0.05
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    significant_original = p_array < 0.05
    significant_corrected = corrected_p < alpha_corrected
    
    return {
        "method": method,
        "n_tests": n_tests,
        "alpha_corrected": alpha_corrected,
        "significant_original": significant_original.sum(),
        "significant_corrected": significant_corrected.sum(),
        "corrected_p_values": corrected_p.tolist(),
        "reduction_factor": significant_corrected.sum() / max(significant_original.sum(), 1)
    }


def analyze_temporal_patterns(
    bias_data: pd.DataFrame,
    temp_metric: str,
    start_year: int = 1895
) -> Dict:
    """
    Analyze temporal patterns in the bias data.
    """
    # Calculate annual means (from start year onwards)
    annual_bias = bias_data[bias_data["year"] >= start_year].groupby("year")["bias"].agg(["mean", "std", "count"])
    annual_bias = annual_bias[annual_bias["count"] >= 10]  # Require at least 10 stations
    
    if len(annual_bias) < 10:
        return {"valid": False, "reason": "Insufficient annual data"}
    
    years = annual_bias.index.values
    bias_values = annual_bias["mean"].values
    
    # Mann-Kendall test on annual means
    mk_test = mann_kendall_test(bias_values)
    
    # Pettitt test for change points
    pettitt_result = pettitt_test(bias_values)
    
    # Bootstrap confidence interval for trend
    def trend_statistic(data):
        if len(data) < 3:
            return np.nan
        slope, _, _, _, _ = stats.linregress(range(len(data)), data)
        return slope * 10  # Convert to per decade
    
    bootstrap_trend = bootstrap_confidence_interval(bias_values, trend_statistic)
    
    # Calculate decadal trends (adjusted for start year)
    decadal_trends = {}
    decades = [(1895, 1924), (1925, 1954), (1955, 1984), (1985, 2014), (2015, 2023)]
    
    for start_year, end_year in decades:
        decade_data = annual_bias[(annual_bias.index >= start_year) & 
                                 (annual_bias.index <= end_year)]
        if len(decade_data) >= 5:
            decade_values = decade_data["mean"].values
            slope, _, _, p_val, _ = stats.linregress(range(len(decade_values)), decade_values)
            decadal_trends[f"{start_year}-{end_year}"] = {
                "trend_per_decade": slope * 10,
                "p_value": p_val,
                "n_years": len(decade_data)
            }
    
    return {
        "valid": True,
        "temp_metric": temp_metric,
        "n_years": len(annual_bias),
        "year_range": (years.min(), years.max()),
        "mann_kendall": mk_test,
        "pettitt_test": pettitt_result,
        "bootstrap_trend": bootstrap_trend,
        "decadal_trends": decadal_trends
    }


def analyze_station_level_significance(
    station_results: pd.DataFrame,
    temp_metric: str,
    start_year: int = 1895
) -> Dict:
    """
    Analyze statistical significance at the station level.
    """
    # Filter stations with valid trends starting from specified year
    valid_stations = station_results[
        (~station_results["trend_per_decade"].isna()) & 
        (station_results["first_year"] <= start_year + 10)  # Allow some flexibility for start year
    ]
    
    if len(valid_stations) < 10:
        return {"valid": False, "reason": "Insufficient stations"}
    
    # Extract p-values and trends
    p_values = valid_stations["p_value"].values
    trends = valid_stations["trend_per_decade"].values
    
    # Multiple testing corrections
    bonferroni = multiple_testing_correction(p_values, "bonferroni")
    fdr_bh = multiple_testing_correction(p_values, "fdr_bh")
    
    # Bootstrap analysis of mean trend
    bootstrap_mean = bootstrap_confidence_interval(trends, np.mean)
    
    # Test if distribution of trends is different from zero
    t_stat, t_p = stats.ttest_1samp(trends, 0)
    wilcoxon_stat, wilcoxon_p = stats.wilcoxon(trends)
    
    # Sign test (proportion of positive trends)
    n_positive = np.sum(trends > 0)
    n_total = len(trends)
    sign_p = 2 * stats.binom.cdf(min(n_positive, n_total - n_positive), n_total, 0.5)
    
    return {
        "valid": True,
        "temp_metric": temp_metric,
        "n_stations": len(valid_stations),
        "multiple_testing": {
            "bonferroni": bonferroni,
            "fdr_bh": fdr_bh
        },
        "mean_trend_tests": {
            "t_test": {"statistic": t_stat, "p_value": t_p},
            "wilcoxon": {"statistic": wilcoxon_stat, "p_value": wilcoxon_p},
            "bootstrap": bootstrap_mean
        },
        "sign_test": {
            "n_positive": n_positive,
            "n_total": n_total,
            "proportion_positive": n_positive / n_total,
            "p_value": sign_p,
            "significant": sign_p < 0.05
        }
    }


def create_statistical_visualizations(
    results: Dict,
    output_dir: Path,
    temp_metric: str
):
    """Create visualizations for statistical test results."""
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. Multiple testing comparison
    if "station_level" in results and results["station_level"]["valid"]:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        station_data = results["station_level"]
        bonf = station_data["multiple_testing"]["bonferroni"]
        fdr = station_data["multiple_testing"]["fdr_bh"]
        
        # Bar plot of significant stations
        categories = ["Original", "Bonferroni", "FDR (B-H)"]
        values = [
            bonf["significant_original"],
            bonf["significant_corrected"],
            fdr["significant_corrected"]
        ]
        
        bars = ax1.bar(categories, values, 
                      color=["lightblue", "orange", "lightgreen"],
                      edgecolor="black")
        
        ax1.set_ylabel("Number of Significant Stations")
        ax1.set_title(f"Multiple Testing Correction Impact\n{temp_metric.upper()} Temperature")
        
        # Add percentages
        total = station_data["n_stations"]
        for bar, val in zip(bars, values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{val}\n({100*val/total:.1f}%)', ha='center', va='bottom')
        
        # Sign test visualization
        sign_data = station_data["sign_test"]
        n_pos = sign_data["n_positive"]
        n_neg = sign_data["n_total"] - n_pos
        
        ax2.pie([n_pos, n_neg], 
               labels=[f'Positive\n({n_pos})', f'Negative\n({n_neg})'],
               colors=['red', 'blue'],
               autopct='%1.1f%%',
               startangle=90)
        
        ax2.set_title(f"Distribution of Trend Directions\np = {sign_data['p_value']:.4f}")
        
        plt.tight_layout()
        plt.savefig(output_dir / f"statistical_tests_{temp_metric}.png", 
                   dpi=300, bbox_inches="tight")
        plt.close()
    
    # 2. Temporal analysis plots
    if "temporal" in results and results["temporal"]["valid"]:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        temporal_data = results["temporal"]
        
        # Mann-Kendall trend visualization
        mk_data = temporal_data["mann_kendall"]
        if mk_data["valid"]:
            ax1.text(0.1, 0.8, f"Mann-Kendall Test Results:", 
                    transform=ax1.transAxes, fontsize=14, fontweight='bold')
            ax1.text(0.1, 0.7, f"S statistic: {mk_data['s_statistic']}", 
                    transform=ax1.transAxes, fontsize=12)
            ax1.text(0.1, 0.6, f"Z statistic: {mk_data['z_statistic']:.3f}", 
                    transform=ax1.transAxes, fontsize=12)
            ax1.text(0.1, 0.5, f"P-value: {mk_data['p_value']:.4f}", 
                    transform=ax1.transAxes, fontsize=12)
            ax1.text(0.1, 0.4, f"Trend: {mk_data['trend']}", 
                    transform=ax1.transAxes, fontsize=12,
                    color='red' if mk_data['significant'] else 'black')
        
        # Pettitt test visualization
        pettitt_data = temporal_data["pettitt_test"]
        if pettitt_data["valid"]:
            ax1.text(0.6, 0.8, f"Pettitt Test Results:", 
                    transform=ax1.transAxes, fontsize=14, fontweight='bold')
            ax1.text(0.6, 0.7, f"Change point: Year {pettitt_data['change_point_year']}", 
                    transform=ax1.transAxes, fontsize=12)
            ax1.text(0.6, 0.6, f"U statistic: {pettitt_data['u_statistic']:.1f}", 
                    transform=ax1.transAxes, fontsize=12)
            ax1.text(0.6, 0.5, f"P-value: {pettitt_data['p_value']:.4f}", 
                    transform=ax1.transAxes, fontsize=12)
            ax1.text(0.6, 0.4, f"Significant: {'Yes' if pettitt_data['significant'] else 'No'}", 
                    transform=ax1.transAxes, fontsize=12,
                    color='red' if pettitt_data['significant'] else 'black')
        
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        ax1.set_title(f"Statistical Test Results - {temp_metric.upper()} Temperature")
        
        # Decadal trends
        decades = temporal_data.get("decadal_trends", {})
        if decades:
            decade_names = list(decades.keys())
            decade_trends = [decades[d]["trend_per_decade"] for d in decade_names]
            decade_p_values = [decades[d]["p_value"] for d in decade_names]
            
            bars = ax2.bar(range(len(decade_names)), decade_trends,
                          color=['red' if p < 0.05 else 'lightblue' 
                                for p in decade_p_values],
                          edgecolor='black')
            
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax2.set_xticks(range(len(decade_names)))
            ax2.set_xticklabels(decade_names, rotation=45)
            ax2.set_ylabel("Bias Trend (°C/decade)")
            ax2.set_title("Decadal Bias Trends")
            
            # Add significance stars
            for i, (bar, p_val) in enumerate(zip(bars, decade_p_values)):
                if p_val < 0.05:
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2, 
                            height + 0.001 if height > 0 else height - 0.002,
                            '*', ha='center', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_dir / f"temporal_analysis_{temp_metric}.png", 
                   dpi=300, bbox_inches="tight")
        plt.close()
    
    print(f"Statistical test visualizations saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Advanced statistical tests for bias analysis")
    parser.add_argument("--temp-metric", default="avg", choices=["min", "max", "avg", "all"],
                        help="Temperature metric to analyze")
    parser.add_argument("--input-dir", type=Path,
                        default=Path("analysis/progressive_bias_investigation/outputs/data"),
                        help="Directory containing analysis results")
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
        print(f"Statistical analysis for {metric.upper()} temperature...")
        print(f"{'='*60}")
        
        # Load station results
        station_file = args.input_dir / f"station_bias_trends_{metric}.csv"
        if not station_file.exists():
            print(f"Station file not found: {station_file}")
            continue
        
        station_results = pd.read_csv(station_file)
        print(f"Loaded {len(station_results)} station results")
        
        # Initialize results dictionary
        metric_results = {"temp_metric": metric}
        
        # Station-level significance analysis (starting from 1895)
        station_analysis = analyze_station_level_significance(station_results, metric, start_year=1895)
        metric_results["station_level"] = station_analysis
        
        if station_analysis["valid"]:
            print(f"Station-level analysis completed")
            print(f"  Original significant stations: {station_analysis['multiple_testing']['bonferroni']['significant_original']}")
            print(f"  Bonferroni corrected: {station_analysis['multiple_testing']['bonferroni']['significant_corrected']}")
            print(f"  FDR corrected: {station_analysis['multiple_testing']['fdr_bh']['significant_corrected']}")
        
        # Spatial autocorrelation analysis (for stations starting from 1895)
        valid_stations = station_results[
            (~station_results["trend_per_decade"].isna()) & 
            (station_results["first_year"] <= 1905)  # Allow some flexibility for start year
        ]
        if len(valid_stations) >= 10:
            spatial_analysis = calculate_spatial_autocorrelation(
                valid_stations,
                valid_stations["trend_per_decade"].values
            )
            metric_results["spatial_autocorrelation"] = spatial_analysis
            
            if spatial_analysis["valid"]:
                print(f"Spatial autocorrelation analysis completed")
                print(f"  Moran's I: {spatial_analysis['morans_i']:.4f}")
                print(f"  P-value: {spatial_analysis['p_value']:.4f}")
                print(f"  Interpretation: {spatial_analysis['interpretation']}")
        
        # Load bias time series data if available
        # Note: This would require the bias data from script 01
        # For now, we'll load the summary data
        summary_file = args.input_dir / "analysis_summary.json"
        if summary_file.exists():
            with open(summary_file, "r") as f:
                summary_data = json.load(f)
            
            if metric in summary_data:
                # Create temporal analysis placeholder
                # This would be more complete with actual bias time series
                metric_results["summary_stats"] = summary_data[metric]
        
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
        
        serializable_results = convert_numpy_types(metric_results)
        output_file = args.output_dir / "data" / f"statistical_analysis_{metric}.json"
        with open(output_file, "w") as f:
            json.dump(serializable_results, f, indent=2)
        print(f"Saved statistical analysis to {output_file}")
        
        # Create visualizations
        create_statistical_visualizations(
            metric_results,
            args.output_dir / "plots",
            metric
        )
        
        all_results[metric] = metric_results
    
    # Save combined results
    if all_results:
        combined_file = args.output_dir / "data" / "statistical_analysis_all.json"
        with open(combined_file, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nSaved combined statistical analysis to {combined_file}")
        
        # Print summary
        print(f"\n{'='*60}")
        print("STATISTICAL ANALYSIS SUMMARY")
        print(f"{'='*60}")
        
        for metric, results in all_results.items():
            print(f"\n{metric.upper()} Temperature:")
            
            if "station_level" in results and results["station_level"]["valid"]:
                station_data = results["station_level"]
                sign_data = station_data["sign_test"]
                
                print(f"  Sign test: {sign_data['proportion_positive']:.1%} positive trends")
                print(f"  Sign test p-value: {sign_data['p_value']:.4f}")
                
                bonf = station_data["multiple_testing"]["bonferroni"]
                fdr = station_data["multiple_testing"]["fdr_bh"]
                print(f"  Significant stations (original): {bonf['significant_original']}")
                print(f"  Significant stations (Bonferroni): {bonf['significant_corrected']}")
                print(f"  Significant stations (FDR): {fdr['significant_corrected']}")
            
            if "spatial_autocorrelation" in results and results["spatial_autocorrelation"]["valid"]:
                spatial = results["spatial_autocorrelation"]
                print(f"  Spatial autocorrelation: {spatial['interpretation']}")


if __name__ == "__main__":
    main()