import React, { useState, useEffect, useRef } from 'react';
import { Calendar as CalendarIcon, RefreshCw, Zap, Clock, User, Briefcase, FastForward } from 'lucide-react';
import CalendarView from '../components/CalendarView';
import ReasoningPanel from '../components/ReasoningPanel';
import { NotificationPopup } from '../components/NotificationPopup';
import { fetchReset, optimize, fetchNotifications, respondToEvent, tickTime } from '../services/api';

const Dashboard = () => {
  const [events, setEvents] = useState([]);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [viewMode, setViewMode] = useState('before'); // 'before' or 'after'
  const [currentTime, setCurrentTime] = useState("08:00");
  const [activeNotification, setActiveNotification] = useState(null);
  
  const pollingRef = useRef(null);

  const handleReset = async () => {
    setLoading(true);
    const data = await fetchReset();
    setEvents(data.events || []);
    setCurrentTime(data.current_time || "08:00");
    setExplanation(null);
    setViewMode('before');
    setActiveNotification(null);
    setLoading(false);
  };

  const handleOptimize = async () => {
    setOptimizing(true);
    const data = await optimize();
    if (data) {
      setEvents(data.events);
      setExplanation(data.explanation);
      setViewMode('after');
    }
    setOptimizing(false);
  };

  const handleTick = async () => {
    const data = await tickTime(30);
    if (data) {
      setCurrentTime(data.current_time);
      checkNotifications();
    }
  };

  const checkNotifications = async () => {
    const data = await fetchNotifications();
    if (data.notifications && data.notifications.length > 0) {
      // Pick the first one for now
      setActiveNotification({
        message: data.notifications[0].message,
        event: data.notifications[0].event
      });
    } else {
      setActiveNotification(null);
    }
  };

  const handleComplete = async (eventName) => {
    const data = await respondToEvent(eventName, 'yes');
    if (data) {
      setEvents(data.events);
      setActiveNotification(null);
    }
  };

  const handleExtend = async (eventName) => {
    const data = await respondToEvent(eventName, 'no');
    if (data) {
      setEvents(data.events);
      setActiveNotification(null);
    }
  };

  useEffect(() => {
    handleReset();
    
    // Setup Polling
    pollingRef.current = setInterval(checkNotifications, 10000);
    return () => clearInterval(pollingRef.current);
  }, []);

  const today = new Date();

  return (
    <div className="flex h-screen w-screen bg-white overflow-hidden text-gray-900 font-sans">
      
      {/* Real-time Notifications */}
      <NotificationPopup 
        notification={activeNotification}
        onComplete={handleComplete}
        onExtend={handleExtend}
      />

      {/* --- Sidebar (Left) --- */}
      <aside className="w-80 border-r flex flex-col p-8 bg-gray-50 flex-shrink-0 overflow-y-auto">
        <div className="flex items-center gap-3 mb-10">
          <div className="p-2.5 bg-indigo-600 rounded-xl text-white shadow-lg shadow-indigo-100">
            <CalendarIcon size={24} />
          </div>
          <h1 className="text-2xl font-black tracking-tighter italic">LifeWeaver</h1>
        </div>

        <div className="mb-10">
          <h2 className="text-xl font-bold">{today.strftime ? today.strftime("%A") : today.toLocaleDateString('en-US', { weekday: 'long' })}</h2>
          <div className="flex justify-between items-center mt-1">
            <p className="text-gray-400 font-medium text-sm">{today.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
            <span className="bg-indigo-100 text-indigo-700 text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-tighter flex items-center gap-1">
              <Clock size={10} /> {currentTime}
            </span>
          </div>
        </div>

        <div className="space-y-3 mb-auto">
          <button 
            onClick={handleReset}
            disabled={loading || optimizing}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-100 transition-all font-bold shadow-sm disabled:opacity-50"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            New Day
          </button>
          
          <button 
            onClick={handleOptimize}
            disabled={loading || optimizing}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-xl hover:bg-indigo-600 transition-all font-bold shadow-xl shadow-gray-200 disabled:opacity-50"
          >
            <Zap size={18} fill="currentColor" />
            Optimize
          </button>

          <button 
            onClick={handleTick}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-indigo-50 text-indigo-600 rounded-xl hover:bg-indigo-100 transition-all font-bold"
          >
            <FastForward size={18} />
            Advance 30m
          </button>
        </div>

        {/* Info Legend */}
        <div className="mt-10 p-4 bg-white rounded-xl border border-gray-100 space-y-4">
           <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-blue-400" />
              <span className="text-xs font-bold text-gray-500 uppercase tracking-tighter">Professional</span>
           </div>
           <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-green-400" />
              <span className="text-xs font-bold text-gray-500 uppercase tracking-tighter">Personal</span>
           </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200 opacity-50">
           <p className="text-[10px] font-black uppercase text-gray-400 tracking-widest">Multi-Agent Orchestration</p>
           <p className="text-[10px] font-medium text-gray-500 mt-1">OpenEnv Standard v1.0.0</p>
        </div>
      </aside>

      {/* --- Main Content (Right) --- */}
      <main className="flex-1 flex flex-col p-10 bg-white overflow-hidden">
        
        {/* Toggle & Stats Header */}
        <div className="flex justify-between items-center mb-8">
           <div className="inline-flex p-1 bg-gray-100 rounded-xl">
              <button 
                onClick={() => setViewMode('before')}
                className={`px-6 py-2 rounded-lg text-xs font-black uppercase transition-all ${viewMode === 'before' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
              >
                Original
              </button>
              <button 
                onClick={() => setViewMode('after')}
                className={`px-6 py-2 rounded-lg text-xs font-black uppercase transition-all ${viewMode === 'after' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
              >
                Optimized
              </button>
           </div>

           <div className="flex gap-8">
              <div className="text-right">
                <span className="text-[10px] font-black uppercase text-gray-400 block">Conflict Status</span>
                <span className={`text-sm font-bold ${explanation?.conflict_detected ? 'text-red-500' : 'text-green-500'}`}>
                   {explanation?.conflict_detected ? "Overlaps Detected" : "Clear Schedule"}
                </span>
              </div>
           </div>
        </div>

        <div className="flex-1 flex gap-10 min-h-0">
          {/* Calendar Section */}
          <section className="flex-[2] flex flex-col min-h-0">
             {loading ? (
               <div className="flex-1 bg-slate-50 rounded-2xl flex items-center justify-center border-2 border-dashed border-slate-200">
                  <RefreshCw className="animate-spin text-indigo-500 mr-3" />
                  <span className="text-slate-400 font-bold uppercase tracking-widest text-xs">Simulating Scenario...</span>
               </div>
             ) : (
               <CalendarView events={viewMode === 'after' && explanation ? explanation.state_change.after : (explanation ? explanation.state_change.before : events)} />
             )}
          </section>

          {/* Reasoning Section */}
          <section className="flex-1 flex flex-col overflow-y-auto">
             <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-6">AI Decision Lifecycle</h3>
             <ReasoningPanel explanation={explanation} />
          </section>
        </div>

      </main>

    </div>
  );
};

export default Dashboard;
