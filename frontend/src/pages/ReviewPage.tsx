import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { screeningApi, reviewApi } from '../services/api';
import type { ScreeningResponse, ReviewRequest, ReviewResponse } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  ShieldAlert, 
  ArrowLeft, 
  CheckCircle2, 
  UserCheck, 
  Send
} from 'lucide-react';
import confetti from 'canvas-confetti';

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<ScreeningResponse | null>(null);
  const [reviews, setReviews] = useState<ReviewResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const [form, setForm] = useState<ReviewRequest>({
    reviewer: '',
    decision: 'approved',
    notes: '',
  });

  useEffect(() => {
    if (!id) return;
    Promise.all([
      screeningApi.get(id).then(setResult),
      reviewApi.getAll(id).then(setReviews).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !form.reviewer.trim()) return;

    setSubmitting(true);
    try {
      const review = await reviewApi.submit(id, form);
      setReviews(prev => [review, ...prev]);
      setSubmitted(true);
      confetti({ particleCount: 40, spread: 50 });
    } catch {
      alert('Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading review case file..." />;
  if (!result) return <p className="text-rose-400">Screening record not found.</p>;

  const highMatches = result.matches.filter(m => m.priority === 'high');

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      <div>
        <Link to={`/screen/${id}`} className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-cyan-400 transition-colors mb-2">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to screening results
        </Link>
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <UserCheck className="w-8 h-8 text-cyan-400" />
            Human Review Console
          </h1>
          <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300">
            {result.screening_id}
          </span>
        </div>
        <p className="text-slate-400 text-sm mt-1">
          Specialist verification and sign-off for mark: <span className="text-white font-semibold">{result.proposed_mark}</span>
        </p>
      </div>

      {/* Flagged High Priority Candidates */}
      {highMatches.length > 0 && (
        <div className="p-6 rounded-2xl bg-rose-950/30 border border-rose-800/60 space-y-4 shadow-xl">
          <div className="flex items-center gap-2 text-rose-300 font-semibold text-base">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span>{highMatches.length} Critical Conflict Flag{highMatches.length > 1 ? 's' : ''} Requiring Disposition</span>
          </div>
          <div className="space-y-3">
            {highMatches.map(m => (
              <div key={m.trademark_id} className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-base">{m.mark_name}</span>
                    <span className="text-xs font-mono text-slate-500">({m.trademark_id})</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Text: {m.textual_similarity.toFixed(0)}% • Phonetic: {m.phonetic_similarity.toFixed(0)}% • Goods: {m.goods_overlap.toFixed(0)}%
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-xs font-semibold text-slate-500 uppercase">Score</div>
                  <div className="text-xl font-black text-rose-400">{m.combined_score.toFixed(0)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit Review Submissions */}
      {reviews.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white tracking-tight">Recorded Decisions</h2>
          <div className="space-y-3">
            {reviews.map(r => (
              <div key={r.id} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white text-sm">{r.reviewer}</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                    r.decision === 'approved' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
                    r.decision === 'rejected' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                    'bg-amber-950 text-amber-300 border border-amber-800'
                  }`}>
                    {r.decision}
                  </span>
                </div>
                {r.notes && <p className="text-slate-300 text-xs leading-relaxed">{r.notes}</p>}
                <div className="text-[11px] text-slate-500 font-mono">
                  {r.reviewed_at ? new Date(r.reviewed_at).toLocaleString() : ''}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Review Submission Form */}
      {!submitted ? (
        <form onSubmit={handleSubmit} className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-5 shadow-xl">
          <h2 className="text-lg font-bold text-white tracking-tight">Record Specialist Decision</h2>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Legal Examiner / Reviewer Name <span className="text-cyan-400">*</span>
            </label>
            <input
              type="text"
              value={form.reviewer}
              onChange={e => setForm(prev => ({ ...prev, reviewer: e.target.value }))}
              placeholder="e.g. Adv. Sharma, Lead IP Examiner"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 text-sm"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Disposition Decision <span className="text-cyan-400">*</span>
            </label>
            <select
              value={form.decision}
              onChange={e => setForm(prev => ({ ...prev, decision: e.target.value as ReviewRequest['decision'] }))}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 text-sm"
            >
              <option value="approved">Approved — No substantial conflict concern</option>
              <option value="rejected">Rejected — High likelihood of customer confusion</option>
              <option value="needs_more_info">Needs More Information / Further Evidence</option>
              <option value="escalated">Escalated — Require Senior Counsel / External Clearance</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Evaluation Rationale & Notes
            </label>
            <textarea
              value={form.notes || ''}
              onChange={e => setForm(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Record justification, prior rights analysis, or class distinction arguments..."
              rows={3}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 text-sm leading-relaxed"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-sm shadow-xl shadow-cyan-500/25 transition-all disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            <span>{submitting ? 'Recording Decision...' : 'Save Audit Decision'}</span>
          </button>
        </form>
      ) : (
        <div className="glass-panel p-8 rounded-2xl border border-emerald-800/60 bg-emerald-950/30 text-center space-y-3">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
          <h3 className="text-xl font-bold text-white">Review Successfully Logged</h3>
          <p className="text-slate-300 text-sm">Decision and examiner notes have been permanently stored in the audit trail.</p>
          <div className="pt-2">
            <Link
              to={`/screen/${id}`}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-colors"
            >
              Return to Results View
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
