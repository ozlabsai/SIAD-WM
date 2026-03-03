#!/usr/bin/env python3
"""Create standalone HTML demo viewer with embedded gallery data

Generates a single HTML file with all predictions embedded as base64 images.
"""

import json
import numpy as np
import base64
from pathlib import Path
from io import BytesIO
from PIL import Image


def rgb_to_base64(rgb: np.ndarray) -> str:
    """Convert RGB numpy array to base64 PNG"""
    if rgb.dtype != np.uint8:
        rgb = (rgb * 255).astype(np.uint8)

    img = Image.fromarray(rgb)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    b64 = base64.b64encode(buffer.read()).decode('utf-8')
    return f"data:image/png;base64,{b64}"


def create_viewer(gallery_path: str, output_path: str):
    """Create standalone HTML viewer with embedded data"""
    gallery_path = Path(gallery_path)

    # Load metadata
    with open(gallery_path / "gallery.json") as f:
        gallery_meta = json.load(f)

    with open(gallery_path / "stats.json") as f:
        stats = json.load(f)

    # Load all tiles
    tiles_data = []
    all_tile_ids = (
        gallery_meta["best"] +
        gallery_meta["average"] +
        gallery_meta["worst"]
    )

    print(f"Loading {len(all_tile_ids)} tiles...")

    for tile_id in all_tile_ids:
        tile_file = gallery_path / f"{tile_id}.npz"

        if not tile_file.exists():
            print(f"  Warning: {tile_id} not found")
            continue

        data = np.load(tile_file)

        # Determine category
        if tile_id in gallery_meta["best"]:
            category = "best"
        elif tile_id in gallery_meta["worst"]:
            category = "worst"
        else:
            category = "average"

        # Convert images
        context_b64 = rgb_to_base64(data['context_rgb'])
        pred_b64 = [rgb_to_base64(data['pred_rgbs'][i]) for i in range(len(data['pred_rgbs']))]
        target_b64 = [rgb_to_base64(data['target_rgbs'][i]) for i in range(len(data['target_rgbs']))]

        avg_mse = float(np.mean(data['mse_per_step']))

        tiles_data.append({
            "tile_id": tile_id,
            "category": category,
            "mse": avg_mse,
            "mse_per_step": data['mse_per_step'].tolist(),
            "context": context_b64,
            "predictions": pred_b64,
            "targets": target_b64
        })

        print(f"  ✓ {tile_id} ({category}, MSE: {avg_mse:.4f})")

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIAD Command Center - Gallery</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Consolas', 'Monaco', monospace;
            background: #0a0a0a;
            color: #f5f5f5;
        }}

        .header {{
            background: #1a1a1a;
            border-bottom: 2px solid #14b8a6;
            padding: 2rem;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2rem;
            color: #14b8a6;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            text-shadow: 0 0 20px rgba(20, 184, 166, 0.5);
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .stat {{
            background: #1a1a1a;
            border: 1px solid #262626;
            padding: 1.5rem;
            text-align: center;
        }}

        .stat-label {{
            color: #737373;
            font-size: 0.75rem;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }}

        .stat-value {{
            color: #14b8a6;
            font-size: 1.5rem;
            font-weight: bold;
        }}

        .tabs {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            padding: 2rem;
        }}

        .tab {{
            background: transparent;
            border: 1px solid #14b8a6;
            color: #14b8a6;
            padding: 0.75rem 1.5rem;
            cursor: pointer;
            font-size: 0.875rem;
            text-transform: uppercase;
        }}

        .tab:hover {{ background: rgba(20, 184, 166, 0.1); }}
        .tab.active {{ background: #f59e0b; border-color: #f59e0b; color: #0a0a0a; }}

        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .tile-card {{
            background: #1a1a1a;
            border: 1px solid #262626;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .tile-card:hover {{
            border-color: #14b8a6;
            box-shadow: 0 0 15px rgba(20, 184, 166, 0.3);
        }}

        .tile-img {{
            width: 100%;
            height: 200px;
            object-fit: cover;
            display: block;
        }}

        .tile-info {{
            padding: 1rem;
        }}

        .tile-id {{
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }}

        .tile-mse {{
            font-size: 0.75rem;
            color: #737373;
        }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            font-size: 0.625rem;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }}

        .badge.best {{ background: rgba(34, 197, 94, 0.2); color: #22c55e; }}
        .badge.worst {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
        .badge.average {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; }}

        .modal {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(10, 10, 10, 0.95);
            z-index: 1000;
            overflow-y: auto;
            padding: 2rem;
        }}

        .modal.active {{ display: block; }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 2rem;
        }}

        .modal-header h2 {{ color: #14b8a6; }}

        .close-btn {{
            background: #ef4444;
            border: none;
            color: white;
            padding: 0.5rem 1rem;
            cursor: pointer;
        }}

        .timeline {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 1rem;
        }}

        .timeline-item {{
            text-align: center;
        }}

        .timeline-label {{
            color: #737373;
            font-size: 0.75rem;
            margin-bottom: 0.5rem;
        }}

        .timeline-img {{
            width: 100%;
            border: 1px solid #262626;
        }}

        .comparison {{
            margin-top: 2rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }}

        .comparison h3 {{
            color: #14b8a6;
            margin-bottom: 1rem;
        }}

        .comparison-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SIAD Command Center</h1>
        <p style="color: #737373; margin-top: 0.5rem;">6-Month Satellite Prediction Gallery</p>
    </div>

    <div class="stats">
        <div class="stat">
            <div class="stat-label">Tiles</div>
            <div class="stat-value">{stats['num_tiles']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Best MSE</div>
            <div class="stat-value">{stats['best_mse']:.4f}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Median MSE</div>
            <div class="stat-value">{stats['median_mse']:.4f}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Worst MSE</div>
            <div class="stat-value">{stats['worst_mse']:.4f}</div>
        </div>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="filterGallery('all')">All</button>
        <button class="tab" onclick="filterGallery('best')">Best</button>
        <button class="tab" onclick="filterGallery('average')">Average</button>
        <button class="tab" onclick="filterGallery('worst')">Worst</button>
    </div>

    <div class="gallery" id="gallery"></div>

    <div class="modal" id="modal">
        <div class="modal-header">
            <h2 id="modal-title">Tile Viewer</h2>
            <button class="close-btn" onclick="closeModal()">Close</button>
        </div>
        <div id="modal-content"></div>
    </div>

    <script>
        const tilesData = {json.dumps(tiles_data, indent=2)};

        let currentFilter = 'all';

        function filterGallery(category) {{
            currentFilter = category;

            // Update tabs
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');

            renderGallery();
        }}

        function renderGallery() {{
            const gallery = document.getElementById('gallery');
            gallery.textContent = '';

            const filtered = currentFilter === 'all'
                ? tilesData
                : tilesData.filter(t => t.category === currentFilter);

            filtered.forEach((tile, idx) => {{
                const card = document.createElement('div');
                card.className = 'tile-card';
                card.onclick = () => showModal(tile);

                const img = document.createElement('img');
                img.className = 'tile-img';
                img.src = tile.context;

                const info = document.createElement('div');
                info.className = 'tile-info';

                const badge = document.createElement('span');
                badge.className = `badge ${{tile.category}}`;
                badge.textContent = tile.category;

                const tileId = document.createElement('div');
                tileId.className = 'tile-id';
                tileId.textContent = tile.tile_id;

                const mse = document.createElement('div');
                mse.className = 'tile-mse';
                mse.textContent = `MSE: ${{tile.mse.toFixed(4)}}`;

                info.appendChild(badge);
                info.appendChild(tileId);
                info.appendChild(mse);

                card.appendChild(img);
                card.appendChild(info);

                gallery.appendChild(card);
            }});
        }}

        function showModal(tile) {{
            document.getElementById('modal-title').textContent = tile.tile_id;

            const content = document.getElementById('modal-content');
            content.textContent = '';

            // Timeline
            const timeline = document.createElement('div');
            timeline.className = 'timeline';

            // Context
            const contextItem = document.createElement('div');
            contextItem.className = 'timeline-item';
            const contextLabel = document.createElement('div');
            contextLabel.className = 'timeline-label';
            contextLabel.textContent = 'Context';
            const contextImg = document.createElement('img');
            contextImg.className = 'timeline-img';
            contextImg.src = tile.context;
            contextItem.appendChild(contextLabel);
            contextItem.appendChild(contextImg);
            timeline.appendChild(contextItem);

            // Predictions
            for (let i = 0; i < 6; i++) {{
                const item = document.createElement('div');
                item.className = 'timeline-item';
                const label = document.createElement('div');
                label.className = 'timeline-label';
                label.textContent = `Month ${{i+1}}`;
                const img = document.createElement('img');
                img.className = 'timeline-img';
                img.src = tile.predictions[i];
                item.appendChild(label);
                item.appendChild(img);
                timeline.appendChild(item);
            }}

            content.appendChild(timeline);

            // Comparison
            const comparison = document.createElement('div');
            comparison.className = 'comparison';

            const predSection = document.createElement('div');
            const predTitle = document.createElement('h3');
            predTitle.textContent = 'Predictions';
            const predGrid = document.createElement('div');
            predGrid.className = 'comparison-grid';
            tile.predictions.forEach((pred, i) => {{
                const img = document.createElement('img');
                img.src = pred;
                img.style.width = '100%';
                img.style.border = '1px solid #262626';
                predGrid.appendChild(img);
            }});
            predSection.appendChild(predTitle);
            predSection.appendChild(predGrid);

            const targetSection = document.createElement('div');
            const targetTitle = document.createElement('h3');
            targetTitle.textContent = 'Ground Truth';
            const targetGrid = document.createElement('div');
            targetGrid.className = 'comparison-grid';
            tile.targets.forEach((target, i) => {{
                const img = document.createElement('img');
                img.src = target;
                img.style.width = '100%';
                img.style.border = '1px solid #262626';
                targetGrid.appendChild(img);
            }});
            targetSection.appendChild(targetTitle);
            targetSection.appendChild(targetGrid);

            comparison.appendChild(predSection);
            comparison.appendChild(targetSection);

            content.appendChild(comparison);

            document.getElementById('modal').classList.add('active');
        }}

        function closeModal() {{
            document.getElementById('modal').classList.remove('active');
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModal();
        }});

        // Initial render
        renderGallery();
    </script>
</body>
</html>"""

    # Write HTML
    output_path = Path(output_path)
    output_path.write_text(html)

    print(f"\n✓ Created demo viewer: {output_path}")
    print(f"  Open in browser: file://{output_path.absolute()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--gallery", default="siad-command-center/data/gallery")
    parser.add_argument("--output", default="siad-command-center/demo.html")

    args = parser.parse_args()

    create_viewer(args.gallery, args.output)
