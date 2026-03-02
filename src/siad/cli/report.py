"""Report command - delegates to Reporting agent."""

import click
import logging
from pathlib import Path

from siad.config import load_config

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to YAML config file",
)
@click.option(
    "--hotspots",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to hotspots.json from detection",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output path for HTML report",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate inputs without generating report",
)
@click.pass_context
def report(
    ctx: click.Context,
    config: Path,
    hotspots: Path,
    output: Path,
    dry_run: bool,
) -> None:
    """Generate HTML report from detection results.

    Creates an interactive HTML report with:
    - Hotspot map (leaflet.js)
    - Ranked detections with confidence tiers
    - Before/after thumbnails (SAR, optical, lights)
    - Attribution breakdown (modality contributions)

    Example:
        siad report --config configs/quickstart-demo.yaml \\
            --hotspots data/outputs/quickstart-demo/hotspots.json \\
            --output data/outputs/quickstart-demo/report.html \\
            --dry-run
    """
    verbose = ctx.obj.get("verbose", False)
    logger.info("=== SIAD Report Command ===")

    # Load and validate config
    try:
        cfg = load_config(config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise click.ClickException(str(e))

    # Log report plan
    logger.info(f"AOI ID: {cfg.aoi.aoi_id}")
    logger.info(f"Hotspots file: {hotspots}")
    logger.info(f"Output report: {output}")

    if dry_run:
        logger.info("DRY RUN: Report plan validated, no report generated")
        click.echo("Report configuration valid. Use without --dry-run to execute.")
        return

    # Create output directory if needed
    output.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output.parent}")

    # TODO: Delegate to Reporting agent's report generation module
    logger.error("Report generation not yet available (Reporting agent pending)")
    click.echo(
        "Report functionality will be implemented by Reporting agent.\n"
        "Stub: Would generate HTML report from {} to {}".format(hotspots.name, output)
    )
    raise click.ClickException(
        "Report not implemented (waiting for Reporting agent, tasks T054-T059)"
    )
