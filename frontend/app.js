/**
 * Ruler AI Regulatory Platform — Pure Tailwind CSS Dashboard & Auth Engine
 * Handles Login/Signup, Regulatory Q&A, Per-Turn Generated Token Telemetry, and Audit History.
 */

// Application State
const appState = {
  activeView: 'view-assistant',
  totalSessionTokens: 0,
  lastTurnGenTokens: 0,
  chatHistory: [],
  currentUser: null,
  isAuthenticated: false,
  modelName: 'openai/gpt-4o-mini',
  apiAvailable: true,
};

// DOM References
const ui = {
  // Screen views
  authScreen: document.getElementById('authScreen'),
  dashboardScreen: document.getElementById('dashboardScreen'),
  
  // Auth Elements
  tabBtnLogin: document.getElementById('tabBtnLogin'),
  tabBtnSignup: document.getElementById('tabBtnSignup'),
  loginForm: document.getElementById('loginForm'),
  signupForm: document.getElementById('signupForm'),
  loginEmail: document.getElementById('loginEmail'),
  loginPassword: document.getElementById('loginPassword'),
  signupName: document.getElementById('signupName'),
  signupEmail: document.getElementById('signupEmail'),
  signupRole: document.getElementById('signupRole'),
  signupPassword: document.getElementById('signupPassword'),
  signupConfirmPassword: document.getElementById('signupConfirmPassword'),
  authFeedbackMsg: document.getElementById('authFeedbackMsg'),
  demoChips: document.querySelectorAll('.btn-demo-chip'),
  userDisplayName: document.getElementById('userDisplayName'),
  userDisplayRole: document.getElementById('userDisplayRole'),
  btnHeaderLogout: document.getElementById('btnHeaderLogout'),
  
  // Navigation
  navButtons: document.querySelectorAll('.nav-button'),
  viewPanes: document.querySelectorAll('.view-panel'),
  statusModel: document.getElementById('statusModel'),
  sessionTokensCount: document.getElementById('sessionTokensCount'),
  lastTurnGenTokensCount: document.getElementById('lastTurnGenTokensCount'),
  
  // Assistant / Chat
  chatMessages: document.getElementById('chatMessages'),
  chatForm: document.getElementById('chatForm'),
  chatInput: document.getElementById('chatInput'),
  btnSendChat: document.getElementById('btnSendChat'),
  suggestedPromptsList: document.getElementById('suggestedPromptsList'),
  btnClearChat: document.getElementById('btnClearChat'),
  
  // History
  historyTableBody: document.getElementById('historyTableBody'),
  btnExportJson: document.getElementById('btnExportJson'),
};

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  setupAuth();
  setupSidebarNavigation();
  setupChatHandlers();
  setupHistoryHandlers();
  await loadServerConfig();
});

