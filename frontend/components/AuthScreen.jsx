'use client';

import React, { useState } from 'react';

// Helper to get registered users from localStorage
function getRegisteredUsers() {
  if (typeof window === 'undefined') return [];
  try {
    const data = localStorage.getItem('ruler_registered_users');
    return data ? JSON.parse(data) : [];
  } catch (e) {
    console.warn('Error reading registered users from localStorage:', e);
    return [];
  }
}

// Helper to save registered users
function saveRegisteredUser(newUser) {
  if (typeof window === 'undefined') return;
  try {
    const existing = getRegisteredUsers();
    existing.push(newUser);
    localStorage.setItem('ruler_registered_users', JSON.stringify(existing));
  } catch (e) {
    console.warn('Error saving registered user to localStorage:', e);
  }
}

export default function AuthScreen({ onLoginSuccess }) {
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'signup'
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);

  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupRole, setSignupRole] = useState('Compliance Specialist');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupConfirmPassword, setSignupConfirmPassword] = useState('');

  const [feedback, setFeedback] = useState({ text: '', type: '' });

  // Handle Sign In
  const handleLoginSubmit = (e) => {
    e.preventDefault();
    const cleanEmail = loginEmail.trim().toLowerCase();
    const cleanPassword = loginPassword;

    if (!cleanEmail || !cleanPassword) {
      setFeedback({ text: 'Please enter both your bank email and password.', type: 'error' });
      return;
    }

    const registeredUsers = getRegisteredUsers();
    const matchedUser = registeredUsers.find((u) => u.email.toLowerCase() === cleanEmail);

    if (!matchedUser) {
      setFeedback({
        text: 'No user account found with this email. Please register via "Register User" first.',
        type: 'error',
      });
      return;
    }

    if (matchedUser.password !== cleanPassword) {
      setFeedback({
        text: 'Invalid password. Please enter your registered credentials.',
        type: 'error',
      });
      return;
    }

    const userSession = {
      name: matchedUser.name,
      role: matchedUser.role,
      email: matchedUser.email,
    };

    if (rememberMe) {
      localStorage.setItem('ruler_user', JSON.stringify(userSession));
    }

    setFeedback({ text: `Welcome back, ${matchedUser.name}! Opening User Portal...`, type: 'success' });
    setTimeout(() => {
      onLoginSuccess(userSession);
    }, 350);
  };

  // Handle Sign Up
  const handleSignupSubmit = (e) => {
    e.preventDefault();
    const cleanName = signupName.trim();
    const cleanEmail = signupEmail.trim().toLowerCase();
    const cleanPassword = signupPassword;
    const cleanConfirm = signupConfirmPassword;

    if (!cleanName || !cleanEmail || !cleanPassword) {
      setFeedback({ text: 'Please fill in all required fields.', type: 'error' });
      return;
    }

    if (cleanPassword !== cleanConfirm) {
      setFeedback({ text: 'Passwords do not match. Please verify.', type: 'error' });
      return;
    }

    const registeredUsers = getRegisteredUsers();
    const alreadyExists = registeredUsers.some((u) => u.email.toLowerCase() === cleanEmail);

    if (alreadyExists) {
      setFeedback({
        text: 'An account is already registered with this bank email. Please switch to "User Sign In".',
        type: 'error',
      });
      return;
    }

    const newUser = {
      name: cleanName,
      email: cleanEmail,
      role: signupRole,
      password: cleanPassword,
      registeredAt: new Date().toISOString(),
    };

    saveRegisteredUser(newUser);

    // Switch to Sign In tab and prepopulate email
    setLoginEmail(cleanEmail);
    setLoginPassword('');
    setAuthMode('login');

    setSignupName('');
    setSignupEmail('');
    setSignupPassword('');
    setSignupConfirmPassword('');

    setFeedback({
      text: `Account created for ${cleanName}. Please enter your password to sign in.`,
      type: 'success',
    });
  };

  return (
    <div className="fixed inset-0 bg-[#FAF8F5] z-50 flex items-center justify-center p-4 overflow-y-auto font-sans select-none text-[#002147]">
      {/* Oxford & Tan Auth Container */}
      <div className="w-full max-w-md bg-white border border-[#D8CCBD] rounded-[12px] p-8 flex flex-col gap-6 my-auto shadow-sm">
        {/* Header */}
        <div className="text-center flex flex-col items-center gap-2">
          <div className="px-4 py-1.5 rounded-[12px] bg-[#002147] text-[#D2B48C] flex items-center justify-center text-xs font-bold shadow-sm uppercase tracking-wider">
            RULER
          </div>
          <h1 className="text-xl font-bold text-[#002147] tracking-tight">Ruler Intelligence</h1>
          <p className="text-xs text-[#8C7A68]">Banking Regulatory AI & Compliance Platform</p>
        </div>

        {/* Tab Switcher - 2 Clean Modes (User Only) */}
        <div className="flex bg-[#F5EFEB] border border-[#D8CCBD] rounded-[12px] p-1 gap-1">
          <button
            type="button"
            onClick={() => {
              setAuthMode('login');
              setFeedback({ text: '', type: '' });
            }}
            className={`flex-1 py-2 rounded-[10px] text-xs font-bold transition ${
              authMode === 'login'
                ? 'bg-[#002147] text-[#D2B48C] shadow-sm'
                : 'text-[#002147] hover:bg-[#E6D9C8]'
            }`}
          >
            User Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setAuthMode('signup');
              setFeedback({ text: '', type: '' });
            }}
            className={`flex-1 py-2 rounded-[10px] text-xs font-bold transition ${
              authMode === 'signup'
                ? 'bg-[#002147] text-[#D2B48C] shadow-sm'
                : 'text-[#002147] hover:bg-[#E6D9C8]'
            }`}
          >
            Register User
          </button>
        </div>

        {/* Mode 1: User Sign In Form */}
        {authMode === 'login' && (
          <form onSubmit={handleLoginSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-[#002147]" htmlFor="loginEmail">
                Bank Corporate Email
              </label>
              <input
                type="email"
                id="loginEmail"
                value={loginEmail}
                onChange={(e) => {
                  setLoginEmail(e.target.value);
                  setFeedback({ text: '', type: '' });
                }}
                className="bg-white border border-[#D8CCBD] rounded-[12px] px-4 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147] transition placeholder-[#B8A898]"
                placeholder="compliance.officer@bank.com"
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-[#002147]" htmlFor="loginPassword">
                Password
              </label>
              <input
                type="password"
                id="loginPassword"
                value={loginPassword}
                onChange={(e) => {
                  setLoginPassword(e.target.value);
                  setFeedback({ text: '', type: '' });
                }}
                className="bg-white border border-[#D8CCBD] rounded-[12px] px-4 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147] transition placeholder-[#B8A898]"
                placeholder="••••••••••••"
                required
              />
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center gap-2 text-[#6A5A4A] cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="accent-[#002147] rounded-[4px]"
                />
                <span>Remember session</span>
              </label>
              <button
                type="button"
                onClick={() => {
                  setAuthMode('signup');
                  setFeedback({ text: '', type: '' });
                }}
                className="text-[#002147] font-semibold hover:underline"
              >
                Create an account
              </button>
            </div>

            <button
              type="submit"
              className="w-full bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold py-3 rounded-[12px] text-xs transition duration-150 shadow-sm mt-1"
            >
              Sign In to User Portal
            </button>
          </form>
        )}

        {/* Mode 2: Register User Form */}
        {authMode === 'signup' && (
          <form onSubmit={handleSignupSubmit} className="flex flex-col gap-3.5">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-bold text-[#002147]" htmlFor="signupName">
                Officer Full Name
              </label>
              <input
                type="text"
                id="signupName"
                value={signupName}
                onChange={(e) => {
                  setSignupName(e.target.value);
                  setFeedback({ text: '', type: '' });
                }}
                className="bg-white border border-[#D8CCBD] rounded-[12px] px-4 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147] transition placeholder-[#B8A898]"
                placeholder="e.g. Eleanor Vance"
                required
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-bold text-[#002147]" htmlFor="signupEmail">
                Official Bank Email
              </label>
              <input
                type="email"
                id="signupEmail"
                value={signupEmail}
                onChange={(e) => {
                  setSignupEmail(e.target.value);
                  setFeedback({ text: '', type: '' });
                }}
                className="bg-white border border-[#D8CCBD] rounded-[12px] px-4 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147] transition placeholder-[#B8A898]"
                placeholder="officer@bank.gov"
                required
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-bold text-[#002147]" htmlFor="signupRole">
                User Operational Role
              </label>
              <select
                id="signupRole"
                value={signupRole}
                onChange={(e) => setSignupRole(e.target.value)}
                className="bg-white border border-[#D8CCBD] rounded-[12px] px-4 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147] transition"
              >
                <option value="Compliance Specialist">Compliance Specialist</option>
                <option value="Regulatory Auditor">Regulatory Auditor</option>
                <option value="Risk & Governance Analyst">Risk & Governance Analyst</option>
                <option value="Banking Legal Counsel">Banking Legal Counsel</option>
                <option value="Credit Risk Officer">Credit Risk Officer</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-bold text-[#002147]" htmlFor="signupPassword">
                  Password
                </label>
                <input
                  type="password"
                  id="signupPassword"
                  value={signupPassword}
                  onChange={(e) => {
                    setSignupPassword(e.target.value);
                    setFeedback({ text: '', type: '' });
                  }}
                  className="bg-white border border-[#D8CCBD] rounded-[12px] px-3.5 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147] transition placeholder-[#B8A898]"
                  placeholder="••••••••"
                  required
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-bold text-[#002147]" htmlFor="signupConfirmPassword">
                  Confirm Password
                </label>
                <input
                  type="password"
                  id="signupConfirmPassword"
                  value={signupConfirmPassword}
                  onChange={(e) => {
                    setSignupConfirmPassword(e.target.value);
                    setFeedback({ text: '', type: '' });
                  }}
                  className="bg-white border border-[#D8CCBD] rounded-[12px] px-3.5 py-2.5 text-xs text-[#002147] focus:outline-none focus:border-[#002147] transition placeholder-[#B8A898]"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-[#002147] hover:bg-[#001630] text-[#D2B48C] font-bold py-3 rounded-[12px] text-xs transition duration-150 shadow-sm mt-1"
            >
              Register & Continue
            </button>
          </form>
        )}

        {/* Feedback Alert */}
        {feedback.text && (
          <div
            className={`p-3 rounded-[12px] text-xs font-semibold text-center ${
              feedback.type === 'success'
                ? 'bg-[#F5EFEB] border border-[#D2B48C] text-[#002147]'
                : 'bg-red-50 border border-red-200 text-red-800'
            }`}
          >
            {feedback.text}
          </div>
        )}

        {/* Footer Security Notice */}
        <div className="text-center pt-2 border-t border-[#F5EFEB] text-[11px] text-[#8C7A68]">
          <span>Protected by Institutional Regulatory AI & Role-Based Access Control</span>
        </div>
      </div>
    </div>
  );
}
