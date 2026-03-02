"""Train command - delegates to World Model agent."""

import click
import logging
from pathlib import Path

from siad.config import load_config
from siad.utils import set_seed

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to YAML config file",
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
    help="Output directory for model checkpoints",
)
@click.option(
    "--epochs",
    type=int,
    default=None,
    help="Override number of training epochs from config",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate inputs without training",
)
@click.pass_context
def train(
    ctx: click.Context,
    config: Path,
    manifest: str,
    output: Path,
    epochs: int | None,
    dry_run: bool,
) -> None:
    """Train world model on exported satellite data.

    Trains a JEPA-style encoder-dynamics model to predict future observations
    conditioned on climate action vectors (rain/temp anomalies).

    Example:
        siad train --config configs/quickstart-demo.yaml \\
            --manifest gs://siad-exports/siad/quickstart-demo/manifest.jsonl \\
            --output data/models/run1 \\
            --dry-run
    """
    verbose = ctx.obj.get("verbose", False)
    logger.info("=== SIAD Train Command ===")

    # Load and validate config
    try:
        cfg = load_config(config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise click.ClickException(str(e))

    # Override epochs if provided
    if epochs:
        logger.info(f"Overriding epochs: {cfg.model.epochs} -> {epochs}")
        cfg.model.epochs = epochs

    # Log training plan
    logger.info(f"Manifest: {manifest}")
    logger.info(f"Output directory: {output}")
    logger.info(f"Latent dim: {cfg.model.latent_dim}")
    logger.info(f"Context length: {cfg.model.context_length} months")
    logger.info(f"Rollout horizon: {cfg.model.rollout_horizon} months")
    logger.info(f"Batch size: {cfg.model.batch_size}")
    logger.info(f"Epochs: {cfg.model.epochs}")
    logger.info(f"Learning rate: {cfg.model.learning_rate}")
    logger.info(f"Seed: {cfg.model.seed}")

    # Set random seed for reproducibility
    set_seed(cfg.model.seed)

    if dry_run:
        logger.info("DRY RUN: Training plan validated, no model trained")
        click.echo("Training configuration valid. Use without --dry-run to execute.")
        return

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output directory: {output}")

    # TODO: Delegate to World Model agent's training module
    logger.error("Training implementation not yet available (Model agent pending)")
    click.echo(
        "Training functionality will be implemented by World Model agent.\n"
        "Stub: Would train model with {} epochs on {}".format(cfg.model.epochs, manifest)
    )
    raise click.ClickException(
        "Training not implemented (waiting for Model agent, tasks T030-T044)"
    )
