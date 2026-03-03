/**
 * Sidebar Component - Placeholder
 * Left navigation panel for accessing main features
 */

interface SidebarProps {
  isOpen?: boolean
  onClose?: () => void
}

export function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  return (
    <aside
      className={`border-thin border-r-1 w-64 bg-dark-secondary flex flex-col transition-all ${
        !isOpen ? '-translate-x-full' : ''
      }`}
    >
      <nav className="flex-1 p-6 space-y-2">
        <NavLink href="/gallery" icon="🖼️" label="Gallery" />
        <NavLink href="/map" icon="🗺️" label="Hex Map" />
        <NavLink href="/inspector" icon="🔍" label="Inspector" />
        <NavLink href="/settings" icon="⚙️" label="Settings" />
      </nav>

      <div className="border-thin border-t p-4 text-dim text-xs">
        <p>SIAD v1.0.0</p>
        <p className="mt-2">Tactical Intelligence Dashboard</p>
      </div>
    </aside>
  )
}

interface NavLinkProps {
  href: string
  icon: string
  label: string
}

function NavLink({ href, icon, label }: NavLinkProps) {
  return (
    <a
      href={href}
      className="flex items-center gap-3 px-4 py-2 rounded hover:bg-dark-tertiary transition-colors"
    >
      <span className="text-lg">{icon}</span>
      <span className="text-sm">{label}</span>
    </a>
  )
}

export default Sidebar
