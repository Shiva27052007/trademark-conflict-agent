import type { MatchResult } from '../types';
import { 
  AlertTriangle, 
  ChevronDown, 
  Volume2,
  FileText,
  Tag
} from 'lucide-react';
import { useState } from 'react';

interface Props {
  match: MatchResult;
  rank: number;
}

export default function MatchCard({ match, rank }: Props) {
  const [expanded, setExpanded] = useState(false);

  const priorityStyles: Record<string, { bg: string; text: string; border: string; badge: string }> = {
    high: {
      bg: 'from-rose-500/10 via-slate-900 to-slate-900',
      text: 'text-rose-400',
      border: 'border-rose-500/30 hover:border-rose-500/50',
      badge: 'bg-rose-950/80 text-rose-300 border-rose-800/80',
    },
    medium: {
      bg: 'from-amber-500/10 via-slate-900 to-slate-900',
      text: 'text-amber-400',
      border: 'border-amber-500/30 hover:border-amber-500/50',
      badge: 'bg-amber-950/80 text-amber-300 border-amber-800/80',
    },
    low: {
      bg: 'from-emerald-500/10 via-slate-900 to-slate-900',
      text: 'text-emerald-400',
      border: 'border-emerald-500/20 hover:border-emerald-500/40',
      badge: 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80',
    },
    insufficient: {
      bg: 'from-slate-800/20 via-slate-900 to-slate-900',
      text: 'text-slate-400',
      border: 'border-slate-800',
      badge: 'bg-slate-900 text-slate-400 border-slate-800',
    },
  };

  const pConfig = priorityStyles[match.priority] || priorityStyles.insufficient;

  return (
    <div className={`rounded-2xl border ${pConfig.border} bg-gradient-to-r ${pConfig.bg} p-6 shadow-xl transition-all duration-300`}>
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-slate-800/90 border border-slate-700/80 flex items-center justify-center font-bold text-sm text-cyan-400 shadow-inner">
            #{rank}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xl font-bold text-white tracking-tight">{match.mark_name}</h3>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase border ${pConfig.badge}`}>
                {match.priority} PRIORITY
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Registry ID: <span className="text-slate-300">{match.trademark_id}</span> • Jurisdiction: {match.jurisdiction}
            </p>
          </div>
        </div>

        {/* Combined Screening Score Circle / Metric */}
        <div className="flex items-center gap-3 self-end sm:self-auto bg-slate-950/60 px-4 py-2 rounded-xl border border-slate-800">
          <div className="text-right">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Conflict Score</div>
            <div className={`text-2xl font-black ${pConfig.text} leading-none mt-0.5`}>
              {match.combined_score.toFixed(0)}<span className="text-xs text-slate-500 font-normal">/100</span>
            </div>
          </div>
        </div>
      </div>

      {/* Signal Bars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 mb-5 p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/80">
        <SignalProgress 
          label="Textual Match" 
          value={match.textual_similarity} 
          icon={FileText} 
          barColor="bg-blue-500" 
        />
        <SignalProgress 
          label="Phonetic Match" 
          value={match.phonetic_similarity} 
          icon={Volume2} 
          barColor="bg-purple-500" 
        />
        <SignalProgress 
          label="Goods Overlap" 
          value={match.goods_overlap} 
          icon={Tag} 
          barColor="bg-emerald-500" 
        />
      </div>

      {/* Nice Class Badges */}
      {match.nice_classes && match.nice_classes.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap mb-4">
          <span className="text-xs text-slate-400">Class Coverage:</span>
          {match.nice_classes.map(c => (
            <span key={c} className="px-2 py-0.5 rounded-md bg-slate-800/80 border border-slate-700/60 text-[11px] font-mono text-cyan-300">
              Class {c}
            </span>
          ))}
        </div>
      )}

      {/* Escalation Flag */}
      {match.requires_human_review && (
        <div className="flex items-center gap-2.5 p-3 rounded-xl bg-amber-950/40 border border-amber-800/50 text-amber-300 text-xs mb-4">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-400" />
          <span>This match scores above review thresholds and is marked for legal specialist review.</span>
        </div>
      )}

      {/* Expandable Explanation Details */}
      <div className="pt-2 border-t border-slate-800/60">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-between w-full text-xs font-semibold text-cyan-400 hover:text-cyan-300 py-1 transition-colors"
        >
          <span>{expanded ? 'Hide evidence & analysis breakdown' : 'Inspect evidence, metaphone keys & agent rationale'}</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </button>

        {expanded && (
          <div className="mt-3 p-4 rounded-xl bg-slate-950 border border-slate-800/90 space-y-3 animate-fade-in text-xs font-mono">
            <div className="text-slate-300 whitespace-pre-wrap leading-relaxed">
              {match.explanation}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SignalProgress({ label, value, icon: Icon, barColor }: { 
  label: string; 
  value: number; 
  icon: any; 
  barColor: string; 
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400 flex items-center gap-1.5 font-medium">
          <Icon className="w-3.5 h-3.5 text-slate-500" />
          {label}
        </span>
        <span className="font-mono font-bold text-slate-200">{value.toFixed(0)}%</span>
      </div>
      <div className="w-full bg-slate-800/90 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  );
}
