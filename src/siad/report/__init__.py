"""
SIAD Report Generation Module

Generates briefing-grade HTML reports from hotspot detection outputs.

Components:
- map_generator: AOI overview maps with hotspot markers
- hotspot_cards: Before/after thumbnail panels
- timeline: Temporal residual score plots
- scenario_comparison: Counterfactual heatmap comparisons
- report_builder: Orchestrates all components into HTML report

Usage:
    from siad.report import build_report

    build_report(
        hotspots_json_path="data/outputs/quickstart-demo/hotspots.json",
        manifest_path="data/outputs/quickstart-demo/manifest.jsonl",
        config_path="configs/quickstart-demo.yaml",
        output_html_path="data/outputs/quickstart-demo/report.html"
    )
"""

from .report_builder import build_report

__all__ = ["build_report"]
__version__ = "1.0.0"
