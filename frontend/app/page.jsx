'use client';

import React, { useState, useEffect } from 'react';
import AuthScreen from '../components/AuthScreen';
import AppOverview from '../components/AppOverview';
import UserDashboard from '../components/UserDashboard';
import AdminDashboard from '../components/AdminDashboard';
import { fetchUserHistory } from '../lib/api';

export default function AppRoot() {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentPortal, setCurrentPortal] = useState('overview'); // 'overview' | 'user' | 'admin'
  const [chatHistory, setChatHistory] = useState([]);

  // 1. Check saved user session and load user-specific chat history
  useEffect(() => {
    const saved = localStorage.getItem('ruler_user');
    if (saved) {
      try {
        const u = JSON.parse(saved);
        setCurrentUser(u);
        setIsAuthenticated(true);
        loadUserChatHistory(u);

        if (u.role === 'Administrator' || (u.email && u.email.toLowerCase().includes('admin'))) {
          setCurrentPortal('admin');
        } else {
          setCurrentPortal('overview');
        }
      } catch (e) {
        console.warn('Could not parse user from localStorage');
      }
    }
  }, []);

  // 2. Load chat history specific to user account from LocalStorage + MongoDB
  const loadUserChatHistory = async (user) => {
    if (!user || !user.email) return;
    const userEmailKey = `ruler_chat_${user.email.toLowerCase().trim()}`;
    
    let localHistory = [];
    try {
      const savedChat = localStorage.getItem(userEmailKey);
      if (savedChat) {
        localHistory = JSON.parse(savedChat);
      }
    } catch (e) {
      console.warn('Could not read user chat from localStorage:', e);
    }

    if (localHistory.length > 0) {
      setChatHistory(localHistory);
    }

    // Also fetch historical queries from MongoDB to ensure complete history across sessions
    try {
      const serverRes = await fetchUserHistory(user.email);
      if (serverRes?.queries && serverRes.queries.length > 0) {
        const reconstructed = [];
        serverRes.queries.forEach((q, idx) => {
          const turnId = idx + 1;
          const timeStr = q.created_at
            ? new Date(q.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : 'Past Session';

          reconstructed.push({
            turnId,
            role: 'user',
            content: q.question,
            timestamp: timeStr,
          });

          reconstructed.push({
            turnId,
            role: 'assistant',
            content: q.answer,
            isGrounded: q.is_grounded !== false,
            confidence: q.confidence || 'high',
            status: q.status || 'success',
            tokens: {
              completion_tokens: q.tokens_generated || Math.round((q.answer || '').split(/\s+/).length * 1.3),
            },
            sources: q.sources || [],
            timestamp: timeStr,
            userQuestion: q.question,
            feedback: null,
            userThoughts: '',
          });
        });

        if (localHistory.length === 0) {
          setChatHistory(reconstructed);
          try {
            localStorage.setItem(userEmailKey, JSON.stringify(reconstructed));
          } catch (e) {}
        } else {
          // Merge preserving local ratings/thoughts while incorporating missing server queries
          const merged = [...localHistory];
          reconstructed.forEach((item) => {
            if (item.role === 'user') {
              const exists = merged.some((m) => m.role === 'user' && m.content === item.content);
              if (!exists) {
                const turnId = Math.floor(merged.length / 2) + 1;
                merged.push({ ...item, turnId });
                const matchingAssistant = reconstructed.find((a) => a.role === 'assistant' && a.userQuestion === item.content);
                if (matchingAssistant) {
                  merged.push({ ...matchingAssistant, turnId });
                }
              }
            }
          });
          setChatHistory(merged);
          try {
            localStorage.setItem(userEmailKey, JSON.stringify(merged));
          } catch (e) {}
        }
      }
    } catch (e) {
      console.warn('Could not fetch server queries for user:', e);
    }
  };

  // 3. Auto-save chat history to user account key whenever chatHistory changes
  useEffect(() => {
    if (currentUser?.email && chatHistory && chatHistory.length > 0) {
      const userEmailKey = `ruler_chat_${currentUser.email.toLowerCase().trim()}`;
      try {
        localStorage.setItem(userEmailKey, JSON.stringify(chatHistory));
        localStorage.setItem('ruler_chat_history', JSON.stringify(chatHistory));
      } catch (e) {
        console.warn('Failed to save user chat history:', e);
      }
    }
  }, [chatHistory, currentUser]);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
    loadUserChatHistory(user);

    if (user.role === 'Administrator' || (user.email && user.email.toLowerCase().includes('admin'))) {
      setCurrentPortal('admin');
    } else {
      setCurrentPortal('overview');
    }
  };

  const handleLogout = () => {
    if (confirm('Sign out from Ruler Regulatory AI Dashboard?')) {
      localStorage.removeItem('ruler_user');
      setCurrentUser(null);
      setIsAuthenticated(false);
      setChatHistory([]);
      setCurrentPortal('overview');
    }
  };

  if (!isAuthenticated) {
    return <AuthScreen onLoginSuccess={handleLoginSuccess} />;
  }

  // Render Admin Dashboard
  if (currentPortal === 'admin') {
    return (
      <AdminDashboard
        currentUser={currentUser}
        chatHistory={chatHistory}
        onLogout={handleLogout}
        onSwitchToUserPortal={() => setCurrentPortal('user')}
      />
    );
  }

  // Render Intermediate Overview / About Page with AI Launch Button & Contact Info
  if (currentPortal === 'overview') {
    return (
      <AppOverview
        currentUser={currentUser}
        onEnterAI={() => setCurrentPortal('user')}
        onLogout={handleLogout}
      />
    );
  }

  // Render Interactive User Portal (Chat Space, History, Feedback)
  return (
    <UserDashboard
      currentUser={currentUser}
      chatHistory={chatHistory}
      setChatHistory={setChatHistory}
      onLogout={handleLogout}
      onBackToOverview={() => setCurrentPortal('overview')}
    />
  );
}

