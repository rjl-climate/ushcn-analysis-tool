# USHCN Heat Island Analysis v5 - Urban Heat Island Investigation

## Objective
Transform the system from general temperature anomaly analysis into focused urban heat island investigation by overlaying temperature data with urban context to demonstrate heat generation areas and their temperature impacts.

## Current State (v4)
- Enhanced contour mapping with scientific rigor and validation
- Geographic and confidence-based masking systems
- Cross-validation framework with coverage analysis
- Publication-quality visualizations with methodological defensibility

## Target Enhancement (v5)
Add urban context layers to investigate and illustrate potential heat island effects by showing relationships between temperature anomalies and urban areas, cities, and heat-generating zones.

## Core Requirements

### 1. Urban Context Data Integration
**Data Sources Needed**:
- US Census Urban Areas: Official urban boundary definitions
- Natural Earth Cities: Major world cities database for US cities
- US Census Places: Incorporated cities and towns
- Population data for city sizing and classification

**Urban Classification Hierarchy**:
- **Urban Core**: Within major city boundaries (population > 100,000)
- **Urban Fringe**: Within Census urban areas but outside core cities
- **Suburban**: Within metropolitan influence zone (50-100km from urban core)
- **Rural**: Outside urban influence zones (>100km from cities)

### 2. Station Classification System
**Classification Criteria**:
- Distance to nearest city center (multiple thresholds)
- Containment within Census urban area boundaries
- Local population density within radius
- Land use characteristics (if available)

**Implementation Approach**:
- Spatial joins between weather stations and urban boundaries
- Distance calculations to nearest city centers
- Multi-level classification with configurable thresholds
- Metadata attachment to existing station results

## Technical Implementation

### 3. New Architecture Components

#### A. Urban Context Management (`urban_context.py`)
```python
class UrbanContextManager:
    def load_cities_data(min_population: int = 50000) -> gpd.GeoDataFrame:
        # Load US cities from Natural Earth or Census data
        # Filter by population threshold
        # Return GeoDataFrame with city points, names, population
    
    def load_urban_areas() -> gpd.GeoDataFrame:
        # Load US Census Urban Areas polygons
        # Return GeoDataFrame with urban boundaries
    
    def classify_stations_urban_rural(
        stations_gdf: gpd.GeoDataFrame,
        cities_gdf: gpd.GeoDataFrame,
        urban_areas_gdf: gpd.GeoDataFrame,
        urban_distance_threshold: float = 50.0,
        suburban_distance_threshold: float = 100.0
    ) -> gpd.GeoDataFrame:
        # Classify each station as urban/suburban/rural
        # Add classification metadata columns
        # Calculate distance to nearest city
        # Return enhanced stations GeoDataFrame
    
    def calculate_urban_proximity_metrics(
        stations_gdf: gpd.GeoDataFrame,
        cities_gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        # Calculate distance to nearest city
        # Identify nearest city name and population
        # Add proximity metrics to station data
```

#### B. Heat Island Analysis Module (`heat_island_analysis.py`)
```python
def calculate_urban_rural_statistics(
    results_gdf: gpd.GeoDataFrame
) -> Dict[str, Any]:
    # Urban vs rural temperature anomaly statistics
    # Mean temperatures by classification
    # Statistical significance testing (t-tests, Mann-Whitney U)
    # Effect size calculations (Cohen's d)
    # Return comprehensive statistics dictionary

def analyze_distance_gradients(
    results_gdf: gpd.GeoDataFrame,
    cities_gdf: gpd.GeoDataFrame,
    max_distance: float = 200.0
) -> Dict[str, Any]:
    # Temperature vs distance from urban centers
    # Heat island intensity by city size classes
    # Gradient analysis with binning by distance
    # Correlation analysis between city size and heat effect
    # Return gradient analysis results

def calculate_heat_island_intensity(
    urban_temps: np.ndarray,
    rural_temps: np.ndarray
) -> Dict[str, float]:
    # Urban Heat Island Intensity (UHII) = mean(urban) - mean(rural)
    # Statistical significance testing
    # Confidence intervals for UHII
    # Effect size metrics
    # Return intensity statistics

def generate_heat_island_report(
    results_gdf: gpd.GeoDataFrame,
    urban_context: Dict[str, Any]
) -> Dict[str, Any]:
    # Comprehensive heat island analysis report
    # Urban effect quantification by city size
    # Regional heat island patterns
    # Scientific interpretation and summary
    # Methodology documentation
```

### 4. Enhanced Visualization System

