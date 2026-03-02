"""
Visualization utilities for anomaly validation.

Generates sanity plots to verify anomaly computation:
1. Time series plot: rain_anom and temp_anom over time
2. Histogram: distribution of anomalies (should be ~Gaussian centered at 0)

Example:
    >>> plot_anomaly_timeseries(
    ...     rain_anomalies={"2023-01": -0.35, ...},
    ...     temp_anomalies={"2023-01": 0.12, ...},
    ...     output_path="data/outputs/anomaly_timeseries.png"
    ... )
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Optional


def plot_anomaly_timeseries(
    rain_anomalies: Dict[str, float],
    temp_anomalies: Optional[Dict[str, float]] = None,
    output_path: str = "anomaly_timeseries.png"
) -> None:
    """
    Plot time series of rain and temperature anomalies.

    Args:
        rain_anomalies: Dictionary mapping "YYYY-MM" -> rain z-score
        temp_anomalies: Optional dictionary mapping "YYYY-MM" -> temp z-score
        output_path: Path to save plot PNG

    Expected pattern:
        - Seasonal patterns removed (no obvious cyclicality)
        - Roughly centered around 0.0
        - Occasional spikes/dips (extreme events)
    """
    months = sorted(rain_anomalies.keys())
    rain_values = [rain_anomalies[m] for m in months]
    temp_values = [temp_anomalies[m] for m in months] if temp_anomalies else None

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    # Rain anomalies
    axes[0].plot(months, rain_values, marker='o', linewidth=2, markersize=4, label='Rain Anomaly')
    axes[0].axhline(0, color='red', linestyle='--', alpha=0.5, label='Baseline (z=0)')
    axes[0].fill_between(range(len(months)), -1, 1, alpha=0.1, color='gray', label='±1σ range')
    axes[0].set_ylabel('Rain Z-Score', fontsize=12)
    axes[0].set_title('Rainfall Anomaly Time Series (Month-of-Year Baseline)', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc='upper left')

    # Temp anomalies
    if temp_values:
        axes[1].plot(months, temp_values, marker='s', linewidth=2, markersize=4, color='orange', label='Temp Anomaly')
        axes[1].axhline(0, color='red', linestyle='--', alpha=0.5, label='Baseline (z=0)')
        axes[1].fill_between(range(len(months)), -1, 1, alpha=0.1, color='gray', label='±1σ range')
    else:
        axes[1].text(0.5, 0.5, 'Temperature data unavailable',
                     ha='center', va='center', transform=axes[1].transAxes, fontsize=14, color='gray')

    axes[1].set_ylabel('Temp Z-Score', fontsize=12)
    axes[1].set_xlabel('Month', fontsize=12)
    axes[1].set_title('Temperature Anomaly Time Series (Month-of-Year Baseline)', fontsize=14)
    axes[1].grid(True, alpha=0.3)
    if temp_values:
        axes[1].legend(loc='upper left')

    # Rotate x-axis labels for readability
    # Show every 3rd month to avoid crowding
    tick_positions = range(0, len(months), 3)
    tick_labels = [months[i] for i in tick_positions]
    axes[1].set_xticks(tick_positions)
    axes[1].set_xticklabels(tick_labels, rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved anomaly time series plot to: {output_path}")


def plot_anomaly_histogram(
    rain_anomalies: Dict[str, float],
    temp_anomalies: Optional[Dict[str, float]] = None,
    output_path: str = "anomaly_histogram.png"
) -> None:
    """
    Plot histogram of anomaly distributions.

    Args:
        rain_anomalies: Dictionary mapping "YYYY-MM" -> rain z-score
        temp_anomalies: Optional dictionary mapping "YYYY-MM" -> temp z-score
        output_path: Path to save plot PNG

    Expected pattern:
        - Approximately Gaussian distribution
        - Centered at 0.0 (mean ≈ 0)
        - Most values in [-2, +2] range (95% confidence)
    """
    rain_values = list(rain_anomalies.values())
    temp_values = list(temp_anomalies.values()) if temp_anomalies else None

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Rain histogram
    axes[0].hist(rain_values, bins=20, alpha=0.7, color='blue', edgecolor='black', density=True)
    axes[0].axvline(0, color='red', linestyle='--', linewidth=2, label='Mean = 0')

    # Overlay Gaussian curve
    x = np.linspace(min(rain_values), max(rain_values), 100)
    gaussian = (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * x**2)
    axes[0].plot(x, gaussian, 'k--', linewidth=2, alpha=0.5, label='Standard Normal')

    axes[0].set_xlabel('Rain Anomaly Z-Score', fontsize=12)
    axes[0].set_ylabel('Density', fontsize=12)
    axes[0].set_title(f'Rain Anomaly Distribution (N={len(rain_values)})', fontsize=14)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Add stats text
    rain_mean = np.mean(rain_values)
    rain_std = np.std(rain_values)
    axes[0].text(0.05, 0.95, f'Mean: {rain_mean:.3f}\nStd: {rain_std:.3f}',
                 transform=axes[0].transAxes, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Temp histogram
    if temp_values:
        axes[1].hist(temp_values, bins=20, alpha=0.7, color='orange', edgecolor='black', density=True)
        axes[1].axvline(0, color='red', linestyle='--', linewidth=2, label='Mean = 0')

        # Overlay Gaussian curve
        x = np.linspace(min(temp_values), max(temp_values), 100)
        gaussian = (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * x**2)
        axes[1].plot(x, gaussian, 'k--', linewidth=2, alpha=0.5, label='Standard Normal')

        axes[1].set_xlabel('Temp Anomaly Z-Score', fontsize=12)
        axes[1].set_ylabel('Density', fontsize=12)
        axes[1].set_title(f'Temp Anomaly Distribution (N={len(temp_values)})', fontsize=14)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        # Add stats text
        temp_mean = np.mean(temp_values)
        temp_std = np.std(temp_values)
        axes[1].text(0.05, 0.95, f'Mean: {temp_mean:.3f}\nStd: {temp_std:.3f}',
                     transform=axes[1].transAxes, verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    else:
        axes[1].text(0.5, 0.5, 'Temperature data unavailable',
                     ha='center', va='center', transform=axes[1].transAxes, fontsize=14, color='gray')
        axes[1].set_title('Temp Anomaly Distribution', fontsize=14)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved anomaly histogram plot to: {output_path}")


def generate_validation_plots(
    rain_anomalies: Dict[str, float],
    temp_anomalies: Optional[Dict[str, float]] = None,
    output_dir: str = "data/outputs"
) -> None:
    """
    Generate all validation plots for anomaly computation.

    Creates:
    - anomaly_timeseries.png: Time series of rain and temp anomalies
    - anomaly_histogram.png: Histogram of anomaly distributions

    Args:
        rain_anomalies: Dictionary mapping "YYYY-MM" -> rain z-score
        temp_anomalies: Optional dictionary mapping "YYYY-MM" -> temp z-score
        output_dir: Directory to save plots
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    timeseries_path = os.path.join(output_dir, "anomaly_timeseries.png")
    histogram_path = os.path.join(output_dir, "anomaly_histogram.png")

    plot_anomaly_timeseries(rain_anomalies, temp_anomalies, timeseries_path)
    plot_anomaly_histogram(rain_anomalies, temp_anomalies, histogram_path)

    print(f"\nValidation plots generated in: {output_dir}")
    print(f"  - {timeseries_path}")
    print(f"  - {histogram_path}")
