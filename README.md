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

### 🏙️ **Urban Heat Island Investigation (v5)**
- **4-level urban classification**: Urban core, urban fringe, suburban, and rural station categorization
- **Static cities database**: 743 US cities ≥50k population with quality-controlled coordinates
- **Population-based thresholds**: Scientific classification using city population and distance criteria
- **Urban context overlays**: City markers, urban area boundaries, and station classification visualization
- **Heat island statistics**: Urban vs rural temperature comparison with statistical significance testing
- **No network dependencies**: Reliable offline operation with comprehensive geographic coverage

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

# Urban heat island investigation with city overlays and station classification
python -m src.ushcn_heatisland.main analyze simple --temp-metric min --visualization-type contours --show-cities --classify-stations --urban-analysis

# Comprehensive heat island analysis with full reporting
python -m src.ushcn_heatisland.main analyze simple --temp-metric min --visualization-type contours --show-cities --classify-stations --urban-analysis --heat-island-report --show-urban-areas
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

Urban Heat Island Investigation (v5):
  --show-cities                Show major cities overlay [default: False]
  --city-population-threshold  Minimum city population to display [default: 100000]
  --show-urban-areas          Show urban area boundaries [default: False]
  --classify-stations         Color-code stations by urban/rural classification [default: False]
  --urban-analysis            Generate urban heat island statistics [default: False]
  --heat-island-report        Generate comprehensive heat island analysis [default: False]
  --urban-distance-threshold  Maximum distance to classify as urban (km) [default: 50.0]
  --suburban-distance-threshold Maximum distance for suburban classification (km) [default: 100.0]
  --gradient-analysis         Analyze temperature gradients from cities [default: False]
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

### Urban Heat Island Analysis (v5)
Our urban heat island investigation provides robust classification and analysis capabilities:

**Station Classification Results**:
- **Urban Core**: 26 stations (2.1%) - <25km from cities with 250k+ population
- **Urban Fringe**: 120 stations (9.9%) - 25-50km from cities with 100k+ population
- **Suburban**: 405 stations (33.3%) - 50-100km from cities with 50k+ population
- **Rural**: 667 stations (54.8%) - >100km from any significant city

**Urban Context Database**:
- **743 US cities** with population ≥50,000 (quality-controlled static database)
- **98% geographic coverage** (50/51 US states represented)
- **Population range**: 50,111 (Casa Grande, AZ) to 8,405,837 (New York City)
- **No network dependencies**: Reliable offline operation with validated coordinates

**Heat Island Detection**:
- **Population-based thresholds**: Scientific classification using city size and proximity
- **4-level hierarchy**: More nuanced analysis than traditional urban/rural binary
- **Statistical validation**: Cross-referenced against Census Bureau data
- **Visual correlation**: Temperature anomalies overlaid with urban context for investigation

## Urban Context Database Documentation

### Static Cities Database (`data/cities/us_cities_static.csv`)

The urban heat island analysis relies on a comprehensive, quality-controlled database of US cities created specifically for this project.

#### Database Creation Process

1. **Source Data Collection**:
   - Downloaded from Plotly's Top 1000 US Cities dataset (GitHub: plotly/datasets)
   - Contains city names, states, population, latitude, and longitude
   - Based on official Census Bureau and authoritative geographic sources

2. **Quality Control Pipeline** (`scripts/create_static_cities_db.py`):
   ```bash
   # Create the static database with validation
   python scripts/create_static_cities_db.py --min-population 50000
   ```

3. **Geographic Validation**:
   - **Coordinate bounds checking**: Validates all coordinates within US territory (18°N-71.5°N, -180°W to -65°W)
   - **Missing data removal**: Eliminates cities with incomplete coordinate or population data
   - **Duplicate resolution**: Removes duplicate city entries, keeping highest population version

4. **Population Filtering**:
   - **Minimum threshold**: 50,000 population (urban area classification standard)
   - **Range validation**: Population data cross-checked for reasonableness
   - **Statistical analysis**: Population distribution validated (range: 50,111 - 8,405,837)

5. **Coverage Analysis**:
   - **State coverage**: 98% (50/51 states - only Vermont missing due to population threshold)
   - **Geographic distribution**: Comprehensive coverage from Alaska to Hawaii
   - **Urban hierarchy**: 77 cities ≥250k, 293 cities ≥100k, 743 cities ≥50k population

6. **Cross-Validation Sample**:
   - **Sample verification**: 20 cities validated against Census Bureau coordinates
   - **Distance accuracy**: Geographic calculations verified for major metropolitan areas
   - **Population verification**: Sample population data cross-referenced with official sources

#### Database Schema

| Column | Type | Description |
|--------|------|-------------|
| `city_name` | string | Official city name |
| `state` | string | US state name |
| `population` | integer | City population (≥50,000) |
| `latitude` | float | Decimal degrees (WGS84) |
| `longitude` | float | Decimal degrees (WGS84) |
| `data_source` | string | Source tracking (`plotly_top1k`) |

#### Classification Methodology

The 4-level urban classification system uses distance-based thresholds combined with city population criteria:

1. **Urban Core** (<25km from 250k+ cities):
   - Major metropolitan centers with strong urban heat island effects
   - Examples: Baltimore (1.1km), Seattle (6.0km), Bloomington (9.0km)

2. **Urban Fringe** (25-50km from 100k+ cities):
   - Urban periphery with moderate urban influence
   - Examples: Rochester area (36.0km), Columbia area (44.0km)

3. **Suburban** (50-100km from 50k+ cities):
   - Mixed urban-rural transition zones
   - Examples: 63-81km from various cities

4. **Rural** (>100km from any 50k+ city):
   - Minimal urban influence, baseline climate conditions
   - Examples: >103km from nearest cities

#### Quality Assurance

- **No network dependencies**: Static database eliminates API failures and connectivity issues
- **Version controlled**: Database changes tracked in git for reproducibility
- **Metadata documentation**: Complete provenance and creation process documented
- **Validation scripts**: Automated quality checks ensure data integrity
- **Scientific defensibility**: Methodology based on established urban climatology standards

This robust urban context foundation enables reliable heat island investigation without the complexity and failure points of dynamic data fetching systems.

## Contributing

Contributions welcome! Please ensure:
- Code follows existing patterns and type hints
- New algorithms implement the standard interface
- Tests verify functionality with actual USHCN data
- Documentation updated for new features

---

**Note**: This tool is designed for scientific analysis and investigation of climate data processing methods. Results should be interpreted in the context of broader climate science research.