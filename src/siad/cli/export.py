"""Export command - delegates to Data/GEE agent."""

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
    "--aoi-id",
    type=str,
    default=None,
    help="Override AOI ID from config (optional)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate inputs without executing export",
)
@click.pass_context
def export(ctx: click.Context, config: Path, aoi_id: str | None, dry_run: bool) -> None:
    """Export satellite imagery from Google Earth Engine.

    Exports multi-modal satellite data (Sentinel-1, Sentinel-2, VIIRS) for the
    AOI defined in the config file. Creates GeoTIFF tiles and manifest.jsonl.

    Example:
        siad export --config configs/quickstart-demo.yaml --dry-run
    """
    verbose = ctx.obj.get("verbose", False)
    logger.info("=== SIAD Export Command ===")

    # Load and validate config
    try:
        cfg = load_config(config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise click.ClickException(str(e))

    # Override AOI ID if provided
    if aoi_id:
        logger.info(f"Overriding AOI ID: {cfg.aoi.aoi_id} -> {aoi_id}")
        cfg.aoi.aoi_id = aoi_id

    # Log export plan
    logger.info(f"AOI ID: {cfg.aoi.aoi_id}")
    logger.info(f"Bounds: {cfg.aoi.bounds}")
    logger.info(f"Date range: {cfg.data.start_month} to {cfg.data.end_month}")
    logger.info(f"GCS bucket: {cfg.data.gcs_bucket}")
    logger.info(f"Data sources: {', '.join(cfg.data.sources)}")

    if dry_run:
        logger.info("DRY RUN: Export plan validated, no data exported")
        click.echo("Export configuration valid. Use without --dry-run to execute.")
        return

    # Execute export
    try:
        from siad.data.export_orchestrator import ExportOrchestrator

        # Create orchestrator
        orchestrator = ExportOrchestrator(
            aoi_config={
                'aoi_id': cfg.aoi.aoi_id,
                'bounds': cfg.aoi.bounds,
                'tile_size_px': cfg.aoi.tile_size_px,
                'resolution_m': cfg.aoi.resolution_m,
                'projection': cfg.aoi.projection
            },
            data_config={
                'gcs_bucket': cfg.data.gcs_bucket,
                'gcp_project': getattr(cfg.data, 'gcp_project', None),
                'start_month': cfg.data.start_month,
                'end_month': cfg.data.end_month,
                'sources': cfg.data.sources
            }
        )

        # Run export
        manifest_path = orchestrator.export()

        logger.info(f"Export complete! Manifest: {manifest_path}")
        click.echo(f"\n✅ Export tasks submitted successfully!")
        click.echo(f"\nManifest: {manifest_path}")
        click.echo(f"\nMonitor progress at: https://code.earthengine.google.com/tasks")

    except Exception as e:
        logger.error(f"Export failed: {e}")
        import traceback
        traceback.print_exc()
        raise click.ClickException(f"Export failed: {e}")
