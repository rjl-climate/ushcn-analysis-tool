# USHCN Temperature Data Analysis Tool

A Python library for comprehensive analysis of temperature data from the United States Historical Climatology Network (USHCN).

## Overview

This tool provides a flexible framework for loading, processing, and analyzing USHCN temperature datasets. Whether you're investigating climate trends, urban heat island effects, or data quality issues, this library offers the algorithms and visualizations you need. TEST

## Key Features

**📊 Data Management**

- Load raw, TOBs-adjusted, and fully adjusted USHCN datasets
- Efficient Parquet format for fast data access
- Built-in data validation and quality checks

**🔬 Analysis Algorithms**

- Temperature anomaly calculations
- Urban heat island intensity quantification
- Adjustment impact assessment
- Trend analysis across multiple time scales

**🗺️ Visualizations**

- Spatial temperature maps with confidence intervals
- Station classification visualizations
- Time series comparisons
- Publication-quality figures

**🏗️ Extensible Architecture**

- Plugin system for custom algorithms
- Configurable analysis pipelines
- Multiple output formats (JSON, CSV, PNG)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/rjl-climate/ushcn-heatisland.git
cd ushcn-heatisland

# Install the package
pip install -e .
```

### Basic Usage

```bash
# List available algorithms
ushcn-heatisland list-algos

# Run a temperature anomaly analysis
ushcn-heatisland analyze simple --temp-metric min

# Generate urban heat island analysis
ushcn-heatisland analyze simple --urban-analysis --heat-island-report
```

## Citation

If you use this tool in your research, please cite:

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

## Support

- **Issues**: [GitHub Issues](https://github.com/rjl-climate/ushcn-heatisland/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rjl-climate/ushcn-heatisland/discussions)
- **Email**: richlyon@fastmail.com

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/rjl-climate/ushcn-heatisland/blob/main/LICENSE) file for details.
