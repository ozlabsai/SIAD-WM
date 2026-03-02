"""
Report Builder

Orchestrates all report components and renders final HTML output.
Combines AOI maps, hotspot cards, timelines, and scenario comparisons into
a single self-contained HTML file.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from jinja2 import Template
import yaml

from .map_generator import generate_aoi_map, generate_aoi_map_fallback
from .hotspot_cards import generate_hotspot_thumbnails
from .timeline import generate_timeline_plot, aggregate_residuals_for_hotspot
from .scenario_comparison import generate_scenario_comparison

logger = logging.getLogger(__name__)


def build_report(
    hotspots_json_path: str,
    manifest_path: str,
    config_path: str,
    output_html_path: str,
    scenarios: Optional[List[str]] = None,
    skip_timelines: bool = False,
    residuals_csv_path: Optional[str] = None
) -> None:
    """
    Build complete HTML report from hotspot detection outputs.

    Args:
        hotspots_json_path: Path to hotspots.json (from Detection agent)
        manifest_path: Path to manifest.jsonl (from Data agent)
        config_path: Path to AOI config YAML
        output_html_path: Output HTML file path
        scenarios: List of scenario names for comparison (default: ["neutral", "observed"])
        skip_timelines: If True, skip timeline generation (faster)
        residuals_csv_path: Path to residuals_timeseries.csv (optional, for timelines)

    Outputs:
        - HTML report written to output_html_path
        - Logs progress to stderr

    Raises:
        FileNotFoundError: If input files missing
        ValueError: If hotspots.json schema invalid
    """
    logger.info("Starting report generation")

    # Default scenarios
    if scenarios is None:
        scenarios = ["neutral", "observed"]

    # Load inputs
    logger.info("Loading inputs...")
    hotspots = _load_hotspots(hotspots_json_path)
    manifest = _load_manifest(manifest_path)
    config = _load_config(config_path)

    if not hotspots:
        logger.warning("No hotspots detected, generating minimal report")
        _generate_empty_report(output_html_path, config)
        return

    # Rank hotspots (Structural > Activity > Environmental, then by max_acceleration_score)
    logger.info(f"Ranking {len(hotspots)} hotspots...")
    hotspots_ranked = _rank_hotspots(hotspots)

    # Generate AOI overview map
    logger.info("Generating AOI overview map...")
    try:
        aoi_map_base64 = generate_aoi_map(
            aoi_bounds=config["aoi"]["bounds"],
            hotspots=hotspots_ranked
        )
    except Exception as e:
        logger.error(f"AOI map generation failed: {e}")
        aoi_map_base64 = generate_aoi_map_fallback(str(e))

    # Generate hotspot cards (thumbnails + timelines)
    logger.info("Generating hotspot cards...")
    for i, hotspot in enumerate(hotspots_ranked):
        logger.info(f"  Processing {hotspot['hotspot_id']} ({i+1}/{len(hotspots_ranked)})")

        # Extract thumbnails
        thumbnails = generate_hotspot_thumbnails(hotspot, manifest)
        hotspot["thumbnails"] = thumbnails

        # Calculate before/after months for display
        from dateutil.relativedelta import relativedelta
        first_detected = datetime.strptime(hotspot["first_detected_month"], "%Y-%m")
        before_month = first_detected - relativedelta(months=6)
        after_month = first_detected + relativedelta(months=hotspot["persistence_months"])
        hotspot["before_month"] = before_month.strftime("%Y-%m")
        hotspot["after_month"] = after_month.strftime("%Y-%m")

        # Generate timeline (unless skipped)
        if not skip_timelines and residuals_csv_path:
            residuals = aggregate_residuals_for_hotspot(hotspot, residuals_csv_path)
            timeline_b64 = generate_timeline_plot(
                hotspot_id=hotspot["hotspot_id"],
                residuals_timeseries=residuals,
                first_detected_month=hotspot["first_detected_month"],
                persistence_months=hotspot["persistence_months"]
            )
            hotspot["timeline_plot_b64"] = timeline_b64
        else:
            hotspot["timeline_plot_b64"] = None

    # Generate scenario comparison heatmaps
    scenario_comparison = None
    if scenarios and len(scenarios) > 0:
        logger.info(f"Generating scenario comparison for: {', '.join(scenarios)}")
        scores_dir = Path(output_html_path).parent / "scores"  # Assume scores in same dir
        try:
            scenario_comparison = generate_scenario_comparison(
                aoi_id=config["aoi"]["aoi_id"],
                scenarios=scenarios,
                scores_dir=str(scores_dir),
                aoi_bounds=config["aoi"]["bounds"]
            )
        except Exception as e:
            logger.error(f"Scenario comparison generation failed: {e}")
            scenario_comparison = None

    # Prepare template context
    logger.info("Rendering HTML template...")
    context = _build_template_context(
        aoi_id=config["aoi"]["aoi_id"],
        hotspots_ranked=hotspots_ranked,
        aoi_map_base64=aoi_map_base64,
        scenarios=scenarios,
        scenario_comparison=scenario_comparison,
        config=config
    )

    # Render template
    html_content = _render_template(context)

    # Write output
    logger.info(f"Writing report to {output_html_path}")
    Path(output_html_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_html_path).write_text(html_content, encoding="utf-8")

    # Log summary
    file_size_mb = Path(output_html_path).stat().st_size / (1024 * 1024)
    logger.info(f"Report generated successfully: {file_size_mb:.2f} MB")


def _load_hotspots(path: str) -> List[Dict]:
    """Load and validate hotspots.json."""
    with open(path, "r") as f:
        hotspots = json.load(f)
    # TODO: Validate schema against CONTRACTS.md Section 5
    return hotspots


def _load_manifest(path: str) -> Dict:
    """Load manifest.jsonl into dict mapping (tile_id, month) -> gcs_uri."""
    manifest = {}
    with open(path, "r") as f:
        for line in f:
            entry = json.loads(line)
            key = (entry["tile_id"], entry["month"])
            manifest[key] = entry["gcs_uri"]
    return manifest


def _load_config(path: str) -> Dict:
    """Load AOI config YAML."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _rank_hotspots(hotspots: List[Dict]) -> List[Dict]:
    """
    Rank hotspots by confidence tier and max_acceleration_score.

    Tier priority: Structural > Activity > Environmental
    Within tier: Sort by max_acceleration_score descending
    """
    tier_priority = {"Structural": 0, "Activity": 1, "Environmental": 2}

    def sort_key(h):
        tier_rank = tier_priority.get(h["confidence_tier"], 999)
        score = h["max_acceleration_score"]
        return (tier_rank, -score)  # Negative score for descending order

    return sorted(hotspots, key=sort_key)


