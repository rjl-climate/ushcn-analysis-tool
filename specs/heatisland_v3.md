# USHCN Heat Island Analysis v3 - Isothermal Heat Contour Mapping

## Objective
Generate continuous isothermal heat contour maps from discrete station temperature anomaly data using spatial interpolation, replacing discrete station point visualization.

## Current State
- System generates point-based maps showing individual station anomalies
- Station data: 1,218 stations covering continental US (24.56°N to 49.00°N, -124.35°W to -66.99°W)
- Station density: 0.87 stations per degree² across 1,402 degree² area
- Algorithms output station-level results with lat/lon coordinates and anomaly values

## Technical Approach

### Spatial Interpolation Method
**Implementation**: scipy.interpolate.griddata with 'cubic' method
- Smooth interpolation suitable for climate data
- Handles scattered station data well
- Built-in edge case handling

### Grid Specification
- **Coverage**: Continental US bounds (24.56°N to 49.00°N, -124.35°W to -66.99°W)
- **Resolution**: 0.1° spacing (~11km) for balance of detail vs performance
- **Grid Size**: ~245 x 575 = ~140,000 grid points

## Required Changes

### 1. Dependencies (`pyproject.toml`)
Add: `"scipy>=1.10.0"` to dependencies list

### 2. Interpolation Functions (`plotting.py`)
**New Function**: `interpolate_to_grid()`
```python
def interpolate_to_grid(
    lats: np.ndarray, 
    lons: np.ndarray, 
    values: np.ndarray,
    grid_resolution: float = 0.1,
    method: str = 'cubic'
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Returns: grid_lats, grid_lons, interpolated_values
```

**New Function**: `plot_contour_map()`
```python
def plot_contour_map(
    results_gdf: gpd.GeoDataFrame,
    title: str,
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (12, 8),
    colormap: str = "RdBu_r",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    temp_metric: str = "Temperature",
    grid_resolution: float = 0.1,
    interpolation_method: str = 'cubic',
    show_stations: bool = False,
    contour_levels: Optional[int] = None
) -> plt.Figure:
```

### 3. CLI Interface (`main.py`)
**New Options**:
- `--visualization-type`: choices=["points", "contours"], default="points"
- `--grid-resolution`: float, default=0.1, help="Grid resolution in degrees"
- `--interpolation-method`: choices=["linear", "cubic", "nearest"], default="cubic"
- `--show-stations`: bool, default=False, help="Show station points on contour map"
- `--contour-levels`: int, default=None, help="Number of contour levels"

**Implementation**: Update analyze() function to call appropriate plotting function based on visualization_type

### 4. Visualization Integration
**Contour Plotting**:
- Use `matplotlib.pyplot.contourf()` for filled contours
- Add `matplotlib.pyplot.contour()` for contour lines
- Integrate with existing contextily basemap system
- Maintain colorbar functionality with temperature metric labels

**Output Files**:
- Points: `{algorithm}_{metric}_anomaly_map.png` (existing)
- Contours: `{algorithm}_{metric}_contour_map.png` (new)

## Implementation Sequence

### Phase 1: Core Infrastructure
1. Add scipy dependency to pyproject.toml
2. Implement `interpolate_to_grid()` function
3. Test interpolation with sample data
4. Validate grid coverage and resolution

### Phase 2: Contour Visualization
1. Implement `plot_contour_map()` function  
2. Integrate contourf/contour plotting
3. Add basemap integration
4. Test with existing algorithm results

### Phase 3: CLI Integration
1. Add visualization type CLI option
2. Add contour-specific parameters
3. Update main() function routing logic
4. Maintain backward compatibility

### Phase 4: Testing & Validation
1. Test with all three algorithms (simple, min_obs, adjustment_impact)
2. Test with all temperature metrics (min, max, avg)
3. Validate interpolation quality
4. Performance testing with different grid resolutions

## Key Implementation Details

### Interpolation Process
1. Extract coordinates and values from algorithm results GeoDataFrame
2. Filter out NaN/invalid values
3. Create regular lat/lon grid covering continental US
4. Use scipy.interpolate.griddata() with specified method
5. Handle extrapolation limits to avoid artifacts

### Contour Visualization
1. Generate filled contours with contourf()
2. Overlay contour lines for clarity
3. Add station points overlay (optional)
4. Integrate with contextily basemap
5. Apply consistent colormap and scaling

### Error Handling
- Insufficient station data for interpolation
- Extrapolation beyond reasonable limits
- Grid memory constraints for high resolution
- Invalid interpolation method selection

## Example Usage
```bash
# Current point-based visualization (default, backward compatible)
python -m src.ushcn_heatisland.main analyze simple --temp-metric min

# New contour-based visualization
python -m src.ushcn_heatisland.main analyze simple --temp-metric min --visualization-type contours

# Advanced contour options
python -m src.ushcn_heatisland.main analyze simple \
  --temp-metric min \
  --visualization-type contours \
  --grid-resolution 0.05 \
  --interpolation-method cubic \
  --show-stations \
  --contour-levels 20

# Adjustment impact with contours
python -m src.ushcn_heatisland.main analyze adjustment_impact \
  --temp-metric min \
  --visualization-type contours
```

## Scientific Benefits
1. **Continuous spatial representation** of temperature anomalies
2. **Regional pattern identification** (heat islands, geographic trends)
3. **Professional cartographic output** suitable for publications
4. **Gradient visualization** showing smooth temperature transitions
5. **Enhanced spatial analysis** capabilities for climate research

## Technical Validation
- Station density (0.87/degree²) adequate for 0.1° grid interpolation
- Continental US coverage complete with minimal extrapolation needed
- Cubic interpolation provides smooth, realistic temperature fields
- Performance suitable for interactive analysis and report generation

## Backward Compatibility
- Default behavior unchanged (point visualization)
- All existing CLI options preserved
- Same algorithm outputs and statistics files
- Optional contour visualization via explicit user selection