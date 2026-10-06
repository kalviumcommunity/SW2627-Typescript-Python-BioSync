import { Bell, HelpCircle, Search, Sparkles, UserCircle2 } from 'lucide-react'

interface HeaderProps {
  title?: string
}

export function Header({ title }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/80 backdrop-blur-sm">
      <div className="flex items-center justify-between gap-4 px-6 py-3.5">
        <div className="flex items-center gap-3 text-sm text-slate-500">
          {title ? <span className="font-medium text-slate-700">{title}</span> : null}
        </div>

        <div className="flex min-w-0 flex-1 items-center justify-end gap-4">
          <label className="relative hidden w-full max-w-xl lg:block">
            <span className="sr-only">Search workspace</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              placeholder="Search documents, experiments, findings..."
              aria-label="Search documents, experiments, and findings"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-12 text-sm text-slate-700 outline-none transition focus:border-brand-500 focus:bg-white focus:ring-2 focus:ring-brand-500/10"
            />
            <span aria-hidden="true" className="absolute right-3 top-1/2 -translate-y-1/2 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
              Ctrl K
            </span>
          </label>

          <div className="flex items-center gap-2">
            <button className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700" aria-label="Help">
              <HelpCircle className="h-4 w-4" />
            </button>
            <button className="relative rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700" aria-label="Notifications">
              <Bell className="h-4 w-4" />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-brand-500" />
            </button>
            <button type="button" aria-label="Open user profile" className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-2 py-1.5 text-sm text-slate-700 hover:bg-slate-100">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-[10px] font-semibold text-white">SC</div>
              <span className="hidden sm:inline">Dr. Chen</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