def _build_template_context(
    aoi_id: str,
    hotspots_ranked: List[Dict],
    aoi_map_base64: str,
    scenarios: List[str],
    scenario_comparison: Optional[List[Dict]],
    config: Dict
) -> Dict:
    """Build Jinja2 template context."""
    # Calculate tier counts and max scores
    tier_counts = {"structural": 0, "activity": 0, "environmental": 0}
    tier_max_scores = {"structural": 0.0, "activity": 0.0, "environmental": 0.0}

    for h in hotspots_ranked:
        tier = h["confidence_tier"].lower()
        tier_counts[tier] += 1
        tier_max_scores[tier] = max(tier_max_scores[tier], h["max_acceleration_score"])

    # Extract time range from config
    start_month = config.get("data", {}).get("start_month", "N/A")
    end_month = config.get("data", {}).get("end_month", "N/A")

    return {
        "aoi_id": aoi_id,
        "start_month": start_month,
        "end_month": end_month,
        "generation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scenarios": scenarios,
        "tier_counts": tier_counts,
        "tier_max_scores": tier_max_scores,
        "aoi_map_base64": aoi_map_base64,
        "hotspots_ranked": hotspots_ranked,
        "scenario_comparison": scenario_comparison
    }


def _render_template(context: Dict) -> str:
    """Render Jinja2 template with context."""
    template_path = Path(__file__).parent / "template.html"
    template_str = template_path.read_text(encoding="utf-8")
    template = Template(template_str)
    return template.render(**context)


def _generate_empty_report(output_path: str, config: Dict) -> None:
    """Generate minimal report when no hotspots detected."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SIAD Report - No Hotspots</title>
        <style>
            body {{ font-family: sans-serif; padding: 40px; text-align: center; }}
            h1 {{ color: #333; }}
            p {{ color: #666; }}
        </style>
    </head>
    <body>
        <h1>SIAD Report - {config["aoi"]["aoi_id"]}</h1>
        <p>No infrastructure acceleration hotspots detected in this AOI.</p>
        <p>This may indicate stable conditions or insufficient temporal coverage.</p>
    </body>
    </html>
    """
    Path(output_path).write_text(html, encoding="utf-8")
    logger.info(f"Empty report written to {output_path}")
