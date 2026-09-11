'use client';

import React from 'react';

export default function Header({
  modelName,
  lastTurnGenTokens,
  totalSessionTokens,
  onLogout,
}) {
  return (
    <header className="h-16 bg-[#111827] border-b border-slate-800 flex items-center justify-between px-6 flex-shrink-0 z-30">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 font-extrabold text-xl text-white">
          <span className="text-2xl">⚖️</span>
          <span className="tracking-tight">Ruler</span>
        </div>
        <div className="w-px h-5 bg-slate-700" />
        <span className="text-xs font-medium text-slate-400 hidden sm:inline">
          Banking Regulatory AI Assistant
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Connected Model */}
        <div
          className="flex items-center gap-2 bg-slate-800/60 border border-slate-700/60 px-3 py-1.5 rounded-full text-xs font-mono text-slate-300"
          title="Connected LLM Endpoint"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>{modelName || 'openai/gpt-4o-mini'}</span>
        </div>

        {/* Generated Tokens in Last Turn */}
        <div
          className="flex items-center gap-1.5 bg-purple-500/10 border border-purple-500/30 px-3 py-1.5 rounded-full text-xs font-mono font-semibold text-purple-300"
          title="Tokens Generated in Last Turn"
        >
          <span>✨</span>
          <span>{lastTurnGenTokens.toLocaleString()} gen tokens</span>
        </div>

        {/* Total Tokens in Session */}
        <div
          className="flex items-center gap-1.5 bg-sky-500/10 border border-sky-500/30 px-3 py-1.5 rounded-full text-xs font-mono font-semibold text-sky-400"
          title="Total Tokens in Session"
        >
          <span>⚡</span>
          <span>{totalSessionTokens.toLocaleString()} total tokens</span>
        </div>

        {/* Sign Out Button */}
        <button
          onClick={onLogout}
          className="bg-slate-800 hover:bg-red-500/20 hover:border-red-500/40 border border-slate-700 text-slate-300 hover:text-red-300 px-3 py-1.5 rounded-lg text-xs font-semibold transition ml-1"
          title="Sign Out"
        >
          🚪 Sign Out
        </button>
      </div>
    </header>
  );
}
