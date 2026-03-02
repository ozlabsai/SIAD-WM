"""Detect command - delegates to Detection agent."""

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
    "--checkpoint",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to trained model checkpoint (.pth)",
)
@click.option(
    "--manifest",
    type=str,
    required=True,
    help="GCS or local path to manifest.jsonl",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory for detection results",
)
@click.option(
    "--scenarios",
    type=str,
    default=None,
    help="Comma-separated scenarios (overrides config, e.g., 'neutral,observed')",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate inputs without running detection",
)
@click.pass_context
def detect(
    ctx: click.Context,
    config: Path,
    checkpoint: Path,
    manifest: str,
    output: Path,
    scenarios: str | None,
    dry_run: bool,
) -> None:
    """Run anomaly detection with trained model.

    Computes acceleration scores by comparing counterfactual rollouts (neutral
    climate) with observed rollouts. Identifies persistent hotspots and clusters.

    Example:
        siad detect --config configs/quickstart-demo.yaml \\
            --checkpoint data/models/run1/checkpoint_best.pth \\
            --manifest gs://siad-exports/siad/quickstart-demo/manifest.jsonl \\
            --output data/outputs/quickstart-demo \\
            --scenarios neutral,observed \\
            --dry-run
    """
    verbose = ctx.obj.get("verbose", False)
    logger.info("=== SIAD Detect Command ===")

    # Load and validate config
    try:
        cfg = load_config(config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise click.ClickException(str(e))

    # Override scenarios if provided
    if scenarios:
        scenario_list = [s.strip() for s in scenarios.split(",")]
        logger.info(f"Overriding scenarios: {cfg.detection.scenarios} -> {scenario_list}")
        cfg.detection.scenarios = scenario_list

    # Log detection plan
    logger.info(f"Checkpoint: {checkpoint}")
    logger.info(f"Manifest: {manifest}")
    logger.info(f"Output directory: {output}")
    logger.info(f"Scenarios: {', '.join(cfg.detection.scenarios)}")
    logger.info(f"Percentile threshold: {cfg.detection.percentile_threshold}")
    logger.info(f"Persistence months: {cfg.detection.persistence_months}")
    logger.info(f"Min cluster size: {cfg.detection.min_cluster_size}")

    if dry_run:
        logger.info("DRY RUN: Detection plan validated, no detection run")
        click.echo("Detection configuration valid. Use without --dry-run to execute.")
        return

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output directory: {output}")

    # TODO: Delegate to Detection agent's detect module
    logger.error("Detection implementation not yet available (Detection agent pending)")
    click.echo(
        "Detection functionality will be implemented by Detection agent.\n"
        "Stub: Would run detection on {} with scenarios {}".format(
            checkpoint.name, cfg.detection.scenarios
        )
    )
    raise click.ClickException(
        "Detection not implemented (waiting for Detection agent, tasks T045-T053)"
    )
