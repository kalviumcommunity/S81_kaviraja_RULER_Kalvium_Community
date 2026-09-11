'use client';

import React, { useState, useEffect, useRef } from 'react';
import { uploadDocumentText, uploadDocumentFile, fetchDocuments, fetchServerConfig } from '../lib/api';

export default function AdminDashboard({
  currentUser,
  chatHistory = [],
  onLogout,
  onSwitchToUserPortal,
}) {
  const [adminTab, setAdminTab] = useState('conversations'); // 'overview' | 'conversations' | 'ingestion' | 'documents'
  const [activeFilter, setActiveFilter] = useState('all'); // 'all' | 'positive' | 'negative' | 'thoughts'
  const [searchQuery, setSearchQuery] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Ingestion State
  const [uploadMode, setUploadMode] = useState('text'); // 'text' | 'file'
  const [uploadText, setUploadText] = useState('');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadCategory, setUploadCategory] = useState('Institutional Regulation');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState({ text: '', type: '' });
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  // Documents & Server Config
  const [documentsList, setDocumentsList] = useState([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [serverConfig, setServerConfig] = useState(null);

  useEffect(() => {
    loadServerData();
  }, []);

  const loadServerData = async () => {
    try {
      const cfg = await fetchServerConfig();
      if (cfg?.config) setServerConfig(cfg.config);
    } catch (e) {
      console.warn('Config fetch error:', e);
    }

    try {
      setIsLoadingDocs(true);
      const docRes = await fetchDocuments();
      if (docRes?.documents) {
        setDocumentsList(docRes.documents);
      }
    } catch (e) {
      console.warn('Doc fetch error:', e);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const handleUploadText = async (e) => {
    e.preventDefault();
    if (!uploadText.trim()) return;

    setIsUploading(true);
    setUploadStatus({ text: 'Processing text, chunking, and indexing into vector database...', type: 'info' });

    try {
      const res = await uploadDocumentText({
        text: uploadText,
        title: uploadTitle || 'Regulatory Policy',
        category: uploadCategory,
      });

      setUploadStatus({
        text: `Success: Policy "${uploadTitle || 'Document'}" indexed successfully (${res.chunks_indexed || 1} chunks created).`,
        type: 'success',
      });
      setUploadText('');
      setUploadTitle('');
      loadServerData();
    } catch (err) {
      setUploadStatus({
        text: `Indexing error: ${err.message}`,
        type: 'error',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleUploadFile = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadStatus({ text: `Uploading and indexing "${selectedFile.name}" into knowledge base...`, type: 'info' });

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('category', uploadCategory);

      const res = await uploadDocumentFile(formData);

      setUploadStatus({
        text: `Success: File "${selectedFile.name}" indexed successfully (${res.data?.total_chunks || 1} chunks).`,
        type: 'success',
      });
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      loadServerData();
    } catch (err) {
      setUploadStatus({
        text: `File indexing error: ${err.message}`,
        type: 'error',
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Process user conversations and metrics
  const assistantEntries = chatHistory.filter((m) => m.role === 'assistant' && !m.isLoading);
  const totalGenTokens = assistantEntries.reduce(
    (acc, m) => acc + (m.tokens?.completion_tokens || 0),
    0
  );
  const totalQueries = assistantEntries.length;
  const positiveFeedbacks = assistantEntries.filter((m) => m.feedback === 'positive').length;
  const negativeFeedbacks = assistantEntries.filter((m) => m.feedback === 'negative').length;
  const thoughtsCount = assistantEntries.filter((m) => m.userThoughts && m.userThoughts.trim()).length;
  const satisfactionRate = totalQueries > 0 && (positiveFeedbacks + negativeFeedbacks > 0)
    ? Math.round((positiveFeedbacks / (positiveFeedbacks + negativeFeedbacks)) * 100)
    : 100;

  // Filter conversations
  const filteredConversations = assistantEntries.filter((entry) => {
    if (activeFilter === 'positive' && entry.feedback !== 'positive') return false;
    if (activeFilter === 'negative' && entry.feedback !== 'negative') return false;
    if (activeFilter === 'thoughts' && (!entry.userThoughts || !entry.userThoughts.trim())) return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchQuestion = (entry.userQuestion || '').toLowerCase().includes(q);
      const matchAnswer = (entry.content || '').toLowerCase().includes(q);
      const matchThoughts = (entry.userThoughts || '').toLowerCase().includes(q);
      if (!matchQuestion && !matchAnswer && !matchThoughts) return false;
    }

    return true;
  });

  return (
    <div className="flex flex-col h-screen w-full bg-[#FAF8F5] overflow-hidden select-none font-sans text-[#002147]">
      {/* Top Header - Oxford Blue with Tan */}
      <header className="h-16 bg-[#002147] border-b border-[#001630] px-4 sm:px-6 flex items-center justify-between flex-shrink-0 z-20 shadow-sm">
        <div className="flex items-center gap-3">
          {/* 3-Lines Hamburger Menu Button */}
          <button
            type="button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 rounded-[12px] bg-[#001630] hover:bg-[#083266] border border-[#083266] text-[#D2B48C] hover:text-white text-base font-bold flex items-center justify-center transition shadow-sm"
            title={isSidebarOpen ? 'Close Menu (✕)' : 'Open Menu (☰)'}
            aria-label="Toggle Sidebar Menu"
          >
            {isSidebarOpen ? '✕' : '☰'}
          </button>

          <div className="px-3 py-1 rounded-[12px] bg-[#D2B48C] text-[#002147] flex items-center justify-center text-xs font-bold shadow-sm uppercase tracking-wider">
            🏛️ RULER
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold text-white tracking-tight">Ruler Intelligence</h1>
              <span className="bg-[#001630] border border-[#083266] text-[#D2B48C] text-[10px] font-bold px-2 py-0.5 rounded-[12px] uppercase">
                Admin Console
              </span>
            </div>
            <p className="text-[11px] text-[#D2B48C] hidden sm:block">System Oversight, Document Ingestion & Feedback Analytics</p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <span className="text-xs font-bold text-white block">
              {currentUser?.name || 'Administrator'}
            </span>
            <span className="text-[10px] text-[#D2B48C] font-mono block">
              {currentUser?.email || 'admin@bank.gov'}
            </span>
          </div>

          <button
            type="button"
            onClick={onSwitchToUserPortal}
            className="bg-[#001630] hover:bg-[#083266] border border-[#D2B48C]/50 text-[#D2B48C] text-xs font-bold px-3 py-2 rounded-[12px] transition"
          >
            User Portal →
          </button>
          <button
            type="button"
            onClick={onLogout}
            className="bg-transparent hover:bg-[#D2B48C] hover:text-[#002147] border border-[#D2B48C] text-[#D2B48C] text-xs font-bold px-3 py-2 rounded-[12px] transition"
          >
            Sign Out
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
                <span>Admin Navigation</span>
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
              onClick={() => setAdminTab('overview')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-[12px] text-xs font-bold text-left transition ${
                adminTab === 'overview'
                  ? 'bg-[#D2B48C] text-[#002147] shadow-sm font-extrabold'
                  : 'text-[#D2B48C] hover:bg-white/10 hover:text-white'
              }`}
            >
              <span className="text-sm">📊</span>
              <span>Overview & Telemetry</span>
            </button>

            <button
              type="button"
              onClick={() => setAdminTab('conversations')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-[12px] text-xs font-bold text-left transition ${
                adminTab === 'conversations'
                  ? 'bg-[#D2B48C] text-[#002147] shadow-sm font-extrabold'
                  : 'text-[#D2B48C] hover:bg-white/10 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-sm">💬</span>
                <span className="truncate">User Feedback</span>
              </div>
              {totalQueries > 0 && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${
                  adminTab === 'conversations' ? 'bg-[#002147] text-[#D2B48C]' : 'bg-[#D2B48C] text-[#002147]'
                }`}>
                  {totalQueries}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setAdminTab('ingestion')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-[12px] text-xs font-bold text-left transition ${
                adminTab === 'ingestion'
                  ? 'bg-[#D2B48C] text-[#002147] shadow-sm font-extrabold'
                  : 'text-[#D2B48C] hover:bg-white/10 hover:text-white'
              }`}
            >
              <span className="text-sm">📥</span>
              <span>Policy Ingestion</span>
            </button>

            <button
              type="button"
              onClick={() => setAdminTab('documents')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-[12px] text-xs font-bold text-left transition ${
                adminTab === 'documents'
                  ? 'bg-[#D2B48C] text-[#002147] shadow-sm font-extrabold'
                  : 'text-[#D2B48C] hover:bg-white/10 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-sm">📚</span>
                <span>Knowledge Base</span>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${
                adminTab === 'documents' ? 'bg-[#002147] text-[#D2B48C]' : 'bg-[#D2B48C] text-[#002147]'
              }`}>
                {documentsList.length}
              </span>
            </button>
          </div>

          {/* Sidebar Footer */}
          <div className="border-t border-[#002855] pt-4 flex flex-col gap-2">
            <div className="flex items-center justify-between px-2 text-[11px] text-[#D2B48C]/80">
              <span>Compliance Engine</span>
              <span className="inline-flex items-center gap-1.5 text-emerald-400 font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Active</span>
              </span>
            </div>
            <button
              type="button"
              onClick={onSwitchToUserPortal}
              className="w-full bg-[#002147] hover:bg-[#083266] border border-[#D2B48C]/40 text-[#D2B48C] text-xs font-bold py-2 px-3 rounded-[12px] transition flex items-center justify-center gap-1.5 shadow-sm"
            >
              <span>Switch to User Portal</span>
              <span>→</span>
            </button>
          </div>
          </aside>
        )}

        {/* Main Container */}
        <main className="flex-1 overflow-y-auto p-8 max-w-6xl w-full mx-auto flex flex-col gap-6">

        {/* ----------------- TAB 1: SYSTEM OVERVIEW ----------------- */}
        {adminTab === 'overview' && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between pb-3 border-b border-[#D8CCBD]">
              <div>
                <h2 className="text-base font-bold text-[#002147]">System Telemetry & Activity</h2>
                <p className="text-xs text-[#6A5A4A]">Real-time query volume, token consumption, feedback satisfaction, and pipeline status</p>
              </div>
              <span className="px-3 py-1 bg-white border border-[#D8CCBD] text-[#002147] text-xs font-bold rounded-[12px] shadow-sm flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#002147]"></span>
                <span>Banking Compliance Engine Online</span>
              </span>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white border border-[#D8CCBD] p-5 rounded-[12px] flex flex-col gap-1.5 shadow-sm">
                <span className="text-xs text-[#6A5A4A] font-semibold">User Queries Handled</span>
                <span className="text-3xl font-bold text-[#002147]">{totalQueries}</span>
                <span className="text-[11px] text-[#8C7A68]">Active compliance sessions</span>
              </div>

              <div className="bg-white border border-[#D8CCBD] p-5 rounded-[12px] flex flex-col gap-1.5 shadow-sm">
                <span className="text-xs text-[#6A5A4A] font-semibold">Total Generated Tokens</span>
                <span className="text-3xl font-bold text-[#002147] font-mono">{totalGenTokens}</span>
                <span className="text-[11px] text-[#8C7A68]">Assistant completion usage</span>
              </div>

              <div className="bg-white border border-[#D8CCBD] p-5 rounded-[12px] flex flex-col gap-1.5 shadow-sm">
                <span className="text-xs text-[#6A5A4A] font-semibold">User Satisfaction</span>
                <span className="text-3xl font-bold text-[#002147]">{satisfactionRate}%</span>
                <span className="text-[11px] text-[#8C7A68]">👍 {positiveFeedbacks} Helpful / 👎 {negativeFeedbacks} Needs Revision</span>
              </div>

              <div className="bg-white border border-[#D8CCBD] p-5 rounded-[12px] flex flex-col gap-1.5 shadow-sm">
                <span className="text-xs text-[#6A5A4A] font-semibold">Shared Officer Thoughts</span>
                <span className="text-3xl font-bold text-[#002147]">{thoughtsCount}</span>
                <span className="text-[11px] text-[#8C7A68]">Notes & compliance annotations</span>
              </div>
            </div>


            {/* Quick Actions Card */}
            <div className="bg-white border border-[#D8CCBD] p-6 rounded-[12px] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
              <div className="flex flex-col gap-1">
                <h4 className="text-sm font-bold text-[#002147]">Knowledge Base & Document Upload Access</h4>
                <p className="text-xs text-[#6A5A4A]">Only administrators have authority to upload new policies, compliance directives, and audit reports.</p>
              </div>
              <button
                type="button"
                onClick={() => setAdminTab('ingestion')}
                className="bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold text-xs px-4 py-2 rounded-[12px] transition whitespace-nowrap shadow-sm"
              >
                Upload New Policy / Audit →
              </button>
            </div>
          </div>
        )}

        {/* ----------------- TAB 2: USER CONVERSATIONS & FEEDBACK ----------------- */}
        {adminTab === 'conversations' && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#D8CCBD] gap-3">
              <div>
                <h2 className="text-base font-bold text-[#002147]">User Conversations & Feedback Center</h2>
                <p className="text-xs text-[#6A5A4A]">Inspect user queries with chatbot, exact question timestamps, generated tokens, feedback ratings, and officer thoughts</p>
              </div>

              {/* Filters & Search */}
              <div className="flex items-center gap-2 flex-wrap">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search queries or answers..."
                  className="bg-white border border-[#D8CCBD] rounded-[12px] px-3 py-1.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147] w-48 shadow-sm"
                />
                <div className="flex bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] p-0.5">
                  <button
                    type="button"
                    onClick={() => setActiveFilter('all')}
                    className={`px-2.5 py-1 rounded-[10px] text-xs font-bold transition ${
                      activeFilter === 'all' ? 'bg-[#002147] text-[#D2B48C]' : 'text-[#002147] hover:bg-[#D2B48C]'
                    }`}
                  >
                    All ({assistantEntries.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveFilter('positive')}
                    className={`px-2.5 py-1 rounded-[10px] text-xs font-bold transition ${
                      activeFilter === 'positive' ? 'bg-[#002147] text-[#D2B48C]' : 'text-[#002147] hover:bg-[#D2B48C]'
                    }`}
                  >
                    👍 Helpful ({positiveFeedbacks})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveFilter('negative')}
                    className={`px-2.5 py-1 rounded-[10px] text-xs font-bold transition ${
                      activeFilter === 'negative' ? 'bg-[#002147] text-[#D2B48C]' : 'text-[#002147] hover:bg-[#D2B48C]'
                    }`}
                  >
                    👎 Needs Revision ({negativeFeedbacks})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveFilter('thoughts')}
                    className={`px-2.5 py-1 rounded-[10px] text-xs font-bold transition ${
                      activeFilter === 'thoughts' ? 'bg-[#002147] text-[#D2B48C]' : 'text-[#002147] hover:bg-[#D2B48C]'
                    }`}
                  >
                    ✏️ Notes ({thoughtsCount})
                  </button>
                </div>
              </div>
            </div>

            {/* Conversation Records */}
            {filteredConversations.length === 0 ? (
              <div className="bg-white border border-[#D8CCBD] rounded-[12px] p-12 text-center flex flex-col items-center gap-3 shadow-sm my-auto">
                <h3 className="text-sm font-bold text-[#002147]">No User Conversations Found</h3>
                <p className="text-xs text-[#8C7A68] max-w-md">
                  {assistantEntries.length === 0
                    ? 'No queries have been submitted in this session yet. User conversations and their timestamps will appear here once officers ask questions in the User Portal.'
                    : 'No conversation entries match your current filter or search criteria.'}
                </p>
                {assistantEntries.length === 0 && (
                  <button
                    type="button"
                    onClick={onSwitchToUserPortal}
                    className="mt-2 bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold text-xs px-4 py-2 rounded-[12px] transition shadow-sm"
                  >
                    Open User Portal to Test Query →
                  </button>
                )}
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                {filteredConversations.map((entry, idx) => (
                  <div
                    key={idx}
                    className="bg-white border border-[#D8CCBD] rounded-[12px] p-6 flex flex-col gap-4 shadow-sm"
                  >
                    {/* Header with Query & Exact Timestamp */}
                    <div className="flex items-start justify-between gap-4 border-b border-[#F5EFEB] pb-3">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[11px] font-bold text-[#8C7A68] uppercase tracking-wider">
                            Turn #{entry.turnId || idx + 1}
                          </span>
                          <span className="text-[11px] font-mono text-[#002147] bg-[#F5EFEB] px-2 py-0.5 rounded-[6px] border border-[#D8CCBD]">
                            Officer Query
                          </span>
                        </div>
                        <h3 className="text-sm font-bold text-[#002147] mt-0.5">
                          &quot;{entry.userQuestion || 'Regulatory Query'}&quot;
                        </h3>
                      </div>

                      <div className="flex flex-col items-end gap-1 flex-shrink-0">
                        <span className="text-xs text-[#002147] font-mono font-bold bg-[#F5EFEB] px-2.5 py-1 rounded-[12px] border border-[#D8CCBD]">
                          🕒 Asked at: {entry.timestamp}
                        </span>
                      </div>
                    </div>

                    {/* Chatbot Response */}
                    <div className="flex flex-col gap-1.5">
                      <span className="text-xs font-bold text-[#002147]">Chatbot Response:</span>
                      <div className="p-4 bg-[#F5EFEB] rounded-[12px] text-xs text-[#002147] leading-relaxed font-sans whitespace-pre-wrap border border-[#D8CCBD]">
                        {entry.content}
                      </div>
                    </div>

                    {/* Generated Token Usage & Feedback Badges */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 border-t border-[#F5EFEB]">
                      {/* Generated Tokens */}
                      <div className="bg-[#002147] rounded-[12px] p-3 flex items-center justify-between text-[#D2B48C]">
                        <span className="text-xs font-bold flex items-center gap-1.5">
                          <span>⚡</span>
                          <span>Generated Tokens:</span>
                        </span>
                        <span className="font-mono text-xs font-bold text-[#002147] bg-[#D2B48C] px-2.5 py-0.5 rounded-[12px]">
                          {entry.tokens?.completion_tokens || 0} tokens
                        </span>
                      </div>

                      {/* User Feedback Rating */}
                      <div className="bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] p-3 flex items-center justify-between">
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
                            <span className="text-[#8C7A68]">Unrated</span>
                          )}
                        </span>
                      </div>

                      {/* Sources Cited */}
                      <div className="bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] p-3 flex items-center justify-between">
                        <span className="text-xs font-bold text-[#002147]">Citations:</span>
                        <span className="text-xs font-mono font-bold text-[#002147]">
                          {entry.sources?.length || 0} chunks used
                        </span>
                      </div>
                    </div>

                    {/* Officer Shared Thoughts & Notes if submitted */}
                    {entry.userThoughts && (
                      <div className="bg-[#FAF8F5] border border-[#D8CCBD] rounded-[12px] p-3.5 text-xs text-[#002147]">
                        <div className="font-bold text-[11px] text-[#8C7A68] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                          <span>✏️</span>
                          <span>Officer Compliance Thoughts & Notes:</span>
                        </div>
                        <p className="italic text-[#002147] leading-relaxed">&quot;{entry.userThoughts}&quot;</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ----------------- TAB 3: POLICY & AUDIT INGESTION (ADMIN EXCLUSIVE) ----------------- */}
        {adminTab === 'ingestion' && (
          <div className="flex flex-col gap-6">
            <div className="pb-3 border-b border-[#D8CCBD] flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-[#002147]">Policy, Audit & Document Ingestion</h2>
                <p className="text-xs text-[#6A5A4A]">Exclusive Administrator Authority: Upload and index banking policies, audit guidelines, or compliance standards into the vector database</p>
              </div>
              <div className="flex bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] p-1">
                <button
                  type="button"
                  onClick={() => setUploadMode('text')}
                  className={`px-3 py-1.5 rounded-[10px] text-xs font-bold transition ${
                    uploadMode === 'text' ? 'bg-[#002147] text-[#D2B48C]' : 'text-[#002147] hover:bg-[#D2B48C]'
                  }`}
                >
                  Text Editor Paste
                </button>
                <button
                  type="button"
                  onClick={() => setUploadMode('file')}
                  className={`px-3 py-1.5 rounded-[10px] text-xs font-bold transition ${
                    uploadMode === 'file' ? 'bg-[#002147] text-[#D2B48C]' : 'text-[#002147] hover:bg-[#D2B48C]'
                  }`}
                >
                  File Upload (.txt, .md, .pdf)
                </button>
              </div>
            </div>

            {/* Ingestion Mode 1: Text Paste */}
            {uploadMode === 'text' && (
              <form onSubmit={handleUploadText} className="bg-white border border-[#D8CCBD] p-6 rounded-[12px] flex flex-col gap-4 shadow-sm">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#002147]">Document / Policy Title</label>
                    <input
                      type="text"
                      value={uploadTitle}
                      onChange={(e) => setUploadTitle(e.target.value)}
                      placeholder="e.g. Basel III Liquidity Standards Update 2026"
                      className="bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] px-4 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147]"
                      required
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#002147]">Document Category</label>
                    <select
                      value={uploadCategory}
                      onChange={(e) => setUploadCategory(e.target.value)}
                      className="bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] px-4 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147]"
                    >
                      <option value="Institutional Regulation">Institutional Regulation</option>
                      <option value="Audit & Compliance Reports">Audit & Compliance Reports</option>
                      <option value="Capital Adequacy & Basel Framework">Capital Adequacy & Basel Framework</option>
                      <option value="AML / KYC Directives">AML / KYC Directives</option>
                      <option value="Cybersecurity & Encryption Standard">Cybersecurity & Encryption Standard</option>
                      <option value="Internal Risk Policy">Internal Risk Policy</option>
                    </select>
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-[#002147]">Policy / Audit Text Content</label>
                  <textarea
                    value={uploadText}
                    onChange={(e) => setUploadText(e.target.value)}
                    placeholder="Paste the full regulatory guidelines, sections, and audit criteria here..."
                    rows={10}
                    className="bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] p-4 text-xs text-[#002147] font-mono focus:outline-none focus:border-[#002147] leading-relaxed"
                    required
                  />
                </div>

                {uploadStatus.text && (
                  <div
                    className={`p-3 rounded-[12px] text-xs font-semibold ${
                      uploadStatus.type === 'success'
                        ? 'bg-[#F5EFEB] border border-[#D2B48C] text-[#002147]'
                        : uploadStatus.type === 'info'
                        ? 'bg-[#F5EFEB] border border-[#D8CCBD] text-[#002147]'
                        : 'bg-red-50 border border-red-200 text-red-800'
                    }`}
                  >
                    {uploadStatus.text}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isUploading || !uploadText.trim()}
                  className="bg-[#002147] hover:bg-[#001630] disabled:opacity-40 text-[#D2B48C] font-bold py-2.5 px-6 rounded-[12px] text-xs transition flex items-center justify-center gap-2 self-start shadow-sm"
                >
                  <span>{isUploading ? 'Chunking & Indexing...' : 'Index Policy into Knowledge Base'}</span>
                  <span>→</span>
                </button>
              </form>
            )}

            {/* Ingestion Mode 2: File Upload */}
            {uploadMode === 'file' && (
              <form onSubmit={handleUploadFile} className="bg-white border border-[#D8CCBD] p-6 rounded-[12px] flex flex-col gap-4 shadow-sm">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-[#002147]">Document Category</label>
                  <select
                    value={uploadCategory}
                    onChange={(e) => setUploadCategory(e.target.value)}
                    className="bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] px-4 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147] max-w-md"
                  >
                    <option value="Institutional Regulation">Institutional Regulation</option>
                    <option value="Audit & Compliance Reports">Audit & Compliance Reports</option>
                    <option value="Capital Adequacy & Basel Framework">Capital Adequacy & Basel Framework</option>
                    <option value="AML / KYC Directives">AML / KYC Directives</option>
                    <option value="Cybersecurity & Encryption Standard">Cybersecurity & Encryption Standard</option>
                    <option value="Internal Risk Policy">Internal Risk Policy</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-[#002147]">Select Document / Policy File</label>
                  <div className="border-2 border-dashed border-[#D8CCBD] rounded-[12px] p-8 text-center bg-[#FAF8F5] flex flex-col items-center justify-center gap-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".txt,.md,.pdf,.json,.csv"
                      onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                      className="text-xs text-[#002147] file:mr-4 file:py-2 file:px-4 file:rounded-[12px] file:border-0 file:text-xs file:font-bold file:bg-[#002147] file:text-[#D2B48C] hover:file:bg-[#001630]"
                    />
                    <p className="text-[11px] text-[#8C7A68] mt-1">
                      Supported formats: TXT, MD, PDF, JSON, CSV (Max 10MB)
                    </p>
                  </div>
                </div>

                {uploadStatus.text && (
                  <div
                    className={`p-3 rounded-[12px] text-xs font-semibold ${
                      uploadStatus.type === 'success'
                        ? 'bg-[#F5EFEB] border border-[#D2B48C] text-[#002147]'
                        : uploadStatus.type === 'info'
                        ? 'bg-[#F5EFEB] border border-[#D8CCBD] text-[#002147]'
                        : 'bg-red-50 border border-red-200 text-red-800'
                    }`}
                  >
                    {uploadStatus.text}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isUploading || !selectedFile}
                  className="bg-[#002147] hover:bg-[#001630] disabled:opacity-40 text-[#D2B48C] font-bold py-2.5 px-6 rounded-[12px] text-xs transition flex items-center justify-center gap-2 self-start shadow-sm"
                >
                  <span>{isUploading ? 'Uploading & Indexing...' : 'Upload & Index Document File'}</span>
                  <span>→</span>
                </button>
              </form>
            )}
          </div>
        )}

        {/* ----------------- TAB 4: KNOWLEDGE BASE DOCUMENTS ----------------- */}
        {adminTab === 'documents' && (
          <div className="flex flex-col gap-6">
            <div className="pb-3 border-b border-[#D8CCBD] flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-[#002147]">Knowledge Base & Document Repository</h2>
                <p className="text-xs text-[#6A5A4A]">Active regulatory documents, policy guidelines, and audit corpora indexed for vector retrieval</p>
              </div>
              <button
                type="button"
                onClick={loadServerData}
                disabled={isLoadingDocs}
                className="bg-[#F5EFEB] hover:bg-[#D2B48C] border border-[#D8CCBD] text-[#002147] text-xs font-bold px-3 py-1.5 rounded-[12px] transition"
              >
                {isLoadingDocs ? 'Refreshing...' : '🔄 Refresh Store'}
              </button>
            </div>

            {documentsList.length === 0 ? (
              <div className="bg-white border border-[#D8CCBD] rounded-[12px] p-12 text-center flex flex-col items-center gap-3 shadow-sm my-auto">
                <h3 className="text-sm font-bold text-[#002147]">Knowledge Base Online</h3>
                <p className="text-xs text-[#8C7A68] max-w-md">
                  Core banking regulation corpus (<code className="font-mono text-[#002147]">sample_banking_regulation.txt</code>) is active and indexed.
                  Upload additional policies to see them listed in this repository.
                </p>
                <button
                  type="button"
                  onClick={() => setAdminTab('ingestion')}
                  className="mt-2 bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold text-xs px-4 py-2 rounded-[12px] transition shadow-sm"
                >
                  Upload First Policy →
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {documentsList.map((doc, idx) => (
                  <div
                    key={idx}
                    className="bg-white border border-[#D8CCBD] rounded-[12px] p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm"
                  >
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="text-xs font-bold text-[#002147] font-mono">
                          {doc.filename || doc.doc_id}
                        </h4>
                        <span className="text-[10px] bg-[#F5EFEB] border border-[#D8CCBD] text-[#6A5A4A] px-2 py-0.5 rounded-[6px] font-semibold">
                          {doc.category || 'Institutional Regulation'}
                        </span>
                        <span className="text-[10px] bg-[#002147] text-[#D2B48C] px-2 py-0.5 rounded-[6px] font-mono">
                          ● Indexed
                        </span>
                      </div>
                      <span className="text-[11px] text-[#8C7A68] font-mono">
                        Doc ID: {doc.doc_id || `DOC_${idx + 1}`}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs font-mono text-[#002147]">
                      <div className="flex flex-col items-end">
                        <span className="font-bold">{doc.chunks_indexed || doc.total_chunks || 'Multiple'} chunks</span>
                        <span className="text-[10px] text-[#8C7A68]">Vectorized</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </main>
      </div>
    </div>
  );
}
