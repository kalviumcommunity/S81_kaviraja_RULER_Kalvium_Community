'use client';

import React, { useState, useRef, useEffect } from 'react';
import { queryRAG } from '../lib/api';

const SUGGESTED_PROMPTS = [
  'What is the mandatory Tier 1 capital adequacy ratio under the regulatory framework?',
  'What are the mandatory data encryption directives and security controls for bank transfers?',
  'What are the Liquidity Coverage Ratio (LCR) calculation guidelines and stress criteria?',
  'What transaction thresholds require unanimous board authorization and regulatory filing?',
  'What are the RBI guidelines for Non-Performing Asset (NPA) classification and provisioning?',
];

export default function AssistantChat({
  chatHistory,
  setChatHistory,
  onTokensUpdated,
}) {
  const [inputText, setInputText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});
  const [showThoughtInput, setShowThoughtInput] = useState({});
  const [thoughtDrafts, setThoughtDrafts] = useState({});
  const streamEndRef = useRef(null);

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleSendQuery = async (question) => {
    const q = (question || inputText).trim();
    if (!q || isSubmitting) return;

    setInputText('');
    setIsSubmitting(true);

    const turnIndex = chatHistory.length + 1;
    const timeStr = new Date().toLocaleTimeString();

    // Add User Message
    const userMsg = {
      turnId: turnIndex,
      role: 'user',
      content: q,
      timestamp: timeStr,
    };

    // Add Loading Assistant Placeholder
    const loadingMsg = {
      turnId: turnIndex,
      role: 'assistant',
      content: 'Retrieving regulatory directives and generating grounded answer...',
      isLoading: true,
      timestamp: timeStr,
      tokens: null,
    };

    setChatHistory((prev) => [...prev, userMsg, loadingMsg]);

    try {
      const data = await queryRAG(q, 3, 0.2);

      const tokensUsed = data.metadata?.tokens_used || {};
      const genTokens = tokensUsed.completion_tokens !== undefined
        ? tokensUsed.completion_tokens
        : Math.round((data.answer || '').split(/\s+/).length * 1.3);
      const promptTokens = tokensUsed.prompt_tokens || 350;
      const totalTurnTokens = tokensUsed.total_tokens || (genTokens + promptTokens);

      if (onTokensUpdated) {
        onTokensUpdated(genTokens, totalTurnTokens);
      }

      // Format sources with sequential 1-based chunk numbers matching citations [1], [2], [3]
      const sourcesWithChunkNumbers = (data.sources || []).map((src, sIdx) => {
        const chunkNum = sIdx + 1;
        return {
          ...src,
          chunkNumber: chunkNum,
          marker: `[${chunkNum}]`,
        };
      });

      const assistantMsg = {
        turnId: turnIndex,
        role: 'assistant',
        content: data.answer,
        isGrounded: data.is_grounded !== false,
        confidence: data.confidence || 'high',
        status: data.status || 'success',
        tokens: {
          completion_tokens: genTokens,
          prompt_tokens: promptTokens,
          total_tokens: totalTurnTokens,
        },
        sources: sourcesWithChunkNumbers,
        timestamp: new Date().toLocaleTimeString(),
        userQuestion: q,
        feedback: null, // 'positive' | 'negative' | null
        userThoughts: '',
      };

      setChatHistory((prev) => {
        const next = [...prev];
        next[next.length - 1] = assistantMsg;
        return next;
      });
    } catch (err) {
      console.error('Query execution error:', err);
      const fallbackTokens = { completion_tokens: 15, prompt_tokens: 50, total_tokens: 65 };
      if (onTokensUpdated) {
        onTokensUpdated(fallbackTokens.completion_tokens, fallbackTokens.total_tokens);
      }

      const errorMsg = {
        turnId: turnIndex,
        role: 'assistant',
        content: `Failed to retrieve answer from knowledge base: ${err.message}. Please verify the server is running.`,
        isGrounded: false,
        confidence: 'low',
        status: 'error',
        tokens: fallbackTokens,
        sources: [],
        timestamp: new Date().toLocaleTimeString(),
        userQuestion: q,
        feedback: null,
      };

      setChatHistory((prev) => {
        const next = [...prev];
        next[next.length - 1] = errorMsg;
        return next;
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFeedback = (turnId, rating) => {
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

  const handleSaveThought = (turnId) => {
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

    setShowThoughtInput((prev) => ({ ...prev, [turnId]: false }));
  };

  const toggleSourceExpand = (msgIdx, srcIdx) => {
    const key = `${msgIdx}_${srcIdx}`;
    setExpandedSources((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendQuery();
    }
  };

  return (
    <div className="flex flex-col h-full w-full overflow-hidden bg-[#FAF8F5] font-sans text-[#002147]">
      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-6 max-w-4xl w-full mx-auto">
        {chatHistory.length === 0 ? (
          <div className="bg-white border border-[#D8CCBD] rounded-[12px] p-8 text-center flex flex-col items-center gap-3 my-auto shadow-sm">
            <div className="w-11 h-11 rounded-[12px] bg-[#002147] text-[#D2B48C] flex items-center justify-center text-lg font-bold">
              R
            </div>
            <h3 className="text-base font-bold text-[#002147]">Ask Regulatory & Compliance Directives</h3>
            <p className="text-xs text-[#6A5A4A] max-w-md leading-relaxed">
              Query banking compliance rules, capital adequacy requirements, risk reserve limits, and reporting standards.
            </p>

            <div className="flex flex-wrap gap-2 justify-center mt-3">
              {SUGGESTED_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendQuery(prompt)}
                  className="bg-[#F5EFEB] hover:bg-[#D2B48C] hover:text-[#002147] border border-[#D8CCBD] text-[#002147] px-3.5 py-2 rounded-[12px] text-xs font-semibold transition duration-150 text-left shadow-sm"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          chatHistory.map((msg, idx) => (
            <div key={idx} className="w-full flex flex-col gap-1 transition-all duration-200">
              {msg.role === 'user' ? (
                <div className="self-end max-w-[80%] ml-auto bg-[#002147] text-white px-5 py-3.5 rounded-[12px] text-sm leading-relaxed shadow-sm">
                  {msg.content}
                </div>
              ) : msg.isLoading ? (
                <div className="w-full bg-white border border-[#D8CCBD] p-5 rounded-[12px] flex flex-col gap-2 shadow-sm">
                  <div className="text-xs font-bold text-[#002147]">Ruler Intelligence Assistant</div>
                  <div className="text-xs text-[#8C7A68] italic flex items-center gap-2">
                    <span>{msg.content}</span>
                  </div>
                </div>
              ) : (
                <div className="w-full bg-white border border-[#D8CCBD] p-6 rounded-[12px] flex flex-col gap-5 shadow-sm">
                  {/* Header */}
                  <div className="flex items-center justify-between border-b border-[#F5EFEB] pb-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-[#002147]">
                      <span>Ruler Intelligence Assistant</span>
                      <span className="text-[10px] text-[#002147] font-mono bg-[#F5EFEB] px-2 py-0.5 rounded-[12px] border border-[#D8CCBD]">
                        Turn #{msg.turnId}
                      </span>
                    </div>
                    <span className="text-xs text-[#8C7A68] font-mono">{msg.timestamp}</span>
                  </div>

                  {/* 1. Answer */}
                  <div className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#002147]">
                      Answer:
                    </span>
                    <div className="text-sm text-[#002147] leading-relaxed font-sans whitespace-pre-wrap">
                      {msg.content}
                    </div>
                  </div>

                  {/* 2. Token Usage */}
                  <div className="flex items-center gap-2 pt-1 border-t border-[#F5EFEB]">
                    <span className="text-xs font-bold text-[#002147]">Tokens used:</span>
                    <span className="font-mono text-xs font-bold px-2.5 py-0.5 bg-[#002147] text-[#D2B48C] rounded-[12px]">
                      {msg.tokens?.completion_tokens !== undefined ? `${msg.tokens.completion_tokens}` : 'Not available'}
                    </span>
                  </div>


                  {/* Display Saved User Thoughts if present */}
                  {msg.userThoughts && (
                    <div className="bg-[#FAF8F5] border border-[#D8CCBD] rounded-[12px] p-3 text-xs text-[#002147]">
                      <div className="font-bold text-[11px] text-[#8C7A68] uppercase tracking-wider mb-0.5">
                        Your Shared Thoughts:
                      </div>
                      <p className="italic">{msg.userThoughts}</p>
                    </div>
                  )}

                  {/* User Feedback & Thoughts Action Row */}
                  <div className="border-t border-[#F5EFEB] pt-3 flex flex-col gap-3">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-[#6A5A4A] font-semibold">Was this answer helpful?</span>
                        <button
                          type="button"
                          onClick={() => handleFeedback(msg.turnId, 'positive')}
                          className={`px-3 py-1.5 rounded-[12px] text-xs font-bold flex items-center gap-1.5 transition ${
                            msg.feedback === 'positive'
                              ? 'bg-[#002147] text-[#D2B48C] shadow-sm'
                              : 'bg-[#F5EFEB] text-[#002147] hover:bg-[#D2B48C] border border-[#D8CCBD]'
                          }`}
                        >
                          <span>👍</span>
                          <span>Helpful</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFeedback(msg.turnId, 'negative')}
                          className={`px-3 py-1.5 rounded-[12px] text-xs font-bold flex items-center gap-1.5 transition ${
                            msg.feedback === 'negative'
                              ? 'bg-[#002147] text-[#D2B48C] shadow-sm'
                              : 'bg-[#F5EFEB] text-[#002147] hover:bg-[#D2B48C] border border-[#D8CCBD]'
                          }`}
                        >
                          <span>👎</span>
                          <span>Needs Revision</span>
                        </button>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            setShowThoughtInput((prev) => ({
                              ...prev,
                              [msg.turnId]: !prev[msg.turnId],
                            }))
                          }
                          className="text-xs text-[#002147] hover:underline font-bold flex items-center gap-1"
                        >
                          <span>✏️</span>
                          <span>{msg.userThoughts ? 'Edit Thoughts' : 'Share Thoughts'}</span>
                        </button>

                        {msg.feedback && (
                          <span className="text-xs text-[#002147] font-bold">
                            ✓ Feedback recorded
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Expandable Thoughts Input Space */}
                    {showThoughtInput[msg.turnId] && (
                      <div className="bg-[#FAF8F5] border border-[#D8CCBD] rounded-[12px] p-3 flex gap-2">
                        <input
                          type="text"
                          value={thoughtDrafts[msg.turnId] !== undefined ? thoughtDrafts[msg.turnId] : msg.userThoughts || ''}
                          onChange={(e) =>
                            setThoughtDrafts((prev) => ({
                              ...prev,
                              [msg.turnId]: e.target.value,
                            }))
                          }
                          placeholder="Write your thoughts or compliance remarks on this response..."
                          className="flex-1 bg-white border border-[#D8CCBD] rounded-[12px] px-3 py-2 text-xs text-[#002147] focus:outline-none focus:border-[#002147] placeholder-[#8C7A68]"
                        />
                        <button
                          type="button"
                          onClick={() => handleSaveThought(msg.turnId)}
                          className="bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold text-xs px-4 py-2 rounded-[12px] transition flex-shrink-0"
                        >
                          Save Thought
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={streamEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-6 bg-white border-t border-[#D8CCBD] flex-shrink-0 shadow-sm">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendQuery();
          }}
          className="flex gap-3 items-end max-w-4xl mx-auto"
        >
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a regulatory compliance question... (Press Enter to send, Shift+Enter for newline)"
            rows={2}
            className="flex-1 bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] px-4 py-3 text-sm text-[#002147] focus:outline-none focus:border-[#002147] resize-none min-h-[52px] max-h-28 transition placeholder-[#8C7A68] font-sans"
            required
          />
          <button
            type="submit"
            disabled={isSubmitting || !inputText.trim()}
            className="h-[52px] px-6 bg-[#002147] hover:bg-[#001630] disabled:opacity-40 disabled:cursor-not-allowed text-[#D2B48C] font-bold rounded-[12px] transition duration-150 flex items-center gap-2 text-sm shadow-sm"
          >
            <span>Ask AI</span>
            <span>→</span>
          </button>
        </form>
      </div>
    </div>
  );
}
