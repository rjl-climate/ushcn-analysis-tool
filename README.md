# USHCN Heat Island Analysis

A Python application for analyzing long-term temperature changes across the United States using USHCN (US Historical Climatology Network) data, with a focus on investigating the impact of official data adjustments on temperature trends.

## Features

### 🌡️ **Temperature Metric Analysis**
- Analyze **minimum**, **maximum**, or **mean** temperatures
- Default analysis uses minimum temperatures
- Compare different metrics to understand varying climate patterns

### 🔍 **Dual-Track Analysis**
- **Primary Track**: Uses officially adjusted USHCN data
- **Skeptical Verification Track**: Compares raw vs adjusted data to quantify adjustment impact
- Investigates whether adjustments systematically alter Urban Heat Island signals

### 📊 **Three Analysis Algorithms**
1. **Simple Anomaly**: Basic temperature trend calculation
2. **Minimum Observations**: Quality-controlled analysis with data requirements
3. **Adjustment Impact**: Quantifies the effect of NOAA adjustments on trends

### 🗺️ **Geospatial Visualization**
- **Point-based maps**: Station-level anomaly visualization with basemap overlays
- **Enhanced isothermal contour maps**: Scientifically rigorous spatial interpolation with confidence masking
- **Geographic masking**: Land boundary clipping and confidence-based interpolation limits
- **Validation framework**: Cross-validation metrics and coverage analysis for scientific defensibility
- **Dual visualization modes**: Choose between discrete station points or smooth contour fields
- Side-by-side comparison plots for adjustment analysis

## Quick Start

### Installation
```bash
# Clone and install dependencies
pip install -e .
```

### Basic Usage
```bash
# Analyze minimum temperature trends (default)
python -m src.ushcn_heatisland.main analyze simple

# Analyze maximum temperature trends
python -m src.ushcn_heatisland.main analyze simple --temp-metric max

# Compare raw vs adjusted data impact
python -m src.ushcn_heatisland.main analyze adjustment_impact

# Quality-controlled analysis
python -m src.ushcn_heatisland.main analyze min_obs --min-observations 300

# Generate enhanced isothermal heat contour maps with land masking
python -m src.ushcn_heatisland.main analyze simple --temp-metric min --visualization-type contours --mask-type land

# Scientifically rigorous contour mapping with confidence-based masking
python -m src.ushcn_heatisland.main analyze simple --temp-metric min --visualization-type contours --mask-type confidence --confidence-levels --show-coverage-report

# Conservative high-quality contours for publication
python -m src.ushcn_heatisland.main analyze simple --temp-metric min --visualization-type contours --mask-type confidence --max-interpolation-distance 50 --min-station-count 3 --confidence-levels --show-coverage-report
```

### Command Line Options
```bash
Core Options:
  --temp-metric TEXT            Temperature metric: min, max, or avg [default: min]
  --baseline-start-year INT     Baseline period start [default: 1951]  
  --current-start-year INT      Current period start [default: 1981]
  --period-length INT           Period length in years [default: 30]
  --min-observations INT        Minimum data required (min_obs algorithm)
  --data-dir PATH              Data directory [default: data]
  --output-dir PATH            Output directory [default: output]

Visualization Options:
  --visualization-type TEXT     Visualization type: points or contours [default: points]
  --grid-resolution FLOAT       Grid resolution in degrees for contour maps [default: 0.1]
  --interpolation-method TEXT   Interpolation method: linear, cubic, or nearest [default: cubic]
  --show-stations              Show station points on contour maps [default: False]
  --contour-levels INT         Number of contour levels (auto if not specified)

Enhanced Masking & Validation (v4):
  --mask-type TEXT             Geographic masking: none, land, confidence [default: land]
  --confidence-levels          Show confidence level variations [default: False]
  --max-interpolation-distance Maximum distance from station (km) [default: 100.0]
  --min-station-count          Minimum stations for interpolation [default: 2]
  --confidence-radius          Radius for station counting (km) [default: 100.0]
  --alpha-high                 Opacity for high confidence areas [default: 0.8]
  --alpha-medium               Opacity for medium confidence areas [default: 0.6]
  --show-coverage-report       Generate station coverage statistics [default: False]
```

## Analysis Results

### Temperature Metrics Comparison
Our analysis reveals different warming patterns across temperature metrics:

- **Minimum temperatures**: Often show stronger warming trends (especially nighttime/winter)
- **Maximum temperatures**: May show different urban heat island signatures  
- **Mean temperatures**: Provide averaged trends but may mask important signals

### Adjustment Impact Findings
The skeptical verification track quantifies how NOAA adjustments affect calculated trends:

- **Mean adjustment impact**: Varies by temperature metric and location
- **Geographic patterns**: Urban vs rural adjustment differences
- **Temporal effects**: How adjustments change over time periods

### Enhanced Visualization & Scientific Rigor (v4)
Our enhanced contour system addresses scientific defensibility for hostile scrutiny:

**Masking Options**:
- **Land masking**: Eliminates artifacts from ocean interpolation, preserves basemap visibility
- **Confidence masking**: Only interpolates within scientifically defensible limits based on station coverage
- **No masking**: Backward compatible with original v3 behavior

**Scientific Validation**:
- **Cross-validation**: Leave-one-out validation with RMSE ≈ 0.40°C, correlation ≈ 0.27, near-zero bias
- **Coverage analysis**: Comprehensive station network statistics (mean spacing ~55km)
- **Confidence levels**: High (≤50km, ≥3 stations), Medium (≤100km, ≥2 stations), Low (limited coverage)
- **Conservative approach**: 34-57% of domain interpolated depending on parameters

**Publication Quality**:
- **Methodological transparency**: All parameters documented and configurable
- **Defensible limitations**: Conservative interpolation prevents extrapolation beyond data
- **Validation reports**: JSON output with interpolation quality metrics and coverage statistics
- **Professional appearance**: Smooth contours with appropriate transparency and geographic context

Example results from minimum temperature analysis:
- Stations processed: 1,218
- Mean anomaly: +0.624°C (1951-1980 vs 1981-2010)
- Adjustment impact: +0.220°C average increase in warming trends

## Contributing

Contributions welcome! Please ensure:
- Code follows existing patterns and type hints
- New algorithms implement the standard interface
- Tests verify functionality with actual USHCN data
- Documentation updated for new features

---

**Note**: This tool is designed for scientific analysis and investigation of climate data processing methods. Results should be interpreted in the context of broader climate science research.