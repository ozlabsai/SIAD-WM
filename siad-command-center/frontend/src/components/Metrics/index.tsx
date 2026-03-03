/**
 * Metrics Component - Placeholder
 * Displays model performance metrics (MSE, PSNR, SSIM, Accuracy)
 */

export function Metrics() {
  return (
    <div className="metrics-container">
      <h2 className="font-tactical text-2xl font-bold mb-6">Model Metrics</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricBadge label="MSE" value="0.0234" variant="mse" />
        <MetricBadge label="PSNR" value="38.2" variant="psnr" />
        <MetricBadge label="SSIM" value="0.894" variant="ssim" />
        <MetricBadge label="Accuracy" value="92.1%" variant="accuracy" />
      </div>
    </div>
  )
}

interface MetricBadgeProps {
  label: string
  value: string
  variant: 'mse' | 'psnr' | 'ssim' | 'accuracy'
}

function MetricBadge({ label, value, variant }: MetricBadgeProps) {
  return (
    <div className={`metric-badge ${variant} p-4 rounded text-center`}>
      <div className="text-xs text-dim mb-1 font-mono">{label}</div>
      <div className="text-lg font-bold">{value}</div>
    </div>
  )
}

export default Metrics
