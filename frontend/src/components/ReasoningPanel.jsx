import React from 'react';
import { Brain, MessageSquare, Zap, Target } from 'lucide-react';

const ReasoningPanel = ({ explanation }) => {
  if (!explanation) return (
    <div className="p-6 bg-indigo-50 text-indigo-400 text-sm font-medium rounded-xl border border-dashed border-indigo-200">
      Awaiting optimization signal...
    </div>
  );

  const opinions = explanation.agent_opinions || {};

  return (
    <div className="space-y-6">
      <div className="bg-white p-4 rounded-xl border shadow-sm">
        <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
          <Brain size={14} className="text-indigo-500" />
          Agent Perspectives
        </h3>
        
        <div className="space-y-4">
          {Object.entries(opinions).map(([agent, text]) => (
            <div key={agent} className="border-l-2 border-indigo-100 pl-4 py-1">
              <span className="text-[10px] font-black uppercase text-indigo-400">{agent}</span>
              <p className="text-xs text-gray-600 leading-relaxed italic">"{text}"</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 p-6 rounded-xl shadow-xl text-white relative overflow-hidden">
        <Zap size={100} className="absolute -right-10 -bottom-10 opacity-5 text-indigo-400" />
        <h3 className="text-xs font-black text-indigo-400 uppercase tracking-widest mb-4 flex items-center gap-2">
          <Target size={14} />
          Final Strategy
        </h3>
        <p className="text-sm font-bold leading-relaxed mb-4">
          {explanation.final_decision?.description || "Compromise found."}
        </p>
        
        <div className="pt-4 border-t border-gray-800">
          <span className="text-[10px] font-black uppercase text-gray-500">Actions Triggered</span>
          <div className="flex flex-wrap gap-2 mt-2">
            {explanation.action_taken?.map((tool, idx) => (
              <span key={idx} className="text-[9px] font-black bg-indigo-900 text-indigo-200 px-2 py-0.5 rounded border border-indigo-700">
                {tool.toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReasoningPanel;
