"""
Actions/Context module for SIAD MVP.

This module computes rainfall and temperature anomalies using month-of-year
climatology baselines and injects them into manifest.jsonl for counterfactual
scenario rollouts.

Contracts:
- Consumes: manifest.jsonl from Data/GEE agent (with rain_anom=0.0 placeholders)
- Produces: Updated manifest.jsonl with filled rain_anom and temp_anom z-scores
- Action Vector: [rain_anom, temp_anom] per timestep for world model conditioning
"""

from .anomaly_computer import compute_month_of_year_anomalies
from .manifest_injector import inject_anomalies_to_manifest

__all__ = [
    "compute_month_of_year_anomalies",
    "inject_anomalies_to_manifest",
]
