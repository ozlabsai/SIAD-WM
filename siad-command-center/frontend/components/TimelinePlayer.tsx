'use client';

import { useEffect, useState } from 'react';
import { Play, Pause } from 'lucide-react';
import { formatMonth, cn } from '@/lib/utils';

interface TimelinePlayerProps {
  months: string[]; // e.g., ["2024-01", "2024-02", ...]
  currentMonth: string;
  onMonthChange: (month: string) => void;
  isPlaying: boolean;
  onPlayToggle: () => void;
  playbackSpeed: 1 | 2 | 4;
  onSpeedChange: (speed: 1 | 2 | 4) => void;
}

export default function TimelinePlayer({
  months,
  currentMonth,
  onMonthChange,
  isPlaying,
  onPlayToggle,
  playbackSpeed,
  onSpeedChange,
}: TimelinePlayerProps) {
  const currentIndex = months.indexOf(currentMonth);

  // Auto-advance when playing
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      const nextIndex = (currentIndex + 1) % months.length;
      onMonthChange(months[nextIndex]);
    }, 1000 / playbackSpeed);

    return () => clearInterval(interval);
  }, [isPlaying, currentIndex, months, playbackSpeed, onMonthChange]);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const index = parseInt(e.target.value);
    onMonthChange(months[index]);
  };

  return (
    <div className="h-20 bg-panel border-t border-border flex items-center px-6 gap-6">
      {/* Play/Pause Button */}
      <button
        onClick={onPlayToggle}
        className="flex items-center justify-center w-10 h-10 rounded bg-accent hover:bg-accent/90 transition-colors"
        aria-label={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? (
          <Pause className="w-5 h-5 text-background" />
        ) : (
          <Play className="w-5 h-5 text-background ml-0.5" />
        )}
      </button>

      {/* Current Month Display */}
      <div className="min-w-[120px]">
        <p className="text-xs text-text-secondary mb-1">Current Period</p>
        <p className="text-lg font-semibold text-text-primary">
          {formatMonth(currentMonth)}
        </p>
      </div>

      {/* Timeline Scrubber */}
      <div className="flex-1 flex flex-col">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-text-secondary">
            {formatMonth(months[0])}
          </span>
          <span className="text-xs text-text-secondary">
            {formatMonth(months[months.length - 1])}
          </span>
        </div>
        <input
          type="range"
          min="0"
          max={months.length - 1}
          value={currentIndex}
          onChange={handleSliderChange}
          className="w-full h-2 rounded-full appearance-none cursor-pointer bg-border"
          style={{
            background: `linear-gradient(to right, var(--accent) 0%, var(--accent) ${
              (currentIndex / (months.length - 1)) * 100
            }%, var(--border) ${
              (currentIndex / (months.length - 1)) * 100
            }%, var(--border) 100%)`,
          }}
        />
        {/* Month markers */}
        <div className="relative h-2 mt-1">
          {months.map((month, index) => (
            <div
              key={month}
              className={cn(
                'absolute w-1 h-1 rounded-full top-0',
                index === currentIndex ? 'bg-accent' : 'bg-border'
              )}
              style={{
                left: `${(index / (months.length - 1)) * 100}%`,
                transform: 'translateX(-50%)',
              }}
            />
          ))}
        </div>
      </div>

      {/* Playback Speed Selector */}
      <div className="flex items-center gap-2">
        <p className="text-xs text-text-secondary">Speed</p>
        <div className="flex gap-1">
          {[1, 2, 4].map((speed) => (
            <button
              key={speed}
              onClick={() => onSpeedChange(speed as 1 | 2 | 4)}
              className={cn(
                'px-3 py-1 text-sm rounded transition-colors',
                playbackSpeed === speed
                  ? 'bg-accent text-background font-semibold'
                  : 'bg-background text-text-secondary hover:text-text-primary'
              )}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
