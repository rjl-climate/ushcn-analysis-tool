"""Core data models and dataclasses for USHCN Heat Island Analysis."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AnalysisConfig:
    """Configuration for USHCN temperature analysis."""

    algorithm: str
    baseline_start_year: int
    baseline_end_year: int
    current_start_year: int
    current_end_year: int
    temp_metric: str = "min"
    min_observations: int | None = None
    data_type: str = "fls52"

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        valid_algorithms = ["simple", "min_obs", "adjustment_impact"]
        if self.algorithm not in valid_algorithms:
            raise ValueError(f"Algorithm must be one of {valid_algorithms}")

        valid_metrics = ["min", "max", "avg"]
        if self.temp_metric not in valid_metrics:
            raise ValueError(f"Temperature metric must be one of {valid_metrics}")

        valid_data_types = ["raw", "tob", "fls52"]
        if self.data_type not in valid_data_types:
            raise ValueError(f"Data type must be one of {valid_data_types}")


@dataclass
class VisualizationConfig:
    """Configuration for visualization parameters."""

    visualization_type: str = "points"
    grid_resolution: float = 0.1
    interpolation_method: str = "cubic"
    show_stations: bool = False
    contour_levels: int | None = None
    mask_type: str = "land"
    confidence_levels: bool = False
    max_interpolation_distance: float = 100.0
    min_station_count: int = 2
    confidence_radius: float = 100.0
    alpha_high: float = 0.8
    alpha_medium: float = 0.6
    show_coverage_report: bool = False

    def __post_init__(self) -> None:
        """Validate visualization parameters."""
        valid_viz_types = ["points", "contours"]
        if self.visualization_type not in valid_viz_types:
            raise ValueError(f"Visualization type must be one of {valid_viz_types}")

        valid_interp_methods = ["linear", "cubic", "nearest"]
        if self.interpolation_method not in valid_interp_methods:
            raise ValueError(f"Interpolation method must be one of {valid_interp_methods}")

        valid_mask_types = ["none", "land", "confidence"]
        if self.mask_type not in valid_mask_types:
            raise ValueError(f"Mask type must be one of {valid_mask_types}")


@dataclass
class UrbanConfig:
    """Configuration for urban heat island analysis."""

    show_cities: bool = False
    city_population_threshold: int = 100000
    show_urban_areas: bool = False
    classify_stations: bool = False
    urban_analysis: bool = False
    heat_island_report: bool = False
    urban_distance_threshold: float = 50.0
    suburban_distance_threshold: float = 100.0
    gradient_analysis: bool = False


@dataclass
class UHIIResult:
    """Results from Urban Heat Island Intensity analysis."""

    uhii_celsius: float
    urban_mean: float
    rural_mean: float
    urban_count: int
    rural_count: int
    p_value: float
    statistical_significance: str
    effect_size: float
    confidence_interval: tuple[float, float]
    analysis_period: str
    temp_metric: str

    @property
    def is_significant(self) -> bool:
        """Check if UHII result is statistically significant."""
        return self.p_value < 0.05

    @property
    def effect_magnitude(self) -> str:
        """Classify effect size magnitude."""
        if abs(self.effect_size) < 0.2:
            return "small"
        if abs(self.effect_size) < 0.5:
            return "medium"
        if abs(self.effect_size) < 0.8:
            return "large"
        return "very large"


@dataclass
class StationClassification:
    """Urban/rural classification for a weather station."""

    station_id: str
    classification: str
    distance_to_nearest_city_km: float
    nearest_city_name: str
    nearest_city_population: int
    urban_area_name: str | None = None

    @property
    def is_urban(self) -> bool:
        """Check if station is classified as urban."""
        return self.classification in ["urban_core", "urban_fringe"]

    @property
    def is_rural(self) -> bool:
        """Check if station is classified as rural."""
        return self.classification == "rural"


@dataclass
class AnalysisResults:
    """Complete analysis results with metadata."""

    config: AnalysisConfig
    stations_processed: int
    stations_with_data: int
    uhii_result: UHIIResult | None
    station_classifications: list[StationClassification]
    statistics: dict[str, Any]
    output_files: list[Path]
    processing_time_seconds: float

    @property
    def success_rate(self) -> float:
        """Calculate percentage of successfully processed stations."""
        if self.stations_processed == 0:
            return 0.0
        return (self.stations_with_data / self.stations_processed) * 100

    def summary(self) -> str:
        """Generate summary string of analysis results."""
        summary_lines = [
            f"Analysis: {self.config.algorithm} algorithm",
            f"Period: {self.config.baseline_start_year}-{self.config.baseline_end_year} vs {self.config.current_start_year}-{self.config.current_end_year}",
            f"Stations: {self.stations_with_data}/{self.stations_processed} processed successfully ({self.success_rate:.1f}%)",
        ]

        if self.uhii_result:
            summary_lines.extend([
                f"UHII: {self.uhii_result.uhii_celsius:.3f}°C ({self.uhii_result.statistical_significance})",
                f"Effect size: {self.uhii_result.effect_size:.3f} ({self.uhii_result.effect_magnitude})",
            ])

        summary_lines.append(f"Processing time: {self.processing_time_seconds:.1f} seconds")

        return "\n".join(summary_lines)
