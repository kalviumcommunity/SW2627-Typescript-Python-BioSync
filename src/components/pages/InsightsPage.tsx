import { ArrowUpRight, BarChart3, CheckCircle2, ChevronRight, CircleAlert, Sparkles, TrendingUp } from 'lucide-react'
import { PageContainer } from '../layout/PageContainer'
import { Button } from '../common/Button'
import { aiInsights, activityData, pipelineStages } from '../../data/dashboard'

const insightGroups = [
  {
    label: 'Evidence pattern',
    title: 'Cell viability improved across three compound A experiments.',
    description: 'The signal appears in 3 experiments using the same concentration range and 24-hour incubation window.',
    confidence: 94,
    tone: 'bg-emerald-50 text-emerald-700'
  },
  {
    label: 'Review needed',
    title: 'Two protocols use different incubation times for similar conditions.',
    description: 'Resolve the discrepancy before the next validation run to keep the comparison reproducible.',
    confidence: 86,
    tone: 'bg-amber-50 text-amber-700'
  },
  {
    label: 'New connection',
    title: 'Recent literature links pathway X with marker Y.',
    description: 'Four indexed papers support the relationship and one active experiment could validate it.',
    confidence: 78,
    tone: 'bg-brand-50 text-brand-700'
  }
]

export function InsightsPage() {
  return (
    <PageContainer
      title="Research Insights"
      subtitle="Evidence-led signals from your documents, experiments, and literature."
      actions={
        <Button variant="secondary" icon={<BarChart3 className="h-4 w-4" />}>
          Export report
        </Button>
      }
    >
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-center justify-between text-sm text-slate-500">
            Evidence confidence <TrendingUp className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="mt-3 text-3xl font-semibold text-slate-900">89%</div>
          <div className="mt-1 text-xs text-emerald-600">+6.4% this month</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-center justify-between text-sm text-slate-500">
            Signals detected <Sparkles className="h-4 w-4 text-brand-600" />
          </div>
          <div className="mt-3 text-3xl font-semibold text-slate-900">24</div>
          <div className="mt-1 text-xs text-slate-500">Across 18 active sources</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-center justify-between text-sm text-slate-500">
            Review queue <CircleAlert className="h-4 w-4 text-amber-600" />
          </div>
          <div className="mt-3 text-3xl font-semibold text-slate-900">7</div>
          <div className="mt-1 text-xs text-amber-600">3 need attention today</div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Priority signals</h2>
              <p className="mt-1 text-sm text-slate-500">Ranked by confidence and potential research impact.</p>
            </div>
            <button type="button" className="text-sm font-medium text-brand-700 hover:text-brand-800">View all</button>
          </div>
          <div className="mt-5 space-y-3">
            {insightGroups.map((insight) => (
              <article key={insight.title} className="rounded-lg border border-slate-200 p-4 transition hover:border-brand-200 hover:bg-brand-50/30">
                <div className="flex items-start gap-3">
                  <div className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${insight.tone}`}>{insight.label}</div>
                  <div className="ml-auto flex items-center gap-1 text-xs font-medium text-slate-500">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> {insight.confidence}% confidence
                  </div>
                </div>
                <h3 className="mt-3 text-sm font-semibold text-slate-900">{insight.title}</h3>
                <p className="mt-1 text-sm leading-6 text-slate-500">{insight.description}</p>
                <button type="button" className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-brand-700">
                  Explore evidence <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <h2 className="text-lg font-semibold text-slate-900">Research momentum</h2>
          <p className="mt-1 text-sm text-slate-500">Documents, experiments, and literature indexed.</p>
          <div className="mt-5 space-y-4">
            {activityData.slice(-4).map((month) => {
              const total = month.Documents + month.Experiments * 8 + month.Literature
              const width = Math.round((total / 480) * 100)
              return (
                <div key={month.month}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-700">{month.month}</span>
                    <span className="text-slate-500">{total} indexed items</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-brand-500" style={{ width: `${width}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
          <div className="mt-6 rounded-lg bg-slate-50 p-4">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">AI summary</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">Research activity is accelerating, with the strongest growth in literature indexing and experiment validation.</p>
          </div>
        </section>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Suggested next actions</h2>
            <p className="mt-1 text-sm text-slate-500">Small actions that improve evidence quality this week.</p>
          </div>
          <ArrowUpRight className="h-5 w-5 text-slate-400" />
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {aiInsights.map((insight) => (
            <button key={insight.action} type="button" className="rounded-lg border border-slate-200 p-4 text-left transition hover:border-brand-200 hover:bg-brand-50/30">
              <div className="text-sm font-medium text-slate-800">{insight.action}</div>
              <div className="mt-2 text-xs leading-5 text-slate-500">{insight.title}</div>
              <div className="mt-3 text-xs font-semibold text-brand-700">Open recommendation →</div>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold text-slate-900">Pipeline health</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-5">
          {pipelineStages.map((stage) => (
            <div key={stage.title} className="rounded-lg bg-slate-50 p-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700">{stage.title}</span>
                <span className="text-slate-500">{stage.count}</span>
              </div>
              <div className="mt-3 h-1.5 rounded-full bg-slate-200">
                <div className="h-1.5 rounded-full bg-brand-500" style={{ width: `${stage.progress}%` }} />
              </div>
              <div className="mt-2 text-[11px] text-slate-500">{stage.progress}% complete</div>
            </div>
          ))}
        </div>
      </section>
    </PageContainer>
  )
}
