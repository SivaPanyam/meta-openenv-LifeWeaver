import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Zap, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';

const App = () => {
  const [data, setData] = useState({ events: [], stress: 0, travel_time: 0 });
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    console.log(">> Fetching from http://localhost:8000/reset");
    try {
      const response = await fetch('http://localhost:8000/reset');
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const json = await response.json();
      console.log(">> Data received:", json);
      
      setData({
        events: Array.isArray(json.events) ? json.events : [],
        stress: json.full_state?.stress || 0,
        travel_time: json.full_state?.travel_time || 0
      });
    } catch (err) {
      console.error(">> Fetch error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const response = await fetch('http://localhost:8000/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const json = await response.json();
      setData(prev => ({ ...prev, events: json.events || [] }));
    } catch (err) {
      console.error(">> Optimize error:", err);
      alert("Optimization failed. Check console.");
    } finally {
      setOptimizing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getPriorityColor = (prio) => {
    switch (prio?.toLowerCase()) {
      case 'high': return 'bg-red-100 border-red-500 text-red-700';
      case 'medium': return 'bg-yellow-100 border-yellow-500 text-yellow-700';
      case 'low': return 'bg-green-100 border-green-500 text-green-700';
      default: return 'bg-gray-100 border-gray-400 text-gray-700';
    }
  };

  const timeSlots = ["18:00", "19:00", "20:00", "21:00", "22:00"];

  if (error) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-gray-900 text-white p-10">
        <AlertTriangle size={64} className="text-red-500 mb-4" />
        <h2 className="text-3xl font-bold">Backend Connection Failed</h2>
        <p className="text-gray-400 mt-2">Is the FastAPI server running on port 8000?</p>
        <code className="bg-black p-4 rounded mt-4 text-red-400">{error}</code>
        <button onClick={fetchData} className="mt-6 px-8 py-3 bg-indigo-600 rounded-lg font-bold hover:bg-indigo-700">Retry</button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen bg-gray-50 overflow-hidden font-sans">
      {/* Top Navigation */}
      <header className="flex items-center justify-between px-10 py-5 bg-white border-b shadow-sm z-20">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-600 rounded-xl text-white shadow-indigo-200 shadow-lg">
            <Calendar size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight">LifeWeaver</h1>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Smart Schedule AI</p>
          </div>
        </div>

        <div className="flex items-center gap-8">
          <div className="flex gap-10">
             <div className="border-l pl-6">
                <p className="text-[10px] font-black text-gray-400 uppercase">Stress</p>
                <p className="text-xl font-mono font-black text-indigo-600">{data.stress.toFixed(2)}</p>
             </div>
             <div className="border-l pl-6">
                <p className="text-[10px] font-black text-gray-400 uppercase">Travel</p>
                <p className="text-xl font-mono font-black text-indigo-600">{data.travel_time}m</p>
             </div>
          </div>
          <div className="flex gap-3">
            <button onClick={fetchData} className="p-3 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all">
              <RefreshCw size={24} className={loading ? 'animate-spin' : ''} />
            </button>
            <button 
              onClick={handleOptimize}
              disabled={optimizing}
              className="flex items-center gap-2 px-8 py-3 bg-gray-900 hover:bg-indigo-600 text-white rounded-xl transition-all font-bold shadow-lg disabled:opacity-50"
            >
              <Zap size={18} fill="currentColor" />
              {optimizing ? 'Optimizing...' : 'Optimize'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 overflow-hidden p-10 flex gap-10">
        
        {/* Calendar View */}
        <div className="flex-1 bg-white rounded-3xl shadow-xl border border-gray-100 flex flex-col overflow-hidden">
          <div className="p-8 border-b bg-gray-50 flex justify-between items-center">
            <h2 className="text-xl font-black text-gray-800 flex items-center gap-3">
              <Clock className="text-indigo-500" />
              Evening Agenda
            </h2>
            <span className="text-sm font-bold text-gray-400">18:00 — 22:00</span>
          </div>

          <div className="flex-1 overflow-y-auto p-10 relative">
            <div className="relative border-l-4 border-indigo-50 ml-24 h-full">
              {timeSlots.map((time) => (
                <div key={time} className="relative h-40 border-t-2 border-gray-50">
                  <span className="absolute -left-24 -top-4 w-20 text-right font-black text-sm text-gray-300">
                    {time}
                  </span>
                  
                  {/* Events Container */}
                  <div className="absolute inset-0 flex flex-wrap gap-4 p-6">
                    {data.events
                      .filter(e => {
                        const h = e.time?.split(':')[0];
                        const slotH = time.split(':')[0];
                        return h === slotH || (parseInt(h) + 12).toString() === slotH;
                      })
                      .map((event, i) => (
                        <div key={i} className={`min-w-[250px] p-5 rounded-2xl border-l-8 shadow-sm transition-all hover:scale-[1.02] hover:shadow-xl ${getPriorityColor(event.priority)}`}>
                          <div className="flex justify-between items-start mb-3">
                            <span className="text-[10px] font-black uppercase opacity-50 tracking-tighter">
                              {event.source}
                            </span>
                            {event.status === 'rescheduled' && <CheckCircle2 size={16} className="text-green-600" />}
                          </div>
                          <h3 className="text-md font-black leading-tight mb-2 uppercase">
                            {event.type?.replace(/_/g, ' ')}
                          </h3>
                          <div className="flex items-center gap-2 text-[11px] font-bold opacity-70">
                            <Clock size={12} /> {event.time} ({event.duration}m)
                          </div>
                        </div>
                      ))
                    }
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Info Sidebar */}
        <div className="w-96 flex flex-col gap-8">
          <div className="bg-indigo-600 rounded-3xl p-8 text-white shadow-2xl relative overflow-hidden">
             <div className="absolute -right-10 -bottom-10 opacity-10">
                <Zap size={200} />
             </div>
             <h3 className="text-lg font-black uppercase tracking-widest mb-4">AI Insight</h3>
             <p className="text-indigo-100 text-sm leading-relaxed font-medium">
               Multi-agent coordination is active. The system is balancing your high-priority work commitments while protecting your social and personal flexibility.
             </p>
          </div>

          <div className="bg-white rounded-3xl p-8 border shadow-lg flex-1">
             <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-6 border-b pb-4">Activity Log</h3>
             <div className="space-y-6">
                {data.events.some(e => e.status === 'rescheduled') ? (
                  <div className="flex gap-4">
                    <div className="w-2 h-2 rounded-full bg-green-500 mt-2" />
                    <p className="text-sm font-bold text-gray-600">Optimal schedule found. Flexible tasks shifted.</p>
                  </div>
                ) : (
                  <div className="flex gap-4 opacity-40">
                    <div className="w-2 h-2 rounded-full bg-gray-300 mt-2" />
                    <p className="text-sm font-bold text-gray-500">Awaiting optimization signal...</p>
                  </div>
                )}
             </div>
          </div>
        </div>

      </main>
    </div>
  );
};

export default App;
