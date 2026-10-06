import { Activity, BarChart3, BookOpen, BrainCircuit, FileText, FlaskConical, HelpCircle, LayoutDashboard, Network, Settings, Sparkles, Users, NotebookPen } from 'lucide-react'
import { NavLink } from 'react-router-dom'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

const navGroups = [
  {
    title: 'OVERVIEW',
    items: [
      { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
      { label: 'Insights', to: '/insights', icon: BarChart3 }
    ]
  },
  {
    title: 'RESEARCH',
    items: [
      { label: 'Documents', to: '/documents', icon: FileText },
      { label: 'Experiments', to: '/experiments', icon: FlaskConical },
      { label: 'Knowledge Graph', to: '/knowledge', icon: Network },
      { label: 'Literature', to: '/literature', icon: BookOpen }
    ]
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { label: 'AI Research Assistant', to: '/ai-assistant', icon: BrainCircuit },
      { label: 'Research Brief', to: '/brief', icon: NotebookPen },
      { label: 'Activity', to: '/activity', icon: Activity }
    ]
  },
  {
    title: 'SYSTEM',
    items: [
      { label: 'Team', to: '/team', icon: Users },
      { label: 'Settings', to: '/settings', icon: Settings }
    ]
  }
]

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside className={`border-r border-slate-200 bg-white/90 backdrop-blur-sm ${collapsed ? 'w-20' : 'w-72'} transition-all duration-200`}>
      <div className="flex h-full flex-col">
        <div className={`flex items-center justify-between border-b border-slate-200 px-4 py-4 ${collapsed ? 'px-3' : ''}`}>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white shadow-sm">B</div>
            {!collapsed && (
              <div>
                <div className="text-[15px] font-semibold text-slate-900">BioSynth</div>
                <div className="text-[11px] text-slate-500">Research Intelligence</div>
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={onToggle}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
          >
            {collapsed ? '→' : '←'}
          </button>
        </div>

        <nav aria-label="Primary navigation" className="flex-1 space-y-6 overflow-y-auto p-3">
          {navGroups.map((group) => (
            <div key={group.title} className="space-y-2">
              {!collapsed && <div className="px-2 text-[10px] font-semibold tracking-[0.18em] text-slate-400">{group.title}</div>}
              {group.items.map(({ label, to, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                      isActive ? 'bg-brand-50 text-brand-700 ring-1 ring-brand-100' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    } ${collapsed ? 'justify-center px-2' : ''}`
                  }
                >
                  <Icon className="h-4 w-4" />
                  {!collapsed && <span>{label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className={`border-t border-slate-200 p-3 ${collapsed ? 'px-2' : ''}`}>
          <div className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-slate-100">
            <div className="relative flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
              SC
              <span role="status" aria-label="Online" className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500" />
            </div>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-slate-900">Dr. Sarah Chen</div>
                <div className="truncate text-xs text-slate-500">Research Scientist</div>
              </div>
            )}
          </div>
          {!collapsed && (
            <div className="mt-3 flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
              <span className="flex items-center gap-2"><Sparkles className="h-3.5 w-3.5 text-brand-600" /> Workspace synced</span>
              <button type="button" aria-label="Workspace sync help" className="text-slate-500 hover:text-slate-700"><HelpCircle className="h-3.5 w-3.5" /></button>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
