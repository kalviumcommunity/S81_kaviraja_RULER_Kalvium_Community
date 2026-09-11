'use client';

import React, { useState, useEffect } from 'react';
import AdminDashboard from '../../components/AdminDashboard';
import { loginAdminPasskey, logoutAdminSession, checkAdminSession } from '../../lib/api';

export default function RulerAdminPage() {
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);
  const [currentAdmin, setCurrentAdmin] = useState(null);
  const [passkeyInput, setPasskeyInput] = useState('');
  const [showPasskey, setShowPasskey] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  // Check server-side session on mount
  useEffect(() => {
    async function verifySession() {
      try {
        const sessionRes = await checkAdminSession();
        if (sessionRes?.authenticated) {
          setIsAdminAuthenticated(true);
          setCurrentAdmin(sessionRes.user);
        } else {
          setIsAdminAuthenticated(false);
          setCurrentAdmin(null);
        }

        // Load shared chat history for admin inspection
        const savedHistory = localStorage.getItem('ruler_chat_history');
        if (savedHistory) {
          setChatHistory(JSON.parse(savedHistory));
        }
      } catch (e) {
        setIsAdminAuthenticated(false);
      } finally {
        setIsLoadingSession(false);
      }
    }

    verifySession();
  }, []);

  const handlePasskeySubmit = async (e) => {
    e.preventDefault();
    const cleanKey = passkeyInput.trim();

    if (!cleanKey) {
      setErrorMsg('Please enter the Admin Passkey.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');

    try {
      // Server-side authentication: POST /api/admin/login
      const data = await loginAdminPasskey(cleanKey);
      setIsAdminAuthenticated(true);
      setCurrentAdmin(data.user);
      setPasskeyInput('');
    } catch (err) {
      setErrorMsg(err.message || 'Invalid administrative passkey. Access denied.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAdminLogout = async () => {
    try {
      await logoutAdminSession();
    } catch (e) {
      console.warn('Logout error:', e);
    } finally {
      setIsAdminAuthenticated(false);
      setCurrentAdmin(null);
      setPasskeyInput('');
    }
  };

  const handleSwitchToUserPortal = () => {
    window.location.href = '/';
  };

  // Loading indicator while verifying server session
  if (isLoadingSession) {
    return (
      <div className="fixed inset-0 bg-[#FAF8F5] z-50 flex items-center justify-center p-4 font-sans text-[#002147]">
        <div className="bg-white border border-[#D8CCBD] rounded-[12px] p-8 flex flex-col items-center gap-3 shadow-sm">
          <div className="px-4 py-1.5 rounded-[12px] bg-[#002147] text-[#D2B48C] flex items-center justify-center text-xs font-bold shadow-sm uppercase tracking-wider">
            RULER
          </div>
          <span className="text-xs font-bold text-[#002147]">Verifying Server Authorization...</span>
        </div>
      </div>
    );
  }

  // If authenticated via server session, render Admin Dashboard
  if (isAdminAuthenticated) {
    return (
      <AdminDashboard
        currentUser={currentAdmin}
        chatHistory={chatHistory}
        onLogout={handleAdminLogout}
        onSwitchToUserPortal={handleSwitchToUserPortal}
      />
    );
  }

  // Otherwise render Admin Passkey Unlock Screen for /ruler
  return (
    <div className="fixed inset-0 bg-[#FAF8F5] z-50 flex items-center justify-center p-4 overflow-y-auto font-sans select-none text-[#002147]">
      <div className="w-full max-w-md bg-white border border-[#D8CCBD] rounded-[12px] p-8 flex flex-col gap-6 my-auto shadow-sm">
        {/* Header */}
        <div className="text-center flex flex-col items-center gap-2">
          <div className="px-4 py-1.5 rounded-[12px] bg-[#002147] text-[#D2B48C] flex items-center justify-center text-xs font-bold shadow-sm uppercase tracking-wider">
            RULER
          </div>
          <h1 className="text-xl font-bold text-[#002147] tracking-tight">Administrator Console</h1>
          <p className="text-xs text-[#8C7A68]">Enter master passkey to unlock access</p>
        </div>

        {/* Passkey Form */}
        <form onSubmit={handlePasskeySubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-[#002147]" htmlFor="rulerPasskey">
                Master Admin Passkey
              </label>
              <button
                type="button"
                onClick={() => setShowPasskey(!showPasskey)}
                className="text-[11px] text-[#002147] hover:underline font-bold"
              >
                {showPasskey ? 'Hide Passkey' : 'Show Passkey'}
              </button>
            </div>

            <input
              type={showPasskey ? 'text' : 'password'}
              id="rulerPasskey"
              value={passkeyInput}
              onChange={(e) => {
                setPasskeyInput(e.target.value);
                setErrorMsg('');
              }}
              className="bg-white border border-[#D8CCBD] rounded-[12px] px-4 py-3 text-xs text-[#002147] font-mono focus:outline-none focus:border-[#002147] transition placeholder-[#B8A898]"
              placeholder="Enter master admin passkey"
              autoFocus
              required
            />
          </div>

          {errorMsg && (
            <div className="p-3 rounded-[12px] text-xs font-semibold text-center bg-red-50 border border-red-200 text-red-800">
              {errorMsg}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !passkeyInput.trim()}
            className="w-full bg-[#002147] hover:bg-[#001630] disabled:opacity-50 text-[#D2B48C] font-bold py-3 rounded-[12px] text-xs transition duration-150 shadow-sm flex items-center justify-center gap-2"
          >
            <span>{isSubmitting ? 'Authenticating...' : 'Unlock Admin Console'}</span>
            <span>→</span>
          </button>
        </form>
      </div>
    </div>
  );
}
