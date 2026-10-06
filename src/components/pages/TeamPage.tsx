import { Mail, MoreHorizontal, Plus, ShieldCheck, Users } from 'lucide-react'
import { PageContainer } from '../layout/PageContainer'
import { Button } from '../common/Button'

const members = [
  { initials: 'SC', name: 'Dr. Sarah Chen', role: 'Research Scientist', team: 'Discovery Unit', activity: 'Active now', tone: 'bg-slate-900' },
  { initials: 'ML', name: 'Dr. Michael Lee', role: 'Principal Investigator', team: 'Translational Biology', activity: '12 min ago', tone: 'bg-brand-600' },
  { initials: 'EW', name: 'Dr. Emily Watson', role: 'Data Scientist', team: 'Discovery Unit', activity: '1 hour ago', tone: 'bg-violet-600' },
  { initials: 'JP', name: 'Dr. James Park', role: 'Research Associate', team: 'Validation Lab', activity: 'Yesterday', tone: 'bg-amber-600' },
  { initials: 'AR', name: 'Alex Rivera', role: 'Lab Operations', team: 'Operations', activity: 'Yesterday', tone: 'bg-emerald-600' }
]

export function TeamPage() {
  return (
    <PageContainer
      title="Research Team"
      subtitle="Manage collaborators, workspace access, and ownership across your lab."
      actions={<Button icon={<Plus className="h-4 w-4" />}>Invite member</Button>}
    >
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-center gap-3 text-sm text-slate-500"><Users className="h-4 w-4 text-brand-600" /> Team members</div>
          <div className="mt-3 text-3xl font-semibold text-slate-900">24</div>
          <div className="mt-1 text-xs text-emerald-600">18 active this week</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-center gap-3 text-sm text-slate-500"><ShieldCheck className="h-4 w-4 text-emerald-600" /> Workspace access</div>
          <div className="mt-3 text-3xl font-semibold text-slate-900">98%</div>
          <div className="mt-1 text-xs text-slate-500">Roles reviewed this quarter</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-center gap-3 text-sm text-slate-500"><Mail className="h-4 w-4 text-violet-600" /> Pending invites</div>
          <div className="mt-3 text-3xl font-semibold text-slate-900">3</div>
          <div className="mt-1 text-xs text-amber-600">Awaiting response</div>
        </div>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white shadow-soft">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-5">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Workspace members</h2>
            <p className="mt-1 text-sm text-slate-500">People with access to BioSynth Research Lab.</p>
          </div>
          <select aria-label="Filter team members" className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
            <option>All teams</option>
            <option>Discovery Unit</option>
            <option>Validation Lab</option>
            <option>Operations</option>
          </select>
        </div>
        <div className="divide-y divide-slate-100">
          {members.map((member) => (
            <div key={member.name} className="flex flex-wrap items-center gap-4 p-4 transition hover:bg-slate-50">
              <div className={`flex h-10 w-10 items-center justify-center rounded-full text-xs font-semibold text-white ${member.tone}`}>{member.initials}</div>
              <div className="min-w-[180px] flex-1">
                <div className="text-sm font-medium text-slate-900">{member.name}</div>
                <div className="mt-1 text-xs text-slate-500">{member.role}</div>
              </div>
              <div className="min-w-[150px] text-sm text-slate-600">{member.team}</div>
              <div className="min-w-[110px] text-xs text-slate-500">{member.activity}</div>
              <button type="button" aria-label={`More options for ${member.name}`} className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"><MoreHorizontal className="h-4 w-4" /></button>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <h2 className="text-lg font-semibold text-slate-900">Team responsibilities</h2>
          <div className="mt-4 space-y-3">
            {['Document review', 'Experiment ownership', 'AI workspace administration'].map((responsibility, index) => (
              <div key={responsibility} className="flex items-center justify-between rounded-lg bg-slate-50 p-3 text-sm">
                <span className="text-slate-700">{responsibility}</span>
                <span className="text-xs font-medium text-slate-500">{[8, 12, 4][index]} owners</span>
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-soft">
          <h2 className="text-lg font-semibold text-slate-900">Access guidance</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">Keep experiment ownership close to the people running the work. Review access for inactive collaborators before publishing sensitive findings.</p>
          <button type="button" className="mt-4 text-sm font-semibold text-brand-700 hover:text-brand-800">Review access policies →</button>
        </section>
      </div>
    </PageContainer>
  )
}
