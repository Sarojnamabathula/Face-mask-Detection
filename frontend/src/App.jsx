import React, { useState, useEffect } from 'react';
import { Camera, Activity, AlertTriangle, History, PieChart, ShieldAlert } from 'lucide-react';
import LiveFeed from './components/LiveFeed';
import AnalyticsView from './components/AnalyticsView';
import HistoryView from './components/HistoryView';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [systemOnline, setSystemOnline] = useState(false);
  const [activeAlerts, setActiveAlerts] = useState(0);

  // Poll system health and active alerts
  useEffect(() => {
    const checkSystem = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        setSystemOnline(res.ok);
      } catch {
        setSystemOnline(false);
      }

      try {
        const res = await fetch(`${API_BASE}/api/analytics`);
        if (res.ok) {
          const data = await res.json();
          const alerts = (data.breakdown?.no_mask || 0) + (data.breakdown?.incorrect_mask || 0);
          setActiveAlerts(alerts);
        }
      } catch {
        // keep previous state
      }
    };

    checkSystem();
    const interval = setInterval(checkSystem, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex bg-dark-bg text-slate-200 font-sans">
      {/* Sidebar */}
      <aside className="w-64 glass m-4 mr-0 p-6 flex flex-col gap-8 h-[calc(100vh-2rem)] shrink-0">
        <div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 flex items-center gap-2">
            <Camera className="text-blue-400" />
            FaceMask AI
          </h1>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider">Enterprise Security</p>
        </div>

        <nav className="flex flex-col gap-2">
          <button 
            onClick={() => setActiveTab('live')}
            className={`flex items-center gap-3 p-3 rounded-lg transition-colors font-medium text-sm ${
              activeTab === 'live' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'hover:bg-slate-800 text-slate-400'
            }`}>
            <Activity size={18} />
            Live Feed
          </button>
          <button 
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-3 p-3 rounded-lg transition-colors font-medium text-sm ${
              activeTab === 'analytics' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'hover:bg-slate-800 text-slate-400'
            }`}>
            <PieChart size={18} />
            Analytics
          </button>
          <button 
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-3 p-3 rounded-lg transition-colors font-medium text-sm ${
              activeTab === 'history' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'hover:bg-slate-800 text-slate-400'
            }`}>
            <History size={18} />
            History Log
          </button>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-4 h-screen overflow-y-auto">
        <header className="glass mb-6 p-4 flex justify-between items-center">
          <h2 className="text-xl font-semibold capitalize">{activeTab} Dashboard</h2>
          <div className="flex gap-4">
            {systemOnline ? (
              <div className="flex items-center gap-2 text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-full text-xs font-semibold border border-emerald-400/20">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                System Online
              </div>
            ) : (
              <div className="flex items-center gap-2 text-rose-400 bg-rose-400/10 px-3 py-1.5 rounded-full text-xs font-semibold border border-rose-400/20">
                <span className="w-2 h-2 rounded-full bg-rose-400"></span>
                API Offline
              </div>
            )}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${
              activeAlerts > 0 ? 'text-amber-400 bg-amber-400/10 border-amber-400/20' : 'text-slate-400 bg-slate-800 border-slate-700'
            }`}>
              <AlertTriangle size={14} />
              {activeAlerts} Violations Logged
            </div>
          </div>
        </header>

        {/* Tab Content */}
        {activeTab === 'live' && <LiveFeed />}
        {activeTab === 'analytics' && <AnalyticsView />}
        {activeTab === 'history' && <HistoryView />}
      </main>
    </div>
  );
}

export default App;
