# USHCN Heat Island Analysis v4 - Enhanced Contour Mapping with Scientific Rigor

## Objective
Enhance isothermal contour mapping to address visual artifacts and ensure methodological defensibility under hostile scientific scrutiny for urban heat island research.

## Current Problems (v3)
1. **Jagged Edges**: Interpolation over areas with no station coverage (oceans, sparse regions)
2. **Map Obscuring**: Contours fill entire rectangular grid, covering basemap and non-data areas
3. **Scientific Vulnerability**: Extrapolation beyond reasonable data limits undermines credibility

## Enhanced Approach (v4)

### Core Principles
- **Conservative Interpolation**: Only interpolate where adequate station coverage exists
- **Geographic Realism**: Respect actual US land boundaries and data coverage
- **Methodological Transparency**: Document limitations and provide validation metrics
- **Visual Clarity**: Preserve basemap visibility while showing data patterns

## Technical Implementation

### 1. Geographic Boundary Masking
**Objective**: Eliminate interpolation over oceans and non-US areas

**Dependencies**:
```python
# Add to pyproject.toml
"naturalearth-data>=1.0.0"  # For US land boundaries
```

**Implementation**:
- Load US land boundary shapefile from Natural Earth
- Clip interpolation grid to land areas only
- Mask ocean and non-US regions as NaN
- Preserve basemap visibility in masked areas

**Function**: `create_land_mask(grid_lats, grid_lons) -> np.ndarray`

### 2. Station Coverage Analysis
**Objective**: Quantify data adequacy for defensible interpolation

**Metrics to Calculate**:
- Nearest neighbor distances for all stations
- Station density per degree square
- Coverage gaps identification
- Voronoi polygon areas (for reference)

**Implementation**:
```python
def analyze_station_coverage(station_coords):
    # Calculate nearest neighbor distances
    # Identify sparse coverage regions
    # Generate coverage statistics
    # Return coverage metrics dict
```

**Output**: Coverage report with statistics for scientific documentation

### 3. Distance-Based Confidence Masking
**Objective**: Only interpolate within scientifically defensible limits

**Confidence Levels**:
- **High Confidence**: Within 50km of ≥3 stations
- **Medium Confidence**: Within 100km of ≥2 stations  
- **Low Confidence**: Beyond limits (masked out)

**Parameters** (CLI configurable):
- `--max-interpolation-distance`: Maximum distance from nearest station (default: 100km)
- `--min-station-count`: Minimum stations within radius (default: 2)
- `--confidence-radius`: Radius for station counting (default: 100km)

**Implementation**:
```python
def create_confidence_mask(
    grid_lats, grid_lons, station_coords,
    max_distance=100, min_stations=2, radius=100
) -> np.ndarray:
    # Calculate distance to nearest station for each grid point
    # Count stations within confidence radius
    # Return confidence mask (0=mask, 1=low, 2=medium, 3=high)
```

### 4. Enhanced Visualization Parameters
**Objective**: Smooth, publication-quality contours with clear confidence indication

**Visual Enhancements**:
- **Alpha Blending**: Smooth transitions at mask boundaries
- **Configurable Opacity**: Based on confidence levels
  - High confidence: alpha=0.8
  - Medium confidence: alpha=0.6
  - Low confidence: alpha=0.3 or masked
- **Subtle Contour Lines**: Thin, semi-transparent for geographic reference
- **Station Overlay**: Optional dots showing data coverage

**New CLI Parameters**:
```bash
--mask-type TEXT              Geographic masking: none, land, confidence [default: land]
--confidence-levels           Show confidence level variations [default: False]
--max-interpolation-distance  Maximum distance from station (km) [default: 100]
--min-station-count          Minimum stations for interpolation [default: 2]
--confidence-radius          Radius for station counting (km) [default: 100]
--alpha-high                 Opacity for high confidence areas [default: 0.8]
--alpha-medium               Opacity for medium confidence areas [default: 0.6]
--show-coverage-report       Generate station coverage statistics [default: False]
```

### 5. Validation and Quality Metrics
**Objective**: Provide scientific validation for interpolation quality

**Cross-Validation**:
- Leave-one-out validation for each station
- Calculate RMSE, MAE, bias statistics
- Report interpolation accuracy by confidence level

**Coverage Statistics**:
- Total stations used
- Coverage area (km²)
- Mean/median station spacing
- Percentage of domain with high/medium/low confidence

**Implementation**:
```python
def validate_interpolation(station_coords, values, method='cubic'):
    # Perform leave-one-out cross-validation
    # Calculate accuracy metrics by confidence level
    # Return validation statistics

def generate_coverage_report(station_coords, grid_coverage):
    # Calculate coverage statistics
    # Generate summary for scientific documentation
    # Return comprehensive coverage report
```

