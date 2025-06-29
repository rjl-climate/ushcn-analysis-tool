# Progressive Bias Investigation in NOAA Temperature Adjustments

## Research Question

Does NOAA's F52 (fully adjusted) temperature dataset introduce a progressive warming bias beyond the legitimate Time of Observation (TOB) adjustments?

## Background

The USHCN temperature network undergoes several levels of adjustment:
1. **Raw data**: Original temperature measurements
2. **TOB adjusted**: Corrects for changes in observation time
3. **F52 adjusted**: Full adjustments including homogenization, station moves, equipment changes

Previous analysis in this repository found that adjustments actually *enhance* urban heat island signals by 9.4% rather than removing them. This investigation extends that work to examine whether the F52 adjustments introduce a systematic, time-dependent warming bias.

## Hypothesis

The F52 adjustments may introduce a progressive warming bias that:
- Increases over time (stronger adjustments in recent decades)
- Cannot be explained by documented station changes
- Affects both urban and rural stations systematically
- Results in an artificial enhancement of warming trends

## Methodology

### 1. Data Analysis Approach

**Bias Calculation**:
```
Bias(station, time) = F52_temp(station, time) - TOB_temp(station, time)
```

This isolates the non-TOB adjustments (homogenization, station moves, etc.) from the time-of-observation corrections.

### 2. Trend Analysis

For each station, we calculate:
- **Temporal trend**: Linear regression of bias over time (1895 onwards)
- **Cumulative bias**: Total adjustment impact from 1895 to present
- **Acceleration**: Rate of change in adjustment magnitude

**Note**: Analysis starts from 1895 to eliminate bias from sparse early station coverage.

### 3. Statistical Tests

- **Mann-Kendall test**: Detect monotonic trends in bias
- **Breakpoint analysis**: Identify sudden changes in adjustment patterns
- **Regional correlation**: Test if adjustments correlate across distant stations

### 4. Control Analyses

- **Urban vs Rural**: Compare adjustment patterns by station type
- **Regional patterns**: Group by climate zones
- **Data quality**: Consider station completeness and quality

## Expected Outputs

1. **Quantitative Metrics**:
   - Mean bias trend (°C/decade) across network
   - Percentage of stations showing positive bias trends
   - Total cumulative warming added by F52 adjustments
   - Statistical significance of trends

2. **Visualizations**:
   - Time series of network-wide bias
   - Spatial maps of bias trends
   - Comparison plots by station characteristics
   - Cumulative bias evolution

3. **Reports**:
   - Statistical summary tables
   - Findings document with interpretation
   - Recommendations for data users

## How to Run the Analysis

```bash
# Basic analysis for all temperature metrics (starts from 1895)
python analysis/progressive_bias_investigation/scripts/01_calculate_bias_trends.py

# Specific temperature metric
python analysis/progressive_bias_investigation/scripts/01_calculate_bias_trends.py --temp-metric max

# Regional analysis
python analysis/progressive_bias_investigation/scripts/02_regional_analysis.py

# Urban/rural comparison
python analysis/progressive_bias_investigation/scripts/03_urban_rural_comparison.py

# Statistical significance tests
python analysis/progressive_bias_investigation/scripts/04_statistical_tests.py

# Run complete analysis pipeline
python analysis/progressive_bias_investigation/scripts/run_full_analysis.py
```

## Interpretation Guidelines

A genuine progressive warming bias would show:
1. Consistent positive trends in F52-TOB difference
2. Acceleration in recent decades
3. Correlation across geographically distant stations
4. Similar patterns in rural stations (no UHI to correct)

Natural/legitimate adjustments would show:
1. Random distribution of positive and negative trends
2. Adjustments clustered around documented station changes
3. Different patterns for urban vs rural stations
4. No systematic time dependence

## Directory Structure

```
progressive_bias_investigation/
├── README.md                    # This file
├── FINDINGS.md                  # Summary of results
├── scripts/                     # Analysis scripts
├── outputs/                     # Generated results
│   ├── plots/                   # Visualizations
│   └── data/                    # Processed data
└── docs/                        # Additional documentation
    └── methodology.md           # Detailed methods
```