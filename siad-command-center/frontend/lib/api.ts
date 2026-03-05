import type { AOI, Hotspot, TileDetail, TileAssets } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function fetchAOI(): Promise<AOI> {
  const response = await fetch(`${API_URL}/api/aoi`);
  if (!response.ok) {
    throw new Error('Failed to fetch AOI data');
  }
  return response.json();
}

export async function fetchHotspots(
  minScore: number = 0.5,
  limit: number = 100
): Promise<Hotspot[]> {
  const response = await fetch(
    `${API_URL}/api/detect/hotspots?min_score=${minScore}&limit=${limit}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch hotspots');
  }
  const data = await response.json();

  // Enhance hotspots with derived UI fields
  const hotspots = (Array.isArray(data) ? data : data.hotspots || []).map((h: Hotspot) => ({
    ...h,
    confidence: h.score >= 0.7 ? 'High' : h.score >= 0.5 ? 'Medium' : 'Low',
    alert_type: h.changeType?.includes('construction') || h.changeType?.includes('infrastructure')
      ? 'Structural'
      : 'Activity',
    onset: h.month,
    duration: 1, // Default, would need timeline data for accurate duration
  }));

  return hotspots;
}

export async function fetchTileDetail(tileId: string): Promise<TileDetail> {
  const response = await fetch(`${API_URL}/api/detect/tile/${tileId}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Tile '${tileId}' not found`);
    }
    throw new Error('Failed to fetch tile detail');
  }
  return response.json();
}

export async function fetchTileAssets(
  tileId: string,
  month: string
): Promise<TileAssets> {
  const response = await fetch(
    `${API_URL}/api/tiles/${tileId}/assets?month=${month}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch tile assets');
  }
  return response.json();
}

export function getStaticAssetUrl(path: string): string {
  // Convert relative path to full URL
  // Example: tiles/tile_042/2024-01/sar.png -> http://localhost:8001/static/tiles/tile_042/2024-01/sar.png
  return `${API_URL}/static/${path}`;
}
