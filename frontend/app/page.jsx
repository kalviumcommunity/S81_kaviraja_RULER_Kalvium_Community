'use client';

import React, { useState, useEffect } from 'react';
import AuthScreen from '../components/AuthScreen';
import AppOverview from '../components/AppOverview';
import UserDashboard from '../components/UserDashboard';
import AdminDashboard from '../components/AdminDashboard';

export default function AppRoot() {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentPortal, setCurrentPortal] = useState('overview'); // 'overview' | 'user' | 'admin'
  const [chatHistory, setChatHistory] = useState([]);

  // Check saved user session
  useEffect(() => {
    const saved = localStorage.getItem('ruler_user');
    if (saved) {
      try {
        const u = JSON.parse(saved);
        setCurrentUser(u);
        setIsAuthenticated(true);
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

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
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
