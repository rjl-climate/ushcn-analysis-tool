# Quality Control Framework

## Overview

This document defines the comprehensive quality control procedures applied to the USHCN maximum/minimum temperature Urban Heat Island analysis. All validation steps are logged and documented to ensure analytical rigor and reproducibility.

## Quality Control Categories

### 1. Data Integrity Validation

#### Station Count Verification
- **Requirement**: All 1,218 USHCN stations must be loaded
- **Test**: Count unique station IDs in dataset
- **Action if Failed**: Analysis termination with diagnostic output
- **Log Entry**: `STATION_COUNT [PASS/ERROR] Total stations: {count}`

#### Geographic Bounds Checking
- **Requirement**: All stations within continental US coordinates
- **Latitude Bounds**: 24.0°N to 50.0°N
- **Longitude Bounds**: -125.0°W to -66.0°W
- **Test**: Validate all lat/lon coordinates within bounds
- **Action if Failed**: Analysis termination with coordinate diagnostics
- **Log Entry**: `GEOGRAPHIC [PASS/ERROR] All stations within CONUS bounds`

#### Coordinate Completeness
- **Requirement**: No missing lat/lon values
- **Test**: Check for NaN values in coordinate columns
- **Action if Failed**: Analysis termination with missing data report
- **Log Entry**: `GEOGRAPHIC [PASS/ERROR] Valid coordinates for all stations`

### 2. Temperature Data Validation

#### Physical Range Checking
- **Temperature Bounds**: -50.0°C to +60.0°C
- **Rationale**: Encompasses extreme continental US temperature records
- **Test**: Validate all temperature values within physically realistic range
- **Action if Failed**: Warning logged, outliers reported but analysis continues
- **Log Entry**: `TEMPERATURE [PASS/WARNING] {metric}: {count} values within bounds`

#### Missing Data Assessment
- **Requirement**: Adequate data coverage for reliable averaging
- **Test**: Count missing values by station and time period
- **Action if Failed**: Warning logged, affected periods documented
- **Log Entry**: `DATA_COVERAGE [PASS/WARNING] Missing data: {percentage}%`

#### Statistical Outlier Detection
- **Method**: Interquartile range (IQR) based outlier detection
- **Threshold**: Values beyond Q3 + 3×IQR or Q1 - 3×IQR
- **Action**: Flag outliers but retain in analysis with documentation
- **Log Entry**: `OUTLIERS [PASS/WARNING] {count} outliers detected`

### 3. Classification Validation

#### Urban Station Counts
- **Expected Urban Core**: 26 stations
- **Expected Urban Fringe**: 120 stations
- **Expected Total Urban**: 146 stations
- **Test**: Verify classification counts match expectations
- **Action if Failed**: Analysis termination with classification diagnostics
- **Log Entry**: `CLASSIFICATION [PASS/ERROR] urban_core: {count} stations`

#### Rural Station Counts
- **Expected Rural**: 667 stations
- **Test**: Verify rural classification count
- **Action if Failed**: Analysis termination with classification diagnostics
- **Log Entry**: `CLASSIFICATION [PASS/ERROR] rural: {count} stations`

#### Classification Completeness
- **Requirement**: All stations assigned to exactly one category
- **Test**: Sum of all categories equals total stations
- **Action if Failed**: Analysis termination with unclassified station report
- **Log Entry**: `CLASSIFICATION [PASS/ERROR] All stations classified`

### 4. Analysis Subset Validation

#### Urban Analysis Set
- **Definition**: Urban Core + Urban Fringe stations
- **Expected Count**: 146 stations (26 + 120)
- **Test**: Verify analysis subset composition
- **Action if Failed**: Analysis termination with subset diagnostics
- **Log Entry**: `ANALYSIS_SUBSET [PASS/ERROR] Urban analysis set: {count} stations`

#### Rural Analysis Set  
- **Definition**: Rural classified stations only
- **Expected Count**: 667 stations
- **Test**: Verify rural analysis subset
- **Action if Failed**: Analysis termination with subset diagnostics
- **Log Entry**: `ANALYSIS_SUBSET [PASS/ERROR] Rural analysis set: {count} stations`

