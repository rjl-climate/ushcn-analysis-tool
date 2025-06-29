"""
Comparative analysis of NOAA adjustment impacts on Urban Heat Island Intensity.
Analyzes patterns across raw, TOBs adjusted, and fully adjusted datasets.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def load_analysis_results():
    """Load analysis results from all three stages."""
    base_path = Path(
        "/Users/richardlyon/dev/mine/python/ushcn-heatisland/output/adjustment_bias_investigation"
    )

    # Load heat island reports
    raw_report_path = (
        base_path / "01_raw_data_analysis" / "simple_min_heat_island_report.json"
    )
    tobs_report_path = (
        base_path / "02_tobs_adjusted_analysis" / "simple_min_heat_island_report.json"
    )
    fls52_report_path = (
        base_path / "03_fully_adjusted_analysis" / "simple_min_heat_island_report.json"
    )

    with open(raw_report_path, "r") as f:
        raw_data = json.load(f)

    with open(tobs_report_path, "r") as f:
        tobs_data = json.load(f)

    with open(fls52_report_path, "r") as f:
        fls52_data = json.load(f)

    return raw_data, tobs_data, fls52_data


def extract_key_metrics(data, dataset_name):
    """Extract key metrics from analysis results."""
    metadata = data["analysis_metadata"]
    urban_rural = data["urban_rural_analysis"]

    # Basic metadata
    metrics = {
        "dataset": dataset_name,
        "total_stations": metadata["total_stations"],
        "urban_core_stations": metadata["urban_context_summary"]["urban_core_stations"],
        "suburban_stations": metadata["urban_context_summary"]["suburban_stations"],
        "rural_stations": metadata["urban_context_summary"]["rural_stations"],
    }

    # Urban vs rural statistics
    if "urban_vs_rural_comparison" in urban_rural:
        comparison = urban_rural["urban_vs_rural_comparison"]
        metrics.update(
            {
                "uhii_celsius": comparison["urban_heat_island_intensity"],
                "urban_mean": comparison["urban_mean"],
                "rural_mean": comparison["rural_mean"],
                "urban_count": comparison["urban_count"],
                "rural_count": comparison["rural_count"],
                "t_test_p_value": comparison["t_test_p_value"],
                "statistical_significance": comparison["statistical_significance"],
                "cohens_d": comparison["cohens_d_effect_size"],
            }
        )

    # Overall statistics by classification
    stats_by_class = urban_rural["statistics_by_classification"]
    for classification, stats in stats_by_class.items():
        metrics[f"{classification}_mean"] = stats["mean"]
        metrics[f"{classification}_count"] = stats["count"]
        metrics[f"{classification}_std"] = stats["std"]

    return metrics


def create_comparison_table():
    """Create comprehensive comparison table."""
    raw_data, tobs_data, fls52_data = load_analysis_results()

    # Extract metrics
    raw_metrics = extract_key_metrics(raw_data, "Raw")
    tobs_metrics = extract_key_metrics(tobs_data, "TOBs Adjusted")
    fls52_metrics = extract_key_metrics(fls52_data, "Fully Adjusted")

    # Create DataFrame
    df = pd.DataFrame([raw_metrics, tobs_metrics, fls52_metrics])

    # Calculate changes
    df["uhii_change_from_raw"] = df["uhii_celsius"] - df.iloc[0]["uhii_celsius"]
    df["uhii_percent_change"] = (
        df["uhii_change_from_raw"] / df.iloc[0]["uhii_celsius"]
    ) * 100

    return df


def create_uhii_progression_chart(df):
    """Create chart showing UHII progression through adjustments."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # UHII values
    datasets = df["dataset"]
    uhii_values = df["uhii_celsius"]

    # Bar chart of UHII values
    bars = ax1.bar(datasets, uhii_values, color=["red", "orange", "blue"], alpha=0.7)
    ax1.set_ylabel("Urban Heat Island Intensity (°C)")
    ax1.set_title("Urban Heat Island Intensity by Dataset")
    ax1.grid(True, alpha=0.3)

    # Add value labels on bars
    for bar, value in zip(bars, uhii_values):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.01,
            f"{value:.3f}°C",
            ha="center",
            va="bottom",
        )

    # Line chart showing progression
    ax2.plot(
        range(len(datasets)),
        uhii_values,
        "o-",
        linewidth=2,
        markersize=8,
        color="darkred",
    )
    ax2.set_xticks(range(len(datasets)))
    ax2.set_xticklabels(datasets)
    ax2.set_ylabel("Urban Heat Island Intensity (°C)")
    ax2.set_title("UHII Progression Through Adjustments")
    ax2.grid(True, alpha=0.3)

    # Add value labels
    for i, value in enumerate(uhii_values):
        ax2.text(i, value + 0.01, f"{value:.3f}°C", ha="center", va="bottom")

    # Add change annotations
    for i in range(1, len(uhii_values)):
        change = uhii_values.iloc[i] - uhii_values.iloc[i - 1]
        color = "green" if change > 0 else "red"
        ax2.annotate(
            f"{change:+.3f}°C",
            xy=(i - 0.5, (uhii_values.iloc[i - 1] + uhii_values.iloc[i]) / 2),
            ha="center",
            va="center",
            color=color,
            fontweight="bold",
        )

    plt.tight_layout()
    return fig