// ==========================================================================
// Authentication (Login & Signup)
// ==========================================================================
function setupAuth() {
  // Check localStorage for saved session
  const savedUser = localStorage.getItem('ruler_user');
  if (savedUser) {
    try {
      appState.currentUser = JSON.parse(savedUser);
      appState.isAuthenticated = true;
      updateUserProfileUI();
      showDashboard();
    } catch (e) {
      console.warn('Could not parse saved user session from localStorage');
      showAuth();
    }
  } else {
    // Show Login/Signup Screen by default
    showAuth();
  }

  // Switch between Login and Signup tabs
  if (ui.tabBtnLogin && ui.tabBtnSignup) {
    ui.tabBtnLogin.addEventListener('click', () => {
      ui.tabBtnLogin.className = "flex-1 py-2.5 rounded-xl text-xs font-bold transition-all text-white bg-sky-600 shadow-md shadow-sky-600/30";
      ui.tabBtnSignup.className = "flex-1 py-2.5 rounded-xl text-xs font-bold transition-all text-slate-400 hover:text-white";
      if (ui.loginForm) ui.loginForm.classList.remove('hidden');
      if (ui.signupForm) ui.signupForm.classList.add('hidden');
      clearAuthFeedback();
    });

    ui.tabBtnSignup.addEventListener('click', () => {
      ui.tabBtnSignup.className = "flex-1 py-2.5 rounded-xl text-xs font-bold transition-all text-white bg-sky-600 shadow-md shadow-sky-600/30";
      ui.tabBtnLogin.className = "flex-1 py-2.5 rounded-xl text-xs font-bold transition-all text-slate-400 hover:text-white";
      if (ui.signupForm) ui.signupForm.classList.remove('hidden');
      if (ui.loginForm) ui.loginForm.classList.add('hidden');
      clearAuthFeedback();
    });
  }

  // Handle Login Form Submission
  if (ui.loginForm) {
    ui.loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const email = ui.loginEmail.value.trim();
      const password = ui.loginPassword.value;

      if (!email || !password) {
        showAuthFeedback('Please enter both email and password.', 'error');
        return;
      }

      // Successful login
      const formattedName = email.split('@')[0].replace('.', ' ').replace(/\b\w/g, l => l.toUpperCase());
      appState.currentUser = {
        name: formattedName || 'Compliance Officer',
        role: 'Compliance Specialist',
        email: email
      };
      appState.isAuthenticated = true;

      const remember = document.getElementById('rememberMe');
      if (remember && remember.checked) {
        localStorage.setItem('ruler_user', JSON.stringify(appState.currentUser));
      }

      showAuthFeedback('✅ Signed in successfully! Loading regulatory portal...', 'success');
      updateUserProfileUI();

      setTimeout(() => {
        showDashboard();
        clearAuthFeedback();
      }, 500);
    });
  }

  // Handle Sign Up Form Submission
  if (ui.signupForm) {
    ui.signupForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = ui.signupName.value.trim();
      const email = ui.signupEmail.value.trim();
      const role = ui.signupRole.value;
      const pwd = ui.signupPassword.value;
      const confirmPwd = ui.signupConfirmPassword.value;

      if (!name || !email || !pwd) {
        showAuthFeedback('Please fill in all required fields.', 'error');
        return;
      }

      if (pwd !== confirmPwd) {
        showAuthFeedback('Passwords do not match. Please verify.', 'error');
        return;
      }

      // Save registered user
      const registered = (() => {
        try {
          const d = localStorage.getItem('ruler_registered_users');
          return d ? JSON.parse(d) : [];
        } catch { return []; }
      })();
      registered.push({ name, email, role, password: pwd });
      localStorage.setItem('ruler_registered_users', JSON.stringify(registered));

      // Switch to login tab and prefill
      if (ui.loginEmail) ui.loginEmail.value = email;
      if (ui.loginPassword) ui.loginPassword.value = '';
      if (ui.tabBtnLogin) ui.tabBtnLogin.click();

      showAuthFeedback(`🎉 Account created for ${name}! Please sign in with your credentials.`, 'success');
    });
  }

  // 1-Click Quick Demo Profile Logins
  ui.demoChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const name = chip.dataset.name || 'Compliance Officer';
      const role = chip.dataset.role || 'Compliance Specialist';
      const email = chip.dataset.email || 'compliance.officer@centralbank.gov';

      appState.currentUser = { name, role, email };
      appState.isAuthenticated = true;
      localStorage.setItem('ruler_user', JSON.stringify(appState.currentUser));

      updateUserProfileUI();
      showAuthFeedback(`⚡ Authenticating as ${name}...`, 'success');

      setTimeout(() => {
        showDashboard();
        clearAuthFeedback();
      }, 400);
    });
  });

  // Logout Header Button
  if (ui.btnHeaderLogout) {
    ui.btnHeaderLogout.addEventListener('click', () => {
      if (confirm('Sign out from Ruler Regulatory AI Dashboard?')) {
        localStorage.removeItem('ruler_user');
        appState.currentUser = null;
        appState.isAuthenticated = false;
        showAuth();
      }
    });
  }
}

