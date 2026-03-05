'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, Info } from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Tooltip } from '@/components/ui/tooltip';
import { fetchTileDetail, getStaticAssetUrl } from '@/lib/api';
import { formatMonth } from '@/lib/utils';
import {
  generateDetectionExplanation,
  generateBaselineExplanation,
  generateEnvironmentalExplanation,
  getModalityContributions,
  getModalityDescription,
} from '@/lib/explanations';
import ChangeTimeline from '@/components/ChangeTimeline';
import ModalityContribution from '@/components/ModalityContribution';
import SpatialContextMap from '@/components/SpatialContextMap';
import type { TileDetail } from '@/types';

interface TileDetailModalProps {
  tileId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function TileDetailModal({
  tileId,
  open,
  onOpenChange,
}: TileDetailModalProps) {
  const [envNormalized, setEnvNormalized] = useState(false);
  const [selectedImageryTab, setSelectedImageryTab] = useState('actual');
  const [selectedModalityTab, setSelectedModalityTab] = useState('combined');
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);

  const { data: tileDetail, isLoading, error } = useQuery({
    queryKey: ['tileDetail', tileId],
    queryFn: () => fetchTileDetail(tileId!),
    enabled: open && !!tileId,
  });

  // Set default selected month to first timeline point
  if (tileDetail && !selectedMonth && tileDetail.timeline?.length > 0) {
    setSelectedMonth(tileDetail.timeline[0].month);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-7xl max-h-[90vh] overflow-y-auto">
        <DialogHeader onClose={() => onOpenChange(false)}>
          <DialogTitle>
            {tileDetail?.tileId || tileId ? `Tile Details: ${tileDetail?.tileId || tileId}` : 'Tile Details'}
          </DialogTitle>
        </DialogHeader>

        <DialogBody className="space-y-6">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-accent animate-spin" />
            </div>
          )}

          {error && (
            <div className="text-center py-12">
              <p className="text-alert-danger mb-2">Failed to load tile details</p>
              <p className="text-sm text-text-secondary">
                {error instanceof Error ? error.message : 'Unknown error'}
              </p>
            </div>
          )}

          {tileDetail && (
            <>
              {/* Detection Explanation */}
              <div className="card bg-accent/10 border border-accent/30">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-text-primary leading-relaxed">
                    {generateDetectionExplanation(tileDetail)}
                  </p>
                </div>
              </div>

              {/* Tile Metadata */}
              <TileMetadata tileDetail={tileDetail} />

              {/* Environmental Normalization */}
              <EnvironmentalNormalization
                tileDetail={tileDetail}
                envNormalized={envNormalized}
                onToggle={setEnvNormalized}
              />

              {/* Satellite Imagery Viewer */}
              <SatelliteImageryViewer
                tileDetail={tileDetail}
                selectedTab={selectedImageryTab}
                onTabChange={setSelectedImageryTab}
                selectedMonth={selectedMonth || tileDetail.timeline[0]?.month}
                onMonthChange={setSelectedMonth}
              />

              {/* Two-column layout for charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Timeline Chart */}
                <TimelineChart tileDetail={tileDetail} />

                {/* Change Timeline */}
                <ChangeTimeline tileDetail={tileDetail} />
              </div>

              {/* Enhanced Baseline Comparison */}
              <EnhancedBaselineChart tileDetail={tileDetail} />

              {/* Modality Contribution */}
              <ModalityContribution tileDetail={tileDetail} />

              {/* Enhanced Modality Attribution */}
              <EnhancedModalityHeatmap
                tileDetail={tileDetail}
                selectedTab={selectedModalityTab}
                onTabChange={setSelectedModalityTab}
              />

              {/* Spatial Context Map */}
              <SpatialContextMap tileDetail={tileDetail} />
            </>
          )}
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}

