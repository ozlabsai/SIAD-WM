#!/usr/bin/env python3
"""
SIAD Report Generator CLI

Generates briefing-grade HTML reports from hotspot detection outputs.

Usage:
    python scripts/generate_report.py \
        --hotspots data/outputs/quickstart-demo/hotspots.json \
        --manifest data/outputs/quickstart-demo/manifest.jsonl \
        --config configs/quickstart-demo.yaml \
        --output data/outputs/quickstart-demo/report.html \
        --scenarios neutral,observed \
        --residuals data/outputs/quickstart-demo/residuals_timeseries.csv

Exit Codes:
    0: Success
    1: Invalid input files (missing or malformed)
    2: Template rendering error
    3: Thumbnail extraction error
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from siad.report import build_report


def setup_logging(verbose: bool = False) -> None:
    """Configure logging to stderr."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr
    )


def validate_inputs(args: argparse.Namespace) -> None:
    """
    Validate input file paths exist.

    Raises:
        FileNotFoundError: If required input files missing
    """
    required_files = [
        ("hotspots", args.hotspots),
        ("manifest", args.manifest),
        ("config", args.config)
    ]

    for name, path in required_files:
        if not Path(path).exists():
            raise FileNotFoundError(f"Missing {name} file: {path}")

    if args.residuals and not Path(args.residuals).exists():
        logging.warning(f"Residuals file not found: {args.residuals}, timelines will be skipped")
        args.residuals = None


def main() -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Generate SIAD HTML report from hotspot detection outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Required arguments
    parser.add_argument(
        "--hotspots",
        required=True,
        help="Path to hotspots.json (from Detection agent)"
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to manifest.jsonl (from Data agent)"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to AOI config YAML"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output HTML file path"
    )

    # Optional arguments
    parser.add_argument(
        "--scenarios",
        default="neutral,observed",
        help="Comma-separated scenario names for comparison (default: neutral,observed)"
    )
    parser.add_argument(
        "--residuals",
        default=None,
        help="Path to residuals_timeseries.csv (optional, for timeline plots)"
    )
    parser.add_argument(
        "--skip-timelines",
        action="store_true",
        help="Skip timeline generation (faster report generation)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs without generating report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging to stderr"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Validate inputs
        logger.info("Validating input files...")
        validate_inputs(args)

        if args.dry_run:
            logger.info("Dry run mode: inputs valid, exiting without generating report")
            print("OK: All inputs valid", file=sys.stdout)
            return 0

        # Parse scenarios
        scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]

        # Build report
        build_report(
            hotspots_json_path=args.hotspots,
            manifest_path=args.manifest,
            config_path=args.config,
            output_html_path=args.output,
            scenarios=scenarios,
            skip_timelines=args.skip_timelines,
            residuals_csv_path=args.residuals
        )

        # Success output to stdout
        print(args.output, file=sys.stdout)
        return 0

    except FileNotFoundError as e:
        logger.error(f"Input validation failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Report generation failed: {e}")
        # Determine exit code based on error type
        if "template" in str(e).lower():
            return 2
        elif "thumbnail" in str(e).lower():
            return 3
        else:
            return 1


if __name__ == "__main__":
    sys.exit(main())
