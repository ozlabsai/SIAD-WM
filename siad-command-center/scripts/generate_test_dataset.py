"""
Generate comprehensive synthetic satellite imagery test dataset for SIAD.

Creates realistic tiles showing infrastructure changes over time with:
- Actual imagery with meaningful changes
- Model predictions (slightly smoothed)
- Residuals showing change detection
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import h5py
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple
import json

# Earth-tone color palettes
COLORS = {
    "vegetation": (34, 139, 34),  # Forest green
    "cleared_land": (139, 90, 43),  # Brown
    "urban": (105, 105, 105),  # Gray
    "concrete": (192, 192, 192),  # Light gray
    "asphalt": (64, 64, 64),  # Dark gray
    "water": (65, 105, 225),  # Royal blue
    "desert": (210, 180, 140),  # Tan
    "snow": (255, 250, 250),  # Snow white
    "crops_green": (154, 205, 50),  # Yellow green
    "crops_brown": (184, 134, 11),  # Dark goldenrod
}


@dataclass
class ChangeEvent:
    """Defines a change event in satellite imagery."""
    change_type: str
    onset_month: int
    region: str
    location: Tuple[int, int]
    size: Tuple[int, int]
    intensity: float = 1.0


class SyntheticImageryGenerator:
    """Generates realistic synthetic satellite imagery with changes."""

    def __init__(self, tile_size: int = 128, seed: int = 42):
        self.tile_size = tile_size
        self.rng = np.random.RandomState(seed)

    def add_texture(self, img_array: np.ndarray, intensity: float = 0.1) -> np.ndarray:
        """Add natural texture variation to imagery."""
        noise = self.rng.normal(0, intensity * 255, img_array.shape)
        return np.clip(img_array + noise, 0, 255).astype(np.uint8)

    def create_base_terrain(self, terrain_type: str) -> np.ndarray:
        """Create base terrain background."""
        img = np.zeros((self.tile_size, self.tile_size, 3), dtype=np.uint8)

        if terrain_type == "forest":
            base_color = COLORS["vegetation"]
        elif terrain_type == "desert":
            base_color = COLORS["desert"]
        elif terrain_type == "agricultural":
            base_color = COLORS["crops_green"]
        else:  # urban
            base_color = COLORS["cleared_land"]

        img[:, :] = base_color
        img = self.add_texture(img, intensity=0.15)
        return img

    def add_building_cluster(self, img: Image.Image, location: Tuple[int, int],
                            size: Tuple[int, int], progress: float = 1.0):
        """Add a cluster of buildings with construction progress."""
        draw = ImageDraw.Draw(img)
        x, y = location
        w, h = size

        # Number of buildings based on progress
        num_buildings = max(1, int(progress * 8))

        for i in range(num_buildings):
            bx = x + self.rng.randint(0, w - 10)
            by = y + self.rng.randint(0, h - 10)
            bw = self.rng.randint(8, 15)
            bh = self.rng.randint(8, 15)

            # Building color varies based on progress
            if progress < 0.5:
                color = COLORS["cleared_land"]  # Construction site
            else:
                color = COLORS["concrete"]

            draw.rectangle([bx, by, bx + bw, by + bh], fill=color, outline=COLORS["asphalt"])

    def add_deforestation(self, img: Image.Image, location: Tuple[int, int],
                         size: Tuple[int, int], progress: float = 1.0):
        """Add deforestation pattern."""
        draw = ImageDraw.Draw(img)
        x, y = location
        w, h = size

        # Clear patches based on progress
        cleared_area = int(w * h * progress)
        num_patches = max(1, int(progress * 20))

        for _ in range(num_patches):
            px = x + self.rng.randint(0, w - 5)
            py = y + self.rng.randint(0, h - 5)
            pw = self.rng.randint(5, 15)
            ph = self.rng.randint(5, 15)

            draw.rectangle([px, py, px + pw, py + ph],
                          fill=COLORS["cleared_land"])

    def add_road(self, img: Image.Image, location: Tuple[int, int],
                size: Tuple[int, int], progress: float = 1.0):
        """Add road construction."""
        draw = ImageDraw.Draw(img)
        x, y = location
        w, h = size

        # Road extends based on progress
        road_length = int(w * progress)
        road_width = 6

        if road_length > 0:
            draw.rectangle([x, y + h // 2 - road_width // 2,
                          x + road_length, y + h // 2 + road_width // 2],
                         fill=COLORS["asphalt"])

    def add_military_installation(self, img: Image.Image, location: Tuple[int, int],
                                  size: Tuple[int, int], progress: float = 1.0):
        """Add military installation structures."""
        draw = ImageDraw.Draw(img)
        x, y = location
        w, h = size

        if progress < 0.3:
            # Site preparation
            draw.rectangle([x, y, x + w, y + h], fill=COLORS["cleared_land"])
        else:
            # Rectangular structures
            structures = int(progress * 4)
            for i in range(structures):
                sx = x + (i % 2) * (w // 2) + 5
                sy = y + (i // 2) * (h // 2) + 5
                sw = w // 2 - 10
                sh = h // 2 - 10
                draw.rectangle([sx, sy, sx + sw, sy + sh],
                             fill=COLORS["concrete"], outline=COLORS["asphalt"])

    def add_seasonal_variation(self, img_array: np.ndarray, month: int,
                              region: str) -> np.ndarray:
        """Add seasonal effects."""
        if region in ["temperate", "agricultural"]:
            # Seasonal crop/vegetation cycles
            season_factor = np.sin((month - 3) * np.pi / 6)  # Peak in summer

            # Adjust green channel based on season
            mask = (img_array[:, :, 1] > img_array[:, :, 0]) & \
                   (img_array[:, :, 1] > img_array[:, :, 2])

            if season_factor > 0:  # Growing season
                img_array[mask, 1] = np.clip(
                    img_array[mask, 1] * (1 + season_factor * 0.3), 0, 255
                )
            else:  # Dormant season
                img_array[mask] = np.clip(
                    img_array[mask] * (1 + season_factor * 0.3), 0, 255
                )

        elif region == "polar":
            # Snow cover in winter months
            if month in [11, 12, 1, 2]:
                snow_coverage = 0.7 if month in [12, 1] else 0.4
                img_array = img_array * (1 - snow_coverage) + \
                           np.array(COLORS["snow"]) * snow_coverage

        return img_array.astype(np.uint8)

    def generate_tile_sequence(self, change_event: ChangeEvent) -> List[np.ndarray]:
        """Generate 12 monthly images for a tile with a change event."""
        terrain_map = {
            "urban_construction": "agricultural",
            "deforestation": "forest",
            "military_installation": "desert",
            "infrastructure": "agricultural",
            "seasonal_only": "agricultural"
        }

        terrain = terrain_map.get(change_event.change_type, "agricultural")
        sequence = []

        for month in range(1, 13):
            # Create base terrain
            base = self.create_base_terrain(terrain)
            img = Image.fromarray(base)

            # Add change if past onset
            if month >= change_event.onset_month and change_event.change_type != "seasonal_only":
                months_since_onset = month - change_event.onset_month
                progress = min(1.0, (months_since_onset + 1) / 4) * change_event.intensity

                if change_event.change_type == "urban_construction":
                    self.add_building_cluster(img, change_event.location,
                                            change_event.size, progress)
                elif change_event.change_type == "deforestation":
                    self.add_deforestation(img, change_event.location,
                                         change_event.size, progress)
                elif change_event.change_type == "infrastructure":
                    self.add_road(img, change_event.location,
                                change_event.size, progress)
                elif change_event.change_type == "military_installation":
                    self.add_military_installation(img, change_event.location,
                                                  change_event.size, progress)

            # Convert back to array and add seasonal variation
            img_array = np.array(img)
            img_array = self.add_seasonal_variation(img_array, month, change_event.region)

            sequence.append(img_array)

        return sequence

    def generate_prediction(self, actual: np.ndarray, smoothing: float = 2.0) -> np.ndarray:
        """Generate model prediction (smoothed version of actual)."""
        img = Image.fromarray(actual)
        img = img.filter(ImageFilter.GaussianBlur(radius=smoothing))
        return np.array(img)

    def compute_residual(self, actual: np.ndarray, predicted: np.ndarray) -> np.ndarray:
        """Compute residual highlighting differences."""
        # Compute absolute difference
        diff = np.abs(actual.astype(np.float32) - predicted.astype(np.float32))

        # Normalize to 0-255 range with enhanced contrast
        diff_norm = np.clip(diff * 2, 0, 255).astype(np.uint8)

        # Convert to heatmap (red = high difference)
        residual = np.zeros_like(actual)
        residual[:, :, 0] = diff_norm.mean(axis=2)  # Red channel
        residual[:, :, 2] = 255 - diff_norm.mean(axis=2)  # Blue channel (inverted)

        return residual


def generate_dataset(output_dir: Path, num_tiles: int = 75, tile_size: int = 128):
    """Generate complete test dataset."""
    output_dir = Path(output_dir)
    tiles_dir = output_dir / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)

    generator = SyntheticImageryGenerator(tile_size=tile_size)

    # Define change events distribution
    change_types = [
        ("urban_construction", 0.3),
        ("deforestation", 0.25),
        ("military_installation", 0.15),
        ("infrastructure", 0.2),
        ("seasonal_only", 0.1)
    ]

    regions = ["temperate", "tropical", "desert", "agricultural", "polar"]

    metadata = {
        "tiles": [],
        "tile_size": tile_size,
        "num_months": 12,
        "change_types": {}
    }

    print(f"Generating {num_tiles} tiles...")

    for tile_id in range(num_tiles):
        # Select change type based on distribution
        change_type = generator.rng.choice(
            [ct for ct, _ in change_types],
            p=[prob for _, prob in change_types]
        )

        # Generate change event
        onset_month = generator.rng.randint(3, 8)  # Changes occur mid-year
        region = generator.rng.choice(regions)

        # Random location and size for change
        max_size = tile_size // 2
        location = (
            generator.rng.randint(10, tile_size - max_size - 10),
            generator.rng.randint(10, tile_size - max_size - 10)
        )
        size = (
            generator.rng.randint(max_size // 2, max_size),
            generator.rng.randint(max_size // 2, max_size)
        )

        event = ChangeEvent(
            change_type=change_type,
            onset_month=onset_month,
            region=region,
            location=location,
            size=size,
            intensity=generator.rng.uniform(0.7, 1.0)
        )

        # Generate tile sequence
        actual_sequence = generator.generate_tile_sequence(event)

        # Create tile directory
        tile_dir = tiles_dir / f"tile_{tile_id:03d}"
        tile_dir.mkdir(exist_ok=True)

        # Save images for each month
        for month_idx, actual in enumerate(actual_sequence, start=1):
            month_dir = tile_dir / f"month_{month_idx:02d}"
            month_dir.mkdir(exist_ok=True)

            # Generate prediction and residual
            predicted = generator.generate_prediction(actual)
            residual = generator.compute_residual(actual, predicted)

            # Save images
            Image.fromarray(actual).save(month_dir / "actual.png")
            Image.fromarray(predicted).save(month_dir / "predicted.png")
            Image.fromarray(residual).save(month_dir / "residual.png")

        # Store metadata
        tile_metadata = {
            "tile_id": tile_id,
            "change_type": change_type,
            "onset_month": onset_month,
            "region": region,
            "location": location,
            "size": size,
            "latitude": generator.rng.uniform(-60, 60),
            "longitude": generator.rng.uniform(-180, 180),
        }
        metadata["tiles"].append(tile_metadata)

        # Count change types
        if change_type not in metadata["change_types"]:
            metadata["change_types"][change_type] = 0
        metadata["change_types"][change_type] += 1

        if (tile_id + 1) % 10 == 0:
            print(f"  Generated {tile_id + 1}/{num_tiles} tiles")

    # Save metadata as JSON
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Save metadata as HDF5
    with h5py.File(output_dir / "metadata.h5", "w") as f:
        f.attrs["tile_size"] = tile_size
        f.attrs["num_tiles"] = num_tiles
        f.attrs["num_months"] = 12

        for tile_meta in metadata["tiles"]:
            tile_grp = f.create_group(f"tile_{tile_meta['tile_id']:03d}")
            # Convert strings to bytes for HDF5 compatibility
            tile_grp.attrs["change_type"] = tile_meta["change_type"].encode('utf-8')
            tile_grp.attrs["onset_month"] = tile_meta["onset_month"]
            tile_grp.attrs["region"] = tile_meta["region"].encode('utf-8')
            tile_grp.attrs["latitude"] = tile_meta["latitude"]
            tile_grp.attrs["longitude"] = tile_meta["longitude"]
            tile_grp.create_dataset("location", data=tile_meta["location"])
            tile_grp.create_dataset("size", data=tile_meta["size"])

    print("\nDataset generation complete!")
    return metadata


def compute_dataset_size(output_dir: Path) -> dict:
    """Compute total size of generated dataset."""
    total_size = 0
    file_counts = {"actual": 0, "predicted": 0, "residual": 0}

    for img_type in ["actual", "predicted", "residual"]:
        pattern = f"**/{img_type}.png"
        files = list(output_dir.glob(pattern))
        file_counts[img_type] = len(files)
        total_size += sum(f.stat().st_size for f in files)

    # Add metadata files
    for meta_file in ["metadata.json", "metadata.h5"]:
        meta_path = output_dir / meta_file
        if meta_path.exists():
            total_size += meta_path.stat().st_size

    return {
        "total_size_mb": total_size / (1024 * 1024),
        "file_counts": file_counts,
        "total_files": sum(file_counts.values()) + 2  # +2 for metadata files
    }


if __name__ == "__main__":
    output_dir = Path("/Users/guynachshon/Documents/ozlabs/labs/SIAD/siad-command-center/data/satellite_imagery")

    print("=" * 60)
    print("SIAD Synthetic Satellite Imagery Generator")
    print("=" * 60)

    # Generate dataset
    metadata = generate_dataset(
        output_dir=output_dir,
        num_tiles=75,
        tile_size=128
    )

    # Compute statistics
    size_info = compute_dataset_size(output_dir)

    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Total tiles generated: {len(metadata['tiles'])}")
    print(f"\nChange type distribution:")
    for change_type, count in metadata["change_types"].items():
        percentage = (count / len(metadata['tiles'])) * 100
        print(f"  - {change_type}: {count} tiles ({percentage:.1f}%)")

    print(f"\nFile structure:")
    print(f"  - Root directory: {output_dir}")
    print(f"  - Tiles directory: tiles/tile_NNN/month_MM/")
    print(f"  - Images per month: actual.png, predicted.png, residual.png")
    print(f"  - Metadata: metadata.json, metadata.h5")

    print(f"\nDataset statistics:")
    print(f"  - Total files: {size_info['total_files']}")
    print(f"  - Actual images: {size_info['file_counts']['actual']}")
    print(f"  - Predicted images: {size_info['file_counts']['predicted']}")
    print(f"  - Residual images: {size_info['file_counts']['residual']}")
    print(f"  - Total size: {size_info['total_size_mb']:.2f} MB")

    print("\n" + "=" * 60)
    print("Dataset ready for SIAD testing!")
    print("=" * 60)
