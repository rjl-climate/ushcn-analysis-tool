"""Main CLI interface for USHCN Heat Island Analysis."""

import typer
from pathlib import Path
from typing import Optional
import json

from .data_loader import load_ushcn_data
from .anomaly_algorithms import get_algorithm, list_algorithms
from .plotting import plot_anomaly_map, plot_contour_map, plot_comparison_maps, create_summary_statistics

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
    temp_metric: str = typer.Option(
        "min", help="Temperature metric to analyze: min, max, or avg"
    ),
    visualization_type: str = typer.Option(
        "points", help="Visualization type: points or contours"
    ),
    grid_resolution: float = typer.Option(
        0.1, help="Grid resolution in degrees for contour maps"
    ),
    interpolation_method: str = typer.Option(
        "cubic", help="Interpolation method: linear, cubic, or nearest"
    ),
    show_stations: bool = typer.Option(
        False, help="Show station points on contour maps"
    ),
    contour_levels: Optional[int] = typer.Option(
        None, help="Number of contour levels (auto if not specified)"
    ),
) -> None:
    """Run temperature anomaly analysis with specified algorithm."""

    # Validate algorithm
    available_algorithms = list_algorithms()
    if algorithm not in available_algorithms:
        typer.echo(f"Error: Unknown algorithm '{algorithm}'")
        typer.echo(f"Available algorithms: {', '.join(available_algorithms)}")
        raise typer.Exit(1)
    
    # Validate temperature metric
    valid_metrics = ["min", "max", "avg"]
    if temp_metric not in valid_metrics:
        typer.echo(f"Error: Unknown temperature metric '{temp_metric}'")
        typer.echo(f"Valid metrics: {', '.join(valid_metrics)}")
        raise typer.Exit(1)
    
    # Validate visualization type
    valid_viz_types = ["points", "contours"]
    if visualization_type not in valid_viz_types:
        typer.echo(f"Error: Unknown visualization type '{visualization_type}'")
        typer.echo(f"Valid types: {', '.join(valid_viz_types)}")
        raise typer.Exit(1)
    
    # Validate interpolation method
    valid_interp_methods = ["linear", "cubic", "nearest"]
    if interpolation_method not in valid_interp_methods:
        typer.echo(f"Error: Unknown interpolation method '{interpolation_method}'")
        typer.echo(f"Valid methods: {', '.join(valid_interp_methods)}")
        raise typer.Exit(1)

    # Set default output directory
    if output_dir is None:
        output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    typer.echo(f"Running {algorithm} analysis...")
    typer.echo(f"Data directory: {data_dir}")
    typer.echo(f"Temperature metric: {temp_metric}")
    typer.echo(f"Visualization type: {visualization_type}")
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
            temp_metric=temp_metric,
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
        stats_file = output_dir / f"{algorithm}_{temp_metric}_statistics.json"
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
        typer.echo(f"Statistics saved to: {stats_file}")

        # Create visualizations
        typer.echo("Creating visualizations...")

        if algorithm == "adjustment_impact":
            # Create comparison maps for adjustment impact
            title = f"{temp_metric.title()} Temperature Anomaly Analysis ({baseline_start_year}-{baseline_end} vs {current_start_year}-{current_end})"
            plot_comparison_maps(results, title, output_dir, temp_metric=temp_metric.title())

        else:
            # Create visualization based on type
            title = f"{algorithm.title()} Algorithm: {temp_metric.title()} Temperature Anomalies ({baseline_start_year}-{baseline_end} vs {current_start_year}-{current_end})"
            
            if visualization_type == "contours":
                output_path = output_dir / f"{algorithm}_{temp_metric}_contour_map.png"
                plot_contour_map(
                    results, title, output_path, 
                    temp_metric=temp_metric.title(),
                    grid_resolution=grid_resolution,
                    interpolation_method=interpolation_method,
                    show_stations=show_stations,
                    contour_levels=contour_levels
                )
            else:
                output_path = output_dir / f"{algorithm}_{temp_metric}_anomaly_map.png"
                plot_anomaly_map(results, title, output_path, temp_metric=temp_metric.title())

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
