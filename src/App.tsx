import { Route, Routes, Navigate } from 'react-router-dom'
import { useState } from 'react'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { PageContainer } from './components/layout/PageContainer'
import { Button } from './components/common/Button'
import { EmptyState } from './components/common/EmptyState'
import { ActivityChart } from './components/dashboard/ActivityChart'
import { AIInsights } from './components/dashboard/AIInsights'
import { KnowledgeGraphPreview } from './components/dashboard/KnowledgeGraphPreview'
import { MetricCard } from './components/dashboard/MetricCard'
import { RecentResearch } from './components/dashboard/RecentResearch'
import { ResearchPipeline } from './components/dashboard/ResearchPipeline'
import { DocumentFilters } from './components/documents/DocumentFilters'
import { DocumentTable } from './components/documents/DocumentTable'
import { UploadDocumentModal } from './components/documents/UploadDocumentModal'
import { ExperimentCard } from './components/experiments/ExperimentCard'
import { ExperimentFilters } from './components/experiments/ExperimentFilters'
import { ExperimentTable } from './components/experiments/ExperimentTable'
import { KnowledgeDetailsPanel } from './components/knowledge/KnowledgeDetailsPanel'
import { KnowledgeFilters } from './components/knowledge/KnowledgeFilters'
import { KnowledgeGraph } from './components/knowledge/KnowledgeGraph'
import { LiteratureCard } from './components/literature/LiteratureCard'
import { LiteratureFilters } from './components/literature/LiteratureFilters'
import { ChatInterface } from './components/ai/ChatInterface'
import { ResearchBriefPage } from './components/research/ResearchBriefPage'
import { Badge } from './components/common/Badge'
import { SearchInput } from './components/common/SearchInput'
import { activityItems } from './data/activity'
import { activityData, aiInsights, metrics, pipelineStages, recentResearch } from './data/dashboard'
import { documents } from './data/documents'
import { experiments } from './data/experiments'
import { knowledgeInsight, knowledgeNodes, knowledgeConnections } from './data/knowledge'
import { literaturePapers } from './data/literature'
import { ArrowUpRight, Bell, HelpCircle, Plus, Search, Settings, Upload } from 'lucide-react'

function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  )
}

