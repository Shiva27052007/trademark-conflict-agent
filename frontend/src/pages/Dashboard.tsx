import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { screeningApi } from '../services/api';
import type { ScreeningListItem } from '../types';
import { 
  Sparkles, 
  ArrowRight, 
  ShieldAlert, 
  CheckCircle2, 
  FileSearch, 
  Layers,
  ChevronRight
} from 'lucide-react';

export default function Dashboard() {
  const [screenings, setScreenings] = useState<ScreeningListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    screeningApi.history(1, 5).then(data => {
      setScreenings(data.items);
      setTotal(data.total);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const highPriority = screenings.filter(s => s.status === 'awaiting_review').length;
  const completed = screenings.filter(s => s.status === 'completed').length;

  return (
    <div className="space-y-10 animate-fade-in">
      {/* Hero Banner with Modern Call-to-Action */}
      <div className="relative rounded-2xl glass-panel p-8 sm:p-10 overflow-hidden border border-slate-800">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-cyan-500/10 via-blue-500/5 to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/70 border border-cyan-800/60 text-cyan-300 text-xs font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            Multi-Signal AI Screening Engine
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Screen proposed trademarks against conflicts in seconds.
          </h1>
          <p className="text-slate-400 text-base leading-relaxed">
            Evaluates phonetic resemblance, orthographic Levenshtein similarity, goods/services taxonomy overlaps, and Nice Class relationships using autonomous agents.
          </p>
          <div className="pt-2 flex flex-wrap gap-4">
            <Link
              to="/screen"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 transition-all group"
            >
              <span>Start New Screening</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/history"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700 font-semibold text-sm transition-all"
            >
              <span>Explore Audit Log</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard 
          label="Total Screenings" 
          value={total} 
          icon={FileSearch} 
          color="cyan"
          subtitle="Processed across jurisdictions"
        />
        <MetricCard 
          label="Completed Cases" 
          value={completed} 
          icon={CheckCircle2} 
          color="emerald"
          subtitle="All signals cross-analyzed"
        />
        <MetricCard 
          label="Awaiting Review" 
          value={highPriority} 
          icon={ShieldAlert} 
          color="amber"
          subtitle="High similarity detected"
        />
        <MetricCard 
          label="System Architecture" 
          value="4 Agents" 
          icon={Layers} 
          color="blue"
          subtitle="RapidFuzz + Metaphone + NLP"
        />
      </div>

      {/* Recent Screenings Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Recent Screening Audits</h2>
            <p className="text-slate-400 text-xs">Live feed of processed trademark clearance assessments</p>
          </div>
          <Link to="/history" className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
            View full log <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="glass-panel rounded-xl p-8 text-center text-slate-500 text-sm">
            Fetching recent screening activity...
          </div>
        ) : screenings.length === 0 ? (
          <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800/80 space-y-3">
            <FileSearch className="w-12 h-12 text-slate-600 mx-auto" />
            <h3 className="text-lg font-semibold text-white">No screenings found yet</h3>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              Run your first trademark conflict screening to evaluate similarity scores and generate audit reports.
            </p>
            <Link
              to="/screen"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm transition-colors"
            >
              Start First Screening
            </Link>
          </div>
        ) : (
          <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/50 text-[11px] uppercase tracking-wider text-slate-400">
                    <th className="px-6 py-4 font-semibold">Audit ID</th>
                    <th className="px-6 py-4 font-semibold">Proposed Mark</th>
                    <th className="px-6 py-4 font-semibold">Jurisdiction</th>
                    <th className="px-6 py-4 font-semibold">Audit Status</th>
                    <th className="px-6 py-4 font-semibold">Candidates</th>
                    <th className="px-6 py-4 font-semibold">Timestamp</th>
                    <th className="px-6 py-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {screenings.map(s => (
                    <tr key={s.screening_id} className="hover:bg-slate-800/30 transition-colors group">
                      <td className="px-6 py-4 font-mono font-medium text-cyan-400">
                        {s.screening_id}
                      </td>
                      <td className="px-6 py-4 font-semibold text-white">
                        {s.proposed_mark}
                      </td>
                      <td className="px-6 py-4 text-slate-300">
                        <span className="inline-flex items-center px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-xs">
                          {s.jurisdiction}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <StatusPill status={s.status} />
                      </td>
                      <td className="px-6 py-4 text-slate-300 font-medium">
                        {s.total_candidates} records
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-xs">
                        {s.created_at ? new Date(s.created_at).toLocaleString() : '-'}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/screen/${s.screening_id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 bg-cyan-950/40 hover:bg-cyan-900/40 px-3 py-1.5 rounded-md border border-cyan-800/40 transition-colors"
                        >
                          <span>Review</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value, icon: Icon, color, subtitle }: { 
  label: string; 
  value: string | number; 
  icon: any; 
  color: 'cyan' | 'emerald' | 'amber' | 'blue';
  subtitle: string;
}) {
  const colorStyles = {
    cyan: 'from-cyan-500/15 to-transparent text-cyan-400 border-cyan-500/20',
    emerald: 'from-emerald-500/15 to-transparent text-emerald-400 border-emerald-500/20',
    amber: 'from-amber-500/15 to-transparent text-amber-400 border-amber-500/20',
    blue: 'from-blue-500/15 to-transparent text-blue-400 border-blue-500/20',
  }[color];

  return (
    <div className={`glass-panel p-6 rounded-2xl border bg-gradient-to-b ${colorStyles} space-y-3`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">{label}</span>
        <Icon className="w-5 h-5 opacity-90" />
      </div>
      <div>
        <div className="text-3xl font-extrabold text-white tracking-tight">{value}</div>
        <p className="text-[11px] text-slate-500 mt-1">{subtitle}</p>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60',
    processing: 'bg-blue-950/60 text-blue-300 border-blue-800/60',
    pending: 'bg-slate-900 text-slate-400 border-slate-700',
    failed: 'bg-rose-950/60 text-rose-300 border-rose-800/60',
    awaiting_review: 'bg-amber-950/60 text-amber-300 border-amber-800/60',
    incomplete: 'bg-orange-950/60 text-orange-300 border-orange-800/60',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status] || styles.pending}`}>
      {status.replace('_', ' ').toUpperCase()}
    </span>
  );
}
