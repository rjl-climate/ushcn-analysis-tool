# USHCN Heat Island Analysis v2 - Temperature Metric Selection

## Objective
Add the ability to select between minimum, maximum, or mean temperature for all algorithms, defaulting to minimum temperature.

## Current State
- System hardcodes using average temperature (`avg_` columns)
- Data contains `min_`, `max_`, and `avg_` columns for each adjustment type (raw, tob, fls52)
- Three algorithms work with temperature data: simple_anomaly, min_obs_anomaly, adjustment_impact

## Required Changes

### 1. Data Loader (`src/ushcn_heatisland/data_loader.py`)
**Function: `load_ushcn_monthly_data()`**
- Add parameter: `temp_metric: Literal["min", "max", "avg"] = "min"`
- Change line 58: `temp_col = f"avg_{data_type}"` → `temp_col = f"{temp_metric}_{data_type}"`
- Add validation for column existence

**Function: `load_ushcn_data()`**
- Add parameter: `temp_metric: Literal["min", "max", "avg"] = "min"`
- Pass `temp_metric` to both `load_ushcn_monthly_data()` calls

### 2. CLI Interface (`src/ushcn_heatisland/main.py`)
**Function: `analyze()`**
- Add CLI option: `temp_metric: str = typer.Option("min", help="Temperature metric to analyze: min, max, or avg")`
- Pass `temp_metric` parameter to `load_ushcn_data()` calls
- Update console output to show selected metric

### 3. Visualization (`src/ushcn_heatisland/plotting.py`)
**Functions: `plot_anomaly_map()` and `plot_comparison_maps()`**
- Update plot titles to include temperature metric
- Update colorbar labels from "Temperature Anomaly (°C)" to "{Metric} Temperature Anomaly (°C)"

### 4. Algorithm Documentation
**Files: All algorithm files (.py)**
- Update docstrings to mention temperature metric is passed via data loader
- No code changes needed - algorithms work with whatever data is provided

## Implementation Sequence
1. Update `data_loader.py` with temp_metric parameter
2. Update `main.py` CLI interface 
3. Update `plotting.py` visualization labels
4. Update algorithm docstrings
5. Test with different metrics
6. Verify backward compatibility

## Validation Steps
1. Confirm all three metrics (min/max/avg) work with all three algorithms
2. Verify output files include metric in names/titles
3. Test adjustment_impact algorithm with different metrics
4. Confirm default behavior uses minimum temperature

## Key Implementation Details
- Default changes from mean to minimum temperature
- Temperature metric selection happens at data loading level
- Algorithms remain unchanged - they process whatever temperature data is loaded
- All output (plots, statistics, console) should clearly indicate selected metric

## Example Usage
```bash
# Use minimum temperature (default)
python -m src.ushcn_heatisland.main analyze simple

# Use maximum temperature
python -m src.ushcn_heatisland.main analyze simple --temp-metric max

# Use mean temperature (previous default)
python -m src.ushcn_heatisland.main analyze simple --temp-metric avg
```