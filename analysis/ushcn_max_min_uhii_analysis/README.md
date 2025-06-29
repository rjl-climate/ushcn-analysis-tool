# USHCN Maximum/Minimum Temperature Urban Heat Island Analysis

## Project Overview

This analysis investigates Urban Heat Island Intensity (UHII) effects in the United States Historical Climatology Network (USHCN) temperature record by comparing maximum and minimum temperature metrics separately. The goal is to provide clear, defensible evidence of urban heat island contamination in the official U.S. temperature record.

## Research Questions

1. **Which temperature metric shows stronger UHII signals**: maximum temperatures (daytime heating) or minimum temperatures (nighttime heat retention)?
2. **What are the optimal temporal analysis periods** for detecting UHII effects?
3. **How significant is urban heat island contamination** in the USHCN temperature record used for climate assessments?

## Key Methodology Distinctions

### Maximum Temperature Analysis
- **Temporal Focus**: Summer months only (June-August) when urban heating effects are strongest
- **Physical Mechanism**: Urban heat absorption and reduced albedo during peak solar heating
- **Expected Results**: Temperature ranges in familiar 80-95°F (27-35°C) zone
- **Policy Relevance**: Heat waves, cooling energy demand, urban planning

### Minimum Temperature Analysis  
- **Temporal Focus**: Year-round analysis (all 12 months) since nighttime effects persist
- **Physical Mechanism**: Urban heat retention due to thermal mass and reduced radiative cooling
- **Expected Results**: Stronger UHII signal due to fundamental thermal properties
- **Scientific Relevance**: Demonstrates systematic urban infrastructure effects

## Dataset Information

- **Source**: United States Historical Climatology Network (USHCN)
- **Temporal Coverage**: 1875-2023 (149 years)
- **Spatial Coverage**: Continental United States
- **Total Stations**: 1,218 weather stations
- **Data Type**: Fully adjusted monthly temperature data (FLS52)

## Station Classification

**Urban Stations (146 total)**:
- **Urban Core**: 26 stations (<25km from cities >250k population)
- **Urban Fringe**: 120 stations (25-50km from cities >100k population)

**Rural Stations (667 total)**:
- **Rural**: >100km from any city with >50k population
- **Conservative Definition**: Ensures minimal urban influence

## Quality Control Framework

Each analysis includes comprehensive validation:
- Station count verification (all 1,218 stations)
- Geographic bounds checking (continental US)
- Temperature range validation (-50°C to +60°C)
- Missing data assessment
- UHII magnitude reasonableness checks
- Temporal coverage verification

## File Structure

```
ushcn_max_min_uhii_analysis/
├── README.md                           # This file
├── methodology.md                      # Detailed analytical methods
├── quality_control.md                  # QC procedures and standards
├── findings_summary.md                 # Key results and conclusions
├── validation_logger.py                # Shared QC utilities
├── create_max_temp_uhii_plot.py       # Summer maximum analysis
├── create_min_temp_uhii_plot.py       # Year-round minimum analysis
├── max_temp_uhii_plot.png             # Maximum temperature visualization
├── min_temp_uhii_plot.png             # Minimum temperature visualization
├── max_temp_validation_log.txt        # Maximum analysis QC results
├── min_temp_validation_log.txt        # Minimum analysis QC results
├── max_temp_statistics.json           # Maximum temperature UHII stats
└── min_temp_statistics.json           # Minimum temperature UHII stats
```

## Key Findings Preview

*[To be populated after analysis completion]*

## Scientific Significance

This analysis provides critical evidence for climate policy discussions by:
1. **Quantifying urban contamination** in official temperature records
2. **Demonstrating systematic biases** in climate trend calculations
3. **Providing defensible methodology** immune to statistical manipulation claims
4. **Supporting infrastructure planning** and urban heat mitigation strategies

## Author

**Richard Lyon** (richlyon@fastmail.com)  
Date: 2025-06-29  
Version: 1.0

## Reproducibility

All analysis scripts include extensive quality control logging and can be executed independently to reproduce results. The methodology is fully documented and transparent for peer review and replication.