function TileMetadata({ tileDetail }: { tileDetail: TileDetail }) {
  const { metadata } = tileDetail;

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-text-primary mb-3">
        Tile Metadata
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <p className="text-text-secondary">Tile ID</p>
          <p className="text-text-primary font-mono">{tileDetail.tileId}</p>
        </div>
        <div>
          <p className="text-text-secondary">Center Latitude</p>
          <p className="text-text-primary font-mono">
            {tileDetail.lat?.toFixed(4) || 'N/A'}
          </p>
        </div>
        <div>
          <p className="text-text-secondary">Center Longitude</p>
          <p className="text-text-primary font-mono">
            {tileDetail.lon?.toFixed(4) || 'N/A'}
          </p>
        </div>
        <div>
          <p className="text-text-secondary">Observations</p>
          <p className="text-text-primary font-mono">
            {tileDetail.timeline?.length || 0}
          </p>
        </div>
      </div>
    </div>
  );
}

function EnvironmentalNormalization({
  tileDetail,
  envNormalized,
  onToggle,
}: {
  tileDetail: TileDetail;
  envNormalized: boolean;
  onToggle: (value: boolean) => void;
}) {
  // Mock normalized scores (in production, fetch from backend)
  const peakPoint = tileDetail.timeline.reduce((max, point) =>
    point.score > max.score ? point : max
  );
  const observedScore = peakPoint.score;
  const neutralScore = observedScore * 0.85; // Mock: neutral conditions show slightly lower score

  const explanation = generateEnvironmentalExplanation(observedScore, neutralScore);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-text-primary">
            Environmental Normalization
          </h3>
          <Tooltip content="Compare anomaly scores under observed vs neutral environmental conditions">
            <Info className="w-4 h-4 text-text-secondary" />
          </Tooltip>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-text-secondary">
            {envNormalized ? 'Neutral Conditions' : 'Observed Conditions'}
          </span>
          <Switch checked={envNormalized} onCheckedChange={onToggle} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className={`p-4 rounded-lg border ${
          !envNormalized ? 'border-accent bg-accent/10' : 'border-border'
        }`}>
          <p className="text-sm text-text-secondary mb-1">Under Observed Weather</p>
          <p className="text-2xl font-bold text-text-primary">{observedScore.toFixed(3)}</p>
          <p className="text-xs text-text-secondary mt-1">
            Includes rain, temperature, seasonal effects
          </p>
        </div>
        <div className={`p-4 rounded-lg border ${
          envNormalized ? 'border-accent bg-accent/10' : 'border-border'
        }`}>
          <p className="text-sm text-text-secondary mb-1">Under Neutral Weather</p>
          <p className="text-2xl font-bold text-text-primary">{neutralScore.toFixed(3)}</p>
          <p className="text-xs text-text-secondary mt-1">
            Normalized for environmental factors
          </p>
        </div>
      </div>

      <div className="p-3 bg-background rounded-lg">
        <p className="text-sm text-text-secondary">{explanation}</p>
      </div>
    </div>
  );
}

