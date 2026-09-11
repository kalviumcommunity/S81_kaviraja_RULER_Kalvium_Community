'use client';

import React from 'react';

export default function AuditHistory({ chatHistory, modelName, totalSessionTokens, currentUser }) {
  const assistantTurns = chatHistory.filter((m) => m.role === 'assistant' && !m.isLoading);

  const handleExportJSON = () => {
    const exportPayload = {
      exportTimestamp: new Date().toISOString(),
      user: currentUser,
      model: modelName,
      totalSessionTokens,
      chatHistory,
    };

    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(exportPayload, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `ruler_audit_log_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-8 max-w-6xl w-full mx-auto">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 flex-shrink-0">
        <div>
          <h2 className="text-lg font-bold text-white">Application Dialogue History & Token Telemetry</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Comprehensive audit trail of questions, responses, generated tokens, and session telemetry
          </p>
        </div>
        <div>
          <button
            onClick={handleExportJSON}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold px-4 py-2 rounded-lg transition flex items-center gap-1.5"
          >
            <span>📥</span>
            <span>Export Audit Log (JSON)</span>
          </button>
        </div>
      </div>

      <div className="bg-[#18233C] border border-slate-800 rounded-2xl overflow-y-auto flex-1 mt-4">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-[#131D31] text-slate-400 font-bold uppercase tracking-wider border-b border-slate-800 sticky top-0">
              <th className="py-3 px-4">Turn #</th>
              <th className="py-3 px-4">Question</th>
              <th className="py-3 px-4">Answer Preview</th>
              <th className="py-3 px-4">Tokens Generated</th>
              <th className="py-3 px-4">Context Tokens</th>
              <th className="py-3 px-4">Total Tokens</th>
              <th className="py-3 px-4">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-slate-200">
            {assistantTurns.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center text-slate-500 py-12">
                  No dialogue turns recorded yet. Ask questions in the Assistant view to generate audit history.
                </td>
              </tr>
            ) : (
              assistantTurns.map((turn, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-bold text-sky-400">#{turn.turnId}</td>
                  <td className="py-3 px-4 max-w-[200px] truncate">{turn.userQuestion || ''}</td>
                  <td className="py-3 px-4 max-w-[280px] truncate text-slate-300">
                    {(turn.content || '').slice(0, 80)}...
                  </td>
                  <td className="py-3 px-4 text-purple-300 font-bold">
                    {turn.tokens?.completion_tokens || 0} tokens
                  </td>
                  <td className="py-3 px-4 text-slate-400">{turn.tokens?.prompt_tokens || 0} tokens</td>
                  <td className="py-3 px-4 text-sky-400 font-bold">{turn.tokens?.total_tokens || 0} tokens</td>
                  <td className="py-3 px-4 text-slate-500 text-[11px]">{turn.timestamp}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
