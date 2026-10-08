import { useMemo, useState } from 'react'
import { ArrowUpRight, Bookmark, Check, Clock3, FileText, Search, Sparkles } from 'lucide-react'
import { PageContainer } from '../layout/PageContainer'
import { Button } from '../common/Button'

type Resource = {
  title: string
  description: string
  type: 'Protocol' | 'Review' | 'Dataset' | 'Guide'
  author: string
  updated: string
  tags: string[]
  featured?: boolean
}

const resources: Resource[] = [
  {
    title: 'CRISPR screening design principles',
    description: 'A practical synthesis of library design, controls, and quality thresholds for pooled screens.',
    type: 'Guide',
    author: 'Dr. Michael Lee',
    updated: 'Updated 2 days ago',
    tags: ['CRISPR', 'Screening'],
    featured: true
  },
  {
    title: 'Single-cell RNA-seq analysis checklist',
    description: 'Reusable checkpoints for sample preparation, QC, normalization, and cell-type annotation.',
    type: 'Protocol',
    author: 'Dr. Emily Watson',
    updated: 'Updated 1 week ago',
    tags: ['scRNA-seq', 'Analysis']
  },
  {
    title: 'Inflammation pathway literature review',
    description: 'Evidence map of pathway interactions and the most frequently cited experimental findings.',
    type: 'Review',
    author: 'AI Research Assistant',
    updated: 'Updated 12 days ago',
    tags: ['Immunology', 'Literature']
  },
  {
    title: 'Reference expression dataset · v3',
    description: 'Curated baseline expression profiles used across the discovery team’s validation experiments.',
    type: 'Dataset',
    author: 'Discovery Unit',
    updated: 'Updated 3 weeks ago',
    tags: ['Expression', 'Validation']
  },
  {
    title: 'Cell viability assay: internal protocol',
    description: 'Validated procedure with expected ranges, troubleshooting notes, and acceptance criteria.',
    type: 'Protocol',
    author: 'Dr. Sarah Chen',
    updated: 'Updated 1 month ago',
    tags: ['Assay', 'Cell biology']
  },
  {
    title: 'Translational research handoff guide',
    description: 'Shared guidance for moving promising findings from discovery into validation planning.',
    type: 'Guide',
    author: 'Research Operations',
    updated: 'Updated 1 month ago',
    tags: ['Workflow', 'Translational']
  }
]

const filters = ['All resources', 'Protocols', 'Reviews', 'Datasets', 'Guides']

export function KnowledgeHubPage() {
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState('All resources')
  const [saved, setSaved] = useState<string[]>([])

  const filteredResources = useMemo(() => {
    const query = search.trim().toLowerCase()
    return resources.filter((resource) => {
      const matchesFilter = activeFilter === 'All resources' || `${resource.type}s` === activeFilter
      const searchable = `${resource.title} ${resource.description} ${resource.tags.join(' ')}`.toLowerCase()
      return matchesFilter && searchable.includes(query)
    })
  }, [activeFilter, search])

  const toggleSaved = (title: string) => {
    setSaved((current) => current.includes(title) ? current.filter((item) => item !== title) : [...current, title])
  }

  return (
    <PageContainer
      title="Knowledge Hub"
      subtitle="Find trusted protocols, datasets, and research guidance curated for your workspace."
      actions={<Button icon={<Sparkles className="h-4 w-4" />}>Ask AI to recommend</Button>}
    >
      <section className="rounded-2xl bg-gradient-to-br from-brand-900 via-brand-700 to-brand-600 p-6 text-white shadow-soft">
        <div className="max-w-2xl">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-100">Your research library</div>
          <h2 className="mt-2 text-2xl font-semibold">Turn scattered evidence into your next decision.</h2>
          <p className="mt-2 text-sm leading-6 text-brand-50">Search across internal knowledge and saved literature to move from question to experiment with confidence.</p>
          <label className="mt-5 flex max-w-xl items-center gap-3 rounded-lg bg-white px-4 py-3 text-slate-500 shadow-sm">
            <Search className="h-4 w-4 shrink-0" />
            <span className="sr-only">Search the knowledge hub</span>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search protocols, findings, or topics..." className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400" />
            <kbd className="hidden rounded border border-slate-200 px-1.5 py-0.5 text-[10px] sm:block">⌘ K</kbd>
          </label>
        </div>
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Knowledge resource types">
          {filters.map((filter) => (
            <button key={filter} type="button" role="tab" aria-selected={activeFilter === filter} onClick={() => setActiveFilter(filter)} className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${activeFilter === filter ? 'bg-brand-600 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50'}`}>
              {filter}
            </button>
          ))}
        </div>
        <div className="text-sm text-slate-500">{filteredResources.length} resources · {saved.length} saved</div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_300px]">
        <div className="grid gap-4 md:grid-cols-2">
          {filteredResources.map((resource) => {
            const isSaved = saved.includes(resource.title)
            return (
              <article key={resource.title} className={`rounded-xl border bg-white p-5 shadow-soft transition hover:-translate-y-0.5 hover:shadow-md ${resource.featured ? 'border-brand-200 ring-1 ring-brand-100' : 'border-slate-200'}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-brand-700"><FileText className="h-4 w-4" /> {resource.type}</div>
                  <button type="button" aria-label={`${isSaved ? 'Remove' : 'Save'} ${resource.title}`} onClick={() => toggleSaved(resource.title)} className={`rounded-md p-1.5 transition ${isSaved ? 'bg-brand-50 text-brand-700' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-700'}`}>
                    {isSaved ? <Check className="h-4 w-4" /> : <Bookmark className="h-4 w-4" />}
                  </button>
                </div>
                <h3 className="mt-4 text-base font-semibold text-slate-900">{resource.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{resource.description}</p>
                <div className="mt-4 flex flex-wrap gap-2">{resource.tags.map((tag) => <span key={tag} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">{tag}</span>)}</div>
                <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4 text-xs text-slate-500">
                  <span>{resource.author}</span>
                  <span className="flex items-center gap-1"><Clock3 className="h-3.5 w-3.5" /> {resource.updated.replace('Updated ', '')}</span>
                </div>
                <button type="button" className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:text-brand-800">Open resource <ArrowUpRight className="h-4 w-4" /></button>
              </article>
            )
          })}
          {filteredResources.length === 0 && <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center md:col-span-2"><Search className="mx-auto h-6 w-6 text-slate-400" /><h3 className="mt-3 font-semibold text-slate-900">No resources found</h3><p className="mt-1 text-sm text-slate-500">Try a different search term or resource type.</p></div>}
        </div>

        <aside className="h-fit rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900"><Sparkles className="h-4 w-4 text-brand-600" /> Quick start</div>
          <p className="mt-2 text-sm leading-6 text-slate-500">Build a focused reading list for your next research question.</p>
          <div className="mt-4 space-y-3">
            {['Start with a protocol', 'Compare related findings', 'Save a reusable reference'].map((step, index) => (
              <div key={step} className="flex items-center gap-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-700"><span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">{index + 1}</span>{step}</div>
            ))}
          </div>
          <Button variant="outline" className="mt-4 w-full">Create reading list</Button>
        </aside>
      </div>
    </PageContainer>
  )
}
