#!/usr/bin/env python3
"""
Run the complete progressive bias investigation.

This script orchestrates all analysis components:
1. Calculate bias trends
2. Regional analysis
3. Urban/rural comparison
4. Statistical significance tests
5. Generate comprehensive report
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json

def run_script(script_path: Path, args: list, description: str) -> bool:
    """Run a script with given arguments and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: python {script_path} {' '.join(args)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)] + args,
            capture_output=False,
            text=True,
            check=True
        )
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"✗ {description} failed with error: {e}")
        return False


def generate_summary_report(
    output_dir: Path,
    temp_metrics: list,
    success_log: dict
) -> None:
    """Generate a comprehensive summary report."""
    report_file = output_dir / "ANALYSIS_REPORT.md"
    
    with open(report_file, "w") as f:
        f.write("# Progressive Bias Investigation - Analysis Report\n\n")
        f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Analysis Status
        f.write("## Analysis Status\n\n")
        for step, status in success_log.items():
            status_symbol = "✓" if status else "✗"
            f.write(f"- {status_symbol} {step}\n")
        
        f.write("\n## Temperature Metrics Analyzed\n\n")
        for metric in temp_metrics:
            f.write(f"- {metric.upper()} temperature\n")
        
        # Key Files Generated
        f.write("\n## Key Output Files\n\n")
        f.write("### Data Files\n")
        for metric in temp_metrics:
            f.write(f"- `data/station_bias_trends_{metric}.csv` - Per-station bias trends\n")
            f.write(f"- `data/regional_statistics_{metric}.csv` - Regional analysis\n")
            f.write(f"- `data/urban_rural_analysis_{metric}.json` - Urban vs rural comparison\n")
            f.write(f"- `data/statistical_analysis_{metric}.json` - Statistical tests\n")
        
        f.write("\n### Visualization Files\n")
        for metric in temp_metrics:
            f.write(f"\n**{metric.upper()} Temperature:**\n")
            f.write(f"- `plots/bias_timeseries_{metric}.png` - Network-wide bias over time\n")
            f.write(f"- `plots/trend_distribution_{metric}.png` - Distribution of station trends\n")
            f.write(f"- `plots/cumulative_bias_{metric}.png` - Cumulative bias evolution\n")
            f.write(f"- `plots/regional_boxplot_{metric}.png` - Regional trend comparison\n")
            f.write(f"- `plots/urban_rural_boxplot_{metric}.png` - Urban vs rural comparison\n")
            f.write(f"- `plots/statistical_tests_{metric}.png` - Statistical test results\n")
        
        # Analysis Summary
        f.write("\n## Quick Results Summary\n\n")
        
        # Load and summarize key results
        for metric in temp_metrics:
            f.write(f"### {metric.upper()} Temperature\n\n")
            
            # Load summary data
            summary_file = output_dir / "data" / "analysis_summary.json"
            if summary_file.exists():
                try:
                    with open(summary_file, "r") as sf:
                        summary_data = json.load(sf)
                    
                    if metric in summary_data:
                        data = summary_data[metric]
                        f.write(f"- **Stations analyzed:** {data.get('stations_analyzed', 'N/A')}\n")
                        f.write(f"- **Mean bias trend:** {data.get('mean_trend_per_decade', 'N/A'):.3f} °C/decade\n")
                        f.write(f"- **Stations with significant positive trend:** {data.get('stations_significant_positive', 'N/A')} ({data.get('percent_significant_positive', 'N/A'):.1f}%)\n")
                
                except Exception as e:
                    f.write(f"- Could not load summary data: {e}\n")
            
            # Load urban/rural comparison
            urban_rural_file = output_dir / "data" / f"urban_rural_analysis_{metric}.json"
            if urban_rural_file.exists():
                try:
                    with open(urban_rural_file, "r") as urf:
                        ur_data = json.load(urf)
                    
                    if ur_data.get("analysis_possible", False):
                        f.write(f"- **Urban mean trend:** {ur_data['urban']['mean_trend']:.3f} °C/decade\n")
                        f.write(f"- **Rural mean trend:** {ur_data['rural']['mean_trend']:.3f} °C/decade\n")
                        f.write(f"- **Urban vs Rural difference:** {ur_data['comparison']['interpretation']}\n")
                
                except Exception as e:
                    f.write(f"- Could not load urban/rural data: {e}\n")
            
            f.write("\n")
        
        # Interpretation Guidelines
        f.write("## Interpretation Guidelines\n\n")
        f.write("### Evidence of Progressive Bias Would Include:\n")
        f.write("- Majority of stations showing positive bias trends\n")
        f.write("- Statistically significant network-wide positive trend\n")
        f.write("- Similar patterns in rural stations (no urban effects to correct)\n")
        f.write("- Acceleration of bias in recent decades\n")
        f.write("- Spatial correlation of trends across distant stations\n\n")
        
        f.write("### Evidence Against Progressive Bias Would Include:\n")
        f.write("- Random distribution of positive and negative trends\n")
        f.write("- No significant network-wide trend\n")
        f.write("- Different patterns for urban vs rural stations\n")
        f.write("- Adjustments clustered around documented station changes\n")
        f.write("- No systematic temporal patterns\n\n")
        
        # Next Steps
        f.write("## Recommended Next Steps\n\n")
        f.write("1. **Review detailed results** in the FINDINGS.md document\n")
        f.write("2. **Examine visualizations** to understand spatial and temporal patterns\n")
        f.write("3. **Compare with known station history** to identify legitimate adjustments\n")
        f.write("4. **Consider additional analyses** based on initial findings\n")
        f.write("5. **Document conclusions** and implications for temperature record reliability\n\n")
        
        # File Locations
        f.write("## File Organization\n\n")
        f.write("```\n")
        f.write("progressive_bias_investigation/\n")
        f.write("├── README.md              # Project overview and methodology\n")
        f.write("├── FINDINGS.md            # Detailed results (update this!)\n")
        f.write("├── ANALYSIS_REPORT.md     # This summary report\n")
        f.write("├── scripts/               # Analysis scripts\n")
        f.write("├── outputs/\n")
        f.write("│   ├── data/             # CSV and JSON results\n")
        f.write("│   └── plots/            # All visualizations\n")
        f.write("└── docs/\n")
        f.write("    └── methodology.md    # Detailed technical methods\n")
        f.write("```\n\n")
        
        f.write("---\n")
        f.write("*This report was automatically generated by the progressive bias investigation pipeline.*\n")
    
    print(f"Summary report generated: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="Run complete progressive bias investigation")
    parser.add_argument("--temp-metric", default="all", choices=["min", "max", "avg", "all"],
                        help="Temperature metric(s) to analyze")
    parser.add_argument("--data-dir", type=Path, default=Path("data"),
                        help="Directory containing USHCN data files")
    parser.add_argument("--output-dir", type=Path,
                        default=Path("analysis/progressive_bias_investigation/outputs"),
                        help="Output directory for results")
    parser.add_argument("--skip-bias-calc", action="store_true",
                        help="Skip bias calculation if already done")
    parser.add_argument("--parallel", action="store_true",
                        help="Run temperature metrics in parallel (experimental)")
    
    args = parser.parse_args()
    
    # Determine which metrics to analyze
    if args.temp_metric == "all":
        temp_metrics = ["min", "max", "avg"]
    else:
        temp_metrics = [args.temp_metric]
    
    print(f"Progressive Bias Investigation")
    print(f"Temperature metrics: {', '.join(temp_metrics)}")
    print(f"Output directory: {args.output_dir}")
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Track success of each step
    success_log = {}
    
    # Step 1: Calculate bias trends (most time-consuming)
    if not args.skip_bias_calc:
        for metric in temp_metrics:
            script_args = [
                "--temp-metric", metric,
                "--data-dir", str(args.data_dir),
                "--output-dir", str(args.output_dir)
            ]
            
            success = run_script(
                script_dir / "01_calculate_bias_trends.py",
                script_args,
                f"Bias trend calculation ({metric})"
            )
            success_log[f"Bias calculation ({metric})"] = success
            
            if not success:
                print(f"⚠️  Bias calculation failed for {metric}, continuing with other metrics...")
    else:
        print("Skipping bias calculation (--skip-bias-calc specified)")
        for metric in temp_metrics:
            success_log[f"Bias calculation ({metric})"] = True  # Assume success
    
    # Step 2: Regional analysis
    for metric in temp_metrics:
        script_args = [
            "--temp-metric", metric,
            "--input-dir", str(args.output_dir / "data"),
            "--output-dir", str(args.output_dir)
        ]
        
        success = run_script(
            script_dir / "02_regional_analysis.py",
            script_args,
            f"Regional analysis ({metric})"
        )
        success_log[f"Regional analysis ({metric})"] = success
    
    # Step 3: Urban/rural comparison
    for metric in temp_metrics:
        script_args = [
            "--temp-metric", metric,
            "--input-dir", str(args.output_dir / "data"),
            "--data-dir", str(args.data_dir),
            "--output-dir", str(args.output_dir)
        ]
        
        success = run_script(
            script_dir / "03_urban_rural_comparison.py",
            script_args,
            f"Urban/rural comparison ({metric})"
        )
        success_log[f"Urban/rural comparison ({metric})"] = success
    
    # Step 4: Statistical tests
    for metric in temp_metrics:
        script_args = [
            "--temp-metric", metric,
            "--input-dir", str(args.output_dir / "data"),
            "--output-dir", str(args.output_dir)
        ]
        
        success = run_script(
            script_dir / "04_statistical_tests.py",
            script_args,
            f"Statistical tests ({metric})"
        )
        success_log[f"Statistical tests ({metric})"] = success
    
    # Step 5: Generate summary report
    generate_summary_report(args.output_dir, temp_metrics, success_log)
    
    # Final summary
    print(f"\n{'='*60}")
    print("ANALYSIS PIPELINE COMPLETE")
    print(f"{'='*60}")
    
    total_steps = len(success_log)
    successful_steps = sum(success_log.values())
    
    print(f"✓ {successful_steps}/{total_steps} analysis steps completed successfully")
    
    if successful_steps == total_steps:
        print("🎉 All analyses completed successfully!")
    else:
        print(f"⚠️  {total_steps - successful_steps} steps failed or were skipped")
        print("Check individual step outputs for details")
    
    print(f"\n📊 Results available in: {args.output_dir}")
    print(f"📋 Summary report: {args.output_dir}/ANALYSIS_REPORT.md")
    print(f"📈 Visualizations: {args.output_dir}/plots/")
    print(f"📄 Data files: {args.output_dir}/data/")
    
    print(f"\n🔍 Next steps:")
    print(f"1. Review the summary report: {args.output_dir}/ANALYSIS_REPORT.md")
    print(f"2. Update findings document: analysis/progressive_bias_investigation/FINDINGS.md")
    print(f"3. Examine key visualizations to understand patterns")
    print(f"4. Draw conclusions about progressive bias evidence")


if __name__ == "__main__":
    main()