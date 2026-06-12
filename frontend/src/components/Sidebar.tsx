import {
  BarChart2,
  Bot,
  LayoutDashboard,
  Megaphone,
  Users,
  UsersRound,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/copilot',   icon: Bot,             label: 'AI Copilot' },
  { to: '/customers', icon: Users,           label: 'Customers' },
  { to: '/segments',  icon: UsersRound,      label: 'Segments' },
  { to: '/campaigns', icon: Megaphone,       label: 'Campaigns' },
]

export default function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Brand */}
      <div className="px-5 py-5 flex items-center gap-3 border-b border-gray-800">
        <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center">
          <BarChart2 size={16} className="text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-none">Xeno</p>
          <p className="text-xs text-gray-500 mt-0.5">Mini CRM</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-violet-600/20 text-violet-400 font-medium'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gray-800">
        <p className="text-xs text-gray-600">Assignment · June 2025</p>
      </div>
    </aside>
  )
}