#### Updated Plotting Functions (`plotting.py`)
```python
def plot_heat_island_map(
    results_gdf: gpd.GeoDataFrame,
    title: str,
    output_path: Optional[Path] = None,
    # ... existing parameters ...
    show_cities: bool = True,
    city_population_threshold: int = 100000,
    show_urban_areas: bool = False,
    classify_stations: bool = True,
    urban_analysis: bool = True,
    population_overlay: bool = False,
    cities_gdf: Optional[gpd.GeoDataFrame] = None,
    urban_areas_gdf: Optional[gpd.GeoDataFrame] = None
) -> Tuple[plt.Figure, Dict[str, Any]]:
    # Enhanced contour/point maps with urban overlays
    # Color-coded stations by urban/rural classification
    # City markers scaled by population size
    # Urban area boundary polygons (optional)
    # Population density background layer (optional)
    # Heat island intensity annotations
    # Maintain existing masking and validation systems

def plot_urban_rural_comparison(
    results_gdf: gpd.GeoDataFrame,
    heat_island_stats: Dict[str, Any],
    output_path: Optional[Path] = None
) -> plt.Figure:
    # Side-by-side comparison of urban vs rural distributions
    # Box plots, violin plots, or histograms
    # Statistical significance annotations
    # Heat island intensity display
    # Summary statistics overlay

def plot_distance_gradient_analysis(
    results_gdf: gpd.GeoDataFrame,
    gradient_analysis: Dict[str, Any],
    output_path: Optional[Path] = None
) -> plt.Figure:
    # Temperature vs distance from cities scatter plot
    # Binned analysis with error bars
    # Trend lines and correlation statistics
    # City size stratification
    # Heat island decay patterns
```

### 5. CLI Integration

#### New Command-Line Options
```python
# Urban Context Options (add to main.py)
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

# Urban Analysis Parameters
urban_distance_threshold: float = typer.Option(
    50.0, help="Maximum distance to classify as urban (km)"
),
suburban_distance_threshold: float = typer.Option(
    100.0, help="Maximum distance for suburban classification (km)"
),
gradient_analysis: bool = typer.Option(
    False, help="Analyze temperature gradients from cities"
),
```

### 6. Enhanced Data Loading

#### Modified Data Loader (`data_loader.py`)
```python
def load_ushcn_data_with_urban_context(
    data_dir: Path,
    adjusted_type: str = "fls52",
    raw_type: str = "raw",
    load_raw: bool = False,
    temp_metric: str = "min",
    include_urban_context: bool = False,
    city_population_threshold: int = 50000,
    urban_distance_threshold: float = 50.0,
    suburban_distance_threshold: float = 100.0
) -> Tuple[gpd.GeoDataFrame, Optional[gpd.GeoDataFrame], Dict[str, Any]]:
    # Load temperature data using existing functions
    # If include_urban_context:
    #   - Load cities and urban areas data
    #   - Classify stations by urban/rural
    #   - Add urban proximity metrics
    #   - Return urban context dictionary
    # Return (adjusted_data, raw_data, urban_context)
```

## Implementation Sequence

### Phase 1: Urban Data Integration
1. **Add Dependencies**
   - Natural Earth data access (geopandas built-in or direct download)
   - US Census data access (consider cenpy or direct API)
   - Enhanced spatial analysis capabilities

2. **Create Urban Context Module**
   - Implement UrbanContextManager class
   - Add city and urban area data loading functions
   - Create station classification algorithms
   - Test with sample USHCN stations

3. **Basic Urban Overlay**
   - Extend plotting functions to show city markers
   - Add simple urban/rural station color coding
   - Test with existing analysis workflows

### Phase 2: Heat Island Analysis Framework
1. **Implement Analysis Functions**
   - Urban vs rural statistical comparisons
   - Heat island intensity calculations
   - Distance gradient analysis
   - Statistical significance testing

2. **Enhanced Visualizations**
   - Urban area boundary overlays
   - Population-scaled city markers
   - Heat island intensity annotations
   - Comparison plot functions

3. **CLI Integration**
   - Add urban context command-line options
   - Integrate with existing analysis workflows
   - Add urban analysis output options

### Phase 3: Advanced Features
1. **Comprehensive Reporting**
   - Heat island analysis reports (JSON output)
   - Urban vs rural comparison statistics
   - Distance gradient analysis results
   - Scientific interpretation summaries

2. **Performance Optimization**
   - Spatial indexing for large datasets
   - Caching of urban context data
   - Vectorized distance calculations

3. **Validation and Testing**
   - Test with known heat island locations
   - Validate against existing heat island studies
   - Cross-validation with urban meteorology research

## Data Requirements and Sources

### Primary Data Sources
1. **US Census Urban Areas**
   - Format: Shapefile or GeoJSON
   - Source: US Census Bureau Geography Division
   - Content: Official urban area boundaries

2. **Natural Earth Cities**
   - Format: Shapefile (included with geopandas)
   - Source: Natural Earth Data
   - Content: World cities with population data

3. **US Census Places** (optional enhancement)
   - Format: Shapefile or API access
   - Source: US Census Bureau
   - Content: Incorporated places and CDP boundaries

### Data Processing Requirements
- Spatial join operations between points and polygons
- Distance calculations using geodesic methods
- Multi-criteria classification algorithms
- Statistical analysis for urban vs rural comparisons

## Scientific Validation Strategy

