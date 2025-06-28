"""Main CLI interface for USHCN Heat Island Analysis."""

import typer
from pathlib import Path
from typing import Optional
import json

from .data_loader import load_ushcn_data
from .anomaly_algorithms import get_algorithm, list_algorithms
from .plotting import plot_anomaly_map, plot_comparison_maps, create_summary_statistics

app = typer.Typer(help="US Long-Term Temperature Change Analyzer")


@app.command()
def analyze(
    algorithm: str = typer.Argument(
        ..., help="Algorithm to use: simple, min_obs, or adjustment_impact"
    ),
    baseline_start_year: int = typer.Option(1951, help="Baseline period start year"),
    current_start_year: int = typer.Option(1981, help="Current period start year"),
    period_length: int = typer.Option(
        30, help="Length of baseline and current periods in years"
    ),
    min_observations: Optional[int] = typer.Option(
        None, help="Minimum observations required (for min_obs algorithm)"
    ),
    data_dir: Path = typer.Option(
        Path("data"), help="Directory containing USHCN data files"
    ),
    output_dir: Optional[Path] = typer.Option(None, help="Output directory for plots"),
) -> None:
    """Run temperature anomaly analysis with specified algorithm."""

    # Validate algorithm
    available_algorithms = list_algorithms()
    if algorithm not in available_algorithms:
        typer.echo(f"Error: Unknown algorithm '{algorithm}'")
        typer.echo(f"Available algorithms: {', '.join(available_algorithms)}")
        raise typer.Exit(1)

    # Set default output directory
    if output_dir is None:
        output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    typer.echo(f"Running {algorithm} analysis...")
    typer.echo(f"Data directory: {data_dir}")
    baseline_end = baseline_start_year + period_length - 1
    current_end = current_start_year + period_length - 1
    typer.echo(f"Baseline period: {baseline_start_year}-{baseline_end}")
    typer.echo(f"Current period: {current_start_year}-{current_end}")
    typer.echo(f"Output directory: {output_dir}")

    try:
        # Load data
        typer.echo("Loading USHCN data...")
        load_raw = algorithm == "adjustment_impact"

        adjusted_data, raw_data = load_ushcn_data(
            data_dir,
            adjusted_type="fls52",  # Use fully adjusted data as "adjusted"
            raw_type="raw",
            load_raw=load_raw,
        )

        typer.echo(f"Loaded {len(adjusted_data)} adjusted data records")
        if raw_data is not None:
            typer.echo(f"Loaded {len(raw_data)} raw data records")

        # Prepare configuration
        config = {}
        if min_observations is not None:
            config["min_observations"] = min_observations

        # Run analysis
        typer.echo("Running analysis...")
        algorithm_func = get_algorithm(algorithm)

        results = algorithm_func(
            gdf_adjusted=adjusted_data,
            baseline_period=(baseline_start_year, baseline_end),
            current_period=(current_start_year, current_end),
            gdf_raw=raw_data,
            config=config if config else None,
        )

        typer.echo(f"Analysis complete! Found results for {len(results)} stations")

        # Generate statistics
        stats = create_summary_statistics(results)
        stats_file = output_dir / f"{algorithm}_statistics.json"
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
        typer.echo(f"Statistics saved to: {stats_file}")

        # Create visualizations
        typer.echo("Creating visualizations...")

        if algorithm == "adjustment_impact":
            # Create comparison maps for adjustment impact
            title = f"Temperature Anomaly Analysis ({baseline_start_year}-{baseline_end} vs {current_start_year}-{current_end})"
            plot_comparison_maps(results, title, output_dir)

        else:
            # Create single anomaly map
            title = f"{algorithm.title()} Algorithm: Temperature Anomalies ({baseline_start_year}-{baseline_end} vs {current_start_year}-{current_end})"
            output_path = output_dir / f"{algorithm}_anomaly_map.png"
            plot_anomaly_map(results, title, output_path)

        typer.echo("Visualization complete!")

        # Print summary
        typer.echo("\n=== Analysis Summary ===")
        typer.echo(f"Algorithm: {algorithm}")
        typer.echo(f"Stations processed: {stats['total_stations']}")
        typer.echo(f"Stations with valid data: {stats['stations_with_data']}")

        if "anomaly_celsius_mean" in stats:
            typer.echo(f"Mean anomaly: {stats['anomaly_celsius_mean']:.3f}°C")
            typer.echo(
                f"Anomaly range: {stats['anomaly_celsius_min']:.3f}°C to {stats['anomaly_celsius_max']:.3f}°C"
            )

        if "adjustment_impact_mean" in stats:
            typer.echo(
                f"Mean adjustment impact: {stats['adjustment_impact_mean']:.3f}°C"
            )
            typer.echo(
                f"Impact range: {stats['adjustment_impact_min']:.3f}°C to {stats['adjustment_impact_max']:.3f}°C"
            )

    except Exception as e:
        typer.echo(f"Error during analysis: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command()
def list_algos() -> None:
    """List available analysis algorithms."""
    algorithms = list_algorithms()
    typer.echo("Available algorithms:")
    for algo in algorithms:
        typer.echo(f"  - {algo}")


if __name__ == "__main__":
    app()