def analyze_adjustment_patterns(df):
    """Analyze patterns in adjustments."""
    analysis = {}

    # UHII changes
    raw_uhii = df.iloc[0]["uhii_celsius"]
    tobs_uhii = df.iloc[1]["uhii_celsius"]
    fls52_uhii = df.iloc[2]["uhii_celsius"]

    # TOBs impact
    tobs_change = tobs_uhii - raw_uhii
    tobs_percent = (tobs_change / raw_uhii) * 100

    # Additional adjustments impact
    additional_change = fls52_uhii - tobs_uhii
    additional_percent = (additional_change / tobs_uhii) * 100

    # Net impact
    net_change = fls52_uhii - raw_uhii
    net_percent = (net_change / raw_uhii) * 100

    analysis["adjustment_impacts"] = {
        "tobs_impact": {
            "uhii_change": tobs_change,
            "percent_change": tobs_percent,
            "direction": "reduces" if tobs_change < 0 else "increases",
        },
        "additional_adjustments": {
            "uhii_change": additional_change,
            "percent_change": additional_percent,
            "direction": "reduces" if additional_change < 0 else "increases",
        },
        "net_impact": {
            "uhii_change": net_change,
            "percent_change": net_percent,
            "direction": "reduces" if net_change < 0 else "increases",
        },
    }

    # Statistical significance preservation
    analysis["significance_preservation"] = {
        "raw_significant": df.iloc[0]["statistical_significance"] == "significant",
        "tobs_significant": df.iloc[1]["statistical_significance"] == "significant",
        "fls52_significant": df.iloc[2]["statistical_significance"] == "significant",
    }

    # Station count changes
    analysis["data_quality"] = {
        "raw_stations": df.iloc[0]["total_stations"],
        "tobs_stations": df.iloc[1]["total_stations"],
        "fls52_stations": df.iloc[2]["total_stations"],
        "net_station_gain": df.iloc[2]["total_stations"] - df.iloc[0]["total_stations"],
    }

    return analysis


def generate_comparative_report(df, analysis, output_dir):
    """Generate comprehensive comparative analysis report."""
    report = {
        "investigation_summary": {
            "analysis_date": "2025-06-28",
            "datasets_analyzed": 3,
            "time_period": "1895-1924 vs 1991-2020 (126 years)",
            "temperature_metric": "minimum",
            "urban_definition": "cities 250k+ population",
        },
        "key_findings": {
            "raw_uhii": f"{df.iloc[0]['uhii_celsius']:.3f}°C",
            "tobs_uhii": f"{df.iloc[1]['uhii_celsius']:.3f}°C",
            "fls52_uhii": f"{df.iloc[2]['uhii_celsius']:.3f}°C",
            "net_uhii_change": f"{analysis['adjustment_impacts']['net_impact']['uhii_change']:+.3f}°C",
            "net_percent_change": f"{analysis['adjustment_impacts']['net_impact']['percent_change']:+.1f}%",
        },
        "adjustment_breakdown": analysis["adjustment_impacts"],
        "statistical_validation": analysis["significance_preservation"],
        "data_quality_impact": analysis["data_quality"],
        "comparative_statistics": df.to_dict(orient="records"),
    }

    # Convert numpy types to Python types for JSON serialization
    def convert_types(obj):
        if hasattr(obj, "item"):
            return obj.item()
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(v) for v in obj]
        return obj

    report = convert_types(report)

    # Save comprehensive report
    output_path = output_dir / "comprehensive_comparison_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


def main():
    """Main analysis function."""
    output_dir = Path(
        "/Users/richardlyon/dev/mine/python/ushcn-heatisland/output/adjustment_bias_investigation/04_comparative_analysis"
    )
    output_dir.mkdir(exist_ok=True)

    print("🔍 Starting Comprehensive Comparative Analysis...")

    # Create comparison table
    print("📊 Creating comparison table...")
    df = create_comparison_table()

    # Save comparison table
    df.to_csv(output_dir / "uhii_comparison_table.csv", index=False)
    print(f"✅ Comparison table saved to {output_dir / 'uhii_comparison_table.csv'}")

    # Create visualizations
    print("📈 Creating UHII progression chart...")
    fig = create_uhii_progression_chart(df)
    fig.savefig(output_dir / "uhii_progression_chart.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Chart saved to {output_dir / 'uhii_progression_chart.png'}")

    # Analyze patterns
    print("🔬 Analyzing adjustment patterns...")
    analysis = analyze_adjustment_patterns(df)

    # Generate comprehensive report
    print("📋 Generating comprehensive report...")
    report = generate_comparative_report(df, analysis, output_dir)
    print(f"✅ Report saved to {output_dir / 'comprehensive_comparison_report.json'}")

    # Print key findings
    print("\n🎯 KEY FINDINGS:")
    print(f"Raw Data UHII:           {df.iloc[0]['uhii_celsius']:.3f}°C")
    print(
        f"TOBs Adjusted UHII:      {df.iloc[1]['uhii_celsius']:.3f}°C ({analysis['adjustment_impacts']['tobs_impact']['uhii_change']:+.3f}°C, {analysis['adjustment_impacts']['tobs_impact']['percent_change']:+.1f}%)"
    )
    print(
        f"Fully Adjusted UHII:     {df.iloc[2]['uhii_celsius']:.3f}°C ({analysis['adjustment_impacts']['additional_adjustments']['uhii_change']:+.3f}°C, {analysis['adjustment_impacts']['additional_adjustments']['percent_change']:+.1f}%)"
    )
    print(
        f"Net Adjustment Impact:    {analysis['adjustment_impacts']['net_impact']['uhii_change']:+.3f}°C ({analysis['adjustment_impacts']['net_impact']['percent_change']:+.1f}%)"
    )
    print(
        f"Statistical Significance: Raw={analysis['significance_preservation']['raw_significant']}, TOBs={analysis['significance_preservation']['tobs_significant']}, FLS52={analysis['significance_preservation']['fls52_significant']}"
    )
    print(
        f"Data Quality Improvement: +{analysis['data_quality']['net_station_gain']} stations"
    )

    print("\n✅ Comparative Analysis Complete!")


if __name__ == "__main__":
    main()
