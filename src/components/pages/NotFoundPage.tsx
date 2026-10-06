import { ArrowLeft, Search } from 'lucide-react'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <div className="max-w-md text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
          <Search className="h-7 w-7" />
        </div>
        <div className="mt-6 text-sm font-semibold uppercase tracking-[0.2em] text-brand-600">404</div>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Page not found</h1>
        <p className="mt-3 text-sm leading-6 text-slate-500">The research view you are looking for does not exist or may have moved.</p>
        <Link to="/dashboard" className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700">
          <ArrowLeft className="h-4 w-4" /> Back to dashboard
        </Link>
      </div>
    </div>
  )
}
