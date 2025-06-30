# Detailed Methodology for Progressive Bias Investigation

## 1. Mathematical Framework

### 1.1 Bias Definition

For each station *i* at time *t*, we define the adjustment bias as:

```
B(i,t) = T_F52(i,t) - T_TOB(i,t)
```

Where:
- `T_F52(i,t)` = Fully adjusted (F52) temperature for station *i* at time *t*
- `T_TOB(i,t)` = Time-of-observation adjusted temperature for station *i* at time *t*
- `B(i,t)` = Non-TOB adjustment applied by NOAA

This isolates the adjustments beyond TOB corrections, including:
- Homogenization adjustments
- Station move corrections
- Equipment change adjustments
- Urban heat island "corrections"

### 1.2 Trend Calculation

For each station, we calculate the temporal trend using ordinary least squares regression:

```
B(i,t) = β₀(i) + β₁(i) × t + ε(i,t)
```

Where:
- `β₁(i)` = Bias trend for station *i* (°C/year)
- `β₀(i)` = Intercept (baseline bias)
- `ε(i,t)` = Residual error

The key metric is `β₁(i) × 10` = trend per decade

### 1.3 Network-Wide Analysis

The network-wide bias trend is calculated as:

```
β̄₁ = (1/N) × Σᵢ β₁(i)
```

With standard error:

```
SE(β̄₁) = σ(β₁) / √N
```

## 2. Data Processing Steps

### 2.1 Data Loading and Matching

1. Load TOB adjusted data for all stations
2. Load F52 adjusted data for all stations
3. Match records by:
   - Station ID
   - Year
   - Month

### 2.2 Quality Control

1. **Temporal Coverage**: Require minimum 10 years of data
2. **Annual Completeness**: Require ≥6 months per year
3. **Trend Reliability**: Require ≥30 data points for trend calculation
4. **Start Year Filter** (for urban/rural analysis): Require first year ≤1905 to ensure consistent long-term coverage from 1895 baseline

### 2.3 Bias Calculation

For each matched record:
1. Calculate monthly bias: `B = F52 - TOB`
2. Aggregate to annual means (requiring ≥6 months)
3. Apply linear regression to annual time series

## 3. Statistical Tests

### 3.1 Individual Station Significance

For each station trend, we test:
- **H₀**: β₁(i) = 0 (no temporal trend)
- **H₁**: β₁(i) ≠ 0 (significant trend)

Using t-test with significance level α = 0.05

### 3.2 Network-Wide Tests

#### Mann-Kendall Test
Non-parametric test for monotonic trends in the network-wide mean bias:

```
S = Σᵢ₌₁ⁿ⁻¹ Σⱼ₌ᵢ₊₁ⁿ sgn(Bⱼ - Bᵢ)
```

Where sgn is the signum function.

#### Breakpoint Detection
Using Pettitt's test to identify sudden changes in adjustment patterns:

```
Uₖ = Σᵢ₌₁ᵏ Σⱼ₌ₖ₊₁ⁿ sgn(Bⱼ - Bᵢ)
```

The most probable breakpoint occurs at k where |Uₖ| is maximum.

### 3.3 Spatial Analysis

Test for spatial autocorrelation using Moran's I:

```
I = (N/W) × (Σᵢ Σⱼ wᵢⱼ(βᵢ - β̄)(βⱼ - β̄)) / (Σᵢ(βᵢ - β̄)²)
```

Where wᵢⱼ are spatial weights based on distance.

## 4. Control Analyses

### 4.1 Urban vs Rural Stratification

#### Station Classification
Stations are classified based on distance to cities with population >50,000:
- **Urban Core**: ≤25 km from large city
- **Urban**: 25-50 km from large city  
- **Suburban**: 50-100 km from large city
- **Rural**: >100 km from any large city

For analysis, these are simplified to binary classification:
- **Urban**: Stations within 100 km of cities >50k population (includes urban core, urban, and suburban)
- **Rural**: Stations >100 km from any city >50k population

#### Temporal Filtering for Urban/Rural Analysis
To ensure consistent time series comparison, stations are filtered by data availability:
- **Inclusion criterion**: Station must have first year of data ≤ 1905 (within 10 years of 1895 start)
- **Rationale**: Ensures all analyzed stations cover most of the study period (1895-2023)
- **Impact**: Excludes 269 stations (22.1%) that began recording after 1905
- **Result**: 949 stations analyzed (668 urban, 281 rural)

This temporal filtering prevents bias from comparing stations with vastly different recording periods and ensures robust long-term trend analysis.

We test if bias trends differ between groups using Welch's t-test and Mann-Whitney U test.

### 4.2 Regional Stratification

Stations are grouped by climate regions to control for:
- Regional climate variations
- Policy implementation differences
- Data density effects

### 4.3 Temporal Stratification

Analysis is performed for multiple time periods:
- Full period (1895-present)
- Early period (1895-1950)
- Middle period (1951-1980)
- Recent period (1981-present)

## 5. Interpretation Framework

### 5.1 Evidence of Systematic Bias

Strong evidence would include:
1. **Consistent Direction**: >70% of stations show positive trends
2. **Statistical Significance**: Network-wide trend p < 0.01
3. **Large Magnitude**: Mean trend >0.01°C/decade
4. **Acceleration**: Trends stronger in recent decades
5. **Spatial Coherence**: Similar trends across regions

### 5.2 Evidence Against Systematic Bias

Would include:
1. **Random Distribution**: ~50% positive, ~50% negative trends
2. **No Significance**: Network-wide p > 0.05
3. **Small Magnitude**: |Mean trend| <0.005°C/decade
4. **Temporal Stability**: No acceleration over time
5. **Spatial Heterogeneity**: Regional differences dominate

### 5.3 Alternative Explanations

Consider whether patterns could result from:
1. **Legitimate adjustments**: Documented station changes
2. **Urban growth**: Increasing UHI requiring correction
3. **Network changes**: Shifting station composition
4. **Methodology artifacts**: Statistical or computational issues

## 6. Uncertainty Quantification

### 6.1 Sources of Uncertainty

1. **Measurement uncertainty**: ±0.1°C typical
2. **Adjustment uncertainty**: Undocumented changes
3. **Sampling uncertainty**: Incomplete station coverage
4. **Trend uncertainty**: Regression standard errors

### 6.2 Propagation Methods

1. **Bootstrap resampling**: 1000 iterations with replacement
2. **Jackknife**: Leave-one-out station analysis
3. **Monte Carlo**: Simulate measurement errors

### 6.3 Reporting

All results reported with:
- 95% confidence intervals
- Standard errors
- Sample sizes
- Significance levels

## 7. Limitations

### 7.1 Data Limitations

- Station coverage varies over time
- Missing data may not be random
- Adjustment algorithms have changed over time

### 7.2 Methodological Limitations

- Linear trends may oversimplify
- Spatial correlation not fully modeled
- Cannot separate all adjustment types

### 7.3 Interpretive Limitations

- Correlation does not imply causation
- Multiple hypotheses increase false positive risk
- Results specific to USHCN network

## 8. Validation Approaches

### 8.1 Sensitivity Analysis

Test robustness to:
- Minimum data requirements
- Trend calculation methods
- Time period selection
- Station selection criteria

### 8.2 Cross-Validation

- Compare with independent temperature datasets
- Check against satellite era (1979+)
- Validate with reanalysis products

### 8.3 Reproducibility

All analysis code is:
- Version controlled
- Fully documented
- Uses fixed random seeds
- Includes data version information