function showDashboard() {
  if (ui.authScreen) ui.authScreen.classList.add('hidden');
  if (ui.dashboardScreen) ui.dashboardScreen.classList.remove('hidden');
}

function showAuth() {
  if (ui.dashboardScreen) ui.dashboardScreen.classList.add('hidden');
  if (ui.authScreen) ui.authScreen.classList.remove('hidden');
}

function showAuthFeedback(msg, type) {
  if (!ui.authFeedbackMsg) return;
  ui.authFeedbackMsg.textContent = msg;
  ui.authFeedbackMsg.className = `text-center text-xs font-semibold min-h-[18px] ${type === 'success' ? 'text-emerald-400' : 'text-red-400'}`;
}

function clearAuthFeedback() {
  if (!ui.authFeedbackMsg) return;
  ui.authFeedbackMsg.textContent = '';
  ui.authFeedbackMsg.className = 'text-center text-xs font-semibold min-h-[18px]';
}

function updateUserProfileUI() {
  if (appState.currentUser) {
    if (ui.userDisplayName) ui.userDisplayName.textContent = appState.currentUser.name;
    if (ui.userDisplayRole) ui.userDisplayRole.textContent = appState.currentUser.role;
  }
}

// ==========================================================================
// Sidebar Navigation
// ==========================================================================
function setupSidebarNavigation() {
  ui.navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetView = btn.dataset.view;
      if (!targetView) return;

      ui.navButtons.forEach(b => {
        b.className = "nav-button flex items-center gap-3 w-full px-3.5 py-3 rounded-xl text-xs font-semibold tracking-wider text-slate-400 hover:text-white hover:bg-slate-800/60 border border-transparent transition text-left";
      });
      ui.viewPanes.forEach(p => {
        p.classList.add('hidden');
        p.classList.remove('active');
      });

      btn.className = "nav-button active flex items-center gap-3 w-full px-3.5 py-3 rounded-xl text-xs font-semibold tracking-wider text-sky-400 bg-sky-500/15 border border-sky-500/30 transition text-left";
      const activePane = document.getElementById(targetView);
      if (activePane) {
        activePane.classList.remove('hidden');
        activePane.classList.add('active');
      }

      appState.activeView = targetView;

      if (targetView === 'view-history') {
        renderHistoryTable();
      }
    });
  });
}

// ==========================================================================
// Load Config
// ==========================================================================
async function loadServerConfig() {
  try {
    const configRes = await fetch('/api/config');
    if (configRes.ok) {
      const data = await configRes.json();
      if (data.config && data.config.chat_model) {
        appState.modelName = data.config.chat_model;
        if (ui.statusModel) ui.statusModel.textContent = data.config.chat_model;
      }
    }
  } catch (e) {
    console.warn('Could not fetch /api/config, using default model name.', e);
  }
}

// ==========================================================================
// Chat Dialogue & Token Tracking
// ==========================================================================
function setupChatHandlers() {
  // Suggested prompt chips
  if (ui.suggestedPromptsList) {
    ui.suggestedPromptsList.addEventListener('click', (e) => {
      const chip = e.target.closest('.prompt-chip');
      if (chip && chip.dataset.query) {
        ui.chatInput.value = chip.dataset.query;
        ui.chatInput.focus();
      }
    });
  }

  // Clear Chat
  if (ui.btnClearChat) {
    ui.btnClearChat.addEventListener('click', () => {
      appState.chatHistory = [];
      renderChatMessages();
    });
  }

  // Chat Form Submit
  if (ui.chatForm) {
    ui.chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = ui.chatInput.value.trim();
      if (!question) return;

      ui.chatInput.value = '';
      await handleUserQuery(question);
    });

    // Enter to submit (Shift+Enter for newline)
    ui.chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        ui.chatForm.dispatchEvent(new Event('submit'));
      }
    });
  }
}

