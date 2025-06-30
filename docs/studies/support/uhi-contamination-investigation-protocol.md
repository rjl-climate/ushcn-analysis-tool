# NOAA Adjustment Bias Investigation Protocol

## Executive Summary

This investigation examines whether NOAA's temperature data adjustments systematically reduce legitimate urban heat island signals more than rural temperature trends. Using the USHCN dataset, we compare urban heat island intensity (UHII) across three data types: raw measurements, time-of-observation adjusted data, and fully adjusted data.

## Research Questions

### Primary Research Question
**Do NOAA adjustments systematically reduce urban heat island intensity, potentially masking legitimate urban warming signals?**

### Secondary Research Questions
1. Are urban stations adjusted more aggressively than rural stations?
2. Which metropolitan areas show the largest UHII reductions after adjustment?
3. Has urban adjustment bias increased over time periods?
4. What is the magnitude of UHII reduction from raw to fully adjusted data?

## Methodology

### Data Sources
- **Raw USHCN Data**: Unadjusted station measurements
- **Time-of-Observation Adjusted (TOBs)**: Corrects for observation time changes only
- **Fully Adjusted (FLs52)**: Includes TOBs + homogenization + other adjustments

### Analysis Framework

#### Temporal Parameters (Optimized for Maximum UHII Detection)
- **Baseline Period**: 1895-1924 (earliest reliable USHCN data)
- **Current Period**: 1991-2020 (recent 30-year climatological period)
- **Period Length**: 30 years (standard climatological period)
- **Temperature Metric**: Minimum temperatures (strongest urban heat island signal)

#### Urban Classification System
- **Urban Core**: <25km from cities with 250,000+ population
- **Urban Fringe**: 25-50km from cities with 100,000+ population  
- **Suburban**: 50-100km from cities with 50,000+ population
- **Rural**: >100km from any city with 50,000+ population

#### Quality Control
- **Algorithm**: Simple anomaly (most straightforward comparison)
- **Data Requirements**: Standard completeness thresholds
- **Station Network**: All available USHCN stations with sufficient data

### Statistical Analysis

#### Urban Heat Island Intensity (UHII) Calculation
```
UHII = Mean(Urban_Core_Anomalies) - Mean(Rural_Anomalies)
```

#### Key Metrics to Compare
1. **Raw Data UHII**: Heat island intensity in unadjusted data
2. **TOBs Adjusted UHII**: Heat island intensity after time-of-observation correction
3. **Fully Adjusted UHII**: Heat island intensity after all adjustments
4. **UHII Reduction**: `Raw_UHII - Adjusted_UHII`
5. **Adjustment Magnitude by Classification**: Mean adjustment by urban/rural category

#### Statistical Testing
- **Significance Testing**: T-tests and Mann-Whitney U tests for UHII comparisons
- **Effect Size**: Cohen's d for practical significance
- **Confidence Intervals**: 95% confidence intervals for all UHII estimates

## Scientific Considerations

### Legitimate Reasons for Urban Station Adjustments

1. **Station Relocations**: Urban stations more likely to be moved due to development
2. **Equipment Changes**: Urban stations may have more frequent equipment updates
3. **Site Changes**: Urban development affecting measurement environment
4. **Observer Changes**: Urban stations may have more personnel transitions
5. **Homogenization**: Removing non-climatic influences from temperature records

### Potential Bias Indicators

#### Red Flags That Would Suggest Systematic Bias
1. **Disproportionate Urban Cooling**: Urban stations consistently adjusted downward more than rural
2. **Geographic Clustering**: Major metropolitan areas all show similar UHII reductions
3. **Temporal Correlation**: Adjustments increasing with urban development over time
4. **Magnitude Disparity**: Urban adjustments significantly larger than explainable by legitimate factors

#### Expected Neutral Patterns
1. **Random Distribution**: Adjustments should show no systematic urban/rural bias if legitimate
2. **Proportional Impact**: Adjustment magnitude should correlate with data quality issues, not urbanization
3. **Transparent Rationale**: Clear documentation for large adjustments

