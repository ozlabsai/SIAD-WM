import type { TileDetail, Hotspot } from '@/types';

interface ModalityContribution {
  modality: string;
  percentage: number;
}

export function getModalityContributions(
  heatmap: TileDetail['heatmap'],
  monthIndex: number
): ModalityContribution[] {
  if (!heatmap || !heatmap.modalities || !heatmap.values) {
    return [];
  }

  const contributions: ModalityContribution[] = [];
  let total = 0;

  // Calculate total contribution for the month
  heatmap.modalities.forEach((modality, idx) => {
    const value = heatmap.values[idx]?.[monthIndex] || 0;
    total += value;
  });

  // Calculate percentages
  if (total > 0) {
    heatmap.modalities.forEach((modality, idx) => {
      const value = heatmap.values[idx]?.[monthIndex] || 0;
      contributions.push({
        modality,
        percentage: (value / total) * 100,
      });
    });
  }

  return contributions.sort((a, b) => b.percentage - a.percentage);
}

export function getDominantModality(
  contributions: ModalityContribution[]
): string | null {
  if (contributions.length === 0) return null;
  return contributions[0].modality;
}

export function getChangeTypeDescription(
  dominantModality: string,
  score: number
): string {
  const modalityDescriptions: Record<string, string> = {
    SAR: 'structural change detected via Synthetic Aperture Radar, suggesting building construction, demolition, or surface modifications',
    Optical: 'visible change detected via optical sensors, indicating land cover transformation or vegetation change',
    VIIRS: 'night-time lighting change detected, suggesting human activity patterns or infrastructure development',
    Lights: 'night-time lighting change detected, suggesting human activity patterns or infrastructure development',
  };

  return modalityDescriptions[dominantModality] || 'multi-modal change detected';
}

export function getDurationDescription(duration: number): string {
  if (duration === 1) return 'single month anomaly';
  if (duration <= 3) return `${duration}-month short-term anomaly`;
  if (duration <= 6) return `${duration}-month persistent change`;
  return `${duration}-month long-term transformation`;
}

export function getConfidenceDescription(score: number): string {
  if (score >= 0.8) return 'Very high confidence';
  if (score >= 0.7) return 'High confidence';
  if (score >= 0.5) return 'Medium confidence';
  return 'Low confidence';
}

export function generateDetectionExplanation(
  tileDetail: TileDetail,
  hotspot?: Hotspot
): string {
  const { timeline, heatmap } = tileDetail;

  if (!timeline || timeline.length === 0) {
    return 'No detection data available.';
  }

  // Find peak score month
  const peakPoint = timeline.reduce((max, point) =>
    point.score > max.score ? point : max
  );
  const peakMonthIndex = timeline.indexOf(peakPoint);
  const onsetMonth = timeline[0].month;
  const duration = timeline.length;

  // Get modality contributions at peak
  const contributions = getModalityContributions(heatmap, peakMonthIndex);
  const dominantModality = getDominantModality(contributions);
  const dominantPercentage = contributions[0]?.percentage || 0;

  // Build explanation
  const confidenceText = getConfidenceDescription(peakPoint.score);
  const durationText = getDurationDescription(duration);
  const changeTypeText = dominantModality
    ? getChangeTypeDescription(dominantModality, peakPoint.score)
    : 'anomalous change';

  let explanation = `${confidenceText} ${durationText} detected starting in ${formatMonthName(onsetMonth)}. `;

  if (dominantModality) {
    explanation += `${dominantModality} sensors show ${dominantPercentage.toFixed(0)}% of the anomaly signal, indicating ${changeTypeText}. `;
  }

  explanation += `Peak anomaly score of ${peakPoint.score.toFixed(2)} observed in ${formatMonthName(peakPoint.month)}.`;

  return explanation;
}

export function generateBaselineExplanation(
  tileDetail: TileDetail
): string | null {
  const { baselines } = tileDetail;

  if (!baselines) return null;

  const persistenceImprovement = baselines.persistence.improvement;
  const seasonalImprovement = baselines.seasonal.improvement;

  const avgImprovement = (persistenceImprovement + seasonalImprovement) / 2;

  if (avgImprovement >= 50) {
    return `World Model significantly outperformed baseline methods, detecting this anomaly ${avgImprovement.toFixed(1)}% more accurately on average.`;
  } else if (avgImprovement >= 25) {
    return `World Model showed moderate improvement over baseline methods, with ${avgImprovement.toFixed(1)}% better detection accuracy.`;
  } else {
    return `World Model detected this anomaly with comparable performance to baseline methods.`;
  }
}

export function generateEnvironmentalExplanation(
  observedScore: number,
  neutralScore: number
): string {
  const difference = Math.abs(observedScore - neutralScore);
  const percentChange = (difference / observedScore) * 100;

  if (percentChange < 10) {
    return 'Environmental conditions have minimal impact on this anomaly. The change is likely structural or activity-based rather than weather-driven.';
  } else if (observedScore > neutralScore) {
    return `Environmental conditions amplify this anomaly by ${percentChange.toFixed(0)}%. Weather factors (rain, temperature) may be making the change appear more significant.`;
  } else {
    return `Under neutral environmental conditions, this anomaly would be ${percentChange.toFixed(0)}% stronger. Current weather may be masking the true extent of the change.`;
  }
}

export function formatMonthName(month: string): string {
  const [year, monthNum] = month.split('-');
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  const monthIndex = parseInt(monthNum, 10) - 1;
  return `${monthNames[monthIndex]} ${year}`;
}

export function getModalityDescription(modality: string): string {
  const descriptions: Record<string, string> = {
    SAR: 'Synthetic Aperture Radar detects structural changes regardless of weather or time of day',
    Optical: 'Optical sensors capture visible and near-infrared light to identify land cover changes',
    VIIRS: 'Visible Infrared Imaging Radiometer measures night-time lights and thermal emissions',
    Lights: 'Night-time lighting data reveals human activity and infrastructure development',
  };
  return descriptions[modality] || modality;
}