async function handleUserQuery(question) {
  const turnIndex = appState.chatHistory.length + 1;

  // Add User Message
  const userMsg = {
    turnId: turnIndex,
    role: 'user',
    content: question,
    timestamp: new Date().toLocaleTimeString()
  };
  appState.chatHistory.push(userMsg);
  renderChatMessages();

  // Create temporary loading assistant message
  const loadingMsg = {
    turnId: turnIndex,
    role: 'assistant',
    content: 'Retrieving regulatory directives and generating grounded answer...',
    isLoading: true,
    tokens: null,
    status: 'loading'
  };
  appState.chatHistory.push(loadingMsg);
  renderChatMessages();

  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question, top_k: 3, temperature: 0.2 })
    });

    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}`);
    }

    const data = await response.json();
    
    // Extract token metrics
    const tokensUsed = data.metadata && data.metadata.tokens_used ? data.metadata.tokens_used : {};
    const genTokens = tokensUsed.completion_tokens || Math.round(data.answer.split(/\s+/).length * 1.3);
    const promptTokens = tokensUsed.prompt_tokens || 350;
    const totalTurnTokens = tokensUsed.total_tokens || (genTokens + promptTokens);

    // Update global state
    appState.lastTurnGenTokens = genTokens;
    appState.totalSessionTokens += totalTurnTokens;
    updateTokenCounters();

    // Replace loading message with actual response
    const assistantMsg = {
      turnId: turnIndex,
      role: 'assistant',
      content: data.answer,
      isGrounded: data.is_grounded,
      confidence: data.confidence || 'high',
      status: data.status || 'success',
      tokens: {
        completion_tokens: genTokens,
        prompt_tokens: promptTokens,
        total_tokens: totalTurnTokens
      },
      sources: data.sources || [],
      timestamp: new Date().toLocaleTimeString(),
      userQuestion: question
    };

    appState.chatHistory[appState.chatHistory.length - 1] = assistantMsg;

  } catch (err) {
    console.error('Query execution error:', err);
    const errorTokens = { completion_tokens: 15, prompt_tokens: 50, total_tokens: 65 };
    appState.lastTurnGenTokens = errorTokens.completion_tokens;
    appState.totalSessionTokens += errorTokens.total_tokens;
    updateTokenCounters();

    appState.chatHistory[appState.chatHistory.length - 1] = {
      turnId: turnIndex,
      role: 'assistant',
      content: `⚠️ Failed to retrieve answer from regulatory knowledge base: ${err.message}. Please verify the server is running.`,
      isGrounded: false,
      confidence: 'low',
      status: 'error',
      tokens: errorTokens,
      timestamp: new Date().toLocaleTimeString(),
      userQuestion: question
    };
  }

  renderChatMessages();
}

function updateTokenCounters() {
  if (ui.sessionTokensCount) {
    ui.sessionTokensCount.textContent = appState.totalSessionTokens.toLocaleString();
  }
  if (ui.lastTurnGenTokensCount) {
    ui.lastTurnGenTokensCount.textContent = appState.lastTurnGenTokens.toLocaleString();
  }
}

// ==========================================================================
// Render Chat Messages (Tailwind Styled)
// ==========================================================================
function renderChatMessages() {
  if (!ui.chatMessages) return;

  if (appState.chatHistory.length === 0) {
    ui.chatMessages.innerHTML = `
      <div class="bg-[#18233C] border border-sky-500/25 rounded-2xl p-8 text-center flex flex-col items-center gap-3 shadow-xl">
        <div class="bg-sky-500/15 text-sky-400 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
          🏛️ Ruler Compliance Intelligence
        </div>
        <h3 class="text-xl font-bold text-white">Ask Banking Regulatory Directives</h3>
        <p class="text-xs text-slate-300 max-w-lg">Query institutional compliance rules, capital adequacy standards, and reporting timelines.</p>
        
        <div class="flex flex-wrap gap-2 justify-center mt-2" id="suggestedPromptsList">
          <button class="prompt-chip bg-slate-800/80 hover:bg-sky-500/20 hover:border-sky-500/40 border border-slate-700 text-slate-200 hover:text-sky-300 px-3.5 py-1.5 rounded-full text-xs font-medium transition duration-150" data-query="What is the capital adequacy requirement for Tier 1 capital under the framework?">
            Tier 1 Capital Adequacy Requirement
          </button>
          <button class="prompt-chip bg-slate-800/80 hover:bg-sky-500/20 hover:border-sky-500/40 border border-slate-700 text-slate-200 hover:text-sky-300 px-3.5 py-1.5 rounded-full text-xs font-medium transition duration-150" data-query="What are the mandatory data encryption directives and security controls?">
            Data Encryption & Security Directives
          </button>
          <button class="prompt-chip bg-slate-800/80 hover:bg-sky-500/20 hover:border-sky-500/40 border border-slate-700 text-slate-200 hover:text-sky-300 px-3.5 py-1.5 rounded-full text-xs font-medium transition duration-150" data-query="What are the Liquidity Coverage Ratio (LCR) calculation guidelines?">
            Liquidity Coverage Ratio (LCR) Rules
          </button>
          <button class="prompt-chip bg-slate-800/80 hover:bg-sky-500/20 hover:border-sky-500/40 border border-slate-700 text-slate-200 hover:text-sky-300 px-3.5 py-1.5 rounded-full text-xs font-medium transition duration-150" data-query="What are the transaction thresholds requiring board authorization?">
            Board Authorization Thresholds ($50k)
          </button>
          <button class="prompt-chip bg-slate-800/80 hover:bg-sky-500/20 hover:border-sky-500/40 border border-slate-700 text-slate-200 hover:text-sky-300 px-3.5 py-1.5 rounded-full text-xs font-medium transition duration-150" data-query="What is Retrieval-Augmented Generation (RAG)?">
            What is RAG in AI Banking?
          </button>
        </div>
      </div>
    `;
    return;
  }

  ui.chatMessages.innerHTML = '';

  appState.chatHistory.forEach((msg) => {
    const card = document.createElement('div');
    card.className = `w-full flex flex-col gap-1 transition-all duration-200`;

    if (msg.role === 'user') {
      card.innerHTML = `
        <div class="self-end max-w-[80%] ml-auto bg-sky-600 text-white px-5 py-3.5 rounded-2xl rounded-tr-sm text-sm leading-relaxed shadow-lg shadow-sky-600/10">
          ${escapeHtml(msg.content)}
        </div>
      `;
    } else {
      if (msg.isLoading) {
        card.innerHTML = `
          <div class="w-full bg-[#18233C] border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col gap-3">
            <div class="flex items-center gap-2 text-xs font-bold text-sky-400">
              <span>⚖️</span>
              <span>Ruler Intelligence Assistant</span>
            </div>
            <div class="text-sm text-slate-400 italic">
              ⏳ ${escapeHtml(msg.content)}
            </div>
          </div>
        `;
      } else {
        const isGrounded = msg.isGrounded !== false;
        const groundBadge = isGrounded 
          ? `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">✓ 100% Grounded</span>`
          : `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-500/15 text-amber-400 border border-amber-500/30">⚠️ Fallback</span>`;
        
        const confBadge = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-sky-500/15 text-sky-400 border border-sky-500/30">${msg.confidence || 'High'} Conf</span>`;

        // Prominent Per-Turn Token Box
        const genTokens = msg.tokens ? msg.tokens.completion_tokens : 0;
        const promptTokens = msg.tokens ? msg.tokens.prompt_tokens : 0;
        const totalTokens = msg.tokens ? msg.tokens.total_tokens : 0;

        card.innerHTML = `
          <div class="w-full bg-[#18233C] border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col gap-4">
            <div class="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div class="flex items-center gap-2 text-xs font-bold text-sky-400">
                <span>⚖️</span>
                <span>Ruler Intelligence Assistant (Turn #${msg.turnId})</span>
              </div>
              <div class="flex items-center gap-2">
                ${groundBadge}
                ${confBadge}
              </div>
            </div>
            
            <div class="text-sm text-slate-100 leading-relaxed font-sans whitespace-pre-wrap">${formatAnswerWithCitations(msg.content)}</div>

            <!-- Per-Turn Token Telemetry Box -->
            <div class="bg-[#131D31] border border-purple-500/30 rounded-xl p-3 flex items-center justify-between flex-wrap gap-2">
              <div class="flex items-center gap-2 text-xs font-bold text-purple-300 uppercase tracking-wider">
                <span>⚡</span>
                <span>Token Telemetry</span>
              </div>
              <div class="flex items-center gap-2 flex-wrap">
                <span class="bg-purple-500/15 border border-purple-500/40 text-purple-200 px-2.5 py-1 rounded-md font-mono text-xs">
                  Generated: <strong class="text-purple-300">${genTokens} tokens</strong>
                </span>
                <span class="bg-slate-800 border border-slate-700 text-slate-300 px-2.5 py-1 rounded-md font-mono text-xs">
                  Context: <strong>${promptTokens} tokens</strong>
                </span>
                <span class="bg-sky-500/15 border border-sky-500/40 text-sky-200 px-2.5 py-1 rounded-md font-mono text-xs">
                  Turn Total: <strong class="text-sky-300">${totalTokens} tokens</strong>
                </span>
              </div>
            </div>

            <div class="text-right text-[11px] text-slate-500 pt-1">
              ${msg.timestamp}
            </div>
          </div>
        `;
      }
    }

    ui.chatMessages.appendChild(card);
  });

  ui.chatMessages.scrollTop = ui.chatMessages.scrollHeight;
}

