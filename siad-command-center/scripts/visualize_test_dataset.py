"""
Visualize the synthetic satellite imagery dataset to showcase the visual story.

Creates composite images showing:
- Time series of changes across months
- Comparison of actual vs predicted vs residual
- Different change types
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json
import matplotlib.pyplot as plt


def create_time_series_composite(tile_dir: Path, months: list = [1, 4, 7, 10]) -> Image.Image:
    """Create a composite showing time progression for a tile."""
    images = []
    for month in months:
        month_dir = tile_dir / f"month_{month:02d}"
        actual = Image.open(month_dir / "actual.png")
        predicted = Image.open(month_dir / "predicted.png")
        residual = Image.open(month_dir / "residual.png")

        # Stack vertically: actual, predicted, residual
        combined = Image.new('RGB', (actual.width, actual.height * 3))
        combined.paste(actual, (0, 0))
        combined.paste(predicted, (0, actual.height))
        combined.paste(residual, (0, actual.height * 2))

        images.append(combined)

    # Create horizontal composite
    total_width = sum(img.width for img in images) + 10 * (len(images) - 1)
    total_height = images[0].height
    composite = Image.new('RGB', (total_width, total_height), color=(255, 255, 255))

    x_offset = 0
    for img in images:
        composite.paste(img, (x_offset, 0))
        x_offset += img.width + 10

    return composite


def create_change_showcase(data_dir: Path, output_dir: Path):
    """Create visualizations showcasing different change types."""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load metadata
    with open(data_dir / "metadata.json") as f:
        metadata = json.load(f)

    # Group tiles by change type
    tiles_by_type = {}
    for tile in metadata["tiles"]:
        change_type = tile["change_type"]
        if change_type not in tiles_by_type:
            tiles_by_type[change_type] = []
        tiles_by_type[change_type].append(tile)

    print("Creating visualizations for each change type...\n")

    # Create visualization for each change type
    for change_type, tiles in tiles_by_type.items():
        if not tiles:
            continue

        # Take first tile of this type
        tile = tiles[0]
        tile_id = tile["tile_id"]
        onset_month = tile["onset_month"]

        print(f"Change type: {change_type}")
        print(f"  Tile ID: {tile_id}")
        print(f"  Onset month: {onset_month}")
        print(f"  Region: {tile['region']}")

        tile_dir = data_dir / "tiles" / f"tile_{tile_id:03d}"

        # Create time series showing before, during, and after change
        months_to_show = [
            max(1, onset_month - 2),  # Before
            onset_month,               # Onset
            min(12, onset_month + 2),  # During
            min(12, onset_month + 4)   # After
        ]

        composite = create_time_series_composite(tile_dir, months_to_show)

        # Add labels
        draw = ImageDraw.Draw(composite)
        label_height = 30
        labeled = Image.new('RGB', (composite.width, composite.height + label_height),
                           color=(255, 255, 255))
        labeled.paste(composite, (0, label_height))

        draw = ImageDraw.Draw(labeled)
        # Add title
        title = f"{change_type.replace('_', ' ').title()} - Months {months_to_show}"
        draw.text((10, 5), title, fill=(0, 0, 0))

        # Add row labels
        row_height = composite.height // 3
        draw.text((5, label_height + row_height // 2), "Actual",
                 fill=(0, 0, 0))
        draw.text((5, label_height + row_height + row_height // 2), "Predicted",
                 fill=(0, 0, 0))
        draw.text((5, label_height + 2 * row_height + row_height // 2), "Residual",
                 fill=(0, 0, 0))

        output_path = output_dir / f"{change_type}_example.png"
        labeled.save(output_path)
        print(f"  Saved: {output_path}\n")


def analyze_residuals(data_dir: Path):
    """Analyze residual statistics across dataset."""
    data_dir = Path(data_dir)

    with open(data_dir / "metadata.json") as f:
        metadata = json.load(f)

    results = []

    for tile in metadata["tiles"][:10]:  # Sample first 10 tiles
        tile_id = tile["tile_id"]
        onset_month = tile["onset_month"]
        change_type = tile["change_type"]
        tile_dir = data_dir / "tiles" / f"tile_{tile_id:03d}"

        tile_results = {
            "tile_id": tile_id,
            "change_type": change_type,
            "onset_month": onset_month,
            "residual_means": []
        }

        for month in range(1, 13):
            month_dir = tile_dir / f"month_{month:02d}"
            residual = np.array(Image.open(month_dir / "residual.png"))
            mean_residual = residual.mean()
            tile_results["residual_means"].append(mean_residual)

        results.append(tile_results)

    # Plot residuals over time
    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    axes = axes.flatten()

    for idx, tile_result in enumerate(results):
        ax = axes[idx]
        months = range(1, 13)
        means = tile_result["residual_means"]
        onset = tile_result["onset_month"]

        ax.plot(months, means, marker='o', linewidth=2)
        ax.axvline(x=onset, color='red', linestyle='--', alpha=0.7, label='Onset')
        ax.set_title(f"{tile_result['change_type']}\n(Tile {tile_result['tile_id']})",
                    fontsize=10)
        ax.set_xlabel("Month")
        ax.set_ylabel("Mean Residual")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    plt.tight_layout()
    output_path = data_dir.parent / "visualizations" / "residual_analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nResidual analysis saved: {output_path}")


def create_summary_stats(data_dir: Path):
    """Create summary statistics visualization."""
    data_dir = Path(data_dir)

    with open(data_dir / "metadata.json") as f:
        metadata = json.load(f)

    # Count statistics
    change_types = metadata["change_types"]
    regions = {}
    onset_months = []

    for tile in metadata["tiles"]:
        region = tile["region"]
        regions[region] = regions.get(region, 0) + 1
        onset_months.append(tile["onset_month"])

    # Create bar charts
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Change types
    ax = axes[0]
    types = list(change_types.keys())
    counts = list(change_types.values())
    ax.bar(range(len(types)), counts, color='steelblue')
    ax.set_xticks(range(len(types)))
    ax.set_xticklabels([t.replace('_', '\n') for t in types], fontsize=9)
    ax.set_ylabel("Count")
    ax.set_title("Change Types Distribution")
    ax.grid(True, alpha=0.3, axis='y')

    # Regions
    ax = axes[1]
    reg_names = list(regions.keys())
    reg_counts = list(regions.values())
    ax.bar(range(len(reg_names)), reg_counts, color='forestgreen')
    ax.set_xticks(range(len(reg_names)))
    ax.set_xticklabels(reg_names, fontsize=9)
    ax.set_ylabel("Count")
    ax.set_title("Regions Distribution")
    ax.grid(True, alpha=0.3, axis='y')

    # Onset months
    ax = axes[2]
    ax.hist(onset_months, bins=range(1, 14), color='coral', edgecolor='black')
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    ax.set_title("Change Onset Distribution")
    ax.set_xticks(range(1, 13))
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_path = data_dir.parent / "visualizations" / "summary_statistics.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Summary statistics saved: {output_path}")


if __name__ == "__main__":
    data_dir = Path("/Users/guynachshon/Documents/ozlabs/labs/SIAD/siad-command-center/data/satellite_imagery")
    viz_dir = data_dir.parent / "visualizations"

    print("=" * 60)
    print("SIAD Dataset Visualization")
    print("=" * 60)
    print()

    # Create change type showcases
    create_change_showcase(data_dir, viz_dir)

    # Analyze residuals
    print("\nAnalyzing residuals across time...")
    analyze_residuals(data_dir)

    # Create summary statistics
    print("\nCreating summary statistics...")
    create_summary_stats(data_dir)

    print("\n" + "=" * 60)
    print(f"All visualizations saved to: {viz_dir}")
    print("=" * 60)
