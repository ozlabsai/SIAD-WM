'use client';

import { cn } from '@/lib/utils';

interface SliderProps {
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  className?: string;
  label?: string;
}

export function Slider({
  value,
  min,
  max,
  step,
  onChange,
  className,
  label,
}: SliderProps) {
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className={cn('w-full', className)}>
      {label && (
        <div className="flex justify-between items-center mb-2">
          <label className="text-sm text-text-secondary">{label}</label>
          <span className="text-sm font-medium text-text-primary">{value}</span>
        </div>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, var(--accent) 0%, var(--accent) ${percentage}%, var(--border) ${percentage}%, var(--border) 100%)`,
        }}
      />
    </div>
  );
}
