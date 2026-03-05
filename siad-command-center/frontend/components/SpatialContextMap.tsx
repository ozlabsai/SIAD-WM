'use client';

import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { TileDetail } from '@/types';

interface SpatialContextMapProps {
  tileDetail: TileDetail;
}

// Initialize Mapbox token (ensure it's set in environment)
const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

export default function SpatialContextMap({ tileDetail }: SpatialContextMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!mapContainer.current || map.current || !MAPBOX_TOKEN || !tileDetail.metadata) return;

    const { center, bounds } = tileDetail.metadata;

    // Initialize map
    mapboxgl.accessToken = MAPBOX_TOKEN;
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [center[1], center[0]], // [lon, lat]
      zoom: 10,
    });

    // Add tile bounds polygon
    map.current.on('load', () => {
      if (!map.current) return;

      const [west, south, east, north] = bounds;

      map.current.addSource('tile-bounds', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [[
              [west, north],
              [east, north],
              [east, south],
              [west, south],
              [west, north],
            ]],
          },
          properties: {},
        },
      });

      map.current.addLayer({
        id: 'tile-bounds-fill',
        type: 'fill',
        source: 'tile-bounds',
        paint: {
          'fill-color': '#22d3ee',
          'fill-opacity': 0.2,
        },
      });

      map.current.addLayer({
        id: 'tile-bounds-outline',
        type: 'line',
        source: 'tile-bounds',
        paint: {
          'line-color': '#22d3ee',
          'line-width': 2,
        },
      });

      // Add center marker
      new mapboxgl.Marker({ color: '#ef4444' })
        .setLngLat([center[1], center[0]])
        .addTo(map.current!);
    });

    return () => {
      map.current?.remove();
    };
  }, [tileDetail]);

  if (!MAPBOX_TOKEN) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-text-primary mb-3">
          Spatial Context
        </h3>
        <div className="text-center py-8 text-text-secondary">
          Map unavailable: Mapbox token not configured
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-text-primary mb-3">
        Spatial Context
      </h3>
      <div
        ref={mapContainer}
        className="w-full h-64 rounded-lg overflow-hidden"
      />
      <div className="mt-3 flex items-center gap-4 text-xs text-text-secondary">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
          <span>Tile Center</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-[#22d3ee]" />
          <span>Tile Bounds</span>
        </div>
      </div>
    </div>
  );
}
