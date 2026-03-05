import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMonth(month: string): string {
  // Convert "2024-01" to "Jan 2024"
  const [year, monthNum] = month.split('-');
  const date = new Date(parseInt(year), parseInt(monthNum) - 1);
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

export function formatScore(score: number): string {
  return score.toFixed(2);
}

export function getConfidenceColor(confidence: string): string {
  switch (confidence) {
    case 'High':
      return 'badge-high';
    case 'Medium':
      return 'badge-medium';
    case 'Low':
      return 'badge-low';
    default:
      return 'badge-low';
  }
}

export function getAlertTypeColor(alertType: string): string {
  switch (alertType) {
    case 'Structural':
      return 'badge-structural';
    case 'Activity':
      return 'badge-activity';
    default:
      return 'badge-low';
  }
}

export function getScoreColor(score: number): string {
  if (score >= 0.7) return '#ef4444'; // red-500
  if (score >= 0.5) return '#fbbf24'; // amber-400
  return '#22d3ee'; // cyan-500
}

export function downloadMapScreenshot(canvas: HTMLCanvasElement, filename: string = 'map-view.png') {
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
}
