'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import MapView from '@/components/MapView';
import DetectionsRail from '@/components/DetectionsRail';
import TimelinePlayer from '@/components/TimelinePlayer';
import TileDetailModal from '@/components/TileDetailModal';
import CaseNotesPanel from '@/components/CaseNotesPanel';
import { fetchAOI, fetchHotspots, fetchTileDetail } from '@/lib/api';
import type { Hotspot, FilterState, TileDetail } from '@/types';

export default function Dashboard() {
  // State
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);
  const [isRailCollapsed, setIsRailCollapsed] = useState(false);
  const [isCaseNotesPanelOpen, setIsCaseNotesPanelOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState('2024-01');
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<1 | 2 | 4>(1);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    minScore: 0.5,
    dateRange: null,
    alertType: 'All',
    confidence: 'All',
    minDuration: 0,
    searchQuery: '',
  });

  // Fetch tile detail for case notes panel
  const { data: tileDetail } = useQuery({
    queryKey: ['tileDetail', selectedHotspot?.tileId],
    queryFn: () => fetchTileDetail(selectedHotspot!.tileId),
    enabled: !!selectedHotspot && isCaseNotesPanelOpen,
  });

  // Fetch AOI metadata
  const { data: aoi, isLoading: aoiLoading } = useQuery({
    queryKey: ['aoi'],
    queryFn: fetchAOI,
  });

  // Fetch hotspots with current filters
  const { data: allHotspots = [], isLoading: hotspotsLoading } = useQuery({
    queryKey: ['hotspots', filters.minScore, 100],
    queryFn: () => fetchHotspots(filters.minScore, 100),
  });

  // Apply client-side filters
  const filteredHotspots = useMemo(() => {
    let filtered = allHotspots;

    // Filter by date range
    if (filters.dateRange) {
      const [start, end] = filters.dateRange;
      filtered = filtered.filter(
        (h) => h.month >= start && h.month <= end
      );
    }

    // Filter by alert type
    if (filters.alertType !== 'All') {
      filtered = filtered.filter((h) => h.alert_type === filters.alertType);
    }

    // Filter by confidence
    if (filters.confidence !== 'All') {
      filtered = filtered.filter((h) => h.confidence === filters.confidence);
    }

    // Filter by search query
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      filtered = filtered.filter((h) =>
        h.tileId.toLowerCase().includes(query)
      );
    }

    // Filter by current month (when timeline is active)
    if (currentMonth && isPlaying) {
      filtered = filtered.filter((h) => h.month === currentMonth);
    }

    return filtered;
  }, [allHotspots, filters, currentMonth, isPlaying]);

  // Generate month range from AOI data
  const months = useMemo(() => {
    if (!aoi?.timeRange) {
      return ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06',
              '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12'];
    }
    const [start, end] = aoi.timeRange;
    const months: string[] = [];
    const startDate = new Date(start + '-01');
    const endDate = new Date(end + '-01');

    let current = new Date(startDate);
    while (current <= endDate) {
      const year = current.getFullYear();
      const month = String(current.getMonth() + 1).padStart(2, '0');
      months.push(`${year}-${month}`);
      current.setMonth(current.getMonth() + 1);
    }

    return months;
  }, [aoi]);

  const isLoading = aoiLoading || hotspotsLoading;

  // Handle hotspot selection - open modal or case notes panel
  const handleHotspotSelect = (hotspot: Hotspot, openCaseNotes = false) => {
    setSelectedHotspot(hotspot);
    if (openCaseNotes) {
      setIsCaseNotesPanelOpen(true);
    } else {
      setIsModalOpen(true);
    }
  };

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-accent animate-spin" />
          <p className="text-text-secondary">Loading hotspots...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background">
        {/* Header */}
        <header className="h-16 bg-panel border-b border-border flex items-center px-6">
        <h1 className="text-xl font-semibold text-text-primary">
          SIAD: Infrastructure Acceleration Detector
        </h1>
        {aoi && (
          <div className="ml-auto flex items-center gap-6 text-sm text-text-secondary">
            <div>
              <span className="font-medium">{aoi.name}</span>
            </div>
            <div>
              <span className="font-medium">{aoi.tileCount}</span> tiles
            </div>
            <div>
              <span className="font-medium">{filteredHotspots.length}</span> hotspots
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map View */}
        <div className="flex-1">
          <MapView
            hotspots={filteredHotspots}
            selectedHotspot={selectedHotspot}
            onHotspotSelect={handleHotspotSelect}
            currentMonth={currentMonth}
          />
        </div>

        {/* Detections Rail */}
        <DetectionsRail
          hotspots={filteredHotspots}
          selectedHotspot={selectedHotspot}
          onHotspotSelect={handleHotspotSelect}
          isCollapsed={isRailCollapsed}
          onToggleCollapse={() => setIsRailCollapsed(!isRailCollapsed)}
          filters={filters}
          onFiltersChange={setFilters}
          availableMonths={months}
        />
      </div>

      {/* Timeline Player */}
      <TimelinePlayer
        months={months}
        currentMonth={currentMonth}
        onMonthChange={setCurrentMonth}
        isPlaying={isPlaying}
        onPlayToggle={() => setIsPlaying(!isPlaying)}
        playbackSpeed={playbackSpeed}
        onSpeedChange={setPlaybackSpeed}
      />

      {/* Tile Detail Modal */}
      <TileDetailModal
        tileId={selectedHotspot?.tileId || null}
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
      />

      {/* Case Notes Panel */}
      <CaseNotesPanel
        hotspot={selectedHotspot}
        tileDetail={tileDetail || null}
        isOpen={isCaseNotesPanelOpen}
        onClose={() => setIsCaseNotesPanelOpen(false)}
      />
    </div>
  );
}
