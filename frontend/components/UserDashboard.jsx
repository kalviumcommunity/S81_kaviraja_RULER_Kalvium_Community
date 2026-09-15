'use client';

import React, { useState } from 'react';
import AssistantChat from './AssistantChat';
import { submitFeedback } from '../lib/api';

export default function UserDashboard({
  currentUser,
  chatHistory,
  setChatHistory,
  onLogout,
  onUnlockAdmin,
  onBackToOverview,
}) {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'history' | 'feedback'
  const [feedbackFilter, setFeedbackFilter] = useState('all'); // 'all' | 'positive' | 'average' | 'negative'
  const [thoughtDrafts, setThoughtDrafts] = useState({});
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [activeChat, setActiveChat] = useState([]);

  // Sync chatHistory to localStorage for /ruler admin inspection and session persistence
  React.useEffect(() => {
    if (chatHistory && chatHistory.length > 0) {
      try {
        localStorage.setItem('ruler_chat_history', JSON.stringify(chatHistory));
        if (currentUser?.email) {
          const userEmailKey = `ruler_chat_${currentUser.email.toLowerCase().trim()}`;
          localStorage.setItem(userEmailKey, JSON.stringify(chatHistory));
        }
      } catch (e) {
        console.warn('Could not save chat history to localStorage:', e);
      }
    }
  }, [chatHistory, currentUser]);

  const assistantEntries = chatHistory.filter((m) => m.role === 'assistant' && !m.isLoading);
  const feedbackEntries = assistantEntries.filter((m) => m.feedback !== null && m.feedback !== undefined);
  const positiveCount = assistantEntries.filter((m) => m.feedback === 'positive').length;
  const averageCount = assistantEntries.filter((m) => m.feedback === 'average').length;
  const negativeCount = assistantEntries.filter((m) => m.feedback === 'negative').length;

  const filteredFeedbackList = feedbackEntries.filter((m) => {
    if (feedbackFilter === 'positive') return m.feedback === 'positive';
    if (feedbackFilter === 'average') return m.feedback === 'average';
    if (feedbackFilter === 'negative') return m.feedback === 'negative';
    return true;
  });

  const handleRecordQuery = (userMsg, assistantMsg) => {
    setChatHistory((prev) => {
      const filtered = prev.filter(
        (m) => !(m.turnId === userMsg.turnId && m.role === userMsg.role)
      );
      const updated = [...filtered, userMsg, assistantMsg];
      if (currentUser?.email) {
        const userEmailKey = `ruler_chat_${currentUser.email.toLowerCase().trim()}`;
        try {
          localStorage.setItem(userEmailKey, JSON.stringify(updated));
          localStorage.setItem('ruler_chat_history', JSON.stringify(updated));
        } catch (e) {}
      }
      return updated;
    });
  };

  const handleUpdateFeedback = async (turnId, rating) => {
    const targetMsg = chatHistory.find((m) => m.turnId === turnId && m.role === 'assistant') ||
      activeChat.find((m) => m.turnId === turnId && m.role === 'assistant');
    const newRating = targetMsg?.feedback === rating ? null : rating;

    // Update global persistent history
    setChatHistory((prev) =>
      prev.map((msg) => {
        if (msg.turnId === turnId && msg.role === 'assistant') {
          return {
            ...msg,
            feedback: newRating,
          };
        }
        return msg;
      })
    );

    // Also update active chat screen if this turn is currently displayed
    setActiveChat((prev) =>
      prev.map((msg) => {
        if (msg.turnId === turnId && msg.role === 'assistant') {
          return {
            ...msg,
            feedback: newRating,
          };
        }
        return msg;
      })
    );

    if (targetMsg && newRating) {
      try {
        const ratingStr = newRating === 'positive' ? 'helpful' : newRating === 'average' ? 'average' : 'needs_revision';
        const ratingScore = newRating === 'positive' ? 1 : newRating === 'average' ? 0 : -1;

        await submitFeedback({
          turn_id: turnId,
          question: targetMsg.userQuestion || '',
          answer: targetMsg.content || '',
          rating: ratingStr,
          rating_score: ratingScore,
          thoughts: targetMsg.userThoughts || '',
          category: 'User Feedback Tab',
          user_email: currentUser?.email || null,
          tokens_generated: targetMsg.tokens?.completion_tokens || 0,
        });
      } catch (err) {
        console.warn('Failed to submit feedback:', err);
      }
    }
  };

  const handleSaveTurnThoughtDirect = async (turnId, text) => {
    if (!text?.trim()) return;

    const targetMsg = chatHistory.find((m) => m.turnId === turnId && m.role === 'assistant') ||
      activeChat.find((m) => m.turnId === turnId && m.role === 'assistant');

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

    setActiveChat((prev) =>
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

    if (targetMsg) {
      try {
        const ratingStr = targetMsg.feedback === 'negative'
          ? 'needs_revision'
          : targetMsg.feedback === 'average'
          ? 'average'
          : 'helpful';
        const ratingScore = targetMsg.feedback === 'negative'
          ? -1
          : targetMsg.feedback === 'average'
          ? 0
          : 1;

        await submitFeedback({
          turn_id: turnId,
          question: targetMsg.userQuestion || '',
          answer: targetMsg.content || '',
          rating: ratingStr,
          rating_score: ratingScore,
          thoughts: text,
          category: 'Officer Compliance Note',
          user_email: currentUser?.email || null,
          tokens_generated: targetMsg.tokens?.completion_tokens || 0,
        });
      } catch (err) {
        console.warn('Failed to submit thought:', err);
      }
    }
  };

  const handleSaveTurnThought = async (turnId) => {
    const text = thoughtDrafts[turnId]?.trim();
    if (!text) return;
    await handleSaveTurnThoughtDirect(turnId, text);
    setThoughtDrafts((prev) => ({ ...prev, [turnId]: '' }));
  };

  // Safe New Chat: Clears active chat window to start a fresh topic, but preserves complete query history in Query History
  const handleNewChat = () => {
    setActiveChat([]);
    setActiveTab('chat');
  };

  // Explicit Clear All History from the Query History tab
  const handleClearAllHistory = () => {
    if (confirm('Are you sure you want to permanently clear all stored query history?')) {
      if (currentUser?.email) {
        const userEmailKey = `ruler_chat_${currentUser.email.toLowerCase().trim()}`;
        try {
          localStorage.removeItem(userEmailKey);
          localStorage.removeItem('ruler_chat_history');
        } catch (e) {}
      }
      setChatHistory([]);
      setActiveChat([]);
    }
  };

  const handleOpenTurnInChat = (entry) => {
    const matchingUser = chatHistory.find(
      (m) => m.turnId === entry.turnId && m.role === 'user'
    ) || {
      turnId: entry.turnId,
      role: 'user',
      content: entry.userQuestion,
      timestamp: entry.timestamp,
    };
    setActiveChat([matchingUser, entry]);
    setActiveTab('chat');
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

          {/* Quick New Chat Button in Header */}
          <button
            type="button"
            onClick={handleNewChat}
            className="ml-2 hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-[12px] bg-[#D2B48C] hover:bg-[#c4a47c] text-[#002147] text-xs font-extrabold transition shadow-sm"
            title="Start a new chat conversation"
          >
            <span className="text-sm font-black">+</span>
            <span>New Chat</span>
          </button>
        </div>

        {/* User Info & Actions */}
        <div className="flex items-center gap-3">
          {/* Mobile New Chat Button */}
          <button
            type="button"
            onClick={handleNewChat}
            className="flex md:hidden items-center gap-1 px-2.5 py-1.5 rounded-[12px] bg-[#D2B48C] hover:bg-[#c4a47c] text-[#002147] text-xs font-bold transition shadow-sm"
            title="Start a new chat"
          >
            <span>+</span>
            <span>New Chat</span>
          </button>

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
            <div className="flex flex-col gap-2">
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

              {/* Primary + New Chat CTA in Sidebar */}
              <button
                type="button"
                onClick={() => {
                  handleNewChat();
                  setIsSidebarOpen(false);
                }}
                className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-[12px] bg-[#D2B48C] hover:bg-[#c4a47c] text-[#002147] text-xs font-extrabold transition shadow-sm mb-1"
              >
                <span className="text-sm font-black">+</span>
                <span>New Chat</span>
              </button>

            <button
              type="button"
              onClick={() => setActiveTab('chat')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-[12px] text-xs font-bold text-left transition ${
                activeTab === 'chat'
                  ? 'bg-[#002147] border border-[#D2B48C]/40 text-[#D2B48C] shadow-sm font-extrabold'
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
                  ? 'bg-[#002147] border border-[#D2B48C]/40 text-[#D2B48C] shadow-sm font-extrabold'
                  : 'text-[#D2B48C] hover:bg-white/10 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-sm">📜</span>
                <span>Query History</span>
              </div>
              {assistantEntries.length > 0 && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  activeTab === 'history' ? 'bg-[#D2B48C] text-[#002147]' : 'bg-[#D2B48C] text-[#002147]'
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
                  ? 'bg-[#002147] border border-[#D2B48C]/40 text-[#D2B48C] shadow-sm font-extrabold'
                  : 'text-[#D2B48C] hover:bg-white/10 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-sm">⭐</span>
                <span>Feedback & Notes</span>
              </div>
              {feedbackEntries.length > 0 && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  activeTab === 'feedback' ? 'bg-[#D2B48C] text-[#002147]' : 'bg-[#D2B48C] text-[#002147]'
                }`}>
                  {feedbackEntries.length}
                </span>
              )}
            </button>

            {/* Recent Stored Queries Quick Jump in Sidebar */}
            {assistantEntries.length > 0 && (
              <div className="mt-3 pt-3 border-t border-[#002855] flex flex-col gap-1.5 overflow-hidden">
                <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-[#D2B48C]/60">
                  Recent Saved Queries ({assistantEntries.length})
                </div>
                <div className="flex flex-col gap-1 max-h-36 overflow-y-auto pr-1">
                  {assistantEntries.slice(-4).reverse().map((entry, rIdx) => (
                    <button
                      key={rIdx}
                      type="button"
                      onClick={() => {
                        handleOpenTurnInChat(entry);
                        setIsSidebarOpen(false);
                      }}
                      className="text-left px-2.5 py-1.5 rounded-[8px] bg-white/5 hover:bg-white/10 text-[#D2B48C] text-[11px] truncate transition flex items-center gap-1.5"
                      title={entry.userQuestion}
                    >
                      <span className="text-[10px] text-[#D2B48C]/60 flex-shrink-0">#{entry.turnId}</span>
                      <span className="truncate">{entry.userQuestion || 'Query'}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
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
            currentUser={currentUser}
            activeMessages={activeChat}
            setActiveMessages={setActiveChat}
            chatHistory={chatHistory}
            setChatHistory={setChatHistory}
            onRecordQuery={handleRecordQuery}
            onNewChat={handleNewChat}
            onUpdateFeedback={handleUpdateFeedback}
            onSaveThought={handleSaveTurnThoughtDirect}
          />
        )}

        {/* Tab 2: Query History */}
        {activeTab === 'history' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-4xl w-full mx-auto flex flex-col gap-6">
            <div className="flex items-center justify-between pb-3 border-b border-[#D8CCBD]">
              <div>
                <h2 className="text-base font-bold text-[#002147]">Query & Answer History</h2>
                <p className="text-xs text-[#6A5A4A]">Past queries, generated token metrics, source chunk numbers, and user feedback (all sessions preserved)</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleNewChat}
                  className="text-xs font-bold text-[#002147] hover:bg-[#c4a47c] bg-[#D2B48C] px-3.5 py-1.5 rounded-[12px] transition flex items-center gap-1 shadow-sm"
                >
                  <span>+</span>
                  <span>New Chat</span>
                </button>
                {assistantEntries.length > 0 && (
                  <button
                    type="button"
                    onClick={handleClearAllHistory}
                    className="text-xs font-semibold text-[#8C7A68] hover:text-rose-600 hover:bg-rose-50 bg-[#F5EFEB] border border-[#D8CCBD] px-3 py-1.5 rounded-[12px] transition"
                  >
                    Clear History
                  </button>
                )}
              </div>
            </div>

            {assistantEntries.length === 0 ? (
              <div className="bg-white border border-[#D8CCBD] rounded-[12px] p-12 text-center flex flex-col items-center gap-3 my-auto shadow-sm">
                <h3 className="text-sm font-bold text-[#002147]">No Query History Yet</h3>
                <p className="text-xs text-[#8C7A68] max-w-sm">
                  Switch to the Compliance Chat tab and ask regulatory questions. All questions, tokens, and sources will be permanently archived here across sessions.
                </p>
                <button
                  type="button"
                  onClick={() => setActiveTab('chat')}
                  className="mt-2 bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold text-xs px-4 py-2 rounded-[12px] transition shadow-sm"
                >
                  Go to Compliance Chat →
                </button>
              </div>
            ) : (
              assistantEntries.map((entry, idx) => (
                <div
                  key={idx}
                  className="bg-white border border-[#D8CCBD] rounded-[12px] p-6 flex flex-col gap-4 shadow-sm"
                >
                  {/* Query Header with Resume in Chat Action */}
                  <div className="flex items-start justify-between gap-4 border-b border-[#F5EFEB] pb-3">
                    <div className="flex flex-col gap-1">
                      <span className="text-[11px] font-bold text-[#8C7A68] uppercase tracking-wider">
                        Query #{entry.turnId || idx + 1}
                      </span>
                      <h4 className="text-sm font-bold text-[#002147]">
                        {entry.userQuestion || 'Regulatory Query'}
                      </h4>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        type="button"
                        onClick={() => handleOpenTurnInChat(entry)}
                        className="text-xs font-bold text-[#002147] hover:bg-[#D2B48C] bg-[#F5EFEB] border border-[#D8CCBD] px-3 py-1.5 rounded-[12px] transition flex items-center gap-1.5 shadow-xs"
                        title="Open and continue this query in Compliance Chat"
                      >
                        <span>💬</span>
                        <span>Open in Chat</span>
                      </button>
                      <span className="text-xs text-[#8C7A68] font-mono bg-[#F5EFEB] px-2.5 py-1.5 rounded-[12px] border border-[#D8CCBD]">
                        {entry.timestamp}
                      </span>
                    </div>
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

                  {/* Feedback Status & Actions */}
                  <div className="bg-[#FAF8F5] border border-[#D8CCBD] rounded-[12px] p-3 flex items-center justify-between flex-wrap gap-2">
                    <span className="text-xs font-bold text-[#002147]">User Feedback:</span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleUpdateFeedback(entry.turnId, 'positive')}
                        className={`px-2.5 py-1 rounded-[10px] text-xs font-bold transition ${
                          entry.feedback === 'positive'
                            ? 'bg-[#002147] text-[#D2B48C]'
                            : 'bg-white text-[#002147] border border-[#D8CCBD] hover:bg-[#D2B48C]'
                        }`}
                      >
                        👍 Helpful
                      </button>
                      <button
                        type="button"
                        onClick={() => handleUpdateFeedback(entry.turnId, 'average')}
                        className={`px-2.5 py-1 rounded-[10px] text-xs font-bold transition ${
                          entry.feedback === 'average'
                            ? 'bg-[#002147] text-[#D2B48C]'
                            : 'bg-white text-[#002147] border border-[#D8CCBD] hover:bg-[#D2B48C]'
                        }`}
                      >
                        😐 Average
                      </button>
                      <button
                        type="button"
                        onClick={() => handleUpdateFeedback(entry.turnId, 'negative')}
                        className={`px-2.5 py-1 rounded-[10px] text-xs font-bold transition ${
                          entry.feedback === 'negative'
                            ? 'bg-[#002147] text-[#D2B48C]'
                            : 'bg-white text-[#002147] border border-[#D8CCBD] hover:bg-[#D2B48C]'
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

        {/* Tab 3: User Feedback Section with Dedicated Thoughts Space Column */}
        {activeTab === 'feedback' && (
          <div className="flex-1 overflow-y-auto p-8 max-w-4xl w-full mx-auto flex flex-col gap-6">
            {/* Feedback Header */}
            <div className="flex items-center justify-between pb-3 border-b border-[#D8CCBD] flex-wrap gap-3">
              <div>
                <h2 className="text-base font-bold text-[#002147]">User Feedback & Thoughts Center</h2>
                <p className="text-xs text-[#6A5A4A]">Share compliance thoughts, notes, and evaluate regulatory response accuracy</p>
              </div>

              {/* Filter Buttons */}
              <div className="flex bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] p-1 text-xs flex-wrap gap-1">
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
                  onClick={() => setFeedbackFilter('average')}
                  className={`px-3 py-1 rounded-[12px] font-bold transition ${
                    feedbackFilter === 'average'
                      ? 'bg-[#002147] text-[#D2B48C]'
                      : 'text-[#002147] hover:bg-[#E6D9C8]'
                  }`}
                >
                  😐 Average ({averageCount})
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

            {/* Metrics Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
                <span className="text-xs text-[#8C7A68] font-medium">Average Ratings</span>
                <span className="text-xl font-bold text-[#002147]">😐 {averageCount}</span>
                <span className="text-[11px] text-[#6A5A4A]">Neutral / satisfactory turns</span>
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
                    ? 'Submit queries in the Chat Space and click the 👍 Helpful, 😐 Average, or 👎 Needs Revision buttons to evaluate answers and attach thoughts.'
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
                              : entry.feedback === 'average'
                              ? 'bg-[#E8DEC8] text-[#002147] border border-[#D8CCBD]'
                              : 'bg-[#002147] text-[#D2B48C]'
                          }`}
                        >
                          {entry.feedback === 'positive' ? '👍 Helpful' : entry.feedback === 'average' ? '😐 Average' : '👎 Needs Revision'}
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
