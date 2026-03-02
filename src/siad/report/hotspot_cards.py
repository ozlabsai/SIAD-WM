"""
Hotspot Card Generator

Extracts before/after thumbnails from GeoTIFF tiles for each detected hotspot.
Generates SAR, optical, and nighttime lights panels.
"""

import io
import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, Optional, Tuple
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


# Band indices from CONTRACTS.md Section 1
BAND_ORDER_V1 = {
    "S2_B2": 0,           # Sentinel-2 Blue
    "S2_B3": 1,           # Sentinel-2 Green
    "S2_B4": 2,           # Sentinel-2 Red
    "S2_B8": 3,           # Sentinel-2 NIR
    "S1_VV": 4,           # Sentinel-1 SAR VV
    "S1_VH": 5,           # Sentinel-1 SAR VH
    "VIIRS_avg_rad": 6,   # VIIRS nighttime lights
    "S2_valid_mask": 7    # Sentinel-2 cloud mask
}


def extract_thumbnail(
    hotspot: Dict,
    manifest: Dict[Tuple[str, str], str],
    modality: str,
    before: bool = True,
    thumbnail_size: int = 512
) -> str:
    """
    Extract before/after thumbnail for a given modality.

    Args:
        hotspot: Hotspot dict from hotspots.json
        manifest: Dict mapping (tile_id, month) -> gcs_uri or local file path
        modality: One of {"sar", "optical", "lights"}
        before: If True, extract "before" image; else "after" image
        thumbnail_size: Max dimension in pixels

    Returns:
        Base64-encoded JPEG image string

    Note:
        This is a skeleton implementation. Full implementation requires:
        1. rasterio to read GeoTIFF bands
        2. Spatial subsetting based on hotspot centroid
        3. Band-specific rendering (SAR grayscale, RGB composite, lights colormap)
    """
    try:
        # Determine target month
        first_detected = datetime.strptime(hotspot["first_detected_month"], "%Y-%m")
        if before:
            target_month = first_detected - relativedelta(months=6)
            temporal_label = "before"
        else:
            target_month = first_detected + relativedelta(months=hotspot["persistence_months"])
            temporal_label = "after"

        target_month_str = target_month.strftime("%Y-%m")

        # Lookup tile in manifest (use first tile in cluster for simplicity)
        tile_id = hotspot["tile_ids"][0]
        key = (tile_id, target_month_str)

        if key not in manifest:
            logger.warning(f"Missing data for {tile_id} at {target_month_str} ({temporal_label})")
            return _generate_placeholder_thumbnail("N/A", f"Data gap: {target_month_str}")

        # TODO: Load GeoTIFF using rasterio
        # geotiff_path = manifest[key]
        # with rasterio.open(geotiff_path) as src:
        #     bands = src.read()  # Shape: (8, 256, 256)
        #     ...

        # SKELETON: Generate mock thumbnail (random noise for now)
        mock_array = _render_mock_thumbnail(modality, thumbnail_size)
        return _array_to_base64_jpeg(mock_array, quality=85)

    except Exception as e:
        logger.error(f"Failed to extract thumbnail for {modality}: {e}")
        return _generate_placeholder_thumbnail("Error", str(e))


def _render_mock_thumbnail(modality: str, size: int) -> np.ndarray:
    """
    Generate mock thumbnail for smoke testing.

    Args:
        modality: One of {"sar", "optical", "lights"}
        size: Image dimension (square)

    Returns:
        RGB array (size, size, 3) with uint8 values
    """
    rng = np.random.RandomState(42)
    if modality == "sar":
        # Grayscale noise
        gray = rng.randint(0, 255, (size, size), dtype=np.uint8)
        return np.stack([gray, gray, gray], axis=-1)
    elif modality == "optical":
        # Color noise
        return rng.randint(0, 255, (size, size, 3), dtype=np.uint8)
    elif modality == "lights":
        # Yellow-orange gradient
        gradient = np.linspace(0, 255, size, dtype=np.uint8)
        r = np.tile(gradient, (size, 1))
        g = np.tile(gradient * 0.7, (size, 1)).astype(np.uint8)
        b = np.zeros((size, size), dtype=np.uint8)
        return np.stack([r, g, b], axis=-1)
    else:
        # Fallback gray
        return np.full((size, size, 3), 128, dtype=np.uint8)


def _array_to_base64_jpeg(array: np.ndarray, quality: int = 85) -> str:
    """
    Convert numpy array to base64-encoded JPEG.

    Args:
        array: RGB array (H, W, 3) with uint8 values
        quality: JPEG compression quality (0-100)

    Returns:
        Base64-encoded JPEG string
    """
    img = Image.fromarray(array, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _generate_placeholder_thumbnail(title: str, message: str, size: int = 512) -> str:
    """
    Generate placeholder image with text annotation.

    Args:
        title: Main text (e.g., "N/A", "Error")
        message: Subtitle text (error message or data gap info)
        size: Image dimension

    Returns:
        Base64-encoded JPEG string
    """
    # Create gray background with text overlay
    from PIL import ImageDraw, ImageFont

    img = Image.new("RGB", (size, size), color="#cccccc")
    draw = ImageDraw.Draw(img)

    # Draw text (centered)
    text = f"{title}\n{message}"
    bbox = draw.textbbox((0, 0), text, font=None)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, text, fill="#666666", font=None, align="center")

    # Encode to JPEG
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_hotspot_thumbnails(
    hotspot: Dict,
    manifest: Dict[Tuple[str, str], str]
) -> Dict[str, str]:
    """
    Generate all before/after thumbnails for a hotspot.

    Args:
        hotspot: Hotspot dict from hotspots.json
        manifest: Dict mapping (tile_id, month) -> file path

    Returns:
        Dict with keys:
            - s1_before_b64, s1_after_b64 (SAR)
            - s2_before_b64, s2_after_b64 (optical)
            - viirs_before_b64, viirs_after_b64 (lights)
    """
    thumbnails = {}

    for modality in ["sar", "optical", "lights"]:
        for temporal in ["before", "after"]:
            key = f"{modality}_{temporal}_b64"
            if modality == "sar":
                prefix = "s1"
            elif modality == "optical":
                prefix = "s2"
            else:
                prefix = "viirs"

            final_key = f"{prefix}_{temporal}_b64"
            thumbnails[final_key] = extract_thumbnail(
                hotspot, manifest, modality, before=(temporal == "before")
            )

    return thumbnails
