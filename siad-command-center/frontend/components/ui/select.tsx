'use client';

import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  className?: string;
  label?: string;
}

export function Select({ value, onChange, options, className, label }: SelectProps) {
  return (
    <div className={cn('w-full', className)}>
      {label && (
        <label className="block text-sm text-text-secondary mb-2">{label}</label>
      )}
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-background border border-border rounded px-3 py-2 pr-10 text-text-primary appearance-none cursor-pointer hover:border-accent/50 transition-colors"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
      </div>
    </div>
  );
}
