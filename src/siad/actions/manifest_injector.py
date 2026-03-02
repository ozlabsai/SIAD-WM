"""
Manifest injector: Update manifest.jsonl with computed anomalies.

Reads manifest.jsonl line by line, adds rain_anom and temp_anom fields,
and writes back atomically (temp file + rename).

Example:
    >>> inject_anomalies_to_manifest(
    ...     manifest_path="data/raw/manifest.jsonl",
    ...     rain_anomalies={"2023-01": -0.35, "2023-02": 0.12},
    ...     temp_anomalies={"2023-01": 0.08, "2023-02": -0.15},
    ...     output_path="data/preprocessed/manifest_with_anomalies.jsonl"
    ... )
"""

import json
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def inject_anomalies_to_manifest(
    manifest_path: str,
    rain_anomalies: Dict[str, float],
    temp_anomalies: Optional[Dict[str, float]] = None,
    output_path: Optional[str] = None
) -> None:
    """
    Read manifest.jsonl, add rain_anom and temp_anom fields, write back.

    Args:
        manifest_path: Path to input manifest.jsonl
        rain_anomalies: Dictionary mapping "YYYY-MM" -> rain z-score anomaly
        temp_anomalies: Optional dictionary mapping "YYYY-MM" -> temp z-score anomaly
        output_path: Path to output manifest. If None, overwrites input.

    Raises:
        FileNotFoundError: If manifest_path does not exist
        ValueError: If manifest contains invalid JSON or missing "month" field
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    if output_path is None:
        output_path = manifest_path

    updated_rows = []
    missing_months = set()

    logger.info(f"Reading manifest from: {manifest_path}")

    with open(manifest_path, 'r') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num}: {e}") from e

            if "month" not in row:
                raise ValueError(f"Missing 'month' field at line {line_num}")

            month = row["month"]

            # Inject rain anomaly (required)
            if month in rain_anomalies:
                row["rain_anom"] = rain_anomalies[month]
            else:
                row["rain_anom"] = 0.0
                missing_months.add(month)

            # Inject temp anomaly (optional)
            if temp_anomalies is not None:
                if month in temp_anomalies:
                    row["temp_anom"] = temp_anomalies[month]
                else:
                    row["temp_anom"] = 0.0
                    if month not in missing_months:
                        missing_months.add(month)
            else:
                # ERA5 unavailable
                row["temp_anom"] = None

            updated_rows.append(row)

    if missing_months:
        logger.warning(f"Missing anomalies for {len(missing_months)} months: {sorted(missing_months)[:5]}...")

    # Write atomically: write to temp file, then rename
    temp_path = output_path + ".tmp"

    logger.info(f"Writing updated manifest to: {temp_path}")

    with open(temp_path, 'w') as f:
        for row in updated_rows:
            f.write(json.dumps(row) + '\n')

    logger.info(f"Renaming {temp_path} -> {output_path}")
    os.replace(temp_path, output_path)

    logger.info(f"Successfully updated {len(updated_rows)} rows in manifest")


def validate_manifest_anomalies(manifest_path: str) -> Dict[str, any]:
    """
    Validate that manifest contains valid anomaly fields.

    Returns statistics about anomalies in manifest.

    Args:
        manifest_path: Path to manifest.jsonl

    Returns:
        Dictionary with statistics:
        {
            "total_rows": int,
            "rain_anom_stats": {"min": float, "max": float, "mean": float, "std": float},
            "temp_anom_stats": {...} or None if temp_anom unavailable,
            "missing_rain_anom": int,
            "missing_temp_anom": int
        }
    """
    import numpy as np

    rain_values = []
    temp_values = []
    missing_rain = 0
    missing_temp = 0
    total_rows = 0

    with open(manifest_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            row = json.loads(line)
            total_rows += 1

            # Rain anomaly
            rain_anom = row.get("rain_anom")
            if rain_anom is not None and not np.isnan(rain_anom):
                rain_values.append(rain_anom)
            else:
                missing_rain += 1

            # Temp anomaly
            temp_anom = row.get("temp_anom")
            if temp_anom is not None and not np.isnan(temp_anom):
                temp_values.append(temp_anom)
            else:
                missing_temp += 1

    stats = {
        "total_rows": total_rows,
        "missing_rain_anom": missing_rain,
        "missing_temp_anom": missing_temp
    }

    if rain_values:
        stats["rain_anom_stats"] = {
            "min": float(np.min(rain_values)),
            "max": float(np.max(rain_values)),
            "mean": float(np.mean(rain_values)),
            "std": float(np.std(rain_values))
        }
    else:
        stats["rain_anom_stats"] = None

    if temp_values:
        stats["temp_anom_stats"] = {
            "min": float(np.min(temp_values)),
            "max": float(np.max(temp_values)),
            "mean": float(np.mean(temp_values)),
            "std": float(np.std(temp_values))
        }
    else:
        stats["temp_anom_stats"] = None

    return stats
