"""Algorithm registry and interface definitions."""

from collections.abc import Callable
from typing import Any, Protocol

import geopandas as gpd

# Import and register algorithms
from . import adjustment_impact, min_obs_anomaly, simple_anomaly


class AlgorithmProtocol(Protocol):
    """Protocol defining the interface for anomaly calculation algorithms."""

    def calculate(
        self,
        gdf_adjusted: gpd.GeoDataFrame,
        baseline_period: tuple[int, int],
        current_period: tuple[int, int],
        gdf_raw: gpd.GeoDataFrame | None = None,
        config: dict[str, Any] | None = None,
    ) -> gpd.GeoDataFrame:
        """
        Calculate temperature anomalies.

        Args:
            gdf_adjusted: Adjusted USHCN temperature data
            baseline_period: Tuple of (start_year, end_year) for baseline
            current_period: Tuple of (start_year, end_year) for current period
            gdf_raw: Optional raw USHCN temperature data
            config: Optional configuration parameters

        Returns:
            GeoDataFrame with anomaly results
        """
        ...


# Algorithm registry
ALGORITHMS: dict[str, Callable] = {}


def register_algorithm(name: str, algorithm_func: Callable) -> None:
    """Register an algorithm function."""
    ALGORITHMS[name] = algorithm_func


def get_algorithm(name: str) -> Callable:
    """Get an algorithm function by name."""
    if name not in ALGORITHMS:
        raise ValueError(
            f"Unknown algorithm: {name}. Available: {list(ALGORITHMS.keys())}"
        )
    return ALGORITHMS[name]


def list_algorithms() -> list[str]:
    """List all registered algorithm names."""
    return list(ALGORITHMS.keys())


register_algorithm("simple", simple_anomaly.calculate)
register_algorithm("min_obs", min_obs_anomaly.calculate)
register_algorithm("adjustment_impact", adjustment_impact.calculate)
