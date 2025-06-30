# USHCN Temperature Data Analysis Tool

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://rjl-climate.github.io/ushcn-heatisland/)

A Python library for analyzing temperature data from the United States Historical Climatology Network (USHCN).

**Full documentation**: https://rjl-climate.github.io/ushcn-analysis-tool/

## Description

This tool provides a comprehensive framework for loading, processing, and analyzing USHCN temperature datasets. It supports multiple data formats (raw, TOBs-adjusted, and fully adjusted), various analysis algorithms, and publication-quality visualizations.

## Installation

```bash
# Clone the repository
git clone https://github.com/rjl-climate/ushcn-heatisland.git
cd ushcn-heatisland

# Install the package
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Data Requirements

The tool requires USHCN data files in Parquet format. Use our [Rust utility](https://crates.io/crates/ushcn) to download them:

```bash
cargo install ushcn
ushcn download
mv ushcn-*.parquet data/
```

## Usage

```bash
# List available analysis algorithms
ushcn-heatisland list-algos

# Run a basic temperature anomaly analysis
ushcn-heatisland analyze simple --temp-metric min

# See all options
ushcn-heatisland --help
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Quick environment check
pytest tests/test_environment.py -v

# Verify data loading
pytest tests/test_data_loading.py -v
```

## Studies Using This Tool

1. **[Urban Heat Island Contamination in USHCN Temperature Records (2025)](https://rjl-climate.github.io/ushcn-analysis-tool/studies/uhi-contamination/)**
   _Finding: NOAA adjustments enhance urban heat island signals by 9.4%_

## Citation

```bibtex
@software{lyon2025ushcn,
  author = {Lyon, Richard},
  title = {USHCN Temperature Data Analysis Tool},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/rjl-climate/ushcn-heatisland},
  version = {1.0.0}
}
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest tests/`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **Documentation**: https://rjl-climate.github.io/ushcn-analysis-tool/
- **Issues**: https://github.com/rjl-climate/ushcn-analysis-tool/issues
