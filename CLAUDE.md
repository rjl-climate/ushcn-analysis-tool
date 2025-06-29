# USHCN Heat Island Analysis Project

## Project Overview

This repository investigates Urban Heat Island (UHI) contamination in USHCN (US Historical Climatology Network) temperature records. The key finding is that NOAA temperature adjustments actually **enhance rather than remove urban heat island signals by 9.4%**, affecting 22.7% of the USHCN network with an average contamination of 0.725°C.

## Architecture & Structure

### Core Package (`src/ushcn_heatisland/`)

The main Python package with modular components:

1. **Data Loading (`data/loaders.py`)**
   - Loads USHCN parquet files (raw, TOB-adjusted, fully adjusted)
   - Handles station metadata and temperature data
   - Key function: `load_ushcn_data()` returns dict with stations GeoDataFrame and temperature DataFrames

2. **Urban Classification (`urban/context.py`)**
   - 4-level urban hierarchy: Large City (>250k), City (50-250k), Town (5-50k), Rural (<5k)
   - Uses US cities database to classify stations by proximity
   - Key function: `classify_stations()` adds urban context to station data

3. **Analysis Algorithms (`analysis/anomaly/`)**
   - `simple.py`: Basic temperature anomaly calculation
   - `min_obs.py`: Requires minimum observation count
   - `adjustment_impact.py`: Compares raw vs adjusted data
   - All implement `AnomalyAlgorithm` protocol

4. **Heat Island Analysis (`analysis/heat_island.py`)**
   - Calculates Urban Heat Island Intensity (UHII)
   - Compares urban vs rural temperature trends
   - Handles regional grouping and statistical analysis

5. **CLI Interface (`cli/main.py`)**
   - Typer-based command line interface
   - Entry point: `ushcn-heatisland` command
   - Supports different analysis algorithms via `--algorithm` flag

6. **Visualization (`visualization/`)**
   - `plotting.py`: Time series and statistical plots
   - `mapping.py`: Geographic visualizations with contextily

### Research Analysis (`analysis/`)

Separate analysis scripts for specific research questions:

1. **UHII Analysis (`ushcn_uhii_analysis_1895_plus/`)**
   - Main analysis comparing raw vs adjusted UHII
   - Shows 9.4% enhancement in UHII from adjustments
   - Key scripts: `create_raw_uhii_plot_1895.py`, `create_adjusted_uhii_plot_1895.py`

2. **Adjustment Bias Investigation (`adjustment_bias_investigation/`)**
   - Systematic study of how adjustments affect different station types
   - Regional analysis showing differential impacts

3. **Network Quality Assessment (`ushcn_network_quality_assessment/`)**
   - Analyzes station coverage over time
   - Identifies data gaps and network changes

## Data Flow

1. **Input Data** (in `data/` directory):
   - `ushcn_v2.5_monthly_raw.parquet`: Raw temperature data
   - `ushcn_v2.5_monthly_tob_adjusted.parquet`: Time-of-observation adjusted
   - `ushcn_v2.5_monthly_adjusted.parquet`: Fully adjusted (F52) data
   - `us_cities.parquet`: Urban population data for classification

2. **Processing Pipeline**:

   ```
   Load Data → Classify Urban Context → Calculate Anomalies →
   Compute UHII → Generate Visualizations → Export Results
   ```

3. **Output**:
   - CSV files with analysis results
   - PNG plots showing temperature trends
   - LaTeX tables for academic paper

## Key Concepts

### Temperature Anomaly Calculation

- Default baseline period: 1895-1925 (configurable via CLI)
- Baseline can be customized with --baseline-start-year and --period-length
- Handles missing data with configurable thresholds
- Calculates monthly anomalies from station means

### Urban Heat Island Intensity (UHII)

- Difference between urban and rural temperature anomalies
- Calculated regionally to account for climate zones
- Uses nearest rural stations for comparison

### NOAA Adjustments

- TOB (Time of Observation): Corrects for observation time changes
- F52 (Fully Adjusted): Includes homogenization, station moves, etc.
- Project finding: These adjustments amplify rather than remove UHI signal

## Development Workflow

### Running Analyses

```bash
# Install package
pip install -e .

# Run basic analysis
ushcn-heatisland analyze simple

# Run adjustment impact analysis
ushcn-heatisland analyze adjustment_impact

# Run specific research analysis
python analysis/ushcn_uhii_analysis_1895_plus/create_raw_uhii_plot_1895.py
```

### Testing

```bash
# Run tests (if available)
pytest

# Type checking
mypy src/
```

### Common Tasks

1. **Adding New Algorithm**:
   - Create new file in `src/ushcn_heatisland/analysis/anomaly/`
   - Implement `AnomalyAlgorithm` protocol
   - Register in `ALGORITHMS` dict in `cli/main.py`

2. **Modifying Urban Classification**:
   - Edit thresholds in `urban/context.py`
   - Update `URBAN_HIERARCHY` configuration

3. **Creating New Visualizations**:
   - Add functions to `visualization/plotting.py` or `mapping.py`
   - Use consistent style with existing plots

## Important Files to Know

- `src/ushcn_heatisland/cli/main.py`: CLI entry point and algorithm registry
- `src/ushcn_heatisland/data/loaders.py`: Data loading logic
- `src/ushcn_heatisland/urban/context.py`: Urban classification system
- `src/ushcn_heatisland/analysis/heat_island.py`: Core UHII calculations
- `analysis/ushcn_uhii_analysis_1895_plus/`: Main research findings

## Environment Variables

- No specific environment variables required
- Data paths are relative to project root

## Dependencies

Main dependencies (see pyproject.toml):

- geopandas>=0.14.0
- pandas>=2.0.0
- matplotlib>=3.7.0
- contextily>=1.4.0
- typer>=0.9.0
- scipy>=1.10.0
- scikit-learn>=1.3.0

## Notes for Future Development

1. The project uses a clean separation between the core package and research scripts
2. All data is in Parquet format for efficient storage and loading
3. The CLI provides a user-friendly interface while research scripts offer detailed analysis
4. Visualization functions handle both time series and geographic data
5. The urban classification system is key to the entire analysis
6. Regional grouping is important to control for climate differences

## Common Issues

1. **Memory Usage**: Large datasets may require chunked processing
2. **Missing Data**: Many stations have gaps; algorithms handle this differently
3. **Coordinate Systems**: Ensure consistent CRS when mapping (project uses EPSG:4326)
4. **Baseline Period**: Default is 1951-1980 but can be modified via CLI parameters
