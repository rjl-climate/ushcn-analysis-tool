#!/usr/bin/env python3
"""
Cross-metric comparison analysis for progressive bias investigation.

This script synthesizes findings across average, minimum, and maximum temperature
metrics to provide a comprehensive view of bias patterns in NOAA adjustments.

Usage:
    python 05_comparative_metrics_analysis.py
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path

# Add the repository root to Python path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(repo_root))

def load_metric_data(metric: str, outputs_dir: Path) -> dict:
    """Load all analysis data for a specific temperature metric."""
    data = {"metric": metric}
    
    # Load summary statistics
    summary_file = outputs_dir / "data" / "analysis_summary.json"
    if summary_file.exists():
        with open(summary_file) as f:
            summary_data = json.load(f)
            if metric in summary_data:
                data["summary"] = summary_data[metric]
    
    # Load station trends
    trends_file = outputs_dir / "data" / f"station_bias_trends_{metric}.csv"
    if trends_file.exists():
        data["station_trends"] = pd.read_csv(trends_file)
    
    # Load urban/rural analysis
    urban_rural_file = outputs_dir / "data" / f"urban_rural_analysis_{metric}.json"
    if urban_rural_file.exists():
        with open(urban_rural_file) as f:
            data["urban_rural"] = json.load(f)
    
    # Load regional statistics
    regional_file = outputs_dir / "data" / f"regional_statistics_{metric}.csv"
    if regional_file.exists():
        data["regional"] = pd.read_csv(regional_file)
    
    return data

def create_metric_comparison_plot(metrics_data: dict, output_dir: Path):
    """Create comprehensive comparison plot across temperature metrics."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Progressive Bias Analysis: Cross-Metric Comparison', fontsize=16, fontweight='bold')
    
    # Extract data for plotting
    metrics = list(metrics_data.keys())
    
    # 1. Mean bias trends comparison
    ax1 = axes[0, 0]
    mean_trends = [metrics_data[m]["summary"]["mean_trend_per_decade"] for m in metrics]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    bars = ax1.bar(metrics, mean_trends, color=colors, alpha=0.7)
    ax1.set_ylabel('Mean Bias Trend (°C/decade)')
    ax1.set_title('Network-Wide Mean Bias Trends')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, mean_trends):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Percentage of stations with significant positive trends
    ax2 = axes[0, 1]
    pct_positive = [metrics_data[m]["summary"]["percent_significant_positive"] for m in metrics]
    bars = ax2.bar(metrics, pct_positive, color=colors, alpha=0.7)
    ax2.set_ylabel('Stations with Significant Positive Trend (%)')
    ax2.set_title('Positive Bias Prevalence')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='Random expectation')
    ax2.legend()
    
    # Add value labels
    for bar, value in zip(bars, pct_positive):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 3. Urban vs Rural mean trends comparison
    ax3 = axes[0, 2]
    urban_trends = [metrics_data[m]["urban_rural"]["urban"]["mean_trend"] for m in metrics]
    rural_trends = [metrics_data[m]["urban_rural"]["rural"]["mean_trend"] for m in metrics]
    
    x = np.arange(len(metrics))
    width = 0.35
    ax3.bar(x - width/2, urban_trends, width, label='Urban', alpha=0.7, color='red')
    ax3.bar(x + width/2, rural_trends, width, label='Rural', alpha=0.7, color='green')
    ax3.set_ylabel('Mean Bias Trend (°C/decade)')
    ax3.set_title('Urban vs Rural Bias Trends')
    ax3.set_xticks(x)
    ax3.set_xticklabels(metrics)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Trend distributions (violin plot)
    ax4 = axes[1, 0]
    trend_data = []
    metric_labels = []
    for metric in metrics:
        if "station_trends" in metrics_data[metric]:
            trends = metrics_data[metric]["station_trends"]["trend_per_decade"].values
            trend_data.extend(trends)
            metric_labels.extend([metric.upper()] * len(trends))
    
    if trend_data:
        trend_df = pd.DataFrame({'Metric': metric_labels, 'Trend': trend_data})
        sns.violinplot(data=trend_df, x='Metric', y='Trend', ax=ax4)
        ax4.set_ylabel('Station Bias Trend (°C/decade)')
        ax4.set_title('Distribution of Station Trends')
        ax4.grid(True, alpha=0.3)
        ax4.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    # 5. Regional comparison (if data available)
    ax5 = axes[1, 1]
    if "regional" in metrics_data[metrics[0]]:
        regional_means = {}
        for metric in metrics:
            if "regional" in metrics_data[metric]:
                regional_data = metrics_data[metric]["regional"]
                for _, row in regional_data.iterrows():
                    region = row["region"]
                    if region not in regional_means:
                        regional_means[region] = {}
                    regional_means[region][metric] = row["mean_trend"]
        
        if regional_means:
            region_df = pd.DataFrame(regional_means).T
            region_df.plot(kind='bar', ax=ax5, alpha=0.7)
            ax5.set_ylabel('Mean Bias Trend (°C/decade)')
            ax5.set_title('Regional Bias Patterns')
            ax5.legend(title='Temperature Metric')
            ax5.grid(True, alpha=0.3)
            plt.setp(ax5.get_xticklabels(), rotation=45, ha='right')
    else:
        ax5.text(0.5, 0.5, 'Regional data\nnot available', ha='center', va='center', 
                transform=ax5.transAxes, fontsize=12)
        ax5.set_title('Regional Analysis')
    
    # 6. Summary statistics table
    ax6 = axes[1, 2]
    ax6.axis('off')
    
    # Create summary table
    summary_data = []
    for metric in metrics:
        data = metrics_data[metric]["summary"]
        summary_data.append([
            metric.upper(),
            f"{data['mean_trend_per_decade']:.3f}",
            f"{data['percent_significant_positive']:.1f}%",
            f"{data['stations_analyzed']}"
        ])
    
    table = ax6.table(cellText=summary_data,
                     colLabels=['Metric', 'Mean Trend\n(°C/decade)', 'Positive\nStations (%)', 'Total\nStations'],
                     cellLoc='center',
                     loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    ax6.set_title('Summary Statistics')
    
    plt.tight_layout()
    
    # Save plot
    plot_file = output_dir / "cross_metric_comparison.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return plot_file

def calculate_cross_metric_correlations(metrics_data: dict) -> dict:
    """Calculate correlations between bias trends across temperature metrics."""
    correlations = {}
    
    # Get station trends for each metric
    trend_data = {}
    for metric in metrics_data:
        if "station_trends" in metrics_data[metric]:
            df = metrics_data[metric]["station_trends"]
            # Use id as key for matching across metrics
            trend_data[metric] = df.set_index("id")["trend_per_decade"]
    
    if len(trend_data) < 2:
        return {"error": "Insufficient metrics for correlation analysis"}
    
    # Calculate pairwise correlations
    metrics = list(trend_data.keys())
    for i, metric1 in enumerate(metrics):
        for j, metric2 in enumerate(metrics[i+1:], i+1):
            # Find common stations
            common_stations = trend_data[metric1].index.intersection(trend_data[metric2].index)
            
            if len(common_stations) > 10:  # Need sufficient data
                trends1 = trend_data[metric1].loc[common_stations]
                trends2 = trend_data[metric2].loc[common_stations]
                
                correlation = np.corrcoef(trends1, trends2)[0, 1]
                correlations[f"{metric1}_vs_{metric2}"] = {
                    "correlation": correlation,
                    "n_stations": len(common_stations),
                    "p_value": None  # Could add statistical test here
                }
    
    return correlations

def generate_comparative_summary(metrics_data: dict, correlations: dict) -> str:
    """Generate a comprehensive summary of cross-metric findings."""
    summary_lines = []
    summary_lines.append("# Cross-Metric Progressive Bias Analysis Summary")
    summary_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Overall findings
    summary_lines.append("\n## Key Findings Across Temperature Metrics")
    
    # Extract key statistics
    metrics = list(metrics_data.keys())
    mean_trends = {m: metrics_data[m]["summary"]["mean_trend_per_decade"] for m in metrics}
    pct_positive = {m: metrics_data[m]["summary"]["percent_significant_positive"] for m in metrics}
    
    # Rank metrics by bias magnitude
    sorted_by_bias = sorted(mean_trends.items(), key=lambda x: x[1], reverse=True)
    
    summary_lines.append(f"\n### Bias Magnitude Ranking (Strongest to Weakest):")
    for i, (metric, trend) in enumerate(sorted_by_bias, 1):
        summary_lines.append(f"{i}. **{metric.upper()}**: {trend:.3f} °C/decade ({pct_positive[metric]:.1f}% stations positive)")
    
    # Urban/Rural patterns
    summary_lines.append(f"\n### Urban vs Rural Patterns:")
    for metric in metrics:
        ur_data = metrics_data[metric]["urban_rural"]
        urban_trend = ur_data["urban"]["mean_trend"]
        rural_trend = ur_data["rural"]["mean_trend"]
        significant_diff = ur_data["comparison"]["groups_differ"]
        
        diff_text = "significantly different" if significant_diff else "not significantly different"
        summary_lines.append(f"- **{metric.upper()}**: Urban {urban_trend:.3f}, Rural {rural_trend:.3f} °C/decade ({diff_text})")
    
    # Cross-metric correlations
    if correlations and "error" not in correlations:
        summary_lines.append(f"\n### Cross-Metric Correlations:")
        for pair, data in correlations.items():
            pair_clean = pair.replace("_vs_", " vs ").upper()
            summary_lines.append(f"- **{pair_clean}**: r = {data['correlation']:.3f} (n = {data['n_stations']} stations)")
    
    # Evidence interpretation
    summary_lines.append(f"\n### Evidence for Progressive Bias:")
    
    # Check if majority show positive trends
    all_positive = all(pct > 50 for pct in pct_positive.values())
    summary_lines.append(f"- **Positive bias prevalence**: {'✓' if all_positive else '✗'} All metrics show >50% stations with positive trends")
    
    # Check if trends are substantial
    substantial_trends = any(abs(trend) > 0.02 for trend in mean_trends.values())
    summary_lines.append(f"- **Substantial magnitude**: {'✓' if substantial_trends else '✗'} At least one metric shows >0.02°C/decade trend")
    
    # Check rural patterns
    rural_positive = all(metrics_data[m]["urban_rural"]["rural"]["mean_trend"] > 0 for m in metrics)
    summary_lines.append(f"- **Rural bias patterns**: {'✓' if rural_positive else '✗'} All metrics show positive rural bias")
    
    # Overall assessment
    evidence_count = sum([all_positive, substantial_trends, rural_positive])
    if evidence_count >= 2:
        assessment = "**STRONG EVIDENCE** for progressive bias across temperature metrics"
    elif evidence_count == 1:
        assessment = "**MODERATE EVIDENCE** for progressive bias"
    else:
        assessment = "**WEAK EVIDENCE** for progressive bias"
    
    summary_lines.append(f"\n### Overall Assessment:")
    summary_lines.append(f"{assessment}")
    
    return "\n".join(summary_lines)

def main():
    """Main analysis function."""
    # Setup paths
    script_dir = Path(__file__).parent
    outputs_dir = script_dir.parent / "outputs"
    
    print("Cross-Metric Progressive Bias Analysis")
    print("=====================================")
    
    # Load data for all available metrics
    available_metrics = []
    metrics_data = {}
    
    for metric in ["avg", "min", "max"]:
        print(f"\nLoading {metric} temperature data...")
        data = load_metric_data(metric, outputs_dir)
        
        if "summary" in data and "station_trends" in data:
            metrics_data[metric] = data
            available_metrics.append(metric)
            print(f"✓ {metric} data loaded successfully")
        else:
            print(f"✗ {metric} data incomplete or missing")
    
    if len(available_metrics) < 2:
        print(f"\nError: Need at least 2 temperature metrics for comparison.")
        print(f"Available: {available_metrics}")
        return
    
    print(f"\nAnalyzing {len(available_metrics)} temperature metrics: {available_metrics}")
    
    # Create comparison visualization
    print("\nGenerating cross-metric comparison plot...")
    plot_file = create_metric_comparison_plot(metrics_data, outputs_dir / "plots")
    print(f"✓ Saved: {plot_file}")
    
    # Calculate cross-metric correlations
    print("\nCalculating cross-metric correlations...")
    correlations = calculate_cross_metric_correlations(metrics_data)
    
    # Save correlation results
    correlation_file = outputs_dir / "data" / "cross_metric_correlations.json"
    with open(correlation_file, 'w') as f:
        json.dump(correlations, f, indent=2)
    print(f"✓ Saved: {correlation_file}")
    
    # Generate comprehensive summary
    print("\nGenerating comparative summary...")
    summary_text = generate_comparative_summary(metrics_data, correlations)
    
    summary_file = outputs_dir / "CROSS_METRIC_SUMMARY.md"
    with open(summary_file, 'w') as f:
        f.write(summary_text)
    print(f"✓ Saved: {summary_file}")
    
    print(f"\nCross-metric analysis complete!")
    print(f"Key outputs:")
    print(f"- Comparison plot: {plot_file}")
    print(f"- Correlations: {correlation_file}")
    print(f"- Summary report: {summary_file}")

if __name__ == "__main__":
    main()