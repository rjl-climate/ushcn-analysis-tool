# 1. Project Overview

This project, "US Long-Term Temperature Change Analyzer," aims to develop a flexible Python application to analyze and visualize long-term temperature changes across the United States.

A key feature of this project is its **dual-track analysis**. The primary track uses the **adjusted USHCN dataset** to calculate standard temperature anomalies. A secondary, **skeptical verification track** will run a parallel analysis using the **raw USHCN data**. This will allow us to **quantify the impact of the official data adjustments** and investigate whether they systematically alter the Urban Heat Island (UHI) signal, which is a core part of our investigation.

The application will be modular, allowing us to easily implement and compare different algorithms for calculating temperature anomalies and their adjustments. The final outputs will be spatial visualizations plotting these findings, with markers for major urban centers to provide context.

# 2. Core Objectives

1.  **Framework Setup:**
    - Create the project file structure, including a dedicated `src/anomaly_algorithms/` directory.
    - Develop modular scripts for data loading (`src/data_loader.py`), which will handle both raw and adjusted datasets, and visualization (`src/plotting.py`).
2.  **Define the Algorithm Interface:**
    - Establish a standard "contract" (function signature and return value) that all analysis algorithms must follow, as detailed in Section 6.
3.  **Implement Core Anomaly Algorithms:**
    - **Algorithm 1 (`simple_anomaly.py`):** A straightforward anomaly calculation using only the adjusted dataset.
    - **Algorithm 2 (`min_obs_anomaly.py`):** A more stringent, configurable anomaly calculation using the adjusted dataset.
4.  **Implement the Skeptical Verification Algorithm:**
    - **Algorithm 3 (`adjustment_impact.py`):** Create a new algorithm that requires _both_ raw and adjusted data. This algorithm will calculate the anomaly using both datasets and then compute the difference, isolating the precise impact of the adjustment on the final anomaly figure for each station.
5.  **Develop the Main Orchestrator (`main.py`):**
    - Write the main script using `Typer` to allow user selection of an analysis algorithm.
    - The script will load the necessary data (raw, adjusted, or both) and execute the chosen algorithm.
    - It will then pass the results to the plotting module to generate and save the appropriate visualization(s).
6.  **Comprehensive Visualization:**
    - Enhance the `plotting.py` module to support creating side-by-side comparison maps (e.g., "Anomaly with Raw Data" vs. "Anomaly with Adjusted Data") and a direct plot of the "Adjustment Impact."

# 3. Technology Stack

- **Data Manipulation:** `pandas`, `geopandas`
- **File I/O:** `pyarrow`
- **Visualization:** `matplotlib`, `contextily`
- **Geospatial Operations:** `shapely` (via GeoPandas)
- **Command-Line Interface:** `Typer`
- **Type Safety:** `pydantic`

# 4. Project File Structure

```
/
├── CLAUDE.md
├── data/
│   ├── ushcn_adjusted.parquet      # Adjusted USHCN temperature data
│   ├── ushcn_raw.parquet           # Raw USHCN temperature data
│   └── us_cities.csv             # Urban center locations
├── output/
│   └── (will be populated with plots)
├── src/
│   ├── main.py                     # Main orchestrator script
│   ├── data_loader.py              # Module for loading raw and adjusted data
│   ├── plotting.py                 # Module for all visualizations
│   └── anomaly_algorithms/         # --- Directory for all algorithms ---
│       ├── __init__.py             # Makes algorithms a package & registers them
│       ├── simple_anomaly.py       # Algorithm #1
│       ├── min_obs_anomaly.py      # Algorithm #2
│       └── adjustment_impact.py      # Algorithm #3 (Skeptical Verification)
└── requirements.txt
```

# 5. Assumed Data Schema

Both `ushcn_adjusted.parquet` and `ushcn_raw.parquet` are expected to share this schema:

- `station_id`: Unique string identifier for the station.
- `timestamp`: Pandas-readable datetime object for the measurement.
- `temperature_celsius`: Float for the monthly temperature value (either raw or adjusted).
- `geometry`: GeoPandas-readable point geometry.

# 6. Pluggable Algorithm Design

All analysis algorithms must adhere to a standard contract to ensure they are swappable.

- **Location:** Each algorithm must be in its own file inside `src/anomaly_algorithms/`.
- **Core Function:** Each file must contain a primary function named `calculate()`.
- **Function Signature:** The function signature will be flexible to accept either one or both datasets.

  ```python
  from typing import Dict, Any, Optional
  import geopandas as gpd

  def calculate(
      gdf_adjusted: gpd.GeoDataFrame,
      baseline_period: tuple[int, int],
      current_period: tuple[int, int],
      gdf_raw: Optional[gpd.GeoDataFrame] = None,
      config: Optional[Dict[str, Any]] = None
  ) -> gpd.GeoDataFrame:
      # ... implementation ...
      pass
  ```

- **Return Value:** The function must return a GeoDataFrame containing the results of its specific analysis. The columns will vary by algorithm but will always include `geometry` and `station_id`.
- **Registration:** Each algorithm must be registered in `src/anomaly_algorithms/__init__.py`.

# 7. Guiding Principles & Interaction Style

- **Explain First, Code Second:** Briefly explain the logic before providing code.
- **Modularity and Single Responsibility:** Each function and module does one thing well.
- **PEP 8 and Type Hinting:** Write clean, readable, and type-hinted Python code.
- **Step-by-Step Workflow:** We will build the application piece by piece according to the Core Objectives.
- **Robustness:** Write code that gracefully handles potential errors like missing files or data.

# 8. Skeptical Verification Track

To ensure the integrity of our findings, we will implement a track to scrutinize the official USHCN data adjustments.

**A. Methodology:**

1.  **Comparative Analysis:** We will run our primary anomaly algorithms using both raw and adjusted data to produce comparable maps.
2.  **Direct Impact Calculation:** We will implement a dedicated algorithm, `adjustment_impact.calculate`, that directly computes the effect of the NOAA adjustments on the long-term temperature anomaly.

**B. Key Algorithm: `adjustment_impact`**

This algorithm is central to the verification track.

- **Purpose:** To isolate and quantify the `adjustment_impact` on the final anomaly value for each station.
- **Calculation:** For each station meeting the data criteria, it will compute:
  1.  `anomaly_adjusted = current_avg_adj - baseline_avg_adj`
  2.  `anomaly_raw = current_avg_raw - baseline_avg_raw`
  3.  `adjustment_impact = anomaly_adjusted - anomaly_raw`
- **Output:** The returned GeoDataFrame will contain columns: `['geometry', 'station_id', 'anomaly_raw', 'anomaly_adjusted', 'adjustment_impact']`.

**C. Visualization and Interpretation:**

The `adjustment_impact.py` algorithm will produce a set of three maps for direct comparison:

1.  **Raw Anomaly Map:** The temperature trend based purely on raw thermometer readings.
2.  **Adjusted Anomaly Map:** The temperature trend based on the official, corrected data.
3.  **Adjustment Impact Map:** This critical map visualizes the `adjustment_impact` value. A negative value on this map indicates that the official adjustment process resulted in a _cooler_ calculated warming trend for that station compared to the raw data. Our skeptical hypothesis would be supported if we observe a pattern of negative impacts concentrated over urban centers.
