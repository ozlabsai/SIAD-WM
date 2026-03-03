/**
 * Header Component - Placeholder
 * Main navigation header with branding and controls
 */

interface HeaderProps {
  apiStatus?: boolean
  apiVersion?: string
}

export function Header({ apiStatus = true, apiVersion = '1.0.0' }: HeaderProps) {
  return (
    <header className="border-thin border-b-1 py-4 px-6 sticky top-0 z-fixed">
      <div className="container flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="font-tactical text-xl font-bold">
            SIAD <span className="text-cyan">Command Center</span>
          </h1>
          <span className="text-dim text-xs px-2 py-1 bg-dark-secondary border-thin rounded">
            API v{apiVersion}
          </span>
        </div>

        <div className="flex items-center gap-4">
          {/* API Status Indicator */}
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                apiStatus ? 'bg-green-500 animate-pulse-cyan' : 'bg-red-500'
              }`}
              aria-label={`API ${apiStatus ? 'connected' : 'disconnected'}`}
            />
            <span className="text-sm text-dim">
              {apiStatus ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
