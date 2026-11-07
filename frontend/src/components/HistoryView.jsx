import React, { useState, useEffect } from 'react';
import { History, Trash2, RefreshCw, Filter, ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const HistoryView = () => {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const url = filter === 'all' 
        ? `${API_BASE}/api/history?limit=100` 
        : `${API_BASE}/api/history?limit=100&prediction=${encodeURIComponent(filter)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
        setTotal(data.total || 0);
      }
    } catch (err) {
      console.error('Failed to load history logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (!window.confirm("Are you sure you want to clear all history records?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/history`, { method: 'DELETE' });
      if (res.ok) {
        fetchLogs();
      }
    } catch (err) {
      console.error('Failed to clear history:', err);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filter]);

  const renderBadge = (pred) => {
    if (pred === 'Mask') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <ShieldCheck size={13} /> Compliant
        </span>
      );
    } else if (pred === 'No Mask') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <ShieldAlert size={13} /> No Mask
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <AlertTriangle size={13} /> Incorrect Mask
        </span>
      );
    }
  };

  return (
    <div className="glass p-6 flex flex-col gap-6">
      {/* Top action bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-glass-border pb-4">
        <div>
          <h3 className="font-semibold text-lg text-slate-100 flex items-center gap-2">
            <History size={20} className="text-blue-400" />
            Detection Event Logs
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Showing {logs.length} of {total} total recorded events</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Status filters */}
          <div className="flex items-center bg-slate-800/80 p-1 rounded-lg border border-slate-700 text-xs">
            {['all', 'Mask', 'No Mask', 'Incorrect Mask'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-md capitalize transition-colors ${
                  filter === f ? 'bg-blue-600 text-white font-medium shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <button
            onClick={fetchLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors border border-slate-700"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>

          <button
            onClick={handleClearHistory}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs transition-colors border border-rose-500/20"
          >
            <Trash2 size={14} />
            Clear Logs
          </button>
        </div>
      </div>

      {/* Log Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-700/60 text-slate-400 text-xs uppercase tracking-wider">
              <th className="py-3 px-4">Log ID</th>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Subject Tracking ID</th>
              <th className="py-3 px-4">Camera</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {loading && logs.length === 0 ? (
              <tr>
                <td colSpan="6" className="py-12 text-center text-slate-500">
                  <RefreshCw className="animate-spin inline-block mb-2 text-blue-400" size={20} />
                  <p>Fetching records...</p>
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan="6" className="py-12 text-center text-slate-500">
                  No detection records found for this filter.
                </td>
              </tr>
            ) : (
              logs.map((row) => (
                <tr key={row.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 text-slate-400 font-mono text-xs">#{row.id}</td>
                  <td className="py-3 px-4 text-slate-300 text-xs font-mono">
                    {row.timestamp ? new Date(row.timestamp).toLocaleString() : 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-slate-200 font-medium">
                    {row.tracking_id !== null ? `ID: #${row.tracking_id}` : 'Unassigned'}
                  </td>
                  <td className="py-3 px-4 text-slate-400 text-xs">{row.camera_id || 'CAM-01'}</td>
                  <td className="py-3 px-4">{renderBadge(row.prediction)}</td>
                  <td className="py-3 px-4 text-slate-300 font-mono text-xs">
                    {(row.confidence * 100).toFixed(1)}%
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default HistoryView;

