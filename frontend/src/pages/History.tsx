import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { screeningApi } from '../services/api';
import type { ScreeningListItem } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  History as HistoryIcon, 
  Search, 
  ChevronRight, 
  ArrowRight
} from 'lucide-react';

export default function History() {
  const [items, setItems] = useState<ScreeningListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const pageSize = 10;

  const fetchHistory = (p: number) => {
    setLoading(true);
    screeningApi.history(p, pageSize)
      .then(data => {
        setItems(data.items);
        setTotal(data.total);
        setPage(data.page);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchHistory(1); }, []);

  const totalPages = Math.ceil(total / pageSize);

  const filteredItems = items.filter(it => 
    it.proposed_mark.toLowerCase().includes(searchFilter.toLowerCase()) ||
    it.screening_id.toLowerCase().includes(searchFilter.toLowerCase()) ||
    it.jurisdiction.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <HistoryIcon className="w-8 h-8 text-cyan-400" />
            Audit History & Records
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Complete persistent log of all performed trademark screening executions
          </p>
        </div>

        <Link
          to="/screen"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/20 transition-all self-start sm:self-auto"
        >
          <span>New Screening</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center gap-3">
        <Search className="w-4 h-4 text-slate-500 ml-1" />
        <input
          type="text"
          value={searchFilter}
          onChange={e => setSearchFilter(e.target.value)}
          placeholder="Search by mark name, screening ID, or jurisdiction..."
          className="bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none w-full"
        />
      </div>

      {loading ? (
        <LoadingSpinner message="Loading audit history records..." />
      ) : filteredItems.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl text-center space-y-4">
          <HistoryIcon className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-lg font-semibold text-white">No records matched your search</h3>
          <p className="text-slate-400 text-sm">Try adjusting your query or initiate a new trademark screening.</p>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/60 text-[11px] uppercase tracking-wider text-slate-400">
                  <th className="px-6 py-4 font-semibold">Screening ID</th>
                  <th className="px-6 py-4 font-semibold">Proposed Mark</th>
                  <th className="px-6 py-4 font-semibold">Jurisdiction</th>
                  <th className="px-6 py-4 font-semibold">Audit State</th>
                  <th className="px-6 py-4 font-semibold">Candidates</th>
                  <th className="px-6 py-4 font-semibold">Date Completed</th>
                  <th className="px-6 py-4 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredItems.map(item => (
                  <tr key={item.screening_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-cyan-400">
                      {item.screening_id}
                    </td>
                    <td className="px-6 py-4 font-semibold text-white">
                      {item.proposed_mark}
                    </td>
                    <td className="px-6 py-4 text-slate-300">
                      <span className="inline-flex items-center px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-xs">
                        {item.jurisdiction}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                        item.status === 'completed' 
                          ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                          : item.status === 'awaiting_review'
                          ? 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                          : 'bg-slate-900 text-slate-400 border-slate-800'
                      }`}>
                        {item.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-300 font-medium">
                      {item.total_candidates}
                    </td>
                    <td className="px-6 py-4 text-slate-500 text-xs">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/screen/${item.screening_id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 bg-cyan-950/40 hover:bg-cyan-900/40 px-3 py-1.5 rounded-md border border-cyan-800/40 transition-colors"
                      >
                        <span>View</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <span>Showing Page {page} of {totalPages}</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => fetchHistory(page - 1)}
                  disabled={page <= 1}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => fetchHistory(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
