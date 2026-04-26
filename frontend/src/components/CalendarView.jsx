import React from 'react';
import { Clock } from 'lucide-react';

const CalendarView = ({ events }) => {
  const timeSlots = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);

  const getMinutes = (timeStr) => {
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + (m || 0);
  };

  const checkConflict = (event, allEvents) => {
    const start = getMinutes(event.time);
    const end = start + (event.duration || 60);
    return allEvents.some(e => {
      if (e === event) return false;
      const eStart = getMinutes(e.time);
      const eEnd = eStart + (e.duration || 60);
      return start < eEnd && eStart < end;
    });
  };

  return (
    <div className="flex-1 bg-white rounded-xl shadow-sm border overflow-hidden flex flex-col h-full">
      <div className="p-4 border-b bg-gray-50 flex items-center gap-2">
        <Clock size={18} className="text-indigo-500" />
        <h2 className="font-bold text-gray-700">Timeline (24h)</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 relative bg-slate-50">
        <div className="relative border-l-2 border-gray-200 ml-16 h-[1440px]">
          {timeSlots.map((time, idx) => (
            <div key={idx} className="relative h-[60px] border-t border-gray-100">
              <span className="absolute -left-16 -top-2.5 w-12 text-right text-[10px] font-bold text-gray-400">
                {time}
              </span>

              {/* Render events starting at this hour */}
              <div className="absolute inset-0 flex gap-2 pl-4 pointer-events-none">
                {events
                  .filter(e => e.time.startsWith(time.split(':')[0]))
                  .map((event, eIdx) => {
                    const hasConflict = checkConflict(event, events);
                    const domainColor = event.domain === 'professional' ? 'bg-blue-50 border-blue-400 text-blue-800' : 'bg-green-50 border-green-400 text-green-800';
                    const conflictStyle = hasConflict ? 'border-2 border-red-500 shadow-lg shadow-red-100 ring-2 ring-red-200' : 'border-l-4 shadow-sm';
                    
                    return (
                      <div 
                        key={eIdx}
                        className={`pointer-events-auto min-w-[180px] p-3 rounded-lg transition-all h-fit ${domainColor} ${conflictStyle}`}
                      >
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-[9px] font-black uppercase opacity-60">{event.source}</span>
                          {hasConflict && <span className="text-[9px] font-bold text-red-600 bg-red-100 px-1 rounded">⚠ CONFLICT</span>}
                        </div>
                        <h3 className="font-bold text-xs uppercase leading-tight">{event.type.replace(/_/g, ' ')}</h3>
                        <div className="text-[10px] font-medium mt-1 opacity-80">{event.time} ({event.duration}m)</div>
                      </div>
                    );
                  })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CalendarView;