function DashboardPage() {
  const [search, setSearch] = useState('')

  return (
    <PageContainer
      title="Good morning, Dr. Chen"
      subtitle="Here's what's happening across your research workspace."
      actions={
        <>
          <Button variant="secondary">Ask AI</Button>
          <Button icon={<Plus className="h-4 w-4" />}>+ Upload Document</Button>
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {metrics.map((metric) => (
          <MetricCard key={metric.id} {...metric} />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
        <ActivityChart data={activityData} />
        <div className="space-y-6">
          <AIInsights insights={aiInsights} />
          <KnowledgeGraphPreview count="12,438 knowledge connections" />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <ResearchPipeline stages={pipelineStages} />
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-lg font-semibold text-slate-900">Activity Summary</h3>
          <div className="mt-4 space-y-4">
            {activityItems.slice(0, 3).map((item) => (
              <div key={item.id} className="flex items-start gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="mt-1 h-2.5 w-2.5 rounded-full bg-brand-500" />
                <div>
                  <div className="text-sm text-slate-700">{item.title}</div>
                  <div className="mt-1 text-xs text-slate-500">{item.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <RecentResearch items={recentResearch} />
    </PageContainer>
  )
}

function DocumentsPage() {
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)

  const filteredDocuments = documents.filter((doc) => doc.title.toLowerCase().includes(search.toLowerCase()))

  return (
    <PageContainer
      title="Research Documents"
      actions={
        <>
          <Button variant="secondary">Filter</Button>
          <Button onClick={() => setIsModalOpen(true)} icon={<Upload className="h-4 w-4" />}>+ Upload Document</Button>
        </>
      }
    >
      <DocumentFilters search={search} onSearch={setSearch} />
      {filteredDocuments.length > 0 ? (
        <DocumentTable rows={filteredDocuments.map((doc) => ({ ...doc, createdAt: doc.createdAt, updatedAt: doc.updatedAt, status: doc.status }))} />
      ) : (
        <EmptyState title="No documents found" description="Try a different search term or upload a new research document." />
      )}
      <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-600 shadow-soft">
        <span>
          Showing {filteredDocuments.length === 0 ? 0 : 1}-{filteredDocuments.length} of {documents.length} documents
        </span>
        <div className="flex items-center gap-2">
          <button className="rounded-md border border-slate-200 bg-white px-3 py-1.5">Previous</button>
          <button className="rounded-md bg-brand-600 px-3 py-1.5 text-white">1</button>
          <button className="rounded-md border border-slate-200 bg-white px-3 py-1.5">Next</button>
        </div>
      </div>
      <UploadDocumentModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </PageContainer>
  )
}

function ExperimentsPage() {
  const [search, setSearch] = useState('')

  const filteredExperiments = experiments.filter((exp) => exp.name.toLowerCase().includes(search.toLowerCase()))

  return (
    <PageContainer
      title="Experiments"
      actions={<Button>New Experiment</Button>}
    >
      <ExperimentFilters search={search} onSearch={setSearch} />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {filteredExperiments.length > 0 ? (
          filteredExperiments.map((experiment) => (
            <ExperimentCard
              key={experiment.id}
              name={experiment.name}
              area={experiment.researchArea}
              owner={experiment.owner}
              status={experiment.status}
              startedAt={experiment.startedAt}
              lastActivity={experiment.lastActivity}
            />
          ))
        ) : (
          <EmptyState title="No experiments found" description="Try a different search term to find an experiment." />
        )}
      </div>
      <ExperimentTable rows={filteredExperiments.map((experiment) => ({ ...experiment }))} />
    </PageContainer>
  )
}

function KnowledgePage() {
  return (
    <PageContainer
      title="Knowledge Graph"
      subtitle="Explore relationships across experiments, protocols, findings and literature."
    >
      <div className="grid gap-6 xl:grid-cols-[260px_1.5fr_0.9fr]">
        <KnowledgeFilters />
        <KnowledgeGraph nodes={knowledgeNodes} connections={knowledgeConnections} />
        <KnowledgeDetailsPanel insight={knowledgeInsight} />
      </div>
    </PageContainer>
  )
}

function LiteraturePage() {
  const [search, setSearch] = useState('')
  const filteredPapers = literaturePapers.filter((paper) => paper.title.toLowerCase().includes(search.toLowerCase()))

  return (
    <PageContainer title="Literature Intelligence">
      <LiteratureFilters search={search} onSearch={setSearch} />
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {filteredPapers.length > 0 ? (
          filteredPapers.map((paper) => (
            <LiteratureCard
              key={paper.id}
              title={paper.title}
              authors={paper.authors}
              journal={paper.journal}
              year={paper.year}
              keyFindings={paper.keyFindings}
              relatedExperiments={paper.relatedExperiments}
            />
          ))
        ) : (
          <EmptyState title="No literature found" description="Try a different search term to find related research." />
        )}
      </div>
    </PageContainer>
  )
}

function AiAssistantPage() {
  return (
    <PageContainer
      title="Research Assistant"
      subtitle="Ask questions across your lab's research knowledge."
    >
      <ChatInterface />
    </PageContainer>
  )
}

function ActivityPage() {
  return (
    <PageContainer title="Research Activity">
      <div className="space-y-4">
        {activityItems.map((item) => (
          <div key={item.id} className="flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-soft">
            <div className="mt-1 flex h-9 w-9 items-center justify-center rounded-full bg-brand-50 text-brand-700">
              {item.type === 'document' ? <Upload className="h-4 w-4" /> : item.type === 'ai' ? <Search className="h-4 w-4" /> : item.type === 'experiment' ? <ArrowUpRight className="h-4 w-4" /> : item.type === 'graph' ? <Bell className="h-4 w-4" /> : <HelpCircle className="h-4 w-4" />}
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-800">{item.title}</div>
              <div className="mt-1 text-xs text-slate-500">{item.time}</div>
            </div>
          </div>
        ))}
      </div>
    </PageContainer>
  )
}

function SettingsPage() {
  return (
    <PageContainer title="Settings">
      <div className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-lg font-semibold text-slate-900">Profile</h3>
          <div className="mt-4 space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">SC</div>
              <div>
                <div className="font-medium text-slate-900">Dr. Sarah Chen</div>
                <div className="text-sm text-slate-500">Research Scientist</div>
              </div>
            </div>
            <input className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm" defaultValue="Dr. Sarah Chen" />
            <input className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm" defaultValue="sarah.chen@biosynth.lab" />
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-lg font-semibold text-slate-900">Workspace</h3>
          <div className="mt-4 space-y-4">
            <input className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm" defaultValue="BioSynth Research Lab" />
            <select className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
              <option>Discovery Unit</option>
              <option>Translational Biology</option>
            </select>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-lg font-semibold text-slate-900">Notifications</h3>
          <div className="mt-4 space-y-3 text-sm text-slate-700">
            {['Email updates', 'Weekly digest', 'Experiment alerts', 'AI summary notifications'].map((item) => (
              <label key={item} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 p-3">
                <span>{item}</span>
                <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-slate-300 text-brand-600" />
              </label>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-lg font-semibold text-slate-900">AI Preferences</h3>
          <div className="mt-4 space-y-4 text-sm text-slate-700">
            <select className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
              <option>Evidence-first summary</option>
              <option>Concise summary</option>
              <option>Detailed synthesis</option>
            </select>
            <div className="rounded-lg bg-slate-50 p-3">
              <div className="font-medium text-slate-900">Confidence threshold</div>
              <input type="range" min="0" max="100" defaultValue="80" className="mt-3 w-full" />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft xl:col-span-2">
          <h3 className="text-lg font-semibold text-slate-900">Security</h3>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <button className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm font-medium text-slate-700">Manage SSO</button>
            <button className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm font-medium text-slate-700">Access policies</button>
            <button className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm font-medium text-slate-700">Audit logs</button>
            <button className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm font-medium text-slate-700">Session controls</button>
          </div>
        </div>
      </div>
    </PageContainer>
  )
}

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/experiments" element={<ExperimentsPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/literature" element={<LiteraturePage />} />
        <Route path="/ai-assistant" element={<AiAssistantPage />} />
        <Route path="/brief" element={<ResearchBriefPage />} />
        <Route path="/activity" element={<ActivityPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </AppLayout>
  )
}
