# USHCN Heat Island Analysis - Integration Tests

## Overview

This test suite provides comprehensive integration testing for the USHCN Heat Island Analysis project. The tests verify end-to-end functionality including data loading, analysis algorithms, urban context classification, CLI interfaces, and output validation.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Pytest configuration and fixtures
├── test_environment.py        # Environment and dependency verification
├── test_data_loading.py       # Data loading functionality tests
├── test_analysis_workflow.py  # Core analysis algorithm tests
├── test_cli_integration.py    # Command-line interface tests
├── test_output_validation.py  # Output format and validation tests
└── README.md                  # This file
```

## Running Tests

### Quick Test Run

```bash
# Run core functionality tests
python -m pytest tests/test_environment.py tests/test_data_loading.py -v

# Run specific test categories
python -m pytest tests/test_analysis_workflow.py -v
python -m pytest tests/test_cli_integration.py -v
```

### Full Test Suite

```bash
# Run all tests with summary



# Run all tests with detailed output
python -m pytest tests/ -v
```

### Individual Test Examples

```bash
# Test data loading
python -m pytest tests/test_data_loading.py::TestDataLoading::test_load_ushcn_data_fls52 -v

# Test CLI commands
python -m pytest tests/test_cli_integration.py::TestCLIBasics::test_list_algorithms_command -v

# Test analysis algorithms
python -m pytest tests/test_analysis_workflow.py::TestAnalysisAlgorithms::test_algorithm_execution -v
```

## Test Coverage

### Environment Tests ✅ (4/4 passing)

- Python version compatibility
- Project structure verification
- Data file existence checks
- Dependency import validation

### Data Loading Tests ✅ (8/8 passing)

- USHCN data loading (all data types: raw, tob, fls52)
- Temperature metric loading (min, max, avg)
- Urban context data loading (cities, urban areas)
- Station classification integration

### Analysis Workflow Tests ✅ (6/9 passing)

- Algorithm listing and retrieval
- Simple and min_obs algorithm execution
- Adjustment impact analysis
- Urban heat island classification workflow
- Temperature data integrity checks

### CLI Integration Tests ✅ (8/8 passing)

- Help and list commands
- Basic analysis workflow
- Urban heat island analysis
- Adjustment impact analysis
- Parameter validation
- Error handling

### Output Validation Tests ⚠️ (4/7 passing)

- Statistics file generation and structure
- Plot file creation and formats
- JSON serialization/deserialization
- Data consistency checks

## Known Issues

### Current Test Failures (6/38)

1. **Heat Island Reports**: Some edge cases in report generation with small data samples
2. **Coordinate Consistency**: Minor precision differences across data types  
3. **Empty Plot Handling**: Some tests generate empty plots causing warnings

### Fixed Issues

- ✅ **CLI Plot Generation**: Fixed CLI logic bug where "points" visualization didn't create plot files

## Test Data Requirements

The tests require the following data files to be present:

- `data/ushcn-monthly-fls52-2025-06-27.parquet` - Fully adjusted temperature data
- `data/ushcn-monthly-raw-2025-06-27.parquet` - Raw temperature data
- `data/ushcn-monthly-tob-2025-06-27.parquet` - Time-of-observation adjusted data
- `data/cities/us_cities_static.csv` - US cities database

## Performance Notes

- Full test suite takes ~2-3 minutes to run
- Individual algorithm tests take 5-10 seconds each
- CLI tests can take 30-60 seconds due to full data processing
- Output validation tests are generally fast (<5 seconds)

## Test Philosophy

These are integration tests focused on:

1. **End-to-end workflows** - Complete data processing pipelines
2. **Interface contracts** - Verifying expected inputs/outputs
3. **Data integrity** - Ensuring data consistency through processing
4. **Real-world usage** - Testing actual CLI commands and workflows

The tests use real data (with small samples for speed) rather than mocked data to catch integration issues that unit tests might miss.
