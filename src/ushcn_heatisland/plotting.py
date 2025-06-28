"""Visualization module for USHCN temperature anomaly results."""

from pathlib import Path
from typing import Optional, Tuple
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import numpy as np


def plot_anomaly_map(
    results_gdf: gpd.GeoDataFrame,
    title: str,
    output_path: Optional[Path] = None,
    figsize: Tuple[int, int] = (12, 8),
    colormap: str = "RdBu_r",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> plt.Figure:
    """
    Create a map visualization of temperature anomalies.

    Args:
        results_gdf: GeoDataFrame with anomaly results
        title: Title for the plot
        output_path: Optional path to save the plot
        figsize: Figure size as (width, height)
        colormap: Matplotlib colormap name
        vmin: Minimum value for color scale
        vmax: Maximum value for color scale

    Returns:
        Matplotlib Figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Determine the value column to plot
    value_col = None
    if "anomaly_celsius" in results_gdf.columns:
        value_col = "anomaly_celsius"
    elif "adjustment_impact" in results_gdf.columns:
        value_col = "adjustment_impact"
    else:
        raise ValueError("No suitable anomaly column found in results")

    # Set color scale limits if not provided
    if vmin is None or vmax is None:
        values = results_gdf[value_col].dropna()
        if len(values) > 0:
            abs_max = max(abs(values.min()), abs(values.max()))
            if vmin is None:
                vmin = -abs_max
            if vmax is None:
                vmax = abs_max
        else:
            vmin, vmax = -1, 1

    # Convert to Web Mercator for basemap compatibility
    results_web_mercator = results_gdf.to_crs("EPSG:3857")

    # Plot the points
    results_web_mercator.plot(
        column=value_col,
        ax=ax,
        cmap=colormap,
        vmin=vmin,
        vmax=vmax,
        markersize=50,
        alpha=0.8,
        edgecolors="black",
        linewidth=0.5,
    )

    # Add basemap
    try:
        ctx.add_basemap(
            ax,
            crs=results_web_mercator.crs,
            source=ctx.providers.CartoDB.Positron,
            alpha=0.7,
        )
    except Exception:
        # Fallback if basemap fails
        ax.set_facecolor("lightgray")

    # Set title and labels
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)

    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Temperature Anomaly (°C)", rotation=270, labelpad=20, fontsize=12)

    # Remove axis ticks for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])

    # Adjust layout
    plt.tight_layout()

    # Save if output path provided
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {output_path}")

    return fig


def plot_comparison_maps(
    results_gdf: gpd.GeoDataFrame,
    title_prefix: str,
    output_dir: Optional[Path] = None,
    figsize: Tuple[int, int] = (18, 6),
) -> plt.Figure:
    """
    Create side-by-side comparison maps for adjustment impact analysis.

    Args:
        results_gdf: GeoDataFrame with adjustment impact results
        title_prefix: Prefix for plot titles
        output_dir: Optional directory to save plots
        figsize: Figure size as (width, height)

    Returns:
        Matplotlib Figure object
    """
    # Verify required columns exist
    required_cols = ["anomaly_raw", "anomaly_adjusted", "adjustment_impact"]
    missing_cols = [col for col in required_cols if col not in results_gdf.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Create figure with three subplots
    fig, axes = plt.subplots(1, 3, figsize=figsize)

    # Convert to Web Mercator for basemap compatibility
    results_web_mercator = results_gdf.to_crs("EPSG:3857")

    # Determine common color scale for anomaly plots
    all_anomalies = np.concatenate(
        [results_gdf["anomaly_raw"].dropna(), results_gdf["anomaly_adjusted"].dropna()]
    )
    if len(all_anomalies) > 0:
        abs_max_anomaly = max(abs(all_anomalies.min()), abs(all_anomalies.max()))
        anomaly_vmin, anomaly_vmax = -abs_max_anomaly, abs_max_anomaly
    else:
        anomaly_vmin, anomaly_vmax = -1, 1

    # Determine color scale for adjustment impact
    impacts = results_gdf["adjustment_impact"].dropna()
    if len(impacts) > 0:
        abs_max_impact = max(abs(impacts.min()), abs(impacts.max()))
        impact_vmin, impact_vmax = -abs_max_impact, abs_max_impact
    else:
        impact_vmin, impact_vmax = -0.5, 0.5

    # Plot configurations
    plot_configs = [
        {
            "column": "anomaly_raw",
            "title": f"{title_prefix} - Raw Data Anomaly",
            "vmin": anomaly_vmin,
            "vmax": anomaly_vmax,
            "cmap": "RdBu_r",
        },
        {
            "column": "anomaly_adjusted",
            "title": f"{title_prefix} - Adjusted Data Anomaly",
            "vmin": anomaly_vmin,
            "vmax": anomaly_vmax,
            "cmap": "RdBu_r",
        },
        {
            "column": "adjustment_impact",
            "title": f"{title_prefix} - Adjustment Impact",
            "vmin": impact_vmin,
            "vmax": impact_vmax,
            "cmap": "RdYlBu_r",
        },
    ]

    # Create each subplot
    for i, config in enumerate(plot_configs):
        ax = axes[i]

        # Plot the points
        results_web_mercator.plot(
            column=config["column"],
            ax=ax,
            cmap=config["cmap"],
            vmin=config["vmin"],
            vmax=config["vmax"],
            markersize=30,
            alpha=0.8,
            edgecolors="black",
            linewidth=0.3,
        )

        # Add basemap
        try:
            ctx.add_basemap(
                ax,
                crs=results_web_mercator.crs,
                source=ctx.providers.CartoDB.Positron,
                alpha=0.7,
            )
        except Exception:
            ax.set_facecolor("lightgray")

        # Set title and remove ticks
        ax.set_title(config["title"], fontsize=12, fontweight="bold", pad=10)
        ax.set_xticks([])
        ax.set_yticks([])

        # Add colorbar
        sm = plt.cm.ScalarMappable(
            cmap=config["cmap"],
            norm=plt.Normalize(vmin=config["vmin"], vmax=config["vmax"]),
        )
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
        cbar.set_label("°C", rotation=0, labelpad=10, fontsize=10)

    # Adjust layout
    plt.tight_layout()

    # Save if output directory provided
    if output_dir:
        output_path = (
            output_dir / f"{title_prefix.lower().replace(' ', '_')}_comparison.png"
        )
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Comparison plot saved to: {output_path}")

    return fig


def create_summary_statistics(results_gdf: gpd.GeoDataFrame) -> dict:
    """
    Generate summary statistics for anomaly results.

    Args:
        results_gdf: GeoDataFrame with anomaly results

    Returns:
        Dictionary with summary statistics
    """
    stats = {
        "total_stations": len(results_gdf),
        "stations_with_data": results_gdf.dropna().shape[0],
    }

    # Add statistics for each numeric column
    numeric_cols = results_gdf.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in results_gdf.columns:
            values = results_gdf[col].dropna()
            if len(values) > 0:
                stats[f"{col}_mean"] = float(values.mean())
                stats[f"{col}_std"] = float(values.std())
                stats[f"{col}_min"] = float(values.min())
                stats[f"{col}_max"] = float(values.max())
                stats[f"{col}_median"] = float(values.median())

    return stats
