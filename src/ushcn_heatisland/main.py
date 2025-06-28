"""Main CLI interface for USHCN Heat Island Analysis."""

import typer
from pathlib import Path
from typing import Optional
import json

from .data_loader import load_ushcn_data
from .anomaly_algorithms import get_algorithm, list_algorithms
from .plotting import plot_anomaly_map, plot_enhanced_contour_map, plot_comparison_maps, create_summary_statistics, plot_heat_island_map
from .urban_context import UrbanContextManager
from .heat_island_analysis import generate_heat_island_report

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
    mask_type: str = typer.Option(
        "land", help="Geographic masking: none, land, confidence"
    ),
    confidence_levels: bool = typer.Option(
        False, help="Show confidence level variations"
    ),
    max_interpolation_distance: float = typer.Option(
        100.0, help="Maximum distance from station (km)"
    ),
    min_station_count: int = typer.Option(
        2, help="Minimum stations for interpolation"
    ),
    confidence_radius: float = typer.Option(
        100.0, help="Radius for station counting (km)"
    ),
    alpha_high: float = typer.Option(
        0.8, help="Opacity for high confidence areas"
    ),
    alpha_medium: float = typer.Option(
        0.6, help="Opacity for medium confidence areas"
    ),
    show_coverage_report: bool = typer.Option(
        False, help="Generate station coverage statistics"
    ),
    # Urban Heat Island Analysis Options
    show_cities: bool = typer.Option(
        False, help="Show major cities overlay"
    ),
    city_population_threshold: int = typer.Option(
        100000, help="Minimum city population to display"
    ),
    show_urban_areas: bool = typer.Option(
        False, help="Show urban area boundaries"
    ),
    classify_stations: bool = typer.Option(
        False, help="Color-code stations by urban/rural classification"
    ),
    urban_analysis: bool = typer.Option(
        False, help="Generate urban heat island statistics"
    ),
    heat_island_report: bool = typer.Option(
        False, help="Generate comprehensive heat island analysis"
    ),
    urban_distance_threshold: float = typer.Option(
        50.0, help="Maximum distance to classify as urban (km)"
    ),
    suburban_distance_threshold: float = typer.Option(
        100.0, help="Maximum distance for suburban classification (km)"
    ),
    gradient_analysis: bool = typer.Option(
        False, help="Analyze temperature gradients from cities"
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
    
    # Validate mask type
    valid_mask_types = ["none", "land", "confidence"]
    if mask_type not in valid_mask_types:
        typer.echo(f"Error: Unknown mask type '{mask_type}'")
        typer.echo(f"Valid types: {', '.join(valid_mask_types)}")
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
        
        # Initialize urban context if needed
        urban_context_manager = None
        cities_gdf = None
        urban_areas_gdf = None
        urban_context_summary = None
        
        if any([show_cities, show_urban_areas, classify_stations, urban_analysis, heat_island_report, gradient_analysis]):
            typer.echo("Loading urban context data...")
            urban_context_manager = UrbanContextManager()
            cities_gdf = urban_context_manager.load_cities_data(min_population=city_population_threshold)
            urban_areas_gdf = urban_context_manager.load_urban_areas()
            typer.echo(f"Loaded {len(cities_gdf)} cities and {len(urban_areas_gdf)} urban areas")

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
        
        # Add urban classification if requested
        if urban_context_manager is not None and (classify_stations or urban_analysis or heat_island_report):
            typer.echo("Classifying stations by urban/rural context...")
            results = urban_context_manager.classify_stations_urban_rural(
                results,
                cities_gdf=cities_gdf,
                urban_areas_gdf=urban_areas_gdf,
                use_4_level_hierarchy=True
            )
            
            # Generate urban context summary
            urban_context_summary = urban_context_manager.get_urban_context_summary(
                results, cities_gdf, urban_areas_gdf
            )
            typer.echo(f"Station classification: {urban_context_summary['urban_core_stations']} urban_core, {urban_context_summary['urban_stations']} urban, {urban_context_summary['suburban_stations']} suburban, {urban_context_summary['rural_stations']} rural")

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
                # Check if we should use heat island visualization
                if any([show_cities, show_urban_areas, classify_stations]):
                    output_path = output_dir / f"{algorithm}_{temp_metric}_heat_island_map.png"
                    fig, coverage_report = plot_heat_island_map(
                        results, title, output_path,
                        temp_metric=temp_metric.title(),
                        grid_resolution=grid_resolution,
                        interpolation_method=interpolation_method,
                        show_stations=show_stations,
                        contour_levels=contour_levels,
                        mask_type=mask_type,
                        confidence_levels=confidence_levels,
                        max_interpolation_distance=max_interpolation_distance,
                        min_station_count=min_station_count,
                        confidence_radius=confidence_radius,
                        alpha_high=alpha_high,
                        alpha_medium=alpha_medium,
                        show_coverage_report=show_coverage_report,
                        show_cities=show_cities,
                        city_population_threshold=city_population_threshold,
                        show_urban_areas=show_urban_areas,
                        classify_stations=classify_stations,
                        urban_analysis=urban_analysis,
                        cities_gdf=cities_gdf,
                        urban_areas_gdf=urban_areas_gdf
                    )
                else:
                    output_path = output_dir / f"{algorithm}_{temp_metric}_contour_map.png"
                    fig, coverage_report = plot_enhanced_contour_map(
                        results, title, output_path, 
                        temp_metric=temp_metric.title(),
                        grid_resolution=grid_resolution,
                        interpolation_method=interpolation_method,
                        show_stations=show_stations,
                        contour_levels=contour_levels,
                        mask_type=mask_type,
                        confidence_levels=confidence_levels,
                        max_interpolation_distance=max_interpolation_distance,
                        min_station_count=min_station_count,
                        confidence_radius=confidence_radius,
                        alpha_high=alpha_high,
                        alpha_medium=alpha_medium,
                        show_coverage_report=show_coverage_report
                    )
                
                # Save coverage report if generated
                if coverage_report and show_coverage_report:
                    coverage_file = output_dir / f"{algorithm}_{temp_metric}_coverage_report.json"
                    with open(coverage_file, "w") as f:
                        json.dump(coverage_report, f, indent=2)
                    typer.echo(f"Coverage report saved to: {coverage_file}")
                    
        # Generate heat island analysis report if requested
        if heat_island_report and urban_context_summary is not None:
            typer.echo("Generating heat island analysis report...")
            heat_island_analysis = generate_heat_island_report(
                results, urban_context_summary, cities_gdf
            )
            
            report_file = output_dir / f"{algorithm}_{temp_metric}_heat_island_report.json"
            with open(report_file, "w") as f:
                json.dump(heat_island_analysis, f, indent=2)
            typer.echo(f"Heat island report saved to: {report_file}")
            
            # Print heat island summary
            if 'heat_island_summary' in heat_island_analysis:
                summary = heat_island_analysis['heat_island_summary']
                typer.echo("\n=== Urban Heat Island Analysis ===")
                if summary.get('heat_island_detected', False):
                    intensity = summary.get('intensity_celsius', 0)
                    significance = summary.get('statistical_significance', 'unknown')
                    typer.echo(f"Heat island intensity: {intensity:.3f}°C ({significance})")
                else:
                    typer.echo("No significant heat island effect detected")
                    
            else:
                output_path = output_dir / f"{algorithm}_{temp_metric}_anomaly_map.png"
                plot_anomaly_map(results, title, output_path, temp_metric=temp_metric.title())

        typer.echo("Visualization complete!")

        # Print summary
        typer.echo("\n=== Analysis Summary ===")
        typer.echo(f"Algorithm: {algorithm}")
        typer.echo(f"Stations processed: {stats['total_stations']}")
        typer.echo(f"Stations with valid data: {stats['stations_with_data']}")
        
        # Print urban context summary if available
        if urban_context_summary is not None:
            typer.echo(f"Urban context: {urban_context_summary['total_cities']} cities, {urban_context_summary['urban_core_stations']} urban_core, {urban_context_summary['urban_stations']} urban, {urban_context_summary['suburban_stations']} suburban, {urban_context_summary['rural_stations']} rural stations")

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
        
        # Urban heat island summary in main stats
        if urban_context_summary and 'mean_distance_to_city_km' in urban_context_summary:
            typer.echo(f"Mean distance to nearest city: {urban_context_summary['mean_distance_to_city_km']:.1f} km")

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
