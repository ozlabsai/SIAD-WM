"""SIAD CLI main entrypoint."""

import click
import logging
import sys

from siad import __version__
from siad.utils import setup_logging

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="siad")
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable DEBUG logging (default: INFO)",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """SIAD - Satellite Imagery Anomaly Detection

    Multi-modal world model for infrastructure change detection.

    Commands:
      export  - Export satellite imagery from GEE
      train   - Train world model on exported data
      detect  - Run anomaly detection with trained model
      report  - Generate HTML report from detections
    """
    # Store verbose flag in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Setup logging once at the CLI group level
    setup_logging(verbose)


# Import subcommands
from .export import export
from .train import train
from .detect import detect
from .report import report

# Register subcommands
cli.add_command(export)
cli.add_command(train)
cli.add_command(detect)
cli.add_command(report)


if __name__ == "__main__":
    cli()