## File Structure Changes

### Enhanced Plotting Module (`plotting.py`)
```python
# New functions to add:
- create_land_mask()
- analyze_station_coverage()
- create_confidence_mask()
- validate_interpolation()
- generate_coverage_report()
- plot_enhanced_contour_map()  # Replaces plot_contour_map()

# Enhanced function signature:
def plot_enhanced_contour_map(
    results_gdf: gpd.GeoDataFrame,
    title: str,
    output_path: Optional[Path] = None,
    # ... existing parameters ...
    mask_type: str = "land",
    confidence_levels: bool = False,
    max_interpolation_distance: float = 100.0,
    min_station_count: int = 2,
    confidence_radius: float = 100.0,
    alpha_high: float = 0.8,
    alpha_medium: float = 0.6,
    show_coverage_report: bool = False
) -> tuple[plt.Figure, dict]:  # Return figure + coverage stats
```

### CLI Updates (`main.py`)
- Add new masking and confidence parameters
- Generate coverage reports when requested
- Validate interpolation quality
- Document methodology in output

### Dependencies (`pyproject.toml`)
```toml
dependencies = [
    # ... existing dependencies ...
    "naturalearth-data>=1.0.0",
    "scikit-learn>=1.3.0",  # For validation metrics
]
```

## Implementation Sequence

### Phase 1: Geographic Masking
1. Add naturalearth-data dependency
2. Implement `create_land_mask()` function
3. Update `plot_contour_map()` to use land masking
4. Test with basic land boundary clipping

### Phase 2: Station Coverage Analysis
1. Implement `analyze_station_coverage()` function
2. Add distance calculation utilities
3. Generate coverage statistics and reports
4. Validate against known USHCN station network

### Phase 3: Confidence-Based Masking
1. Implement `create_confidence_mask()` function
2. Add confidence level visualization
3. Integrate with existing interpolation workflow
4. Test with various confidence parameters

### Phase 4: Enhanced Visualization
1. Add alpha blending and smoothing options
2. Implement multi-level confidence display
3. Add coverage overlay options
4. Update CLI with new parameters

### Phase 5: Validation Framework
1. Implement cross-validation system
2. Add interpolation quality metrics
3. Generate comprehensive coverage reports
4. Document methodology for scientific publication

## Scientific Defense Strategy

### Documentation to Generate
1. **Methodology Report**: Detailed explanation of interpolation approach and limitations
2. **Coverage Analysis**: Station network statistics and adequacy assessment  
3. **Validation Results**: Cross-validation accuracy by region and confidence level
4. **Parameter Sensitivity**: Robustness testing with different thresholds
5. **Comparison Study**: Point-based vs contour visualization agreement

### Key Talking Points for Scrutiny
- "We apply strict geographic and statistical masks to avoid extrapolation beyond our data"
- "Interpolation is limited to areas within [X] km of actual weather stations with adequate coverage"
- "We provide validation metrics and show interpolation confidence levels"
- "Our approach is more conservative than standard meteorological mapping practices"
- "All parameters and limitations are transparently documented and configurable"

## Expected Outcomes

### Visual Improvements
- Clean contours that respect US geography
- Clear basemap visibility
- Smooth, professional appearance
- Confidence-based transparency

### Scientific Rigor
- Defensible methodology under peer review
- Comprehensive validation framework
- Transparent limitation documentation
- Conservative interpolation approach

### Backward Compatibility
- Existing point-based visualization unchanged
- v3 contour options still available with `--mask-type none`
- Enhanced options opt-in via new CLI parameters

## Usage Examples

```bash
# Basic enhanced contour mapping (land masking only)
python -m src.ushcn_heatisland.main analyze simple --visualization-type contours --mask-type land

# Full confidence-based masking with coverage report
python -m src.ushcn_heatisland.main analyze simple \
  --visualization-type contours \
  --mask-type confidence \
  --confidence-levels \
  --max-interpolation-distance 75 \
  --min-station-count 3 \
  --show-coverage-report

# Conservative high-quality contours for publication
python -m src.ushcn_heatisland.main analyze simple \
  --visualization-type contours \
  --mask-type confidence \
  --max-interpolation-distance 50 \
  --min-station-count 3 \
  --confidence-levels \
  --alpha-high 0.7 \
  --show-coverage-report
```

This specification provides a scientifically rigorous foundation for contour mapping that addresses visual artifacts while ensuring methodological defensibility for urban heat island research under potential hostile scrutiny.