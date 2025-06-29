"""Constants and configuration values for USHCN Heat Island Analysis."""


# Geographic boundaries
CONTINENTAL_US_BOUNDS = {
    "lat_min": 24.0,
    "lat_max": 50.0,
    "lon_min": -125.0,
    "lon_max": -66.0,
}

# Analysis defaults
DEFAULT_PERIOD_LENGTH = 30
DEFAULT_GRID_RESOLUTION = 0.1
DEFAULT_MIN_OBSERVATIONS = 10

# Urban classification thresholds (in kilometers)
URBAN_CLASSIFICATION_DISTANCES = {
    "urban_core": 25.0,
    "urban_fringe": 50.0,
    "suburban": 100.0,
}

# City population thresholds
CITY_POPULATION_THRESHOLDS = {
    "urban_core": 250000,
    "urban_fringe": 100000,
    "suburban": 50000,
}

# Statistical significance thresholds
SIGNIFICANCE_LEVELS = {
    "highly_significant": 0.001,
    "significant": 0.01,
    "marginally_significant": 0.05,
}

# Effect size thresholds (Cohen's d)
EFFECT_SIZE_THRESHOLDS = {
    "small": 0.2,
    "medium": 0.5,
    "large": 0.8,
}

# Data quality thresholds
DATA_QUALITY_THRESHOLDS = {
    "min_completeness": 0.25,
    "min_stations_continental": 1000,
    "min_years_analysis": 20,
}

# Network quality thresholds for enhanced analysis
NETWORK_QUALITY_THRESHOLDS = {
    "enhanced_start_year": 1895,
    "min_stations_1895": 1120,
    "target_stations_modern": 1218,
    "network_stability_threshold": 0.95,
    "coverage_adequacy_threshold": 0.90,
}

# Expected UHII ranges by temperature metric (°C)
UHII_EXPECTED_RANGES = {
    "max": (-0.5, 2.0),
    "min": (0.5, 4.0),
    "avg": (0.0, 3.0),
}

# File patterns and extensions
FILE_PATTERNS = {
    "ushcn_daily": "*-daily-*.txt",
    "ushcn_monthly": "*-monthly-*.txt",
    "ushcn_parquet": "*.parquet",
    "cities_data": "us_cities_*.csv",
}

# Plot styling defaults
PLOT_DEFAULTS = {
    "figure_size": (12, 8),
    "dpi": 300,
    "font_size": 12,
    "title_font_size": 14,
    "line_width": 2.0,
    "marker_size": 20,
    "alpha": 0.8,
}

# Color schemes
COLOR_SCHEMES = {
    "temperature_anomaly": "RdBu_r",
    "absolute_temperature": "viridis",
    "uhii": "OrRd",
    "adjustment_impact": "RdYlBu_r",
}

# Station marker colors by classification
STATION_COLORS = {
    "urban_core": "#d73027",      # Red
    "urban_fringe": "#fc8d59",    # Orange
    "suburban": "#fee08b",        # Yellow
    "rural": "#4575b4",           # Blue
}

# Validation message prefixes
VALIDATION_PREFIXES = {
    "pass": "✓",
    "warning": "⚠",
    "error": "✗",
    "info": "ℹ",
    "enhanced": "🔧",
}

# Analysis algorithm metadata
ALGORITHM_METADATA = {
    "simple": {
        "name": "Simple Anomaly",
        "description": "Basic temperature trend calculation",
        "requires_raw_data": False,
    },
    "min_obs": {
        "name": "Minimum Observations",
        "description": "Quality-controlled analysis with data requirements",
        "requires_raw_data": False,
    },
    "adjustment_impact": {
        "name": "Adjustment Impact",
        "description": "Quantifies effect of NOAA adjustments on trends",
        "requires_raw_data": True,
    },
}
