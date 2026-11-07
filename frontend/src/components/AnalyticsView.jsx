import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { ShieldCheck, ShieldAlert, AlertTriangle, RefreshCw, TrendingUp } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const AnalyticsView = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/analytics`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading && !data) {
    return (
      <div className="glass p-12 flex items-center justify-center text-slate-400 gap-3">
        <RefreshCw className="animate-spin text-blue-400" size={24} />
        <span>Loading analytics data...</span>
      </div>
    );
  }

  const breakdown = data?.breakdown || { mask: 0, no_mask: 0, incorrect_mask: 0 };
  const pieData = data?.pie_chart || [];
  const hourlyData = data?.hourly_trend || [];
  const complianceRate = data?.compliance_rate ?? 100;
  const totalDetections = data?.total_detections ?? 0;

  return (
    <div className="flex flex-col gap-6">
      {/* Metric KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass p-5 flex items-center justify-between border-l-4 border-l-blue-500">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">Total Detections</p>
            <h3 className="text-2xl font-bold text-white mt-1">{totalDetections.toLocaleString()}</h3>
          </div>
          <TrendingUp className="text-blue-400 opacity-80" size={28} />
        </div>

        <div className="glass p-5 flex items-center justify-between border-l-4 border-l-emerald-500">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">Compliance Rate</p>
            <h3 className="text-2xl font-bold text-emerald-400 mt-1">{complianceRate}%</h3>
          </div>
          <ShieldCheck className="text-emerald-400 opacity-80" size={28} />
        </div>

        <div className="glass p-5 flex items-center justify-between border-l-4 border-l-rose-500">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">No Mask Violations</p>
            <h3 className="text-2xl font-bold text-rose-400 mt-1">{breakdown.no_mask.toLocaleString()}</h3>
          </div>
          <ShieldAlert className="text-rose-400 opacity-80" size={28} />
        </div>

        <div className="glass p-5 flex items-center justify-between border-l-4 border-l-amber-500">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">Incorrect Mask</p>
            <h3 className="text-2xl font-bold text-amber-400 mt-1">{breakdown.incorrect_mask.toLocaleString()}</h3>
          </div>
          <AlertTriangle className="text-amber-400 opacity-80" size={28} />
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compliance Distribution Pie Chart */}
        <div className="glass p-6 flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-lg text-slate-100">Compliance Distribution</h3>
            <button 
              onClick={fetchAnalytics}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 bg-slate-800/80 px-2.5 py-1 rounded">
              <RefreshCw size={12} /> Refresh
            </button>
          </div>
          <div className="h-[280px]">
            {totalDetections === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                No detection data recorded yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={95}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px' }}
                    itemStyle={{ color: '#f8fafc' }}
                  />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Activity Trend Bar Chart */}
        <div className="glass p-6 flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-lg text-slate-100">Recent Activity Timeline</h3>
            <span className="text-xs text-slate-400">Events by hour</span>
          </div>
          <div className="h-[280px]">
            {hourlyData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                Awaiting activity events
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hourlyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="hour" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px' }}
                    itemStyle={{ color: '#f8fafc' }}
                  />
                  <Bar dataKey="detections" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsView;

