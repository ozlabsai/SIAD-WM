'use client';

import { useMemo } from 'react';
import { ChevronLeft, ChevronRight, Download } from 'lucide-react';
import type { Hotspot, FilterState } from '@/types';
import {
  formatMonth,
  formatScore,
  getConfidenceColor,
  getAlertTypeColor,
  cn,
} from '@/lib/utils';
import FilterPanel from '@/components/FilterPanel';

interface DetectionsRailProps {
  hotspots: Hotspot[];
  selectedHotspot: Hotspot | null;
  onHotspotSelect: (hotspot: Hotspot) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  availableMonths: string[];
}

export default function DetectionsRail({
  hotspots,
  selectedHotspot,
  onHotspotSelect,
  isCollapsed,
  onToggleCollapse,
  filters,
  onFiltersChange,
  availableMonths,
}: DetectionsRailProps) {
  const sortedHotspots = useMemo(() => {
    return [...hotspots].sort((a, b) => b.score - a.score);
  }, [hotspots]);

  const handleExportGeoJSON = () => {
    const geojson = {
      type: 'FeatureCollection',
      features: sortedHotspots.map((hotspot) => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [hotspot.lon, hotspot.lat],
        },
        properties: {
          tileId: hotspot.tileId,
          score: hotspot.score,
          month: hotspot.month,
          changeType: hotspot.changeType,
          region: hotspot.region,
          confidence: hotspot.confidence,
          alertType: hotspot.alert_type,
        },
      })),
    };

    const blob = new Blob([JSON.stringify(geojson, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hotspots-${new Date().toISOString().split('T')[0]}.geojson`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportCSV = () => {
    const headers = [
      'Tile ID',
      'Score',
      'Latitude',
      'Longitude',
      'Month',
      'Change Type',
      'Region',
      'Confidence',
      'Alert Type',
    ];

    const rows = sortedHotspots.map((h) => [
      h.tileId,
      h.score.toFixed(3),
      h.lat.toFixed(6),
      h.lon.toFixed(6),
      h.month,
      h.changeType,
      h.region,
      h.confidence || 'Medium',
      h.alert_type || 'Activity',
    ]);

    const csv = [
      headers.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hotspots-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className={cn(
        'h-full bg-panel border-l border-border transition-all duration-300 flex flex-col',
        isCollapsed ? 'w-12' : 'w-[400px]'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        {!isCollapsed && (
          <h2 className="text-lg font-semibold text-text-primary">
            Detected Hotspots
          </h2>
        )}
        <button
          onClick={onToggleCollapse}
          className="p-2 hover:bg-background rounded transition-colors ml-auto"
          aria-label={isCollapsed ? 'Expand rail' : 'Collapse rail'}
        >
          {isCollapsed ? (
            <ChevronLeft className="w-5 h-5 text-text-secondary" />
          ) : (
            <ChevronRight className="w-5 h-5 text-text-secondary" />
          )}
        </button>
      </div>

      {/* Filter Panel */}
      {!isCollapsed && (
        <FilterPanel
          filters={filters}
          onFiltersChange={onFiltersChange}
          availableMonths={availableMonths}
        />
      )}

      {/* Content */}
      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto">
          {sortedHotspots.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-text-primary font-medium mb-2">
                No hotspots detected
              </p>
              <p className="text-sm text-text-secondary">
                Try adjusting your filters: expand date range, lower minimum
                score, or select &apos;All Types&apos;
              </p>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {sortedHotspots.map((hotspot) => (
                <HotspotCard
                  key={hotspot.tileId}
                  hotspot={hotspot}
                  isSelected={selectedHotspot?.tileId === hotspot.tileId}
                  onClick={() => onHotspotSelect(hotspot)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer with count and export buttons */}
      {!isCollapsed && sortedHotspots.length > 0 && (
        <div className="p-4 border-t border-border space-y-3">
          <p className="text-sm text-text-secondary">
            {sortedHotspots.length} hotspot
            {sortedHotspots.length !== 1 ? 's' : ''}
          </p>
          <div className="flex gap-2">
            <button
              data-testid="export-geojson"
              onClick={handleExportGeoJSON}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-background hover:bg-accent/20 border border-border hover:border-accent rounded text-sm text-text-primary transition-colors"
            >
              <Download className="w-4 h-4" />
              GeoJSON
            </button>
            <button
              data-testid="export-csv"
              onClick={handleExportCSV}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-background hover:bg-accent/20 border border-border hover:border-accent rounded text-sm text-text-primary transition-colors"
            >
              <Download className="w-4 h-4" />
              CSV
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

interface HotspotCardProps {
  hotspot: Hotspot;
  isSelected: boolean;
  onClick: () => void;
}

function HotspotCard({ hotspot, isSelected, onClick }: HotspotCardProps) {
  return (
    <div
      data-testid="hotspot-card"
      onClick={onClick}
      className={cn(
        'card cursor-pointer transition-all',
        isSelected && 'border-accent ring-1 ring-accent'
      )}
    >
      {/* Header with Tile ID and Score */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-sm font-mono text-text-secondary">
            {hotspot.tileId}
          </p>
          <p className="text-2xl font-semibold text-text-primary mt-1">
            {formatScore(hotspot.score)}
          </p>
        </div>
        <div className="flex flex-col gap-1 items-end">
          <span className={cn('badge', getConfidenceColor(hotspot.confidence || 'Medium'))}>
            {hotspot.confidence || 'Medium'}
          </span>
          <span className={cn('badge', getAlertTypeColor(hotspot.alert_type || 'Activity'))}>
            {hotspot.alert_type || 'Activity'}
          </span>
        </div>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p className="text-text-secondary">First Detected</p>
          <p className="text-text-primary font-medium">
            {formatMonth(hotspot.onset || hotspot.month)}
          </p>
        </div>
        <div>
          <p className="text-text-secondary">Change Type</p>
          <p className="text-text-primary font-medium capitalize">
            {hotspot.changeType}
          </p>
        </div>
      </div>

      {/* View Details hint */}
      {isSelected && (
        <div className="mt-3 pt-3 border-t border-border">
          <p className="text-xs text-accent">Selected - View on map</p>
        </div>
      )}
    </div>
  );
}
