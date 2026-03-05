'use client';

import { useState } from 'react';
import { Filter, X } from 'lucide-react';
import { Slider } from '@/components/ui/slider';
import { Select } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import type { FilterState } from '@/types';

interface FilterPanelProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  availableMonths: string[];
}

export default function FilterPanel({
  filters,
  onFiltersChange,
  availableMonths,
}: FilterPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const handleClearFilters = () => {
    onFiltersChange({
      minScore: 0.5,
      dateRange: null,
      alertType: 'All',
      confidence: 'All',
      minDuration: 0,
      searchQuery: '',
    });
  };

  const hasActiveFilters =
    filters.minScore !== 0.5 ||
    filters.dateRange !== null ||
    filters.alertType !== 'All' ||
    filters.confidence !== 'All' ||
    filters.minDuration > 0 ||
    filters.searchQuery !== '';

  return (
    <div className="border-b border-border bg-panel">
      {/* Filter Header */}
      <div className="flex items-center justify-between p-3">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm font-medium text-text-primary hover:text-accent transition-colors"
        >
          <Filter className="w-4 h-4" />
          <span>Filters</span>
          {hasActiveFilters && (
            <span className="ml-2 px-2 py-0.5 bg-accent/20 text-accent text-xs rounded">
              Active
            </span>
          )}
        </button>
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="text-xs text-text-secondary hover:text-text-primary transition-colors flex items-center gap-1"
          >
            <X className="w-3 h-3" />
            Clear all
          </button>
        )}
      </div>

      {/* Filter Controls */}
      {isExpanded && (
        <div className="px-3 pb-4 space-y-4">
          {/* Score Threshold */}
          <Slider
            value={filters.minScore}
            min={0}
            max={1}
            step={0.05}
            onChange={(value) =>
              onFiltersChange({ ...filters, minScore: value })
            }
            label="Minimum Score"
          />

          {/* Date Range */}
          <div>
            <label className="block text-sm text-text-secondary mb-2">
              Date Range
            </label>
            <div className="grid grid-cols-2 gap-2">
              <Select
                value={filters.dateRange?.[0] || 'All'}
                onChange={(value) =>
                  onFiltersChange({
                    ...filters,
                    dateRange:
                      value === 'All'
                        ? null
                        : [value, filters.dateRange?.[1] || availableMonths[availableMonths.length - 1]],
                  })
                }
                options={[
                  { value: 'All', label: 'Start' },
                  ...availableMonths.map((m) => ({ value: m, label: m })),
                ]}
              />
              <Select
                value={filters.dateRange?.[1] || 'All'}
                onChange={(value) =>
                  onFiltersChange({
                    ...filters,
                    dateRange:
                      value === 'All'
                        ? null
                        : [filters.dateRange?.[0] || availableMonths[0], value],
                  })
                }
                options={[
                  { value: 'All', label: 'End' },
                  ...availableMonths.map((m) => ({ value: m, label: m })),
                ]}
              />
            </div>
          </div>

          {/* Alert Type */}
          <Select
            value={filters.alertType}
            onChange={(value) =>
              onFiltersChange({
                ...filters,
                alertType: value as FilterState['alertType'],
              })
            }
            options={[
              { value: 'All', label: 'All Types' },
              { value: 'Activity', label: 'Activity' },
              { value: 'Structural', label: 'Structural' },
            ]}
            label="Alert Type"
          />

          {/* Confidence Level */}
          <Select
            value={filters.confidence}
            onChange={(value) =>
              onFiltersChange({
                ...filters,
                confidence: value as FilterState['confidence'],
              })
            }
            options={[
              { value: 'All', label: 'All Confidence Levels' },
              { value: 'High', label: 'High Confidence' },
              { value: 'Medium', label: 'Medium Confidence' },
              { value: 'Low', label: 'Low Confidence' },
            ]}
            label="Confidence Level"
          />

          {/* Search by Tile ID */}
          <Input
            type="text"
            placeholder="Search by Tile ID..."
            value={filters.searchQuery}
            onChange={(e) =>
              onFiltersChange({ ...filters, searchQuery: e.target.value })
            }
            label="Search"
          />
        </div>
      )}
    </div>
  );
}
