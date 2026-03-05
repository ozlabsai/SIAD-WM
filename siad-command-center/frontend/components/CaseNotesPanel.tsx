'use client';

import { useState, useEffect } from 'react';
import { X, Save, Star } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { formatMonth } from '@/lib/utils';
import type { Hotspot, TileDetail } from '@/types';

interface CaseNotesPanelProps {
  hotspot: Hotspot | null;
  tileDetail: TileDetail | null;
  isOpen: boolean;
  onClose: () => void;
}

interface CaseNote {
  tileId: string;
  notes: string;
  classification: string;
  confidence: number;
  lastUpdated: string;
}

const CHANGE_CLASSIFICATIONS = [
  'Unclassified',
  'Construction',
  'Demolition',
  'Environmental Change',
  'Agricultural Development',
  'Infrastructure Development',
  'Deforestation',
  'Mining Activity',
  'Urban Expansion',
  'False Positive',
];

export default function CaseNotesPanel({
  hotspot,
  tileDetail,
  isOpen,
  onClose,
}: CaseNotesPanelProps) {
  const [notes, setNotes] = useState('');
  const [classification, setClassification] = useState('Unclassified');
  const [confidence, setConfidence] = useState(3);
  const [isSaving, setIsSaving] = useState(false);

  // Load saved notes from localStorage
  useEffect(() => {
    if (!hotspot) return;

    const savedNotes = loadCaseNote(hotspot.tileId);
    if (savedNotes) {
      setNotes(savedNotes.notes);
      setClassification(savedNotes.classification);
      setConfidence(savedNotes.confidence);
    } else {
      // Reset to defaults
      setNotes('');
      setClassification('Unclassified');
      setConfidence(3);
    }
  }, [hotspot]);

  const handleSave = () => {
    if (!hotspot) return;

    setIsSaving(true);
    const caseNote: CaseNote = {
      tileId: hotspot.tileId,
      notes,
      classification,
      confidence,
      lastUpdated: new Date().toISOString(),
    };

    saveCaseNote(caseNote);

    setTimeout(() => {
      setIsSaving(false);
    }, 500);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-16 bottom-0 w-96 bg-panel border-l border-border
      shadow-xl z-40 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h2 className="text-lg font-semibold text-text-primary">Case Notes</h2>
        <button
          onClick={onClose}
          className="text-text-secondary hover:text-text-primary transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {hotspot && (
          <>
            {/* Hotspot Summary */}
            <div className="card">
              <h3 className="text-sm font-semibold text-text-primary mb-2">
                Hotspot Summary
              </h3>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Tile ID:</span>
                  <span className="text-text-primary font-mono">{hotspot.tileId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Score:</span>
                  <span className="text-text-primary">{hotspot.score.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Onset:</span>
                  <span className="text-text-primary">{formatMonth(hotspot.month)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Location:</span>
                  <span className="text-text-primary">
                    {hotspot.lat.toFixed(4)}, {hotspot.lon.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>

            {/* Timeline Events */}
            {tileDetail && (
              <div className="card">
                <h3 className="text-sm font-semibold text-text-primary mb-2">
                  Key Events
                </h3>
                <div className="space-y-2">
                  {tileDetail.timeline.map((point, idx) => {
                    const isOnset = idx === 0;
                    const isPeak = point.score === Math.max(...tileDetail.timeline.map(p => p.score));

                    if (isOnset || isPeak) {
                      return (
                        <div key={point.month} className="flex items-center gap-2 text-xs">
                          <div className={`w-2 h-2 rounded-full ${
                            isPeak ? 'bg-[#ef4444]' : 'bg-[#fbbf24]'
                          }`} />
                          <span className="text-text-secondary">{formatMonth(point.month)}:</span>
                          <span className="text-text-primary">
                            {isPeak ? 'Peak' : 'Onset'} ({point.score.toFixed(3)})
                          </span>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            )}

            {/* Change Classification */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-primary">
                Change Classification
              </label>
              <select
                value={classification}
                onChange={(e) => setClassification(e.target.value)}
                className="w-full px-3 py-2 bg-background text-text-primary border border-border
                  rounded-md focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
              >
                {CHANGE_CLASSIFICATIONS.map((cls) => (
                  <option key={cls} value={cls}>
                    {cls}
                  </option>
                ))}
              </select>
            </div>

            {/* Confidence Rating */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-primary">
                Analyst Confidence
              </label>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((rating) => (
                  <button
                    key={rating}
                    onClick={() => setConfidence(rating)}
                    className={`transition-colors ${
                      rating <= confidence ? 'text-[#fbbf24]' : 'text-border'
                    }`}
                  >
                    <Star className="w-5 h-5" fill={rating <= confidence ? '#fbbf24' : 'none'} />
                  </button>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-primary">
                Analyst Notes
              </label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add observations, context, or analysis notes..."
                rows={8}
                className="text-sm"
              />
            </div>

            {/* Save Button */}
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="w-full flex items-center justify-center gap-2 px-4 py-2
                bg-accent text-background font-medium rounded-md
                hover:bg-accent/90 transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save Notes'}
            </button>

            {/* Related Hotspots (Placeholder) */}
            <div className="card">
              <h3 className="text-sm font-semibold text-text-primary mb-2">
                Related Hotspots
              </h3>
              <p className="text-xs text-text-secondary">
                No related hotspots detected within 10km radius.
              </p>
            </div>
          </>
        )}

        {!hotspot && (
          <div className="text-center py-12 text-text-secondary">
            Select a hotspot to view case notes
          </div>
        )}
      </div>
    </div>
  );
}

// LocalStorage utilities
function loadCaseNote(tileId: string): CaseNote | null {
  if (typeof window === 'undefined') return null;

  const saved = localStorage.getItem(`case-note-${tileId}`);
  if (!saved) return null;

  try {
    return JSON.parse(saved);
  } catch {
    return null;
  }
}

function saveCaseNote(caseNote: CaseNote): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(`case-note-${caseNote.tileId}`, JSON.stringify(caseNote));
}
