'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Download } from 'lucide-react';

interface MapLegendProps {
  showOverlay: boolean;
  onToggleOverlay: (show: boolean) => void;
  onExportMap?: () => void;
}

export default function MapLegend({
  showOverlay,
  onToggleOverlay,
  onExportMap,
}: MapLegendProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="absolute top-4 right-4 z-10 bg-panel border border-border rounded-lg shadow-lg min-w-[200px]">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-border">
        <span className="text-sm font-semibold text-text-primary">Legend</span>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-1 hover:bg-background rounded transition-colors"
        >
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-text-secondary" />
          ) : (
            <ChevronDown className="w-4 h-4 text-text-secondary" />
          )}
        </button>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-3 space-y-4">
          {/* Score Color Scale */}
          <div>
            <p className="text-xs text-text-secondary mb-2">Anomaly Score</p>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-[#ef4444]" />
                <span className="text-xs text-text-primary">0.7 - 1.0 High</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-[#fbbf24]" />
                <span className="text-xs text-text-primary">0.5 - 0.7 Medium</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-[#22d3ee]" />
                <span className="text-xs text-text-primary">0.0 - 0.5 Low</span>
              </div>
            </div>
          </div>

          {/* Residual Overlay Toggle */}
          <div className="pt-3 border-t border-border">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-xs text-text-secondary">Show Residual Overlay</span>
              <input
                type="checkbox"
                checked={showOverlay}
                onChange={(e) => onToggleOverlay(e.target.checked)}
                className="w-4 h-4 rounded bg-background border-border accent-accent cursor-pointer"
              />
            </label>
          </div>

          {/* Marker Size Info */}
          <div className="pt-3 border-t border-border">
            <p className="text-xs text-text-secondary mb-2">Marker Size</p>
            <p className="text-xs text-text-primary">
              Larger markers indicate higher anomaly scores
            </p>
          </div>

          {/* Export Map Button */}
          {onExportMap && (
            <div className="pt-3 border-t border-border">
              <button
                onClick={onExportMap}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-background hover:bg-accent/20 border border-border hover:border-accent rounded text-xs text-text-primary transition-colors"
              >
                <Download className="w-3 h-3" />
                Export Map as PNG
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