### 5. Temporal Coverage Validation

#### Annual Data Availability
- **Requirement**: Adequate station coverage for each analysis year
- **Minimum Threshold**: 50% of stations with data for year inclusion
- **Test**: Count stations with data per year
- **Action if Failed**: Warning logged, affected years documented
- **Log Entry**: `ANNUAL_COVERAGE [PASS/WARNING] Year {year}: {count} stations`

#### Time Series Continuity
- **Requirement**: Reasonable temporal continuity (no large gaps)
- **Test**: Identify years with <10% normal station coverage
- **Action if Failed**: Warning logged, gaps documented
- **Log Entry**: `TEMPORAL_GAPS [PASS/WARNING] Gap detected: {year_range}`

### 6. UHII Magnitude Validation

#### Expected Range Checking
- **Maximum Temperature UHII**: -1.0°C to +3.0°C
- **Minimum Temperature UHII**: 0.0°C to +5.0°C
- **Average Temperature UHII**: -0.5°C to +4.0°C
- **Test**: Verify calculated UHII within expected literature ranges
- **Action if Failed**: Warning logged, magnitude investigated
- **Log Entry**: `UHII_MAGNITUDE [PASS/WARNING] {metric} UHII: {value}°C`

#### Trend Consistency
- **Requirement**: UHII trends consistent with urbanization patterns
- **Test**: Check for physically unrealistic UHII variations
- **Action if Failed**: Warning logged, trend analysis documented
- **Log Entry**: `UHII_TREND [PASS/WARNING] Trend validation complete`

### 7. Output Validation

#### File Generation
- **Requirement**: All expected output files created successfully
- **Test**: Verify existence and readability of output files
- **Action if Failed**: Analysis failure, file system diagnostics
- **Log Entry**: `OUTPUT [PASS/ERROR] File created: {filename}`

#### Plot Quality Checking
- **Requirement**: Generated plots contain expected data ranges
- **Test**: Verify plot axis ranges and data presence
- **Action if Failed**: Warning logged, plot regeneration attempted
- **Log Entry**: `PLOTTING [PASS/WARNING] Plot validation complete`

## Quality Control Implementation

### Validation Logger Class
```python
class ValidationLogger:
    """Comprehensive QC logging and error tracking"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.checks_passed = 0
        self.warnings_issued = 0  
        self.errors_encountered = 0
    
    def log(self, check_type: str, status: str, details: str):
        """Log validation result with timestamp"""
        # Implementation details...
```

### Error Handling Strategy
1. **Critical Errors**: Terminate analysis with full diagnostic output
2. **Warnings**: Continue analysis but flag issues for review
3. **Pass Conditions**: Silent operation with summary logging

### Validation Summary Report
Each analysis generates a final validation summary:
```
Validation Summary:
- Checks Passed: {count}
- Warnings Issued: {count}
- Errors Encountered: {count}
- Analysis Status: [COMPLETED/FAILED]
- Completion Time: {timestamp}
```

## Quality Standards

### Minimum Acceptance Criteria
- **Zero Critical Errors**: Analysis must pass all critical validation checks
- **Data Coverage**: >95% of expected stations and years available
- **UHII Magnitude**: Results within expected physical ranges
- **Classification Accuracy**: 100% station classification completeness

### Warning Thresholds
- **Missing Data**: >5% missing values triggers warning
- **Outliers**: >1% statistical outliers triggers investigation
- **UHII Range**: Values outside literature expectations flagged

### Documentation Requirements
- **Complete Logging**: All validation steps timestamped and recorded
- **Error Diagnostics**: Detailed failure analysis for any errors
- **Reproducibility**: Full parameter documentation for replication
- **Quality Metrics**: Summary statistics for all validation categories

This quality control framework ensures the highest standards of analytical rigor while maintaining transparency and reproducibility for scientific review.