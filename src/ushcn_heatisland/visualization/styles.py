"""Plot styling and color schemes for USHCN visualizations."""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np


def get_temperature_colormap(temp_metric: str = "anomaly") -> str:
    """
    Get appropriate colormap for temperature data visualization.

    Args:
        temp_metric: Type of temperature metric ('anomaly', 'absolute', 'uhii')

    Returns:
        Matplotlib colormap name
    """
    colormap_config = {
        "anomaly": "RdBu_r",  # Red-blue diverging for anomalies
        "absolute": "viridis",  # Sequential for absolute temperatures
        "uhii": "OrRd",  # Orange-red for heat island intensity
        "adjustment": "RdYlBu_r",  # Red-yellow-blue for adjustments
    }

    return colormap_config.get(temp_metric.lower(), "viridis")


def get_station_style_config() -> dict[str, dict[str, Any]]:
    """
    Get station marker styling configuration for urban/rural classification.

    Returns:
        Dictionary mapping classification to style parameters
    """
    return {
        "urban_core": {
            "color": "red",
            "size": 25,
            "marker": "o",
            "alpha": 0.8,
            "edgecolor": "darkred",
            "linewidth": 1,
            "label": "Urban Core",
        },
        "urban_fringe": {
            "color": "orange",
            "size": 20,
            "marker": "s",
            "alpha": 0.7,
            "edgecolor": "darkorange",
            "linewidth": 1,
            "label": "Urban Fringe",
        },
        "suburban": {
            "color": "yellow",
            "size": 15,
            "marker": "^",
            "alpha": 0.6,
            "edgecolor": "gold",
            "linewidth": 1,
            "label": "Suburban",
        },
        "rural": {
            "color": "blue",
            "size": 10,
            "marker": ".",
            "alpha": 0.5,
            "edgecolor": "darkblue",
            "linewidth": 0.5,
            "label": "Rural",
        },
    }


def apply_tufte_style(ax: plt.Axes) -> None:
    """
    Apply Edward Tufte's data visualization principles to a matplotlib axes.

    Args:
        ax: Matplotlib axes to style
    """
    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Lighten remaining spines
    ax.spines["left"].set_color("gray")
    ax.spines["bottom"].set_color("gray")
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)

    # Minimize tick marks
    ax.tick_params(axis="both", which="major", labelsize=10, color="gray")
    ax.tick_params(axis="both", which="minor", labelsize=8, color="lightgray")

    # Add subtle grid
    ax.grid(True, alpha=0.3, linewidth=0.5, linestyle="-", color="lightgray")
    ax.set_axisbelow(True)


def get_contour_levels(data: np.ndarray, n_levels: int | None = None) -> np.ndarray[Any, Any]:
    """
    Generate appropriate contour levels for temperature data.

    Args:
        data: Temperature data array
        n_levels: Number of contour levels (auto-determined if None)

    Returns:
        Array of contour level values
    """
    if data.size == 0 or np.all(np.isnan(data)):
        return np.linspace(-2, 2, 9)  # Default range

    # Remove NaN values
    clean_data = data[~np.isnan(data)]

    if len(clean_data) == 0:
        return np.linspace(-2, 2, 9)

    # Calculate data range
    data_min, data_max = np.percentile(clean_data, [5, 95])  # Use 5-95th percentiles
    data_range = data_max - data_min

    # Auto-determine number of levels if not specified
    if n_levels is None:
        if data_range <= 2:
            n_levels = 9
        elif data_range <= 5:
            n_levels = 11
        else:
            n_levels = 13

    # Generate symmetric levels for anomaly data if data crosses zero
    if data_min < 0 < data_max:
        max_abs = max(abs(data_min), abs(data_max))
        levels = np.linspace(-max_abs, max_abs, n_levels)
    else:
        # Non-symmetric levels for data that doesn't cross zero
        levels = np.linspace(data_min, data_max, n_levels)

    return levels


def get_figure_size(plot_type: str = "standard") -> tuple[float, float]:
    """
    Get appropriate figure size for different plot types.

    Args:
        plot_type: Type of plot ('standard', 'wide', 'square', 'academic')

    Returns:
        Tuple of (width, height) in inches
    """
    size_config = {
        "standard": (12, 8),
        "wide": (16, 10),
        "square": (10, 10),
        "academic": (14, 10),
        "publication": (12, 9),
    }

    return size_config.get(plot_type, (12, 8))
