'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Label,
} from 'recharts';
import { formatMonth } from '@/lib/utils';
import type { TileDetail } from '@/types';

interface ChangeTimelineProps {
  tileDetail: TileDetail;
}

export default function ChangeTimeline({ tileDetail }: ChangeTimelineProps) {
  const { timeline } = tileDetail;

  if (!timeline || timeline.length === 0) {
    return (
      <div className="text-center py-8 text-text-secondary">
        No timeline data available
      </div>
    );
  }

  // Find onset (first significant detection) and peak
  const onsetPoint = timeline[0];
  const peakPoint = timeline.reduce((max, point) =>
    point.score > max.score ? point : max
  );
  const onsetIndex = 0;
  const peakIndex = timeline.indexOf(peakPoint);

  // Prepare chart data
  const chartData = timeline.map((point, index) => ({
    month: formatMonth(point.month),
    score: point.score,
    isOnset: index === onsetIndex,
    isPeak: index === peakIndex,
    index,
  }));

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-text-primary mb-3">
        Change Timeline
      </h3>

      {/* Timeline Metrics */}
      <div className="grid grid-cols-4 gap-4 mb-4 text-sm">
        <div>
          <p className="text-text-secondary">Onset Month</p>
          <p className="text-text-primary font-medium">{formatMonth(onsetPoint.month)}</p>
        </div>
        <div>
          <p className="text-text-secondary">Peak Month</p>
          <p className="text-text-primary font-medium">{formatMonth(peakPoint.month)}</p>
        </div>
        <div>
          <p className="text-text-secondary">Peak Score</p>
          <p className="text-text-primary font-medium">{peakPoint.score.toFixed(3)}</p>
        </div>
        <div>
          <p className="text-text-secondary">Duration</p>
          <p className="text-text-primary font-medium">{timeline.length} months</p>
        </div>
      </div>

      {/* Timeline Chart */}
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
            </linearGradient>
          </defs>
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

          {/* Onset marker */}
          <ReferenceLine
            x={chartData[onsetIndex].month}
            stroke="#fbbf24"
            strokeDasharray="3 3"
            label={{
              value: 'Onset',
              position: 'top',
              fill: '#fbbf24',
              fontSize: 11,
            }}
          />

          {/* Peak marker */}
          <ReferenceLine
            x={chartData[peakIndex].month}
            stroke="#ef4444"
            strokeDasharray="3 3"
            label={{
              value: 'Peak',
              position: 'top',
              fill: '#ef4444',
              fontSize: 11,
            }}
          />

          <Area
            type="monotone"
            dataKey="score"
            stroke="#22d3ee"
            strokeWidth={2}
            fill="url(#scoreGradient)"
            dot={(props: any) => {
              const { cx, cy, payload, key } = props;
              if (payload.isPeak) {
                return (
                  <circle
                    key={key}
                    cx={cx}
                    cy={cy}
                    r={5}
                    fill="#ef4444"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                );
              }
              if (payload.isOnset) {
                return (
                  <circle
                    key={key}
                    cx={cx}
                    cy={cy}
                    r={4}
                    fill="#fbbf24"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                );
              }
              return <circle key={key} cx={cx} cy={cy} r={3} fill="#22d3ee" />;
            }}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Timeline Phases */}
      <div className="mt-4 flex items-center gap-6 text-xs text-text-secondary">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#fbbf24]" />
          <span>Onset Detection</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
          <span>Peak Anomaly</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-12 h-0.5 bg-[#22d3ee]" />
          <span>Anomaly Period</span>
        </div>
      </div>
    </div>
  );
}