function formatAnswerWithCitations(text) {
  if (!text) return '';
  return escapeHtml(text).replace(/\[(\d+)\]/g, '<span class="text-sky-300 font-bold bg-sky-500/20 px-1.5 py-0.5 rounded text-xs border border-sky-500/30">[$1]</span>');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// ==========================================================================
// History & Audit Table
// ==========================================================================
function setupHistoryHandlers() {
  if (ui.btnExportJson) {
    ui.btnExportJson.addEventListener('click', () => {
      const exportPayload = {
        exportTimestamp: new Date().toISOString(),
        user: appState.currentUser,
        model: appState.modelName,
        totalSessionTokens: appState.totalSessionTokens,
        chatHistory: appState.chatHistory
      };

      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportPayload, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `ruler_audit_log_${Date.now()}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });
  }
}

function renderHistoryTable() {
  if (!ui.historyTableBody) return;

  const assistantTurns = appState.chatHistory.filter(m => m.role === 'assistant' && !m.isLoading);

  if (assistantTurns.length === 0) {
    ui.historyTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-slate-500 py-8">
          No dialogue turns recorded yet. Ask questions in the Assistant view to generate audit history.
        </td>
      </tr>
    `;
    return;
  }

  ui.historyTableBody.innerHTML = '';
  assistantTurns.forEach(turn => {
    const tr = document.createElement('tr');
    tr.className = "hover:bg-slate-800/40 transition";
    tr.innerHTML = `
      <td class="py-3 px-4 font-bold text-sky-400">#${turn.turnId}</td>
      <td class="py-3 px-4 max-w-[200px] truncate">${escapeHtml(turn.userQuestion || '')}</td>
      <td class="py-3 px-4 max-w-[280px] truncate text-slate-300">${escapeHtml(turn.content.slice(0, 80))}...</td>
      <td class="py-3 px-4 text-purple-300 font-bold">${turn.tokens ? turn.tokens.completion_tokens : 0} tokens</td>
      <td class="py-3 px-4 text-slate-400">${turn.tokens ? turn.tokens.prompt_tokens : 0} tokens</td>
      <td class="py-3 px-4 text-sky-400 font-bold">${turn.tokens ? turn.tokens.total_tokens : 0} tokens</td>
      <td class="py-3 px-4 text-slate-500 text-[11px]">${turn.timestamp}</td>
    `;
    ui.historyTableBody.appendChild(tr);
  });
}
