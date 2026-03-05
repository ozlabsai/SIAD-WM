'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import type { Hotspot, HotspotFeatureCollection } from '@/types';
import { getScoreColor } from '@/lib/utils';
import MapLegend from '@/components/MapLegend';

interface MapViewProps {
  hotspots: Hotspot[];
  selectedHotspot: Hotspot | null;
  onHotspotSelect: (hotspot: Hotspot) => void;
  showOverlay?: boolean;
  currentMonth?: string;
}

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

export default function MapView({
  hotspots,
  selectedHotspot,
  onHotspotSelect,
  showOverlay = false,
  currentMonth,
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [showResidualOverlay, setShowResidualOverlay] = useState(false);
  const popupRef = useRef<mapboxgl.Popup | null>(null);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    console.log('🗺️ Initializing map with token:', MAPBOX_TOKEN ? 'Token present' : 'NO TOKEN');
    mapboxgl.accessToken = MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [-122.4194, 37.7749], // SF Bay Area
      zoom: 10,
      attributionControl: false,
    });

    map.current.on('load', () => {
      const canvas = map.current?.getCanvas();
      console.log('✅ Map loaded successfully');
      console.log('📐 Canvas dimensions:', {
        width: canvas?.width,
        height: canvas?.height,
        clientWidth: canvas?.clientWidth,
        clientHeight: canvas?.clientHeight
      });
      setMapLoaded(true);
    });

    map.current.on('error', (e) => {
      console.error('❌ Map error:', e);
    });

    map.current.on('styledata', () => {
      console.log('🎨 Map style loaded');
    });

    // Cleanup
    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Update hotspots layer
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    // Convert hotspots to GeoJSON
    const geojson: HotspotFeatureCollection = {
      type: 'FeatureCollection',
      features: hotspots
        .filter((h) => h.lon && h.lat)
        .map((hotspot) => ({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [hotspot.lon, hotspot.lat],
          },
          properties: {
            tile_id: hotspot.tileId,
            score: hotspot.score,
            confidence: hotspot.confidence || 'Medium',
            alert_type: hotspot.alert_type || 'Activity',
          },
        })),
    };

    const sourceId = 'hotspots';
    const source = map.current.getSource(sourceId);

    if (source && source.type === 'geojson') {
      source.setData(geojson);
    } else {
      // Add source
      map.current.addSource(sourceId, {
        type: 'geojson',
        data: geojson,
      });

      // Add circle layer
      map.current.addLayer({
        id: 'hotspots-circles',
        type: 'circle',
        source: sourceId,
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['get', 'score'],
            0.5,
            6,
            1.0,
            12,
          ],
          'circle-color': [
            'case',
            ['>=', ['get', 'score'], 0.7],
            '#ef4444',
            ['>=', ['get', 'score'], 0.5],
            '#fbbf24',
            '#22d3ee',
          ],
          'circle-opacity': 0.8,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
        },
      });

      // Add click handler
      map.current.on('click', 'hotspots-circles', (e) => {
        if (!e.features || e.features.length === 0) return;

        const feature = e.features[0];
        const tileId = feature.properties?.tile_id;

        const hotspot = hotspots.find((h) => h.tileId === tileId);
        if (hotspot) {
          onHotspotSelect(hotspot);
        }
      });

      // Add hover tooltip
      map.current.on('mouseenter', 'hotspots-circles', (e) => {
        if (!map.current || !e.features || e.features.length === 0) return;

        map.current.getCanvas().style.cursor = 'pointer';

        const feature = e.features[0];
        const tileId = feature.properties?.tile_id;
        const score = feature.properties?.score;
        const coordinates = (feature.geometry as any).coordinates.slice();

        // Close existing popup
        if (popupRef.current) {
          popupRef.current.remove();
        }

        // Create tooltip popup
        popupRef.current = new mapboxgl.Popup({
          closeButton: false,
          closeOnClick: false,
          offset: 15,
        })
          .setLngLat(coordinates)
          .setHTML(
            `<div style="padding: 8px; background: var(--panel); color: var(--text-primary); border-radius: 4px;">
              <p style="font-size: 12px; font-family: monospace; margin-bottom: 4px;">${tileId}</p>
              <p style="font-size: 14px; font-weight: bold;">Score: ${score?.toFixed(2)}</p>
            </div>`
          )
          .addTo(map.current);
      });

      map.current.on('mouseleave', 'hotspots-circles', () => {
        if (map.current) {
          map.current.getCanvas().style.cursor = '';
        }
        if (popupRef.current) {
          popupRef.current.remove();
          popupRef.current = null;
        }
      });
    }
  }, [hotspots, mapLoaded, onHotspotSelect]);

  // Highlight selected hotspot
  useEffect(() => {
    if (!map.current || !mapLoaded || !selectedHotspot?.lon || !selectedHotspot?.lat) return;

    // Fly to selected hotspot
    map.current.flyTo({
      center: [selectedHotspot.lon, selectedHotspot.lat],
      zoom: 14,
      duration: 1000,
    });
  }, [selectedHotspot, mapLoaded]);

  // Update overlay visibility
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    // In a real implementation, you would add tile overlay layers here
    // For now, we just track the state for the legend toggle
    // Example: map.current.setLayoutProperty('overlay-layer', 'visibility', showResidualOverlay ? 'visible' : 'none');
  }, [showResidualOverlay, mapLoaded]);

  // Update highlighted month
  useEffect(() => {
    if (!map.current || !mapLoaded || !currentMonth) return;

    // Filter hotspots to highlight current month
    const filter = ['==', ['get', 'month'], currentMonth];
    // In a real implementation, you would apply this filter to a separate layer
    // For now, we keep all hotspots visible
  }, [currentMonth, mapLoaded]);

  const handleExportMap = () => {
    if (!map.current) return;

    const canvas = map.current.getCanvas();
    canvas.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `siad-map-${new Date().toISOString().split('T')[0]}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  };

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Map Legend */}
      {mapLoaded && (
        <MapLegend
          showOverlay={showResidualOverlay}
          onToggleOverlay={setShowResidualOverlay}
          onExportMap={handleExportMap}
        />
      )}

      {/* Month Label */}
      {currentMonth && (
        <div className="absolute bottom-4 left-4 bg-panel border border-border rounded px-4 py-2 z-10">
          <p className="text-xs text-text-secondary mb-1">Current Month</p>
          <p className="text-sm font-semibold text-text-primary">{currentMonth}</p>
        </div>
      )}

      {!MAPBOX_TOKEN && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80 text-center p-8">
          <div>
            <p className="text-text-secondary mb-2">
              Mapbox token not configured
            </p>
            <p className="text-sm text-text-secondary">
              Set NEXT_PUBLIC_MAPBOX_TOKEN in .env.local
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
