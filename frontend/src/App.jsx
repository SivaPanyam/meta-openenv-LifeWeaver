import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Zap, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';

const App = () => {
  const [data, setData] = useState({ events: [], stress: 0, travel_time: 0 });
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/reset');
      const json = await response.json();
      setData(json);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }
    setLoading(false);
  };

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const response = await fetch('http://localhost:8000/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events: data.events }),
      });
      const json = await response.json();
      setData({ ...data, events: json.events });
    } catch (error) {
      console.error('Failed to optimize:', error);
    }
    setOptimizing(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getPriorityColor = (prio) => {
    switch (prio) {
      case 'high': return 'bg-red-100 border-red-500 text-red-700';
      case 'medium': return 'bg-yellow-100 border-yellow-500 text-yellow-700';
      case 'low': return 'bg-green-100 border-green-500 text-green-700';
      default: return 'bg-gray-100 border-gray-500 text-gray-700';
    }
  };

  const timeSlots = ["18:00", "19:00", "20:00", "21:00", "22:00"];

  return (
    <div className="flex flex-col h-screen w-screen bg-gray-50 overflow-hidden font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-4 bg-white border-b shadow-sm z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-600 rounded-lg text-white">
            <Calendar size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">LifeWeaver</h1>
            <p className="text-sm text-gray-500 font-medium">
              {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex gap-8">
            <div className="text-center">
              <p className="text-xs text-gray-400 uppercase tracking-widest font-bold">Stress Index</p>
              <p className="text-lg font-mono font-bold text-indigo-600">{data.stress.toFixed(2)}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-400 uppercase tracking-widest font-bold">Travel Time</p>
              <p className="text-lg font-mono font-bold text-indigo-600">{data.travel_time}m</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button 
              onClick={fetchData}
              className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-full transition-all font-semibold"
            >
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
              Reset
            </button>
            <button 
              onClick={handleOptimize}
              disabled={optimizing}
              className="flex items-center gap-2 px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full transition-all shadow-md hover:shadow-lg disabled:opacity-50 font-bold"
            >
              <Zap size={18} className={optimizing ? 'animate-pulse' : ''} />
              {optimizing ? 'Optimizing...' : 'Optimize Schedule'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto flex gap-8">
          
          {/* Timeline Grid */}
          <div className="flex-1 bg-white rounded-2xl shadow-sm border p-6 min-h-[600px] relative">
            <h2 className="text-xl font-bold mb-8 flex items-center gap-2 text-gray-700">
              <Clock size={20} className="text-indigo-500" />
              Day View (18:00 - 22:00)
            </h2>

            <div className="relative border-l-2 border-gray-100 ml-20 h-full">
              {timeSlots.map((time, idx) => (
                <div key={time} className="relative h-32 border-t border-gray-100">
                  <span className="absolute -left-20 -top-3 w-16 text-right font-mono text-sm text-gray-400 font-bold">
                    {time}
                  </span>
                  
                  {/* Event Rendering Logic */}
                  <div className="absolute inset-0 flex gap-4 p-4 pl-8">
                    {data.events
                      .filter(e => {
                        const eventHour = e.time.split(':')[0];
                        const slotHour = time.split(':')[0];
                        // Fuzzy match for 12/24h formats
                        return eventHour === slotHour || (parseInt(eventHour) + 12).toString() === slotHour;
                      })
                      .map((event, eIdx) => (
                        <div 
                          key={`${event.type}-${eIdx}`}
                          className={`flex-1 p-4 rounded-xl border-l-4 shadow-sm transition-all transform hover:-translate-y-1 hover:shadow-md ${getPriorityColor(event.priority)}`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-[10px] uppercase font-black tracking-tighter opacity-60">
                              {event.source}
                            </span>
                            {event.status === 'rescheduled' && (
                              <CheckCircle2 size={14} className="text-green-600" />
                            )}
                            {event.status === 'conflict' && (
                              <AlertTriangle size={14} className="text-red-600" />
                            )}
                          </div>
                          <h3 className="font-bold text-sm mb-1 capitalize leading-tight">
                            {event.type.replace(/_/g, ' ')}
                          </h3>
                          <div className="flex items-center gap-2 text-[10px] font-bold opacity-80">
                            <Clock size={10} />
                            {event.time} ({event.duration}m)
                          </div>
                          <div className="mt-2 flex gap-1">
                             <span className="text-[9px] px-1.5 py-0.5 bg-white bg-opacity-40 rounded border border-black border-opacity-10 uppercase font-black">
                               {event.priority}
                             </span>
                          </div>
                        </div>
                      ))
                    }
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Panel / Insights */}
          <div className="w-80 flex flex-col gap-6">
            <div className="bg-white rounded-2xl shadow-sm border p-6">
              <h4 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-4">Agent Status</h4>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-sm font-semibold text-gray-700">Environment Active</span>
                </div>
                <div className="p-3 bg-indigo-50 rounded-lg text-indigo-700 text-xs font-medium leading-relaxed italic">
                  "I'm monitoring your schedule for conflicts. Currently considering stress levels and travel times."
                </div>
              </div>
            </div>

            <div className="bg-gray-900 rounded-2xl shadow-xl p-6 text-white overflow-hidden relative">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <Zap size={60} />
              </div>
              <h4 className="text-xs font-black text-indigo-400 uppercase tracking-widest mb-4">AI Insights</h4>
              <p className="text-sm leading-relaxed mb-4 font-medium">
                {data.events.some(e => e.status === 'conflict') 
                  ? "I've detected significant overlaps in your schedule. High-priority items are fixed, while flexible tasks may need rescheduling."
                  : "Your schedule is currently balanced. All high-priority commitments have clear slots."}
              </p>
              <div className="pt-4 border-t border-gray-800 text-[10px] font-mono text-gray-500">
                OpenEnv Standard v1.0.0
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
};

export default App;
