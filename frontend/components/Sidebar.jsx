'use client';

import React from 'react';

export default function Sidebar({ activeView, onViewChange, currentUser }) {
  return (
    <aside className="w-56 bg-[#0F172A] border-r border-slate-800 flex flex-col justify-between p-3.5 flex-shrink-0">
      {/* Navigation Buttons */}
      <div className="flex flex-col gap-1.5">
        <button
          onClick={() => onViewChange('view-assistant')}
          className={`flex items-center gap-3 w-full px-3.5 py-3 rounded-xl text-xs font-semibold tracking-wider transition text-left ${
            activeView === 'view-assistant'
              ? 'text-sky-400 bg-sky-500/15 border border-sky-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60 border border-transparent'
          }`}
        >
          <span className="text-base">🏠</span>
          <span>ASSISTANT</span>
        </button>

        <button
          onClick={() => onViewChange('view-history')}
          className={`flex items-center gap-3 w-full px-3.5 py-3 rounded-xl text-xs font-semibold tracking-wider transition text-left ${
            activeView === 'view-history'
              ? 'text-sky-400 bg-sky-500/15 border border-sky-500/30'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60 border border-transparent'
          }`}
        >
          <span className="text-base">📜</span>
          <span>AUDIT & HISTORY</span>
        </button>
      </div>

      {/* User Profile Card in Sidebar Footer */}
      <div className="border-t border-slate-800 pt-3">
        <div className="flex items-center gap-2.5 bg-slate-800/40 border border-slate-800 p-2.5 rounded-xl">
          <div className="w-8 h-8 rounded-full bg-sky-500/20 flex items-center justify-center text-sm flex-shrink-0">
            <span>👤</span>
          </div>
          <div className="flex flex-col overflow-hidden flex-1">
            <span className="text-xs font-semibold text-white truncate">
              {currentUser ? currentUser.name : 'Regulatory Officer'}
            </span>
            <span className="text-[10px] text-slate-400 truncate">
              {currentUser ? currentUser.role : 'Compliance Specialist'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
