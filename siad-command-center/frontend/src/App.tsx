/**
 * SIAD Command Center - Main Application Component
 * Root component with routing, layout, and global state management setup
 */

import { useEffect, useState } from 'react'
import { checkApiHealth, getApiVersion } from './lib/api.ts'
import './styles/tactical.css'
import './styles/global.css'

function App() {
  const [apiHealth, setApiHealth] = useState(true)
  const [apiVersion, setApiVersion] = useState('loading...')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Check API connectivity
        const isHealthy = await checkApiHealth()
        setApiHealth(isHealthy)

        // Get API version
        const version = await getApiVersion()
        setApiVersion(version)
      } catch (error) {
        console.error('Failed to initialize app:', error)
        setApiHealth(false)
        setApiVersion('error')
      } finally {
        setLoading(false)
      }
    }

    initializeApp()
  }, [])

  if (loading) {
    return (
      <div className="center min-h-screen bg-dark">
        <div className="text-center">
          <div className="animate-pulse-cyan mb-4">
            <div className="hex-tile" style={{ fontSize: '2rem' }}>●</div>
          </div>
          <h1 className="font-tactical text-2xl mb-2">SIAD Command Center</h1>
          <p className="text-dim">Initializing tactical intelligence dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-dark tactical-grid">
      {/* Skip to main content link for accessibility */}
      <a href="#main-content" className="skip-to-main">
        Skip to main content
      </a>

      {/* Header */}
      <header className="border-thin border-b-1 py-4 px-6">
        <div className="container flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="font-tactical text-2xl font-bold">
              SIAD
              <span className="text-cyan"> Command Center</span>
            </div>
            <span className="text-dim text-xs px-2 py-1 bg-dark-secondary border-thin rounded">
              API v{apiVersion}
            </span>
          </div>

          {/* API Status Indicator */}
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                apiHealth ? 'bg-green-500 animate-pulse-cyan' : 'bg-red-500'
              }`}
              aria-label={`API ${apiHealth ? 'connected' : 'disconnected'}`}
            />
            <span className="text-sm text-dim">
              {apiHealth ? 'Backend Connected' : 'Backend Disconnected'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main id="main-content" className="flex-1 overflow-hidden">
        <div className="container py-8">
          {/* Hero Section */}
          <section className="mb-12">
            <h1 className="font-tactical text-5xl font-bold mb-4">
              Tactical Intelligence
              <br />
              <span className="text-cyan">&amp; Action Dashboard</span>
            </h1>
            <p className="text-xl text-secondary max-w-2xl mb-8">
              Real-time satellite imagery analysis, climate modeling, and strategic action planning
              for climate resilience and environmental intelligence.
            </p>

            {/* Navigation Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <NavCard
                title="Gallery"
                description="Explore analyzed satellite imagery and predictions"
                path="/gallery"
                icon="🖼️"
              />
              <NavCard
                title="Hex Map"
                description="Interactive 3D hexagonal map of climate actions and predictions"
                path="/map"
                icon="🗺️"
              />
              <NavCard
                title="Inspector"
                description="Detailed analysis tools and comparison visualizations"
                path="/inspector"
                icon="🔍"
              />
            </div>
          </section>

          {/* Status Sections */}
          {!apiHealth && (
            <section className="border-thick border-red rounded-lg p-6 mb-8 bg-dark-secondary">
              <h2 className="text-red text-lg font-bold mb-2">Backend Connection Issue</h2>
              <p className="text-secondary mb-2">
                Unable to connect to the FastAPI backend at <code>http://localhost:8000</code>
              </p>
              <p className="text-dim text-sm">
                Make sure the backend is running before exploring the dashboard features.
              </p>
            </section>
          )}

          {/* Quick Stats */}
          <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard label="Available Tiles" value="2,847" unit="locations" />
            <StatCard label="Predictions Ready" value="1,243" unit="analyzed" />
            <StatCard label="Climate Actions" value="156" unit="tracked" />
            <StatCard label="Avg Confidence" value="87.3" unit="percent" />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-thin border-t-1 py-6 px-6 text-center text-dim">
        <p className="text-sm">
          SIAD Command Center • Satellite Intelligence & Action Dashboard
          <br />
          <span className="font-mono text-xs mt-2 block opacity-75">
            {new Date().toISOString()}
          </span>
        </p>
      </footer>
    </div>
  )
}

/* ============================================================================
   COMPONENT HELPERS
   ========================================================================== */

interface NavCardProps {
  title: string
  description: string
  path: string
  icon: string
}

function NavCard({ title, description, path, icon }: NavCardProps) {
  return (
    <a
      href={path}
      className="tactical-border p-6 rounded-lg hover:border-cyan hover:shadow-glow-cyan transition-all block"
      style={{ borderColor: 'var(--border-default)', borderWidth: '1px' }}
    >
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="font-tactical text-lg font-bold text-cyan mb-2">{title}</h3>
      <p className="text-sm text-secondary">{description}</p>
    </a>
  )
}

interface StatCardProps {
  label: string
  value: string
  unit: string
}

function StatCard({ label, value, unit }: StatCardProps) {
  return (
    <div
      className="tactical-border p-4 rounded-lg"
      style={{ borderColor: 'var(--border-default)', borderWidth: '1px' }}
    >
      <p className="text-dim text-xs font-mono mb-2">{label}</p>
      <div className="flex items-baseline gap-2">
        <span className="text-cyan font-bold text-2xl">{value}</span>
        <span className="text-secondary text-sm">{unit}</span>
      </div>
    </div>
  )
}

export default App
