import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { screeningApi, classesApi } from '../services/api';
import type { NiceClass, ScreeningRequest } from '../types';
import { 
  Search, 
  Sparkles, 
  Tag, 
  Globe2, 
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';

const JURISDICTIONS = [
  { code: 'IN', name: 'India (IP India)', flag: '🇮🇳' },
  { code: 'US', name: 'United States (USPTO)', flag: '🇺🇸' },
  { code: 'GB', name: 'United Kingdom (UKIPO)', flag: '🇬🇧' },
  { code: 'EU', name: 'European Union (EUIPO)', flag: '🇪🇺' },
  { code: 'JP', name: 'Japan (JPO)', flag: '🇯🇵' },
  { code: 'AU', name: 'Australia (IP Australia)', flag: '🇦🇺' },
  { code: 'CA', name: 'Canada (CIPO)', flag: '🇨🇦' },
  { code: 'SG', name: 'Singapore (IPOS)', flag: '🇸🇬' },
];

export default function NewScreening() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [niceClasses, setNiceClasses] = useState<NiceClass[]>([]);
  const [classFilter, setClassFilter] = useState('');

  const [form, setForm] = useState<ScreeningRequest>({
    brand_name: '',
    goods: '',
    nice_class: undefined,
    nice_classes: [],
    jurisdiction: 'IN',
  });

  useEffect(() => {
    classesApi.getAll().then(setNiceClasses).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!form.brand_name.trim()) {
      setError('Please provide the proposed trademark word mark');
      return;
    }
    if (!form.goods.trim()) {
      setError('Please specify the goods or services description');
      return;
    }

    setLoading(true);
    try {
      const result = await screeningApi.create(form);
      navigate(`/screen/${result.screening_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Screening failed';
      setError(msg);
      setLoading(false);
    }
  };

  const toggleClass = (classNum: number) => {
    setForm(prev => {
      const classes = prev.nice_classes || [];
      const updated = classes.includes(classNum)
        ? classes.filter(c => c !== classNum)
        : [...classes, classNum];
      return { ...prev, nice_classes: updated, nice_class: updated[0] };
    });
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-6">
        <LoadingSpinner message="Coordinating Multi-Agent Screening..." />
        <div className="space-y-2 text-xs text-slate-400 max-w-md mx-auto">
          <p className="flex items-center justify-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            Normalizing mark variants & double-metaphone phonetic keys
          </p>
          <p className="text-slate-500">Cross-referencing goods descriptions against Nice classes 1-45</p>
        </div>
      </div>
    );
  }

  const filteredClasses = niceClasses.filter(nc => 
    nc.title.toLowerCase().includes(classFilter.toLowerCase()) ||
    nc.class_number.toString().includes(classFilter)
  );

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/50 text-cyan-400 text-xs font-medium">
          <Sparkles className="w-3.5 h-3.5" />
          Autonomous Multi-Signal Screening
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Initiate Trademark Screening</h1>
        <p className="text-slate-400 text-sm">
          Submit your candidate mark to trigger deterministic multi-agent similarity scoring across phonetic, textual, and goods classification axes.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800/80 text-rose-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-400" />
          <div>{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-6 shadow-xl">
          {/* Trademark Name */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-slate-200">
              Proposed Word Mark <span className="text-cyan-400">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                value={form.brand_name}
                onChange={e => setForm(prev => ({ ...prev, brand_name: e.target.value }))}
                placeholder="e.g. Nykka, QuickCraft, KwikPay"
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-3.5 text-white font-medium placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition-all text-base"
                maxLength={200}
                required
              />
            </div>
            <p className="text-xs text-slate-500">Case-insensitive. Normalized automatically for phonetic comparison.</p>
          </div>

          {/* Description of Goods */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-slate-200">
              Goods and Services Description <span className="text-cyan-400">*</span>
            </label>
            <textarea
              value={form.goods}
              onChange={e => setForm(prev => ({ ...prev, goods: e.target.value }))}
              placeholder="e.g. Cosmetics and skincare products, facial moisturizers, beauty serums..."
              rows={3}
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition-all text-sm leading-relaxed"
              maxLength={1000}
              required
            />
            <p className="text-xs text-slate-500">
              The Class Overlap Agent parses semantics to calculate category similarity scores.
            </p>
          </div>

          {/* Jurisdiction */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Globe2 className="w-4 h-4 text-cyan-400" />
              Target Jurisdiction
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {JURISDICTIONS.map(j => {
                const isSelected = form.jurisdiction === j.code;
                return (
                  <button
                    key={j.code}
                    type="button"
                    onClick={() => setForm(prev => ({ ...prev, jurisdiction: j.code }))}
                    className={`flex items-center gap-2 p-3 rounded-xl border text-left transition-all text-xs font-medium ${
                      isSelected
                        ? 'bg-cyan-950/70 border-cyan-500/80 text-cyan-300 shadow-sm shadow-cyan-500/20 ring-1 ring-cyan-500/30'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                    }`}
                  >
                    <span className="text-base">{j.flag}</span>
                    <span className="truncate">{j.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Nice Classification Picker */}
          <div className="space-y-3 pt-2 border-t border-slate-800">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Tag className="w-4 h-4 text-cyan-400" />
                  Nice Classification Classes (Optional)
                </label>
                <p className="text-xs text-slate-500">Pick classes or let the system infer automatically.</p>
              </div>
              <input
                type="text"
                value={classFilter}
                onChange={e => setClassFilter(e.target.value)}
                placeholder="Filter classes..."
                className="bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-full sm:w-48"
              />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 max-h-56 overflow-y-auto p-2 bg-slate-950/70 rounded-xl border border-slate-800">
              {filteredClasses.map(nc => {
                const isChecked = (form.nice_classes || []).includes(nc.class_number);
                return (
                  <button
                    key={nc.class_number}
                    type="button"
                    onClick={() => toggleClass(nc.class_number)}
                    className={`px-3 py-2 rounded-lg text-left text-xs font-medium transition-all flex items-center justify-between border ${
                      isChecked
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-sm'
                        : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-300'
                    }`}
                    title={nc.title}
                  >
                    <span className="truncate font-semibold">Class {nc.class_number}</span>
                    {isChecked && <CheckCircle className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 ml-1" />}
                  </button>
                );
              })}
            </div>

            {(form.nice_classes || []).length > 0 && (
              <div className="flex items-center gap-2 text-xs text-cyan-400 pt-1">
                <span>Selected:</span>
                <div className="flex flex-wrap gap-1">
                  {(form.nice_classes || []).sort((a,b) => a - b).map(c => (
                    <span key={c} className="px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 font-mono text-[11px]">
                      Class {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Form Submission */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-xs text-slate-500">
            Automated screening on demonstration dataset. Does not guarantee absolute non-conflict.
          </div>
          <button
            type="submit"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-sm shadow-xl shadow-cyan-500/25 transition-all group"
          >
            <Search className="w-4 h-4 group-hover:scale-110 transition-transform" />
            <span>Launch Multi-Agent Screening</span>
          </button>
        </div>
      </form>
    </div>
  );
}
