import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { screeningApi, reportApi } from '../services/api';
import type { ScreeningResponse } from '../types';
import MatchCard from '../components/MatchCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  Download, 
  ArrowLeft, 
  AlertTriangle, 
  CheckCircle2
} from 'lucide-react';
import confetti from 'canvas-confetti';

export default function ScreeningResults() {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<ScreeningResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [filterPriority, setFilterPriority] = useState<string>('all');

  useEffect(() => {
    if (!id) return;
    screeningApi.get(id)
      .then(res => {
        setResult(res);
        if (res.matches.length > 0 && res.matches.every(m => m.priority === 'low' || m.priority === 'insufficient')) {
          confetti({ particleCount: 50, spread: 60, origin: { y: 0.7 } });
        }
      })
      .catch(() => setError('Failed to load screening results'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDownload = async () => {
    if (!id) return;
    setDownloading(true);
    try {
      await reportApi.download(id);
    } catch {
      alert('Unable to generate or download report.');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Retrieving screening analysis & matches..." />;
  }

  if (error || !result) {
    return (
      <div className="glass-panel max-w-lg mx-auto my-12 p-8 rounded-2xl text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-rose-400 mx-auto" />
        <h2 className="text-xl font-bold text-white">Record Not Found</h2>
        <p className="text-slate-400 text-sm">{error || 'Could not locate the requested screening session.'}</p>
        <Link
          to="/screen"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Start New Screening
        </Link>
      </div>
    );
  }

  const matches = result.matches || [];
  const filteredMatches = filterPriority === 'all' 
    ? matches 
    : matches.filter(m => m.priority === filterPriority);

  const highPriorityCount = matches.filter(m => m.priority === 'high').length;
  const mediumPriorityCount = matches.filter(m => m.priority === 'medium').length;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Breadcrumb & Action bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link to="/" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-cyan-400 transition-colors mb-2">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Screening Results for <span className="text-cyan-400">"{result.proposed_mark}"</span>
            </h1>
            <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300">
              {result.screening_id}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            <span>{downloading ? 'Compiling PDF...' : 'Download PDF Report'}</span>
          </button>
          {result.status === 'awaiting_review' && (
            <Link
              to={`/review/${result.screening_id}`}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-sm shadow-lg shadow-amber-500/20 transition-all"
            >
              <span>Human Review</span>
            </Link>
          )}
        </div>
      </div>

      {/* Summary KPI Panel */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Candidate Mark</span>
            <div className="text-2xl font-bold text-white mt-1">{result.proposed_mark}</div>
          </div>
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Jurisdiction</span>
            <div className="text-2xl font-bold text-cyan-400 mt-1">{result.jurisdiction}</div>
          </div>
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Audit Assessment</span>
            <div className="mt-1">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                result.status === 'completed'
                  ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/80'
                  : 'bg-amber-950/80 text-amber-300 border border-amber-800/80'
              }`}>
                {result.status === 'completed' ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                {result.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          </div>
          <div>
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Matches Evaluated</span>
            <div className="text-2xl font-bold text-white mt-1">{result.total_candidates}</div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
          <div>
            Coverage Status: <span className="text-slate-200 font-mono">{result.search_completeness}</span>
          </div>
          <div>
            High Priority Conflicts: <span className="text-rose-400 font-bold">{highPriorityCount}</span> • 
            Medium Priority: <span className="text-amber-400 font-bold ml-1">{mediumPriorityCount}</span>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between flex-wrap gap-4 pt-2">
        <div className="flex items-center gap-2">
          {['all', 'high', 'medium', 'low'].map(p => (
            <button
              key={p}
              type="button"
              onClick={() => setFilterPriority(p)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
                filterPriority === p
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {p} Matches {p === 'all' ? `(${matches.length})` : ''}
            </button>
          ))}
        </div>
      </div>

      {/* Matches List */}
      {filteredMatches.length > 0 ? (
        <div className="space-y-4">
          {filteredMatches.map((match, i) => (
            <MatchCard key={match.trademark_id} match={match} rank={i + 1} />
          ))}
        </div>
      ) : (
        <div className="glass-panel p-12 rounded-2xl text-center space-y-3">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
          <h3 className="text-lg font-bold text-white">No matches found for this filter</h3>
          <p className="text-slate-400 text-sm">No candidate trademarks matched the selected criteria.</p>
        </div>
      )}

      {/* Standard Disclaimer Notice */}
      <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 text-[11px] text-slate-500 leading-relaxed">
        <strong className="text-slate-400">LegalTech Transparency Notice:</strong> Preliminary algorithmic screening results are generated for guidance and do not guarantee trademark clearance or non-infringement. Always obtain a formal search and opinion from qualified trademark counsel before filing.
      </div>
    </div>
  );
}