### Heat Island Investigation Approach
1. **Visual Evidence**
   - Direct spatial correlation between urban areas and temperature anomalies
   - Color-coded station classification showing urban/rural patterns
   - City-centered temperature gradients

2. **Quantitative Analysis**
   - Statistical testing of urban vs rural temperature differences
   - Heat island intensity measurements with confidence intervals
   - Effect size calculations for practical significance

3. **Methodological Rigor**
   - Multiple urban classification approaches for robustness
   - Distance-based analysis to show heat island footprints
   - Integration with existing validation framework from v4

### Expected Outcomes
- Clear visualization of temperature patterns around urban areas
- Quantitative evidence of urban heat island effects
- Statistical significance of urban vs rural temperature differences
- Professional documentation suitable for scientific publication

## Usage Examples

```bash
# Basic urban heat island visualization
python -m src.ushcn_heatisland.main analyze simple \
  --temp-metric min \
  --visualization-type contours \
  --mask-type confidence \
  --show-cities \
  --classify-stations

# Comprehensive heat island analysis with reporting
python -m src.ushcn_heatisland.main analyze simple \
  --temp-metric min \
  --visualization-type contours \
  --mask-type confidence \
  --urban-analysis \
  --heat-island-report \
  --show-cities \
  --show-urban-areas \
  --classify-stations \
  --gradient-analysis

# Conservative analysis for publication
python -m src.ushcn_heatisland.main analyze simple \
  --temp-metric min \
  --visualization-type contours \
  --mask-type confidence \
  --max-interpolation-distance 50 \
  --min-station-count 3 \
  --urban-analysis \
  --heat-island-report \
  --city-population-threshold 250000 \
  --classify-stations \
  --confidence-levels
```

## Output Files Enhanced
- **Existing**: `{algorithm}_{metric}_contour_map.png`
- **New**: `{algorithm}_{metric}_heat_island_map.png`
- **New**: `{algorithm}_{metric}_urban_rural_comparison.png`
- **New**: `{algorithm}_{metric}_distance_gradient.png`
- **Enhanced**: `{algorithm}_{metric}_coverage_report.json` (includes urban analysis)
- **New**: `{algorithm}_{metric}_heat_island_report.json`

## Backward Compatibility
- All existing functionality preserved
- Urban context features are opt-in via CLI flags
- Default behavior unchanged (no urban overlays)
- Enhanced outputs only generated when requested
- Existing validation and masking systems maintained

## Current Implementation Status (as of session completion)

### ✅ Completed Components
- **Urban Context Management Module** (`urban_context.py`): Basic implementation with UrbanContextManager class
  - Station classification: 1,218 USHCN stations → 82.3% rural, 11.6% suburban, 6.1% urban
  - Distance calculations and proximity metrics working
  - Fallback cities dataset with 49 major US cities
- **Heat Island Analysis Framework** (`heat_island_analysis.py`): Full statistical analysis capabilities
  - Urban vs rural temperature comparison functions
  - Heat island intensity calculations with confidence intervals
  - Distance gradient analysis and scientific interpretation
- **Enhanced Visualization** (`plotting.py`): Urban overlay plotting functions
  - `plot_heat_island_map()` function with city markers and station classification
  - Urban area boundary support and population-scaled markers
- **CLI Integration** (`main.py`): Complete command-line interface
  - All urban context options: `--show-cities`, `--classify-stations`, `--urban-analysis`, etc.
  - Heat island report generation and statistical output

### 🚧 Current Issues Identified
- **Limited Cities Data**: Only 49 hardcoded cities (Natural Earth dataset failing)
- **Incomplete Classification Hierarchy**: Missing "urban_fringe" category from 4-level spec
  - Current: urban/suburban/rural (3 levels)
  - Spec requires: urban_core/urban_fringe/suburban/rural (4 levels)
- **No Caching System**: Repeated data loading without persistence
- **Basic Urban Areas**: Circular buffers around cities, not real Census Urban Areas

### 🎯 Next Priority Tasks
1. **Robust Data Sources**: Create utility to fetch comprehensive US cities data
   - Multiple sources: Natural Earth, US Census Places API, OpenStreetMap
   - Include smaller cities (10k+ population) for better coverage
   - Implement caching system (.csv/.json) for offline use
2. **Proper 4-Level Classification**: 
   - Urban Core: Major city centers (>250k population, <25km)
   - Urban Fringe: Around major cities (25-50km)
   - Suburban: Around smaller cities (50-100km)  
   - Rural: >100km from cities
3. **Real Census Urban Areas**: Load actual US Census Urban Areas polygons

### 📊 Validation Results
- **Module Testing**: All UrbanContextManager functions operational
- **Real Data Processing**: 1,218 unique USHCN stations classified successfully
- **Urban Station Detection**: 215 stations (17.7%) classified as urban/suburban
- **Geographic Accuracy**: Distance calculations validated (e.g., 46.2km to Philadelphia)

This specification provides a complete roadmap for transforming the USHCN analysis tool into a focused urban heat island investigation platform while maintaining scientific rigor and backward compatibility.