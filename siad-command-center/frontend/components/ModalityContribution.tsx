'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { formatMonth } from '@/lib/utils';
import { getModalityDescription } from '@/lib/explanations';
import type { TileDetail } from '@/types';

interface ModalityContributionProps {
  tileDetail: TileDetail;
}

const MODALITY_COLORS: Record<string, string> = {
  SAR: '#22d3ee',
  Optical: '#fbbf24',
  VIIRS: '#fb923c',
  Lights: '#fb923c',
};

export default function ModalityContribution({ tileDetail }: ModalityContributionProps) {
  const { heatmap } = tileDetail;

  if (!heatmap || !heatmap.modalities || !heatmap.values) {
    return (
      <div className="text-center py-8 text-text-secondary">
        No modality data available
      </div>
    );
  }

  // Transform heatmap data into chart format
  const chartData = (heatmap.months || []).map((month, monthIdx) => {
    const dataPoint: any = {
      month: formatMonth(month),
    };

    heatmap.modalities.forEach((modality, modalityIdx) => {
      dataPoint[modality] = heatmap.values[modalityIdx]?.[monthIdx] || 0;
    });

    return dataPoint;
  });

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-text-primary mb-3">
        Modality Contribution Over Time
      </h3>

      <p className="text-sm text-text-secondary mb-4">
        Shows which sensor contributed most to anomaly detection each month.
        Higher values indicate stronger signal from that modality.
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="month"
            stroke="var(--text-secondary)"
            tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
          />
          <YAxis
            stroke="var(--text-secondary)"
            tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--panel)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
            }}
            formatter={(value: number) => value.toFixed(3)}
          />
          <Legend
            wrapperStyle={{ color: 'var(--text-primary)' }}
            iconType="square"
          />

          {heatmap.modalities.map((modality) => (
            <Bar
              key={modality}
              dataKey={modality}
              stackId="a"
              fill={MODALITY_COLORS[modality] || '#a3a3a3'}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {/* Modality Descriptions */}
      <div className="mt-4 space-y-2">
        {heatmap.modalities.map((modality) => (
          <div key={modality} className="flex items-start gap-2 text-xs">
            <div
              className="w-3 h-3 mt-0.5 rounded"
              style={{ backgroundColor: MODALITY_COLORS[modality] || '#a3a3a3' }}
            />
            <div>
              <span className="font-medium text-text-primary">{modality}:</span>{' '}
              <span className="text-text-secondary">
                {getModalityDescription(modality)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
