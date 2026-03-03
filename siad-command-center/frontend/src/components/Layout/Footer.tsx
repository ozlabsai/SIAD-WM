/**
 * Footer Component - Placeholder
 * Application footer with links and information
 */

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-thin border-t-1 py-6 px-6 text-center text-dim">
      <div className="container">
        <p className="text-sm">
          SIAD Command Center • Satellite Intelligence & Action Dashboard
        </p>
        <div className="flex justify-center gap-4 mt-4 text-xs">
          <a href="/docs" className="hover:text-cyan transition-colors">Documentation</a>
          <span>•</span>
          <a href="/about" className="hover:text-cyan transition-colors">About</a>
          <span>•</span>
          <a href="/contact" className="hover:text-cyan transition-colors">Contact</a>
        </div>
        <p className="text-xs mt-4 opacity-75">
          © {currentYear} SIAD. All rights reserved.
        </p>
      </div>
    </footer>
  )
}

export default Footer