### Investigative Approach

#### Steel-Man Strategy
We will use parameters that **maximize** urban heat island detection to provide the strongest possible test of whether adjustments are masking legitimate signals. This approach:
- Uses the longest available high-quality data period
- Focuses on minimum temperatures (strongest physical basis for urban effects)
- Applies conservative urban/rural definitions
- Employs standard climatological methods

This ensures that any reduction in UHII from adjustments cannot be attributed to methodological bias in favor of finding adjustment problems.

## Investigation Stages

### Stage 1: Raw Data Analysis
- Run complete urban heat island analysis on unadjusted USHCN data
- Establish baseline UHII without any adjustments
- Document station classification and data quality

### Stage 2: TOBs Adjusted Analysis  
- Same analysis on time-of-observation corrected data
- Isolate impact of TOBs adjustments specifically
- Compare UHII reduction from raw baseline

### Stage 3: Fully Adjusted Analysis
- Same analysis on completely adjusted data (current standard)
- Document total UHII reduction from raw data
- Compare with current published results

### Stage 4: Comparative Analysis
- Calculate adjustment impact by urban classification
- Identify geographic patterns in UHII reduction
- Perform statistical testing of adjustment bias
- Create visualizations of adjustment patterns

### Stage 5: Case Studies
- Deep dive into major metropolitan areas (NYC, LA, Chicago)
- Station-level adjustment analysis for high-impact stations
- Temporal trend analysis of adjustment bias

## Quality Assurance

### Reproducibility
- All analysis parameters documented
- Command-line arguments recorded for each stage
- Raw data and intermediate results preserved

### Transparency
- Document both concerning and neutral patterns
- Acknowledge legitimate reasons for adjustments
- Present confidence intervals and statistical uncertainty

### Scientific Rigor
- Use established statistical methods
- Compare with published literature where available
- Acknowledge limitations and caveats

## Expected Outcomes

### Possible Findings

#### Scenario 1: No Systematic Bias
- UHII reduction is minimal and within statistical uncertainty
- Urban and rural adjustments are similar in magnitude
- Geographic patterns are random or explainable by data quality

#### Scenario 2: Moderate Bias
- UHII reduction is statistically significant but small (<0.2°C)
- Urban stations show consistently larger adjustments
- Some geographic clustering but limited scope

#### Scenario 3: Systematic Bias
- Large UHII reduction (>0.3°C) from raw to adjusted data
- Urban stations adjusted significantly more than rural
- Widespread geographic pattern across major metropolitan areas

### Implications

Each scenario has different implications for climate research and policy:
- **No bias**: Validates current adjustment procedures for urban heat island research
- **Moderate bias**: Suggests need for refined adjustment methods that preserve urban signals
- **Systematic bias**: Indicates potential fundamental problem with current temperature adjustment approach

## Documentation Standards

Each stage will produce:
1. **Analysis Results**: Complete statistical output and heat island reports
2. **Stage Summary**: Key findings, parameters used, and notable patterns
3. **Visualizations**: Maps and charts showing UHII and adjustment patterns
4. **Quality Metrics**: Data completeness, confidence intervals, and validation checks

## Timeline and Deliverables

### Immediate Deliverables
- Investigation folder structure and protocol (this document)
- Stage-by-stage analysis execution with documentation
- Comparative analysis and visualization
- Final comprehensive report

### Final Report Structure
1. Executive Summary
2. Methodology Summary  
3. Key Findings by Stage
4. Statistical Analysis Results
5. Geographic and Temporal Patterns
6. Discussion and Implications
7. Limitations and Caveats
8. Conclusions and Recommendations

---

**Investigation Start Date**: 2025-06-28  
**Protocol Version**: 1.0  
**Analyst**: USHCN Heat Island Analysis System  
**Data Version**: USHCN v2.5 (Raw, TOBs, FLS52)