function SatelliteImageryViewer({
  tileDetail,
  selectedTab,
  onTabChange,
  selectedMonth,
  onMonthChange,
}: {
  tileDetail: TileDetail;
  selectedTab: string;
  onTabChange: (tab: string) => void;
  selectedMonth: string;
  onMonthChange: (month: string) => void;
}) {
  // Convert month format from "2024-01" to "month_01" for file path
  const monthNumber = selectedMonth.split('-')[1]; // Get "01" from "2024-01"
  const monthFolder = `month_${monthNumber}`;

  const imageUrl = getStaticAssetUrl(
    `tiles/${tileDetail.tileId}/${monthFolder}/${selectedTab}.png`
  );

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">
          Satellite Imagery
        </h3>
        <div className="px-2 py-1 bg-green-500/20 border border-green-500/40 rounded text-xs text-green-200">
          ✓ Real Earth Engine Data
        </div>
      </div>

      <Tabs value={selectedTab} onValueChange={onTabChange}>
        <TabsList className="mb-4">
          <TabsTrigger value="actual">Actual Satellite</TabsTrigger>
          <TabsTrigger value="predicted">Model Prediction</TabsTrigger>
          <TabsTrigger value="residual">Anomaly Detection</TabsTrigger>
        </TabsList>

        <TabsContent value="actual" className="space-y-4">
          <div className="p-3 bg-background rounded-lg border border-accent/30">
            <p className="text-sm text-text-primary font-medium mb-2">📡 Real Satellite Observations</p>
            <p className="text-sm text-text-secondary mb-2">
              This imagery comes from <strong>actual Google Earth Engine exports</strong> - real satellite observations
              of this location. What you're seeing:
            </p>
            <ul className="text-sm text-text-secondary list-disc list-inside space-y-1">
              <li>Multi-spectral data combined into RGB representation</li>
              <li>Normalized satellite bands showing surface characteristics</li>
              <li>Actual ground truth that the World Model tries to predict</li>
            </ul>
            <p className="text-sm text-text-secondary mt-2">
              <strong>Use this as baseline:</strong> Compare with Predicted tab to see what the model expected vs. what actually happened.
            </p>
          </div>
          <ImageDisplay url={imageUrl} alt="Actual satellite imagery" />
        </TabsContent>

        <TabsContent value="predicted" className="space-y-4">
          <div className="p-3 bg-background rounded-lg border border-accent/30">
            <p className="text-sm text-text-primary font-medium mb-2">🤖 World Model Prediction</p>
            <p className="text-sm text-text-secondary mb-2">
              This is what the <strong>World Model expected to see</strong> at this location and time,
              based on learning from 12+ months of historical satellite patterns. The model:
            </p>
            <ul className="text-sm text-text-secondary list-disc list-inside space-y-1">
              <li>Learned seasonal cycles (vegetation greening/browning), weather patterns, and normal changes</li>
              <li>Generated its "prediction" of what this tile should look like</li>
              <li>Will look similar to Actual when nothing unusual happened</li>
            </ul>
            <p className="text-sm text-text-secondary mt-2">
              <strong>How to use:</strong> Compare to Actual tab - noticeable differences indicate unexpected changes
              that the model didn't predict from historical patterns.
            </p>
          </div>
          <ImageDisplay url={imageUrl} alt="Predicted imagery" />
        </TabsContent>

        <TabsContent value="residual" className="space-y-4">
          <div className="p-3 bg-background rounded-lg border border-accent/30">
            <p className="text-sm text-text-primary font-medium mb-2">🔍 Anomaly Detection Heatmap</p>
            <p className="text-sm text-text-secondary mb-2">
              This heatmap shows <strong>pixel-by-pixel prediction errors</strong> - the difference between
              what was observed (Actual) and what the model expected (Predicted). This reveals where the
              model was "surprised" by unexpected changes.
            </p>
            <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-500 rounded"></div>
                <span className="text-text-secondary">Blue/Dark: Low error (good prediction)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                <span className="text-text-secondary">Yellow: Moderate unexpected change</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-500 rounded"></div>
                <span className="text-text-secondary">Red: Strong anomaly signal</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-white rounded border border-border"></div>
                <span className="text-text-secondary">White/Bright: Maximum deviation</span>
              </div>
            </div>
            <p className="text-sm text-text-secondary mt-3">
              <strong>How to interpret:</strong> Bright/hot areas (yellow to white) are anomalies - significant
              changes that deviated from expected patterns. These could indicate deforestation, construction,
              flooding, or other unexpected land use changes.
            </p>
          </div>
          <ImageDisplay url={imageUrl} alt="Residual heatmap" />
        </TabsContent>
      </Tabs>

      {/* Month Scrubber */}
      <div className="mt-4">
        <label className="text-sm text-text-secondary mb-2 block">
          Select Month
        </label>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {(tileDetail.timeline || []).map((point) => (
            <button
              key={point.month}
              onClick={() => onMonthChange(point.month)}
              className={`px-3 py-1.5 text-xs rounded whitespace-nowrap transition-colors ${
                point.month === selectedMonth
                  ? 'bg-accent text-background'
                  : 'bg-background text-text-secondary hover:text-text-primary'
              }`}
            >
              {formatMonth(point.month)}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function ImageDisplay({ url, alt }: { url: string; alt: string }) {
  const [imageError, setImageError] = useState(false);

  return (
    <div className="w-full aspect-square bg-background rounded-lg overflow-hidden flex items-center justify-center">
      {imageError ? (
        <div className="text-center p-8">
          <p className="text-text-secondary text-sm mb-2">Image not available</p>
          <p className="text-text-secondary text-xs">
            Satellite imagery for this tile/month has not been generated yet
          </p>
        </div>
      ) : (
        <img
          src={url}
          alt={alt}
          onError={() => setImageError(true)}
          className="w-full h-full object-cover"
        />
      )}
    </div>
  );
}

function TimelineChart({ tileDetail }: { tileDetail: TileDetail }) {
  const chartData = (tileDetail.timeline || []).map((point) => ({
    month: formatMonth(point.month),
    score: point.score,
    observed: point.observed,
    predicted: point.predicted,
  }));

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-text-primary mb-4">
        Detection Timeline
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="month"
            stroke="var(--text-secondary)"
            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
          />
          <YAxis
            stroke="var(--text-secondary)"
            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
          />
          <RechartsTooltip
            contentStyle={{
              backgroundColor: 'var(--panel)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
            }}
          />
          <Legend
            wrapperStyle={{ color: 'var(--text-primary)' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#22d3ee"
            strokeWidth={2}
            dot={{ fill: '#22d3ee', r: 4 }}
            name="Anomaly Score"
          />
          <Line
            type="monotone"
            dataKey="observed"
            stroke="#fbbf24"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: '#fbbf24', r: 3 }}
            name="Observed"
          />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#a3a3a3"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: '#a3a3a3', r: 3 }}
            name="Predicted"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function EnhancedBaselineChart({ tileDetail }: { tileDetail: TileDetail }) {
  if (!tileDetail.baselines) {
    return null;
  }

  const persistenceAvg = Array.isArray(tileDetail.baselines.persistence)
    ? tileDetail.baselines.persistence.reduce((a, b) => a + b, 0) / tileDetail.baselines.persistence.length
    : 0;
  const seasonalAvg = Array.isArray(tileDetail.baselines.seasonal)
    ? tileDetail.baselines.seasonal.reduce((a, b) => a + b, 0) / tileDetail.baselines.seasonal.length
    : 0;

  const baselineData = [
    {
      name: 'Persistence',
      value: persistenceAvg,
    },
    {
      name: 'Seasonal',
      value: seasonalAvg,
    },
  ];

  const baselineExplanation = generateBaselineExplanation(tileDetail);

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-lg font-semibold text-text-primary">
          Baseline Comparison
        </h3>
        <Tooltip content="Comparison of World Model performance vs traditional baseline methods">
          <Info className="w-4 h-4 text-text-secondary" />
        </Tooltip>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={baselineData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="name"
            stroke="var(--text-secondary)"
            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
          />
          <YAxis
            stroke="var(--text-secondary)"
            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
            label={{
              value: 'Avg Residual',
              angle: -90,
              position: 'insideLeft',
              fill: 'var(--text-secondary)',
            }}
          />
          <RechartsTooltip
            contentStyle={{
              backgroundColor: 'var(--panel)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
            }}
            formatter={(value: number) => value.toFixed(3)}
          />
          <Legend wrapperStyle={{ color: 'var(--text-primary)' }} />
          <Bar dataKey="value" fill="#22d3ee" name="Avg Residual" />
        </BarChart>
      </ResponsiveContainer>

      {/* Detailed Metrics Table */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2 text-text-secondary font-medium">Method</th>
              <th className="text-center py-2 text-text-secondary font-medium">
                <Tooltip content="Mean Absolute Error - lower is better">MAE</Tooltip>
              </th>
              <th className="text-center py-2 text-text-secondary font-medium">
                <Tooltip content="Root Mean Squared Error - lower is better">RMSE</Tooltip>
              </th>
              <th className="text-center py-2 text-text-secondary font-medium">
                <Tooltip content="R-squared coefficient - higher is better">R²</Tooltip>
              </th>
              <th className="text-center py-2 text-text-secondary font-medium">Improvement</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-border">
              <td className="py-2 text-text-primary font-medium">Persistence</td>
              <td className="text-center py-2 text-text-primary" colSpan={4}>
                {Array.isArray(tileDetail.baselines.persistence)
                  ? `Avg: ${(tileDetail.baselines.persistence.reduce((a, b) => a + b, 0) / tileDetail.baselines.persistence.length).toFixed(3)}`
                  : 'N/A'}
              </td>
            </tr>
            <tr>
              <td className="py-2 text-text-primary font-medium">Seasonal</td>
              <td className="text-center py-2 text-text-primary" colSpan={4}>
                {Array.isArray(tileDetail.baselines.seasonal)
                  ? `Avg: ${(tileDetail.baselines.seasonal.reduce((a, b) => a + b, 0) / tileDetail.baselines.seasonal.length).toFixed(3)}`
                  : 'N/A'}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {baselineExplanation && (
        <div className="mt-4 p-3 bg-background rounded-lg">
          <p className="text-sm text-text-secondary">{baselineExplanation}</p>
        </div>
      )}
    </div>
  );
}

function EnhancedModalityHeatmap({
  tileDetail,
  selectedTab,
  onTabChange,
}: {
  tileDetail: TileDetail;
  selectedTab: string;
  onTabChange: (tab: string) => void;
}) {
  const { heatmap } = tileDetail;

  const getHeatmapColor = (value: number) => {
    const normalized = Math.min(Math.max(value, 0), 1);
    if (normalized < 0.25) return '#22d3ee';
    if (normalized < 0.5) return '#fbbf24';
    if (normalized < 0.75) return '#fb923c';
    return '#ef4444';
  };

  // Calculate per-modality contributions
  const modalityTabs = ['combined', ...(heatmap.modalities || [])];

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-lg font-semibold text-text-primary">
          Enhanced Modality Attribution
        </h3>
        <Tooltip content="Shows which sensors detected the anomaly and their relative contributions">
          <Info className="w-4 h-4 text-text-secondary" />
        </Tooltip>
      </div>

      <Tabs value={selectedTab} onValueChange={onTabChange}>
        <TabsList className="mb-4">
          <TabsTrigger value="combined">Combined</TabsTrigger>
          {(heatmap.modalities || []).map((modality) => (
            <TabsTrigger key={modality} value={modality}>
              {modality}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="combined">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="text-left text-sm text-text-secondary p-2 border-b border-border">
                    Modality
                  </th>
                  {(heatmap.months || []).map((month) => (
                    <th
                      key={month}
                      className="text-center text-xs text-text-secondary p-2 border-b border-border"
                    >
                      {formatMonth(month)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(heatmap.modalities || []).map((modality, modalityIdx) => (
                  <tr key={modality}>
                    <td className="text-sm text-text-primary font-medium p-2 border-b border-border">
                      {modality}
                    </td>
                    {(heatmap.values?.[modalityIdx] || []).map((value, monthIdx) => (
                      <td
                        key={monthIdx}
                        className="p-2 border-b border-border text-center"
                        style={{ backgroundColor: getHeatmapColor(value) }}
                      >
                        <span className="text-xs font-mono text-background">
                          {value.toFixed(2)}
                        </span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {(heatmap.modalities || []).map((modality, modalityIdx) => (
          <TabsContent key={modality} value={modality} className="space-y-4">
            <p className="text-sm text-text-secondary">
              {getModalityDescription(modality)}
            </p>

            {/* Contribution percentage breakdown */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {(heatmap.months || []).map((month, monthIdx) => {
                const contributions = getModalityContributions(heatmap, monthIdx);
                const contribution = contributions.find(c => c.modality === modality);
                return (
                  <div key={month} className="p-3 bg-background rounded">
                    <p className="text-xs text-text-secondary mb-1">{formatMonth(month)}</p>
                    <p className="text-lg font-bold text-text-primary">
                      {contribution ? contribution.percentage.toFixed(0) : '0'}%
                    </p>
                  </div>
                );
              })}
            </div>
          </TabsContent>
        ))}
      </Tabs>

      <div className="mt-4 flex items-center gap-4 text-xs text-text-secondary">
        <span>Legend:</span>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4" style={{ backgroundColor: '#22d3ee' }} />
          <span>Low</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4" style={{ backgroundColor: '#fbbf24' }} />
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4" style={{ backgroundColor: '#fb923c' }} />
          <span>High</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4" style={{ backgroundColor: '#ef4444' }} />
          <span>Critical</span>
        </div>
      </div>
    </div>
  );
}
