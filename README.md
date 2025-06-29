# Urban Heat Island Contamination in USHCN Temperature Records

**A comprehensive analysis revealing that NOAA temperature adjustments enhance rather than remove urban heat island signals**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Research](https://img.shields.io/badge/Research-Climate%20Science-green.svg)](https://github.com)

## 🔬 Research Overview

This project investigates a fundamental question in climate science: **Do NOAA temperature adjustments successfully remove urban heat island contamination from the US temperature record?**

Our analysis of 126 years of data from 1,218 weather stations reveals a surprising answer: **NOAA adjustments enhance urban heat island signals by 9.4% rather than removing them**. This finding has profound implications for climate science, as 22.7% of the USHCN network experiences urban heat island contamination averaging 0.725°C that persists through the adjustment process.

### Key Discovery

**Urban heat island intensity increases through NOAA's adjustment process:**

- **Raw data**: 0.662°C urban heat island effect
- **Time-of-observation adjusted**: 0.522°C (-21.1% reduction)
- **Fully adjusted**: 0.725°C (+9.4% enhancement from raw)

Combined with a persistent 2.98°C baseline temperature difference between urban and rural stations, this indicates **total urban contamination approaching 3.7°C affects 22.7% of the USHCN network**.

> **📄 Full Research Paper**: [Urban Heat Island Contamination Persists in Homogenized USHCN Temperature Records: A 126-Year Analysis](analysis/technical_paper/main.pdf)

---

## 🌍 Scientific Context & Motivation

The integrity of global temperature records underpins our understanding of climate change. The US Historical Climatology Network (USHCN) provides critical data for climate assessments, contributing to major international datasets including GHCN and NASA's GISTEMP analysis.

NOAA applies extensive adjustments to raw temperature measurements, including:

- **Time-of-observation bias corrections**
- **Homogenization procedures** to remove discontinuities
- **Quality control modifications**

These adjustments are intended to remove non-climatic influences while preserving genuine climate signals. **The effectiveness of these procedures in removing urban heat island effects has never been comprehensively tested.**

### The Urban Heat Island Challenge

Urban areas create localized warming through:

- Reduced evapotranspiration from vegetation loss
- Increased heat absorption by built surfaces
- Anthropogenic heat release from human activities
- Modified atmospheric circulation patterns

Given that many long-term weather stations are located in or near population centers that have experienced substantial growth over the past century, **urban heat island contamination represents a significant threat to climate record integrity**.

---

## 📊 Key Findings & Implications

### Primary Results

| Dataset            | UHII (°C) | Change from Raw | Statistical Significance | Effect Size  |
| ------------------ | --------- | --------------- | ------------------------ | ------------ |
| Raw                | 0.662     | —               | p = 0.004                | d = 0.58     |
| TOBs Adjusted      | 0.522     | -21.1%          | p = 0.022                | d = 0.46     |
| **Fully Adjusted** | **0.725** | **+9.4%**       | **p < 0.001**            | **d = 0.97** |

### Dual Contamination Pattern

Our analysis reveals **two distinct forms of urban heat island contamination**:

1. **Baseline Temperature Elevation**: 2.98°C persistent difference between urban and rural stations
2. **Differential Warming Trend**: 0.725°C additional warming in urban areas over 126 years
3. **Total Urban Effect**: ~3.7°C combined contamination affecting 22.7% of USHCN stations

### The Adjustment Paradox

The progression through NOAA's adjustment process shows an unexpected **U-shaped pattern**:

- **Step 1**: Time-of-observation corrections reduce urban signals (-21.1%)
- **Step 2**: Homogenization procedures more than reverse this reduction (+38.8%)
- **Net Effect**: Enhancement of urban heat island signals (+9.4%)

### Global Implications

The United States, with only 36 people/km² and 2.1% of stations in urban cores, represents a **conservative scenario**. More densely populated regions face far greater challenges:

- **United Kingdom**: 275 people/km² (7.6× US density)
- **Germany**: 240 people/km² (6.7× US density)
- **Japan**: 347 people/km² (9.6× US density)
- **Netherlands**: 508 people/km² (14.1× US density)

If similar adjustment procedures enhance urban signals in these regions, **global temperature trends may contain substantially larger urban warming biases than previously recognized**.

---

## 🛠️ Installation & Setup

### System Requirements

- **Python 3.12+** (required for modern type hints and performance)
- **8GB RAM minimum** (16GB recommended for large analyses)
- **5GB disk space** (for data files and outputs)
- **Git** (for cloning repository)

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/rjl-climate/ushcn-heatisland.git
cd ushcn-heatisland

# Install the package and dependencies
pip install -e .

# Verify installation
ushcn-heatisland list-algos
```

### Development Setup

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests to verify setup
python -m pytest tests/ -v

# Check code quality
ruff check src/
mypy src/
```

### Data Requirements

The analysis requires USHCN datasets (102MB total) available from NOAA:

#### **Download Required Data Files**

**Due to file size (102MB total), data files are not included in the repository.**

These are not easily accessible. To assist, we've written [a utility](https://github.com/rjl-climate/US-Historical-Climate-Network-downloader) to download them and create the necessary
data files. To install the utility, follow the instructions. Running the utility will create 4 datafiles:

1. **Monthly FLS52 (fully adjusted)**: `ushcn-monthly-fls52-{date}.parquet` (12MB)
2. **Monthly TOBs (time-of-observation adjusted)**: `ushcn-monthly-tob-{date}.parquet` (11MB)
3. **Monthly Raw**: `ushcn-monthly-raw-{date}.parquet` (11MB)
4. **Daily data** (optional): `ushcn-daily-{date}.parquet` (67MB)

Place these in the folder `/data` in the code directory.

#### **Verify Data Integrity:**

```bash
# Run data validation tests (works with any date in filename)
python -m pytest tests/test_environment.py::test_data_directory_exists -v -s
python -m pytest tests/test_environment.py::test_data_file_naming_patterns -v -s
python -m pytest tests/test_data_loading.py::TestDataLoading::test_load_ushcn_data_fls52 -v
```

## 🚀 Usage Guide

### Basic Temperature Anomaly Analysis

```bash
# Analyze minimum temperature trends (primary metric)
ushcn-heatisland analyze simple --temp-metric min

# Compare different temperature metrics
ushcn-heatisland analyze simple --temp-metric max
ushcn-heatisland analyze simple --temp-metric avg

# Use custom time periods
ushcn-heatisland analyze simple --baseline-start-year 1895 --current-start-year 1995 --period-length 30
```

### Urban Heat Island Investigation

```bash
# Basic urban heat island analysis
ushcn-heatisland analyze simple --temp-metric min --classify-stations --urban-analysis

# Comprehensive heat island investigation with reporting
ushcn-heatisland analyze simple --temp-metric min \
  --visualization-type contours \
  --show-cities \
  --classify-stations \
  --urban-analysis \
  --heat-island-report

# Advanced urban context visualization
ushcn-heatisland analyze simple --temp-metric min \
  --visualization-type contours \
  --show-cities \
  --show-urban-areas \
  --classify-stations \
  --city-population-threshold 100000
```

### Adjustment Impact Analysis

```bash
# Investigate NOAA adjustment effects (key analysis)
ushcn-heatisland analyze adjustment_impact --temp-metric min

# Quality-controlled analysis with minimum observation requirements
ushcn-heatisland analyze min_obs --temp-metric min --min-observations 300
```

### Advanced Visualizations

```bash
# Publication-quality contour maps with confidence masking
ushcn-heatisland analyze simple --temp-metric min \
  --visualization-type contours \
  --mask-type confidence \
  --confidence-levels \
  --show-coverage-report \
  --max-interpolation-distance 75 \
  --min-station-count 3

# Conservative high-quality contours for scientific publication
ushcn-heatisland analyze simple --temp-metric min \
  --visualization-type contours \
  --mask-type confidence \
  --max-interpolation-distance 50 \
  --min-station-count 3 \
  --confidence-levels \
  --show-coverage-report \
  --show-stations
```

---

## 🔬 Reproducing Key Research Results

### Main Paper Finding: UHII Enhancement

Reproduce the core finding that adjustments enhance urban heat island signals:

```bash
# Generate adjustment impact analysis (reproduces Table 2 from paper)
ushcn-heatisland analyze adjustment_impact \
  --temp-metric min \
  --baseline-start-year 1895 \
  --current-start-year 1991 \
  --period-length 30 \
  --output-dir results/main_finding

# Results will show:
# Raw UHII: 0.662°C
# TOBs UHII: 0.522°C (-21.1%)
# Fully Adjusted UHII: 0.725°C (+9.4%)
```

### Enhanced 1895+ Analysis

Reproduce the network quality-informed analysis using adequate station coverage:

```bash
# Run enhanced minimum temperature analysis (1895+ start date)
cd analysis/ushcn_uhii_analysis_1895_plus
python create_min_temp_uhii_plot_1895.py

# Run enhanced maximum temperature analysis
python create_max_temp_uhii_plot_1895.py

# Results reproduce the 2.975°C minimum temp UHII and 0.588°C maximum temp UHII
```

### Network Quality Assessment

Validate the station coverage that informed our 1895+ methodology:

```bash
cd analysis/ushcn_network_quality_assessment
python create_station_coverage_plot.py

# Demonstrates the dramatic network expansion 1890-1908 and inadequate pre-1895 coverage
```

### Adjustment Bias Investigation

Reproduce the systematic investigation of adjustment effects across all three datasets:

```bash
cd analysis/adjustment_bias_investigation/04_comparative_analysis
python comparative_analysis.py

# Generates comprehensive comparison showing the U-shaped adjustment pattern
```

### Publication Figures

Generate academic-quality figures used in the technical paper:

```bash
cd analysis/network_visualisation
python create_network_visualisation.py

# Creates Figure 1: USHCN station network map with urban classification
```

---

## 📁 Project Structure

```
ushcn-heatisland/
├── src/ushcn_heatisland/           # Core package
│   ├── analysis/                   # Analysis algorithms
│   │   ├── anomaly/               # Temperature anomaly calculations
│   │   │   ├── simple_anomaly.py  # Basic anomaly algorithm
│   │   │   ├── min_obs_anomaly.py # Quality-controlled analysis
│   │   │   └── adjustment_impact.py # Raw vs adjusted comparison
│   │   └── heat_island.py         # Urban heat island analysis
│   ├── cli/                       # Command-line interface
│   ├── data/                      # Data loading utilities
│   ├── urban/                     # Urban classification system
│   ├── visualization/             # Plotting and mapping
│   └── utils/                     # Utility functions
├── analysis/                      # Research analysis scripts
│   ├── ushcn_uhii_analysis_1895_plus/    # Enhanced UHII analysis
│   ├── adjustment_bias_investigation/     # Systematic adjustment study
│   ├── ushcn_network_quality_assessment/ # Station coverage analysis
│   ├── network_visualisation/            # Academic figure generation
│   └── technical_paper/                  # LaTeX paper source
├── data/                          # Data files
│   ├── ushcn-monthly-*.parquet   # USHCN temperature datasets
│   └── cities/                   # Urban classification database
├── tests/                        # Integration test suite
└── output/                       # Analysis results
```

### Key Components

- **`src/ushcn_heatisland/analysis/anomaly/`**: Core temperature anomaly algorithms
- **`src/ushcn_heatisland/urban/context.py`**: 4-level urban classification system
- **`src/ushcn_heatisland/cli/main.py`**: Command-line interface
- **`analysis/ushcn_uhii_analysis_1895_plus/`**: Network quality-informed enhanced analysis
- **`analysis/adjustment_bias_investigation/`**: Systematic multi-stage comparison study
- **`analysis/technical_paper/main.tex`**: Academic paper documenting findings

---

## 🧪 Scientific Methodology

### Temperature Anomaly Calculation

Temperature anomalies computed using 30-year climatological periods:

```
Anomaly = Mean(Current_Period) - Mean(Baseline_Period)
```

**Default Configuration:**

- **Baseline Period**: 1895-1924 (earliest reliable data)
- **Current Period**: 1991-2020 (recent climatology)
- **Temperature Metric**: Minimum temperatures (strongest urban signal)
- **Analysis Span**: 126 years (maximum temporal leverage)

### Urban Classification System

**4-Level Hierarchy** based on distance to population centers:

1. **Urban Core** (<25km from 250k+ cities): 26 stations (2.1%)
2. **Urban Fringe** (25-50km from 100k+ cities): 120 stations (9.9%)
3. **Suburban** (50-100km from 50k+ cities): 405 stations (33.3%)
4. **Rural** (>100km from any 50k+ city): 667 stations (54.8%)

### Urban Heat Island Intensity (UHII)

```
UHII = Mean(Urban_Anomalies) - Mean(Rural_Anomalies)
```

**Statistical Validation:**

- Independent samples t-test and Mann-Whitney U test
- Effect sizes quantified using Cohen's d
- 95% confidence intervals via bootstrap methods
- Significance threshold: p < 0.05

### Quality Control

- **Temporal completeness**: Sufficient data in both analysis periods
- **Geographic validation**: Coordinate verification against known locations
- **Conservative urban definitions**: Minimize misclassification bias
- **Consistent methodology**: Identical processing across all three datasets

---

## 📚 Data Sources & Requirements

### USHCN Temperature Datasets

**Source**: NOAA National Centers for Environmental Information

- **URL**: https://www.ncei.noaa.gov/products/land-based-station/us-historical-climatology-network
- **Version**: USHCN v2.5
- **Format**: Parquet files (optimized for analysis)
- **Coverage**: 1,218 stations, 1865-2025

**Required Files:**

1. `ushcn-monthly-fls52-2025-06-27.parquet` (12.5 MB) - Fully adjusted data
2. `ushcn-monthly-tob-2025-06-27.parquet` (11.8 MB) - Time-of-observation adjusted
3. `ushcn-monthly-raw-2025-06-27.parquet` (10.2 MB) - Raw measurements

### US Cities Database

**Source**: Plotly's Top 1000 US Cities (based on Census Bureau data)

- **File**: `data/cities/us_cities_static.csv`
- **Coverage**: 743 cities with population ≥50,000
- **Quality Control**: Coordinate validation, duplicate removal, geographic bounds checking
- **Usage**: Urban classification and heat island analysis

### Output Data Structure

Analysis generates structured outputs in `output/` directory:

- **Statistics**: JSON files with quantitative results and metadata
- **Visualizations**: PNG maps and plots (300 DPI, publication quality)
- **Reports**: Comprehensive JSON reports with heat island analysis
- **Validation**: Quality control logs and coverage statistics

---

## 🧪 Development & Testing

### Running Tests

```bash
# Run the full integration test suite
python -m pytest tests/ -v

# Quick verification tests
python -m pytest tests/test_environment.py tests/test_data_loading.py -v

# Test specific components
python -m pytest tests/test_cli_integration.py -v
python -m pytest tests/test_analysis_workflow.py -v
```

### Data Validation Tests

Verify your downloaded data files are correct:

```bash
# Comprehensive data validation
python -m pytest tests/test_environment.py::test_data_directory_exists -v
python -m pytest tests/test_data_loading.py -v

# Test data loading for all formats
python -m pytest tests/test_data_loading.py::TestDataLoading::test_load_all_data_types -v

# Verify urban classification data
python -m pytest tests/test_data_loading.py::TestUrbanContextLoading -v
```

Expected outputs:

- ✅ All data files found and accessible
- ✅ 1,218 stations loaded from monthly data
- ✅ Valid temperature data ranges (-50°C to +50°C)
- ✅ Geographic coordinates within US bounds
- ✅ 743 cities loaded for urban classification

### Code Quality

```bash
# Lint code with ruff
ruff check src/ analysis/

# Type checking with mypy
mypy src/

# Format code
ruff format src/ analysis/
```

### Adding New Analysis Methods

New algorithms should implement the standard interface in `src/ushcn_heatisland/analysis/anomaly/`:

```python
def calculate(
    gdf_adjusted: gpd.GeoDataFrame,
    baseline_period: tuple[int, int],
    current_period: tuple[int, int],
    gdf_raw: gpd.GeoDataFrame | None = None,
    config: dict[str, Any] | None = None,
) -> gpd.GeoDataFrame:
    """
    Calculate temperature anomalies.

    Returns GeoDataFrame with columns:
    - station_id, geometry, anomaly_celsius
    - Plus algorithm-specific metrics
    """
```

Register new algorithms in `src/ushcn_heatisland/analysis/anomaly/__init__.py`.

---

## 📖 Citation & Academic Use

### Citing This Work

**Software Citation:**

```
Lyon, R. (2025). USHCN Heat Island Analysis: Urban Heat Island Contamination
in USHCN Temperature Records. https://github.com/your-username/ushcn-heatisland
```

**Research Citation:**

```
Lyon, R. (2025). Urban Heat Island Contamination Persists in Homogenized
USHCN Temperature Records: A 126-Year Analysis. [Journal/Preprint]
```

### Academic Paper

The complete methodology, findings, and implications are documented in the accompanying technical paper: `analysis/technical_paper/main.pdf`

**Key Sections:**

- **Abstract**: Research question, methodology, and primary findings
- **Methods**: Detailed analytical procedures and validation
- **Results**: Quantitative findings with statistical analysis
- **Discussion**: Scientific implications and global extrapolation
- **Conclusion**: Policy implications and future research priorities

### Data Availability

- **Analysis Code**: Complete source code available in this repository
- **Raw Data**: Public USHCN datasets from NOAA (links provided)
- **Intermediate Results**: Available upon request for verification
- **Reproducibility**: All key findings reproducible using provided scripts

---

## ⚠️ Limitations & Future Research

### Current Limitations

1. **Geographic Scope**: Analysis limited to the United States
2. **Single Network**: Focused on USHCN (though highly representative)
3. **Aggregate Analysis**: Examines patterns rather than individual station adjustments
4. **Correlation vs Causation**: Identifies enhancement pattern but not root cause

### Critical Future Research

#### Immediate Priorities

1. **Global Extension**: Analyze temperature networks in densely populated regions
   - **Europe**: UK, Germany, France, Netherlands, Belgium
   - **East Asia**: Japan, South Korea, Taiwan
   - **Rapidly Urbanizing**: China, India, Brazil

2. **Algorithm Investigation**: Understand why homogenization enhances urban signals
   - Station-by-station adjustment analysis
   - Pairwise comparison methodology evaluation
   - Alternative homogenization approaches (ACMANT, HOMER, RHtest)

3. **Independent Validation**: Compare with non-surface temperature measurements
   - Satellite temperature records (RSS, UAH)
   - Radiosonde networks
   - Purpose-built reference networks (USCRN)

#### Long-term Objectives

4. **Global GHCN Analysis**: Systematic worldwide evaluation
5. **Population Density Studies**: Quantify contamination vs. urbanization intensity
6. **Climate Model Implications**: Assess impact on model validation and projections
7. **Policy Assessment**: Recalibrate temperature targets accounting for measurement bias

### Global Implications

The US finding of 22.7% station contamination averaging 0.725°C likely represents a **conservative lower bound** given:

- **Low population density** (36 people/km²)
- **Abundant rural reference stations**
- **Only 2.1% urban core stations**

Regions with 7-14× higher population density may have:

- **30-50% urban-influenced stations**
- **4-5°C baseline UHI effects**
- **Proportionally larger trend contamination**
- **Limited or no rural reference stations**

---

## 🤝 Contributing

We welcome contributions from climate scientists, data analysts, and software developers. This research benefits from diverse perspectives and expertise.

### Types of Contributions

- **Code improvements**: Algorithm optimization, new analysis methods
- **Scientific validation**: Independent verification, alternative methodologies
- **Global extension**: Analysis of international temperature networks
- **Visualization**: Enhanced plotting and mapping capabilities
- **Documentation**: Methodology clarification, tutorial development

### Contribution Guidelines

1. **Scientific rigor**: Maintain high standards for data analysis and validation
2. **Reproducibility**: All contributions must be fully reproducible
3. **Code quality**: Follow existing patterns, include type hints, add tests
4. **Documentation**: Update relevant README sections and docstrings
5. **Testing**: Verify functionality with integration tests

### Getting Started

```bash
# Fork the repository and create a feature branch
git checkout -b feature/your-contribution

# Make changes and test thoroughly
python -m pytest tests/ -v
ruff check src/
mypy src/

# Submit a pull request with detailed description
```

---

## 📄 License & Disclaimer

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Scientific Disclaimer

This research represents an independent investigation into temperature data processing methods. The findings:

- **Are based on publicly available data** and standard statistical methods
- **Do not constitute evidence of deliberate manipulation** or conspiracy
- **Highlight unintended consequences** of statistical algorithms
- **Contribute to scientific understanding** of measurement uncertainties
- **Support improved accuracy** in climate assessments

### Responsible Use

Results should be interpreted within the broader context of climate science research. The identification of urban heat island contamination:

- **Does not negate anthropogenic climate change**
- **Suggests refinement of warming magnitude estimates**
- **Supports improved measurement accuracy**
- **Benefits all stakeholders in climate science and policy**

---

## 🔗 Links & Resources

- **NOAA USHCN**: https://www.ncei.noaa.gov/products/land-based-station/us-historical-climatology-network
- **Technical Paper**: `analysis/technical_paper/main.pdf`
- **Issue Tracker**: [GitHub Issues](https://github.com/your-username/ushcn-heatisland/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ushcn-heatisland/discussions)

---

_This research contributes to the continuous improvement of climate science through the identification and correction of systematic measurement biases. Scientific progress depends on the willingness to follow evidence wherever it leads, acknowledge uncertainties when discovered, and refine methods accordingly._
