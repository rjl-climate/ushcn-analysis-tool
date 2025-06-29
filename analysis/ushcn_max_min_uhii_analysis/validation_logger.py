#!/usr/bin/env python3
"""
Validation Logger for USHCN UHII Analysis Quality Control

This module provides comprehensive logging and validation utilities for the
USHCN Urban Heat Island analysis, ensuring analytical rigor and reproducibility.

Author: Richard Lyon (richlyon@fastmail.com)
Date: 2025-06-29
Version: 1.0
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
import json


class ValidationLogger:
    """
    Comprehensive validation logging and error tracking for USHCN analysis.

    Provides structured logging of quality control checks with categorized
    status tracking and summary reporting capabilities.
    """

    def __init__(self, log_file: Path, analysis_type: str = "USHCN_UHII"):
        """
        Initialize validation logger.

        Args:
            log_file: Path to validation log file
            analysis_type: Type of analysis being performed
        """
        self.log_file = log_file
        self.analysis_type = analysis_type
        self.checks_passed = 0
        self.warnings_issued = 0
        self.errors_encountered = 0
        self.start_time = datetime.now()

        # Initialize log file with header
        self._initialize_log()

    def _initialize_log(self):
        """Initialize log file with header information."""
        with open(self.log_file, "w") as f:
            f.write(f"{self.analysis_type} Validation Log\n")
            f.write(f"Start Time: {self.start_time.isoformat()}\n")
            f.write("=" * 60 + "\n\n")

    def log(self, check_type: str, status: str, details: str):
        """
        Log a validation check result.

        Args:
            check_type: Category of validation check
            status: Result status (PASS, WARNING, ERROR, START)
            details: Detailed description of check result
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] [{check_type}] [{status}] {details}\n"

        # Write to log file
        with open(self.log_file, "a") as f:
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
        elif status == "START":
            print(f"→ {check_type}: {details}")

    def log_critical_error(
        self, check_type: str, details: str, exception: Optional[Exception] = None
    ):
        """
        Log critical error that should terminate analysis.

        Args:
            check_type: Category of validation check
            details: Error description
            exception: Optional exception object for additional details
        """
        error_msg = details
        if exception:
            error_msg += f" | Exception: {str(exception)}"

        self.log(check_type, "ERROR", error_msg)

        # Log additional exception details if available
        if exception:
            self.log(check_type, "ERROR", f"Exception type: {type(exception).__name__}")

    def validate_station_count(
        self, actual_count: int, expected_count: int = 1218
    ) -> bool:
        """
        Validate total station count.

        Args:
            actual_count: Number of stations loaded
            expected_count: Expected number of stations

        Returns:
            True if validation passes, False otherwise
        """
        if actual_count == expected_count:
            self.log("STATION_COUNT", "PASS", f"Total stations: {actual_count}")
            return True
        else:
            self.log(
                "STATION_COUNT",
                "ERROR",
                f"Expected {expected_count}, got {actual_count}",
            )
            return False

    def validate_classification_counts(
        self, classification_counts: Dict[str, int]
    ) -> bool:
        """
        Validate urban/rural classification counts.

        Args:
            classification_counts: Dictionary of classification -> count

        Returns:
            True if all validations pass, False otherwise
        """
        expected_counts = {
            "urban_core": 26,
            "urban_fringe": 120,
            "suburban": 405,
            "rural": 667,
        }

        all_valid = True
        for category, expected in expected_counts.items():
            actual = classification_counts.get(category, 0)
            if actual == expected:
                self.log("CLASSIFICATION", "PASS", f"{category}: {actual} stations")
            else:
                self.log(
                    "CLASSIFICATION",
                    "ERROR",
                    f"{category}: expected {expected}, got {actual}",
                )
                all_valid = False

        return all_valid

    def validate_geographic_bounds(
        self, stations_data, lat_col: str = "lat", lon_col: str = "lon"
    ) -> bool:
        """
        Validate station coordinates within continental US bounds.

        Args:
            stations_data: DataFrame or GeoDataFrame with station locations
            lat_col: Name of latitude column
            lon_col: Name of longitude column

        Returns:
            True if validation passes, False otherwise
        """
        lat_bounds = (24.0, 50.0)
        lon_bounds = (-125.0, -66.0)

        lat_valid = stations_data[lat_col].between(*lat_bounds).all()
        lon_valid = stations_data[lon_col].between(*lon_bounds).all()
        coord_complete = stations_data[[lat_col, lon_col]].notna().all().all()

        if lat_valid and lon_valid and coord_complete:
            self.log(
                "GEOGRAPHIC",
                "PASS",
                "All stations within CONUS bounds with valid coordinates",
            )
            return True
        else:
            if not lat_valid:
                self.log(
                    "GEOGRAPHIC", "ERROR", "Stations found outside latitude bounds"
                )
            if not lon_valid:
                self.log(
                    "GEOGRAPHIC", "ERROR", "Stations found outside longitude bounds"
                )
            if not coord_complete:
                self.log("GEOGRAPHIC", "ERROR", "Missing coordinate data found")
            return False

    def validate_temperature_bounds(
        self, temp_data, temp_col: str, bounds: Tuple[float, float] = (-50.0, 60.0)
    ) -> bool:
        """
        Validate temperature values within physically realistic range.

        Args:
            temp_data: DataFrame with temperature data
            temp_col: Name of temperature column
            bounds: (min_temp, max_temp) in Celsius

        Returns:
            True if validation passes, False otherwise
        """
        temp_min, temp_max = bounds
        temps = temp_data[temp_col].dropna()

        below_min = (temps < temp_min).sum()
        above_max = (temps > temp_max).sum()
        total_invalid = below_min + above_max

        if total_invalid == 0:
            self.log(
                "TEMPERATURE",
                "PASS",
                f"{temp_col}: all {len(temps)} values within bounds",
            )
            return True
        else:
            self.log(
                "TEMPERATURE",
                "WARNING",
                f"{temp_col}: {total_invalid} values outside bounds "
                f"({below_min} low, {above_max} high)",
            )
            return False

    def validate_uhii_magnitude(self, uhii_value: float, temp_metric: str) -> bool:
        """
        Validate UHII magnitude within expected ranges.

        Args:
            uhii_value: Calculated UHII value in Celsius
            temp_metric: Temperature metric ('max', 'min', 'avg')

        Returns:
            True if within expected range, False otherwise
        """
        expected_ranges = {"max": (-1.0, 3.0), "min": (0.0, 5.0), "avg": (-0.5, 4.0)}

        min_expected, max_expected = expected_ranges.get(temp_metric, (-5.0, 10.0))

        if min_expected <= uhii_value <= max_expected:
            self.log(
                "UHII_MAGNITUDE",
                "PASS",
                f"{temp_metric} UHII: {uhii_value:.3f}°C (within expected range)",
            )
            return True
        else:
            self.log(
                "UHII_MAGNITUDE",
                "WARNING",
                f"{temp_metric} UHII: {uhii_value:.3f}°C "
                f"(outside expected range {min_expected}-{max_expected}°C)",
            )
            return False

    def validate_analysis_subsets(self, urban_count: int, rural_count: int) -> bool:
        """
        Validate urban and rural analysis subset sizes.

        Args:
            urban_count: Number of urban stations in analysis
            rural_count: Number of rural stations in analysis

        Returns:
            True if validation passes, False otherwise
        """
        expected_urban = 146  # urban_core + urban_fringe
        expected_rural = 667

        urban_valid = urban_count == expected_urban
        rural_valid = rural_count == expected_rural

        if urban_valid:
            self.log(
                "ANALYSIS_SUBSET", "PASS", f"Urban analysis set: {urban_count} stations"
            )
        else:
            self.log(
                "ANALYSIS_SUBSET",
                "ERROR",
                f"Urban analysis set: expected {expected_urban}, got {urban_count}",
            )

        if rural_valid:
            self.log(
                "ANALYSIS_SUBSET", "PASS", f"Rural analysis set: {rural_count} stations"
            )
        else:
            self.log(
                "ANALYSIS_SUBSET",
                "ERROR",
                f"Rural analysis set: expected {expected_rural}, got {rural_count}",
            )

        return urban_valid and rural_valid

    def log_data_loading(self, data_type: str, record_count: int, station_count: int):
        """
        Log successful data loading operation.

        Args:
            data_type: Type of data loaded (e.g., 'max temperature')
            record_count: Number of records loaded
            station_count: Number of unique stations
        """
        self.log(
            "TEMP_DATA",
            "PASS",
            f"Loaded {record_count} {data_type} records from {station_count} stations",
        )

    def log_annual_coverage(self, temp_metric: str, urban_years: int, rural_years: int):
        """
        Log annual data coverage validation.

        Args:
            temp_metric: Temperature metric analyzed
            urban_years: Number of years with urban data
            rural_years: Number of years with rural data
        """
        self.log(
            "ANNUAL_MEANS",
            "PASS",
            f"{temp_metric}: {urban_years} urban years, {rural_years} rural years",
        )

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
Validation Summary:
- Checks Passed: {self.checks_passed}
- Warnings Issued: {self.warnings_issued}
- Errors Encountered: {self.errors_encountered}
- Analysis Status: {status}
- Duration: {duration.total_seconds():.1f} seconds
- End Time: {end_time.isoformat()}
"""

        with open(self.log_file, "a") as f:
            f.write(summary)

        # Console summary
        if status == "COMPLETED_SUCCESSFULLY":
            print(f"\n✅ {self.analysis_type} Analysis: {status}")
        elif status == "COMPLETED_WITH_WARNINGS":
            print(f"\n⚠️ {self.analysis_type} Analysis: {status}")
        else:
            print(f"\n❌ {self.analysis_type} Analysis: {status}")

        return {
            "checks_passed": self.checks_passed,
            "warnings_issued": self.warnings_issued,
            "errors_encountered": self.errors_encountered,
            "status": status,
            "duration_seconds": duration.total_seconds(),
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }


def export_validation_summary(logger_stats: Dict, output_file: Path):
    """
    Export validation summary to JSON file.

    Args:
        logger_stats: Statistics from ValidationLogger.finalize()
        output_file: Path to JSON output file
    """
    with open(output_file, "w") as f:
        json.dump(logger_stats, f, indent=2)
