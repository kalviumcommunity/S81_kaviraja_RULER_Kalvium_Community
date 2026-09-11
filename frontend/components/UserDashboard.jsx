'use client';

import React, { useState } from 'react';
import AssistantChat from './AssistantChat';

export default function UserDashboard({
  currentUser,
  chatHistory,
  setChatHistory,
  onLogout,
  onUnlockAdmin,
  onBackToOverview,
}) {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'history' | 'feedback'
  const [feedbackFilter, setFeedbackFilter] = useState('all'); // 'all' | 'positive' | 'negative'
  const [generalThoughts, setGeneralThoughts] = useState('');
  const [generalThoughtsList, setGeneralThoughtsList] = useState([]);
  const [thoughtDrafts, setThoughtDrafts] = useState({});
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Sync chatHistory to localStorage for /ruler admin inspection
  React.useEffect(() => {
    if (chatHistory && chatHistory.length > 0) {
      try {
        localStorage.setItem('ruler_chat_history', JSON.stringify(chatHistory));
      } catch (e) {
        console.warn('Could not save chat history to localStorage:', e);
      }
    }
  }, [chatHistory]);

  const assistantEntries = chatHistory.filter((m) => m.role === 'assistant' && !m.isLoading);
  const feedbackEntries = assistantEntries.filter((m) => m.feedback !== null && m.feedback !== undefined);
  const positiveCount = assistantEntries.filter((m) => m.feedback === 'positive').length;
  const negativeCount = assistantEntries.filter((m) => m.feedback === 'negative').length;

  const filteredFeedbackList = feedbackEntries.filter((m) => {
    if (feedbackFilter === 'positive') return m.feedback === 'positive';
    if (feedbackFilter === 'negative') return m.feedback === 'negative';
    return true;
  });

  const handleUpdateFeedback = (turnId, rating) => {
    setChatHistory((prev) =>
      prev.map((msg) => {
        if (msg.turnId === turnId && msg.role === 'assistant') {
          return {
            ...msg,
            feedback: msg.feedback === rating ? null : rating,
          };
        }
        return msg;
      })
    );
  };

  const handleSaveTurnThought = (turnId) => {
    const text = thoughtDrafts[turnId]?.trim();
    if (!text) return;

    setChatHistory((prev) =>
      prev.map((msg) => {
        if (msg.turnId === turnId && msg.role === 'assistant') {
          return {
            ...msg,
            userThoughts: text,
          };
        }
        return msg;
      })
    );

    setThoughtDrafts((prev) => ({ ...prev, [turnId]: '' }));
  };

  const handlePostGeneralThought = (e) => {
    e.preventDefault();
    if (!generalThoughts.trim()) return;

    const newThought = {
      id: Date.now(),
      author: currentUser?.name || 'Banking Officer',
      text: generalThoughts.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setGeneralThoughtsList((prev) => [newThought, ...prev]);
    setGeneralThoughts('');
  };

  return (
    <div className="flex flex-col h-screen w-full bg-[#FAF8F5] overflow-hidden select-none font-sans text-[#002147]">
      {/* Top Header - Oxford Blue with Tan Accents */}
      <header className="h-16 bg-[#002147] border-b border-[#001630] px-4 sm:px-6 flex items-center justify-between flex-shrink-0 z-20 shadow-sm">
        {/* Brand & Menu Toggle */}
        <div className="flex items-center gap-3">
          {/* 3-Lines Hamburger Menu Button */}
          <button
            type="button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 rounded-[12px] bg-[#001630] hover:bg-[#083266] border border-[#083266] text-[#D2B48C] hover:text-white text-base font-bold flex items-center justify-center transition shadow-sm"
            title={isSidebarOpen ? 'Close Menu (✕)' : 'Open Menu (☰)'}
            aria-label="Toggle Sidebar Navigation"
          >
            {isSidebarOpen ? '✕' : '☰'}
          </button>

          <div className="px-3 py-1 rounded-[12px] bg-[#D2B48C] text-[#002147] flex items-center justify-center text-xs font-bold shadow-sm uppercase tracking-wider">
            🏛️ RULER
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-tight">Ruler Intelligence</h1>
            <p className="text-[11px] text-[#D2B48C] font-medium hidden sm:block">Banking Regulatory Portal</p>
          </div>
        </div>

        {/* User Info & Actions */}
        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-bold text-white">{currentUser?.name || 'Banking Officer'}</div>
            <div className="text-[11px] text-[#D2B48C] font-mono truncate max-w-[180px]">{currentUser?.email}</div>
          </div>
          
          <button
            type="button"
            onClick={onLogout}
            className="bg-transparent hover:bg-[#D2B48C] hover:text-[#002147] border border-[#D2B48C] text-[#D2B48C] text-xs font-bold px-3.5 py-2 rounded-[12px] transition flex items-center gap-1.5"
            title="Sign out from session"
          >
            <span>Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Body with Left Sidebar */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Sidebar Navigation (Visible only when isSidebarOpen is true) */}
        {isSidebarOpen && (
          <aside className="w-64 bg-[#001630] border-r border-[#002855] flex flex-col justify-between p-4 flex-shrink-0 transition-all duration-200 z-30 shadow-lg">
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-[#D2B48C]/70">
                <span>Compliance Navigation</span>
                <button
                  type="button"
                  onClick={() => setIsSidebarOpen(false)}
                  className="text-xs text-[#D2B48C] hover:text-white p-1 rounded hover:bg-white/10"
                  title="Close Sidebar"
                >
                  ✕
                </button>
              </div>

            <button
              type="button"
              onClick={() => setActiveTab('chat')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-[12px] text-xs font-bold text-left transition ${
                activeTab === 'chat'
                  ? 'bg-[#D2B48C] text-[#002147] shadow-sm font-extrabold'
                  : 'text-[#D2B48C] hover:bg-white/10 hover:text-white'
              }`}
            >
              <span className="text-sm">💬</span>
              <span>Compliance Chat</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('history')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-[12px] text-xs font-bold text-left transition ${
                activeTab === 'history'
                  ? 'bg-[#D2B48C] text-[#002147] shadow-sm font-extrabold'
                  : 'text-[#D2B48C] hover:bg-white/10 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-sm">📜</span>
                <span>Query History</span>
              </div>
              {assistantEntries.length > 0 && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  activeTab === 'history' ? 'bg-[#002147] text-[#D2B48C]' : 'bg-[#D2B48C] text-[#002147]'
                }`}>
                  {assistantEntries.length}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('feedback')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-[12px] text-xs font-bold text-left transition ${
                activeTab === 'feedback'
                  ? 'bg-[#D2B48C] text-[#002147] shadow-sm font-extrabold'
                  : 'text-[#D2B48C] hover:bg-white/10 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-sm">⭐</span>
                <span>Feedback & Notes</span>
              </div>
              {feedbackEntries.length > 0 && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  activeTab === 'feedback' ? 'bg-[#002147] text-[#D2B48C]' : 'bg-[#D2B48C] text-[#002147]'
                }`}>
                  {feedbackEntries.length}
                </span>
              )}
            </button>
          </div>

          {/* Sidebar Footer */}
          <div className="border-t border-[#002855] pt-4 flex flex-col gap-2">
            <div className="flex items-center justify-between px-2 text-[11px] text-[#D2B48C]/80">
              <span>Regulatory Base</span>
              <span className="inline-flex items-center gap-1.5 text-emerald-400 font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Active</span>
              </span>
            </div>
            {onBackToOverview && (
              <button
                type="button"
                onClick={onBackToOverview}
                className="w-full bg-[#002147] hover:bg-[#083266] border border-[#D2B48C]/40 text-[#D2B48C] text-xs font-bold py-2 px-3 rounded-[12px] transition flex items-center justify-center gap-1.5 shadow-sm"
              >
                <span>ℹ️</span>
                <span>Overview & Directives</span>
              </button>
            )}
          </div>
        </aside>
      )}

      {/* Main Workspace */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#FAF8F5]">
        {/* Tab 1: Chat Space */}
        {activeTab === 'chat' && (
          <AssistantChat
            chatHistory={chatHistory}
            setChatHistory={setChatHistory}
          />
        )}

        {/* Tab 2: Query History */}
        {activeTab === 'history' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-4xl w-full mx-auto flex flex-col gap-6">
            <div className="flex items-center justify-between pb-3 border-b border-[#D8CCBD]">
              <div>
                <h2 className="text-base font-bold text-[#002147]">Query & Answer History</h2>
                <p className="text-xs text-[#6A5A4A]">Past queries, generated token metrics, source chunk numbers, and user feedback</p>
              </div>
              {assistantEntries.length > 0 && (
                <button
                  type="button"
                  onClick={() => setChatHistory([])}
                  className="text-xs font-semibold text-[#002147] hover:text-white hover:bg-[#002147] bg-[#F5EFEB] border border-[#D8CCBD] px-3 py-1.5 rounded-[12px] transition"
                >
                  Clear History
                </button>
              )}
            </div>

            {assistantEntries.length === 0 ? (
              <div className="bg-white border border-[#D8CCBD] rounded-[12px] p-12 text-center flex flex-col items-center gap-3 my-auto shadow-sm">
                <h3 className="text-sm font-bold text-[#002147]">No Query History Yet</h3>
                <p className="text-xs text-[#8C7A68] max-w-sm">
                  Switch to the Chat Space tab and ask compliance questions to see your questions, generated tokens, and source chunks recorded here.
                </p>
                <button
                  type="button"
                  onClick={() => setActiveTab('chat')}
                  className="mt-2 bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold text-xs px-4 py-2 rounded-[12px] transition shadow-sm"
                >
                  Go to Chat Space →
                </button>
              </div>
            ) : (
              assistantEntries.map((entry, idx) => (
                <div
                  key={idx}
                  className="bg-white border border-[#D8CCBD] rounded-[12px] p-6 flex flex-col gap-4 shadow-sm"
                >
                  {/* Query Header */}
                  <div className="flex items-start justify-between gap-4 border-b border-[#F5EFEB] pb-3">
                    <div className="flex flex-col gap-1">
                      <span className="text-[11px] font-bold text-[#8C7A68] uppercase tracking-wider">
                        Query #{entry.turnId || idx + 1}
                      </span>
                      <h4 className="text-sm font-bold text-[#002147]">
                        {entry.userQuestion || 'Regulatory Query'}
                      </h4>
                    </div>
                    <span className="text-xs text-[#8C7A68] font-mono flex-shrink-0 bg-[#F5EFEB] px-2.5 py-1 rounded-[12px] border border-[#D8CCBD]">
                      {entry.timestamp}
                    </span>
                  </div>

                  {/* 1. Answer */}
                  <div className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[#002147]">Answer:</span>
                    <div className="p-4 bg-[#F5EFEB] rounded-[12px] text-xs text-[#002147] leading-relaxed font-sans whitespace-pre-wrap border border-[#D8CCBD]">
                      {entry.content}
                    </div>
                  </div>

                  {/* 2. Token Usage */}
                  <div className="flex items-center gap-2 pt-1 border-t border-[#F5EFEB]">
                    <span className="text-xs font-bold text-[#002147]">Tokens used:</span>
                    <span className="font-mono text-xs font-bold px-2.5 py-0.5 bg-[#002147] text-[#D2B48C] rounded-[12px]">
                      {entry.tokens?.completion_tokens !== undefined ? `${entry.tokens.completion_tokens}` : 'Not available'}
                    </span>
                  </div>


                  {/* User Thoughts Note if present */}
                  {entry.userThoughts && (
                    <div className="bg-[#FAF8F5] border border-[#D8CCBD] rounded-[12px] p-3 text-xs text-[#002147]">
                      <div className="font-bold text-[11px] text-[#8C7A68] uppercase tracking-wider mb-0.5">
                        Your Shared Thoughts:
                      </div>
                      <p className="italic">{entry.userThoughts}</p>
                    </div>
                  )}

                  {/* Feedback Status */}
                  <div className="bg-[#FAF8F5] border border-[#D8CCBD] rounded-[12px] p-3 flex items-center justify-between">
                    <span className="text-xs font-bold text-[#002147]">User Feedback:</span>
                    <span className="text-xs font-bold">
                      {entry.feedback === 'positive' ? (
                        <span className="text-[#002147] bg-[#D2B48C] px-2.5 py-1 rounded-[12px]">
                          👍 Helpful
                        </span>
                      ) : entry.feedback === 'negative' ? (
                        <span className="text-[#002147] bg-[#E5D9C8] border border-[#D8CCBD] px-2.5 py-1 rounded-[12px]">
                          👎 Needs Revision
                        </span>
                      ) : (
                        <span className="text-[#8C7A68]">None</span>
                      )}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 3: User Feedback Section with Dedicated Thoughts Space Column */}
        {activeTab === 'feedback' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-4xl w-full mx-auto flex flex-col gap-6">
            {/* Feedback Header */}
            <div className="flex items-center justify-between pb-3 border-b border-[#D8CCBD]">
              <div>
                <h2 className="text-base font-bold text-[#002147]">User Feedback & Thoughts Center</h2>
                <p className="text-xs text-[#6A5A4A]">Share compliance thoughts, notes, and evaluate regulatory response accuracy</p>
              </div>

              {/* Filter Buttons */}
              <div className="flex bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] p-1 text-xs">
                <button
                  type="button"
                  onClick={() => setFeedbackFilter('all')}
                  className={`px-3 py-1 rounded-[12px] font-bold transition ${
                    feedbackFilter === 'all'
                      ? 'bg-[#002147] text-[#D2B48C]'
                      : 'text-[#002147] hover:bg-[#E6D9C8]'
                  }`}
                >
                  All ({feedbackEntries.length})
                </button>
                <button
                  type="button"
                  onClick={() => setFeedbackFilter('positive')}
                  className={`px-3 py-1 rounded-[12px] font-bold transition ${
                    feedbackFilter === 'positive'
                      ? 'bg-[#002147] text-[#D2B48C]'
                      : 'text-[#002147] hover:bg-[#E6D9C8]'
                  }`}
                >
                  👍 Helpful ({positiveCount})
                </button>
                <button
                  type="button"
                  onClick={() => setFeedbackFilter('negative')}
                  className={`px-3 py-1 rounded-[12px] font-bold transition ${
                    feedbackFilter === 'negative'
                      ? 'bg-[#002147] text-[#D2B48C]'
                      : 'text-[#002147] hover:bg-[#E6D9C8]'
                  }`}
                >
                  👎 Needs Revision ({negativeCount})
                </button>
              </div>
            </div>

            {/* General Thoughts Column Box */}
            <div className="bg-white border border-[#D8CCBD] p-6 rounded-[12px] flex flex-col gap-3 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="text-lg">💭</span>
                <h3 className="text-sm font-bold text-[#002147]">Share Your Thoughts & Regulatory Notes</h3>
              </div>
              <p className="text-xs text-[#6A5A4A]">
                Write your observations, compliance insights, policy interpretations, or suggestions for the regulatory platform.
              </p>
              <form onSubmit={handlePostGeneralThought} className="flex flex-col gap-3 mt-1">
                <textarea
                  value={generalThoughts}
                  onChange={(e) => setGeneralThoughts(e.target.value)}
                  placeholder="Share your thoughts, compliance observations, or suggestions here..."
                  rows={3}
                  className="w-full bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] p-3 text-xs text-[#002147] focus:outline-none focus:border-[#002147] transition placeholder-[#8C7A68] font-sans"
                  required
                />
                <button
                  type="submit"
                  disabled={!generalThoughts.trim()}
                  className="self-start bg-[#002147] hover:bg-[#001630] disabled:opacity-40 text-[#D2B48C] font-bold py-2 px-5 rounded-[12px] text-xs transition duration-150 flex items-center gap-1.5 shadow-sm"
                >
                  <span>Post Thoughts</span>
                  <span>→</span>
                </button>
              </form>

              {/* Display Posted General Thoughts */}
              {generalThoughtsList.length > 0 && (
                <div className="flex flex-col gap-2 pt-2 border-t border-[#F5EFEB] mt-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#8C7A68]">
                    Recent Officer Thoughts:
                  </span>
                  {generalThoughtsList.map((t) => (
                    <div
                      key={t.id}
                      className="bg-[#FAF8F5] border border-[#D8CCBD] p-3 rounded-[12px] text-xs text-[#002147] flex flex-col gap-1"
                    >
                      <div className="flex items-center justify-between text-[11px] text-[#8C7A68]">
                        <span className="font-bold text-[#002147]">{t.author}</span>
                        <span>{t.timestamp}</span>
                      </div>
                      <p className="leading-relaxed">{t.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Metrics Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white border border-[#D8CCBD] p-4 rounded-[12px] flex flex-col gap-1 shadow-sm">
                <span className="text-xs text-[#8C7A68] font-medium">Total Rated Queries</span>
                <span className="text-xl font-bold text-[#002147]">{feedbackEntries.length}</span>
                <span className="text-[11px] text-[#6A5A4A]">Out of {assistantEntries.length} total turns</span>
              </div>
              <div className="bg-white border border-[#D8CCBD] p-4 rounded-[12px] flex flex-col gap-1 shadow-sm">
                <span className="text-xs text-[#8C7A68] font-medium">Helpful Ratings</span>
                <span className="text-xl font-bold text-[#002147]">👍 {positiveCount}</span>
                <span className="text-[11px] text-[#6A5A4A]">Validated regulatory answers</span>
              </div>
              <div className="bg-white border border-[#D8CCBD] p-4 rounded-[12px] flex flex-col gap-1 shadow-sm">
                <span className="text-xs text-[#8C7A68] font-medium">Revision Requests</span>
                <span className="text-xl font-bold text-[#002147]">👎 {negativeCount}</span>
                <span className="text-[11px] text-[#6A5A4A]">Flagged for review</span>
              </div>
            </div>

            {/* Feedback Cards List with Dedicated Thoughts Column */}
            {filteredFeedbackList.length === 0 ? (
              <div className="bg-white border border-[#D8CCBD] rounded-[12px] p-12 text-center flex flex-col items-center gap-3 my-auto shadow-sm">
                <span className="text-3xl">💬</span>
                <h3 className="text-sm font-bold text-[#002147]">No Query Feedback Recorded Yet</h3>
                <p className="text-xs text-[#8C7A68] max-w-sm">
                  {feedbackEntries.length === 0
                    ? 'Submit queries in the Chat Space and click the 👍 Helpful or 👎 Needs Revision buttons to evaluate answers and attach thoughts.'
                    : 'No entries match your current filter selection.'}
                </p>
                <button
                  type="button"
                  onClick={() => setActiveTab('chat')}
                  className="mt-2 bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold text-xs px-4 py-2 rounded-[12px] transition shadow-sm"
                >
                  Go to Chat Space →
                </button>
              </div>
            ) : (
              filteredFeedbackList.map((entry, idx) => (
                <div
                  key={idx}
                  className="bg-white border border-[#D8CCBD] rounded-[12px] p-6 flex flex-col gap-4 shadow-sm"
                >
                  {/* Feedback Card Header */}
                  <div className="flex items-start justify-between gap-4 border-b border-[#F5EFEB] pb-3">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-bold text-[#8C7A68] uppercase tracking-wider">
                          Turn #{entry.turnId || idx + 1}
                        </span>
                        <span
                          className={`text-xs font-bold px-2.5 py-0.5 rounded-[12px] ${
                            entry.feedback === 'positive'
                              ? 'bg-[#D2B48C] text-[#002147]'
                              : 'bg-[#002147] text-[#D2B48C]'
                          }`}
                        >
                          {entry.feedback === 'positive' ? '👍 Helpful' : '👎 Needs Revision'}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-[#002147] mt-1">
                        {entry.userQuestion || 'Regulatory Query'}
                      </h4>
                    </div>
                    <span className="text-xs text-[#8C7A68] font-mono bg-[#F5EFEB] px-2.5 py-1 rounded-[12px] border border-[#D8CCBD]">
                      {entry.timestamp}
                    </span>
                  </div>

                  {/* Assistant Answer Preview */}
                  <div className="p-4 bg-[#F5EFEB] rounded-[12px] text-xs text-[#002147] leading-relaxed font-sans whitespace-pre-wrap border border-[#D8CCBD]">
                    {entry.content}
                  </div>

                  {/* Display User Thoughts on this specific turn */}
                  {entry.userThoughts && (
                    <div className="bg-[#FAF8F5] border border-[#D8CCBD] rounded-[12px] p-3 text-xs text-[#002147]">
                      <div className="font-bold text-[11px] text-[#8C7A68] uppercase tracking-wider mb-0.5">
                        Your Shared Thoughts on this Answer:
                      </div>
                      <p className="italic">{entry.userThoughts}</p>
                    </div>
                  )}

                  {/* Share Thoughts Input Column for this specific turn */}
                  <div className="bg-[#FAF8F5] border border-[#D8CCBD] rounded-[12px] p-3.5 flex flex-col gap-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#6A5A4A] flex items-center gap-1.5">
                      <span>✏️</span>
                      <span>Share Your Thoughts on this Response:</span>
                    </span>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={thoughtDrafts[entry.turnId] || ''}
                        onChange={(e) =>
                          setThoughtDrafts((prev) => ({
                            ...prev,
                            [entry.turnId]: e.target.value,
                          }))
                        }
                        placeholder="Write your compliance notes, reasoning, or suggestions..."
                        className="flex-1 bg-white border border-[#D8CCBD] rounded-[12px] px-3 py-2 text-xs text-[#002147] focus:outline-none focus:border-[#002147] placeholder-[#8C7A68]"
                      />
                      <button
                        type="button"
                        onClick={() => handleSaveTurnThought(entry.turnId)}
                        disabled={!thoughtDrafts[entry.turnId]?.trim()}
                        className="bg-[#002147] hover:bg-[#001630] disabled:opacity-40 text-[#D2B48C] font-bold text-xs px-4 py-2 rounded-[12px] transition flex-shrink-0"
                      >
                        Save Thought
                      </button>
                    </div>
                  </div>

                  {/* Feedback Action Row */}
                  <div className="flex items-center justify-between flex-wrap gap-2 pt-1 border-t border-[#F5EFEB]">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs font-bold text-[#002147] bg-[#F5EFEB] border border-[#D8CCBD] px-2.5 py-1 rounded-[12px]">
                        ⚡ {entry.tokens?.completion_tokens || 0} tokens generated
                      </span>
                      {entry.sources && entry.sources.length > 0 && (
                        <span className="text-xs text-[#6A5A4A] font-semibold">
                          📑 {entry.sources.length} source chunk{entry.sources.length > 1 ? 's' : ''} cited
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#6A5A4A] font-semibold">Change Rating:</span>
                      <button
                        type="button"
                        onClick={() => handleUpdateFeedback(entry.turnId, 'positive')}
                        className={`px-3 py-1 rounded-[12px] text-xs font-bold transition ${
                          entry.feedback === 'positive'
                            ? 'bg-[#002147] text-[#D2B48C] shadow-sm'
                            : 'bg-[#F5EFEB] text-[#002147] hover:bg-[#D2B48C] border border-[#D8CCBD]'
                        }`}
                      >
                        👍 Helpful
                      </button>
                      <button
                        type="button"
                        onClick={() => handleUpdateFeedback(entry.turnId, 'negative')}
                        className={`px-3 py-1 rounded-[12px] text-xs font-bold transition ${
                          entry.feedback === 'negative'
                            ? 'bg-[#002147] text-[#D2B48C] shadow-sm'
                            : 'bg-[#F5EFEB] text-[#002147] hover:bg-[#D2B48C] border border-[#D8CCBD]'
                        }`}
                      >
                        👎 Needs Revision
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>
      </div>
    </div>
  );
}
