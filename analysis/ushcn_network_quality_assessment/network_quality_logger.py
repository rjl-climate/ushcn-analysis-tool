#!/usr/bin/env python3
"""
Network Quality Assessment Logger for USHCN Coverage Analysis

This module provides comprehensive logging and validation utilities for assessing
USHCN network coverage quality and its impact on temperature trend reliability.

Author: Richard Lyon (richlyon@fastmail.com)
Date: 2025-06-29
Version: 1.0
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import json
import numpy as np
import pandas as pd


class NetworkQualityLogger:
    """
    Comprehensive validation logging for USHCN network quality assessment.
    
    Provides structured logging of network coverage metrics, trend validation,
    and geographic bias assessment with categorized status tracking.
    """
    
    def __init__(self, log_file: Path, analysis_type: str = "USHCN_Network_Quality"):
        """
        Initialize network quality logger.
        
        Args:
            log_file: Path to validation log file
            analysis_type: Type of network analysis being performed
        """
        self.log_file = log_file
        self.analysis_type = analysis_type
        self.checks_passed = 0
        self.warnings_issued = 0
        self.errors_encountered = 0
        self.start_time = datetime.now()
        
        # Network quality thresholds
        self.coverage_thresholds = {
            'continental_minimum': 500,  # Minimum stations for US-wide analysis
            'regional_minimum': 50,     # Minimum stations per major region
            'density_threshold': 0.1,   # Stations per 1000 km²
            'data_completeness': 0.8    # Minimum data availability
        }
        
        # Initialize log file
        self._initialize_log()
    
    def _initialize_log(self):
        """Initialize log file with header information."""
        with open(self.log_file, 'w') as f:
            f.write(f"{self.analysis_type} Validation Log\n")
            f.write(f"Start Time: {self.start_time.isoformat()}\n")
            f.write("Network Quality Assessment Framework\n")
            f.write("=" * 60 + "\n\n")
    
    def log(self, check_type: str, status: str, details: str):
        """
        Log a validation check result.
        
        Args:
            check_type: Category of validation check
            status: Result status (PASS, WARNING, ERROR, INFO)
            details: Detailed description of check result
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] [{check_type}] [{status}] {details}\n"
        
        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(message)
        
        # Console output with appropriate formatting
        if status == "PASS":
            print(f"✓ {check_type}: {details}")
            self.checks_passed += 1
        elif status == "WARNING":
            print(f"⚠ {check_type}: {details}")
            self.warnings_issued += 1
        elif status == "ERROR":
            print(f"✗ {check_type}: {details}")
            self.errors_encountered += 1
        elif status == "INFO":
            print(f"ℹ {check_type}: {details}")
    
    def validate_station_coverage_evolution(self, coverage_data: pd.DataFrame) -> bool:
        """
        Validate station coverage evolution patterns.
        
        Args:
            coverage_data: DataFrame with columns ['year', 'station_count']
            
        Returns:
            True if coverage patterns are valid, False otherwise
        """
        if 'year' not in coverage_data.columns or 'station_count' not in coverage_data.columns:
            self.log("COVERAGE_DATA", "ERROR", "Missing required columns in coverage data")
            return False
        
        # Check temporal range
        year_range = coverage_data['year'].max() - coverage_data['year'].min()
        if year_range < 100:
            self.log("COVERAGE_TEMPORAL", "WARNING", 
                    f"Coverage data spans only {year_range} years")
        else:
            self.log("COVERAGE_TEMPORAL", "PASS", 
                    f"Coverage data spans {year_range} years")
        
        # Check for dramatic expansion around 1890-1910
        pre_1890 = coverage_data[coverage_data['year'] < 1890]['station_count'].mean()
        post_1910 = coverage_data[coverage_data['year'] > 1910]['station_count'].mean()
        
        if post_1910 / pre_1890 > 3:
            self.log("NETWORK_EXPANSION", "WARNING", 
                    f"Dramatic network expansion detected: {pre_1890:.0f} → {post_1910:.0f} stations")
        else:
            self.log("NETWORK_EXPANSION", "PASS", 
                    f"Gradual network evolution: {pre_1890:.0f} → {post_1910:.0f} stations")
        
        return True
    
    def validate_coverage_adequacy(self, year: int, station_count: int, 
                                 analysis_scope: str = 'continental') -> bool:
        """
        Validate whether station coverage is adequate for reliable analysis.
        
        Args:
            year: Year being assessed
            station_count: Number of active stations
            analysis_scope: Scope of analysis ('continental', 'regional', 'local')
            
        Returns:
            True if coverage is adequate, False otherwise
        """
        thresholds = {
            'continental': self.coverage_thresholds['continental_minimum'],
            'regional': self.coverage_thresholds['regional_minimum'],
            'local': 10
        }
        
        threshold = thresholds.get(analysis_scope, 500)
        
        if station_count >= threshold:
            self.log("COVERAGE_ADEQUACY", "PASS", 
                    f"Year {year}: {station_count} stations ≥ {threshold} ({analysis_scope} threshold)")
            return True
        else:
            self.log("COVERAGE_ADEQUACY", "WARNING", 
                    f"Year {year}: {station_count} stations < {threshold} ({analysis_scope} threshold)")
            return False
    
    def validate_geographic_bias(self, regional_counts: Dict[str, int], 
                               total_stations: int) -> bool:
        """
        Validate geographic distribution for bias assessment.
        
        Args:
            regional_counts: Dictionary of region -> station count
            total_stations: Total number of stations
            
        Returns:
            True if geographic distribution is acceptable, False otherwise
        """
        if not regional_counts or total_stations == 0:
            self.log("GEOGRAPHIC_BIAS", "ERROR", "Invalid regional count data")
            return False
        
        # Calculate regional proportions
        proportions = {region: count/total_stations for region, count in regional_counts.items()}
        
        # Check for extreme bias (any region >50% or <5%)
        bias_detected = False
        for region, proportion in proportions.items():
            if proportion > 0.5:
                self.log("GEOGRAPHIC_BIAS", "WARNING", 
                        f"Region {region} over-represented: {proportion:.1%}")
                bias_detected = True
            elif proportion < 0.05 and total_stations > 100:
                self.log("GEOGRAPHIC_BIAS", "WARNING", 
                        f"Region {region} under-represented: {proportion:.1%}")
                bias_detected = True
        
        if not bias_detected:
            self.log("GEOGRAPHIC_BIAS", "PASS", "Regional distribution within acceptable bounds")
        
        return not bias_detected
    
    def validate_data_completeness(self, data_frame: pd.DataFrame, 
                                 temp_columns: List[str]) -> bool:
        """
        Validate data completeness for temperature metrics.
        
        Args:
            data_frame: DataFrame with temperature data
            temp_columns: List of temperature column names
            
        Returns:
            True if data completeness is adequate, False otherwise
        """
        all_adequate = True
        
        for col in temp_columns:
            if col not in data_frame.columns:
                self.log("DATA_COMPLETENESS", "ERROR", f"Column {col} not found")
                all_adequate = False
                continue
            
            total_records = len(data_frame)
            available_records = data_frame[col].notna().sum()
            completeness = available_records / total_records if total_records > 0 else 0
            
            if completeness >= self.coverage_thresholds['data_completeness']:
                self.log("DATA_COMPLETENESS", "PASS", 
                        f"{col}: {completeness:.1%} completeness")
            else:
                self.log("DATA_COMPLETENESS", "WARNING", 
                        f"{col}: {completeness:.1%} completeness < {self.coverage_thresholds['data_completeness']:.1%}")
                all_adequate = False
        
        return all_adequate
    
    def validate_trend_reliability(self, trend_value: float, p_value: float,
                                 station_count: int, time_span: int) -> bool:
        """
        Validate reliability of calculated temperature trends.
        
        Args:
            trend_value: Calculated trend in °C/decade
            p_value: Statistical significance of trend
            station_count: Number of stations used in calculation
            time_span: Number of years in trend calculation
            
        Returns:
            True if trend is reliable, False otherwise
        """
        reliable = True
        
        # Check statistical significance
        if p_value <= 0.05:
            self.log("TREND_SIGNIFICANCE", "PASS", 
                    f"Trend significant: p = {p_value:.3f}")
        else:
            self.log("TREND_SIGNIFICANCE", "WARNING", 
                    f"Trend not significant: p = {p_value:.3f}")
            reliable = False
        
        # Check sample size adequacy
        if station_count >= self.coverage_thresholds['continental_minimum']:
            self.log("TREND_SAMPLE_SIZE", "PASS", 
                    f"Adequate station count: {station_count}")
        else:
            self.log("TREND_SAMPLE_SIZE", "WARNING", 
                    f"Insufficient stations: {station_count} < {self.coverage_thresholds['continental_minimum']}")
            reliable = False
        
        # Check temporal span
        if time_span >= 30:
            self.log("TREND_TEMPORAL_SPAN", "PASS", 
                    f"Adequate time span: {time_span} years")
        else:
            self.log("TREND_TEMPORAL_SPAN", "WARNING", 
                    f"Short time span: {time_span} years < 30")
            reliable = False
        
        # Check for physically reasonable trend magnitude
        if abs(trend_value) <= 1.0:  # ±1°C/decade seems reasonable for most contexts
            self.log("TREND_MAGNITUDE", "PASS", 
                    f"Reasonable trend magnitude: {trend_value:.3f}°C/decade")
        else:
            self.log("TREND_MAGNITUDE", "WARNING", 
                    f"Large trend magnitude: {trend_value:.3f}°C/decade")
        
        return reliable
    
    def log_network_transition(self, year: int, station_count: int, 
                             previous_count: int):
        """
        Log significant network transitions for change point analysis.
        
        Args:
            year: Year of transition
            station_count: Current station count
            previous_count: Previous year station count
        """
        if previous_count > 0:
            change_rate = (station_count - previous_count) / previous_count
            
            if abs(change_rate) > 0.1:  # >10% change
                self.log("NETWORK_TRANSITION", "WARNING", 
                        f"Year {year}: {change_rate:.1%} change ({previous_count} → {station_count})")
            else:
                self.log("NETWORK_TRANSITION", "INFO", 
                        f"Year {year}: {change_rate:.1%} change ({previous_count} → {station_count})")
    
    def assess_early_period_validity(self, early_year_threshold: int = 1900) -> Dict:
        """
        Assess validity of early period climate analysis.
        
        Args:
            early_year_threshold: Year before which data is considered "early"
            
        Returns:
            Dictionary with validity assessment results
        """
        assessment = {
            'early_period_threshold': early_year_threshold,
            'validity_issues': [],
            'recommendations': []
        }
        
        # This would be called with actual coverage data in implementation
        self.log("EARLY_PERIOD", "INFO", 
                f"Assessing pre-{early_year_threshold} data validity")
        
        return assessment
    
    def export_network_quality_metrics(self, output_file: Path, 
                                     coverage_stats: Dict):
        """
        Export comprehensive network quality metrics.
        
        Args:
            output_file: Path to JSON output file
            coverage_stats: Network coverage statistics
        """
        metrics = {
            'analysis_metadata': {
                'analysis_type': self.analysis_type,
                'timestamp': datetime.now().isoformat(),
                'coverage_thresholds': self.coverage_thresholds
            },
            'coverage_statistics': coverage_stats,
            'validation_summary': {
                'checks_passed': self.checks_passed,
                'warnings_issued': self.warnings_issued,
                'errors_encountered': self.errors_encountered
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        self.log("EXPORT", "PASS", f"Network quality metrics exported to {output_file}")
    
    def finalize(self) -> Dict:
        """
        Write final validation summary and return statistics.
        
        Returns:
            Dictionary with validation statistics
        """
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Determine overall status
        if self.errors_encountered > 0:
            status = "FAILED"
        elif self.warnings_issued > 0:
            status = "COMPLETED_WITH_WARNINGS"
        else:
            status = "COMPLETED_SUCCESSFULLY"
        
        summary = f"""
Network Quality Assessment Summary:
- Checks Passed: {self.checks_passed}
- Warnings Issued: {self.warnings_issued}
- Errors Encountered: {self.errors_encountered}
- Analysis Status: {status}
- Duration: {duration.total_seconds():.1f} seconds
- End Time: {end_time.isoformat()}

Network Coverage Thresholds Used:
- Continental Analysis: ≥{self.coverage_thresholds['continental_minimum']} stations
- Regional Analysis: ≥{self.coverage_thresholds['regional_minimum']} stations
- Data Completeness: ≥{self.coverage_thresholds['data_completeness']:.0%}
- Density Threshold: ≥{self.coverage_thresholds['density_threshold']} stations/1000km²
"""
        
        with open(self.log_file, 'a') as f:
            f.write(summary)
        
        # Console summary
        if status == "COMPLETED_SUCCESSFULLY":
            print(f"\n✅ {self.analysis_type}: {status}")
        elif status == "COMPLETED_WITH_WARNINGS":
            print(f"\n⚠️ {self.analysis_type}: {status}")
        else:
            print(f"\n❌ {self.analysis_type}: {status}")
        
        return {
            'checks_passed': self.checks_passed,
            'warnings_issued': self.warnings_issued,
            'errors_encountered': self.errors_encountered,
            'status': status,
            'duration_seconds': duration.total_seconds(),
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'coverage_thresholds': self.coverage_thresholds
        }