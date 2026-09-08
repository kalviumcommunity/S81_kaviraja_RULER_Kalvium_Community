/**
 * Ruler AI Regulatory Platform — Dashboard Engine
 * Implements Sidebar Navigation, RAG Dialogue with 'View Source', 'Helpful', 'Not Helpful' buttons,
 * Interactive Source Grounding Inspector Drawer, Token Chunker, Audit History, and Settings.
 */

// Application State
const appState = {
  activeView: 'view-home',
  documentContent: '',
  documentFilename: 'sample_banking_regulation.txt',
  documentId: 'DOC_BRCF_2026_001',
  chunks: [],
  selectedChunk: null,
  activeMessageSource: null,
  totalSessionTokens: 0,
  chatHistory: [],
  modelName: 'openai/gpt-4o-mini',
  apiAvailable: true,
};

// Preset Scenarios for JSON Fault Recovery
const JSON_PRESETS = {
  markdown_trailing_comma: `\`\`\`json
{
  "answer": "Retrieval-Augmented Generation (RAG) retrieves relevant document snippets.",
  "source": "RAG_Architecture_Doc.pdf",
}
\`\`\``,
  missing_field: `{\n  "answer": "RAG grounds model completions in custom knowledge bases to prevent hallucinations."\n}`,
  embedded_noise: `NOTE: Here is the generated response:\n\n{\n  "answer": "ChromaDB stores high-dimensional vector embeddings and executes fast semantic similarity searches.",\n  "source": "ChromaDB_Integration_Guide.pdf",\n  "confidence": "high"\n}\n\nHope this helps!`,
  unrecoverable_crash: `INTERNAL_SERVER_ERROR: Fatal crash occurred while generating JSON response {{{...`
};

// DOM References
const ui = {
  navButtons: document.querySelectorAll('.nav-button'),
  viewPanes: document.querySelectorAll('.view-panel'),
  statusModel: document.getElementById('statusModel'),
  sessionTokensCount: document.getElementById('sessionTokensCount'),
  
  // Home / Chat
  chatMessages: document.getElementById('chatMessages'),
  chatForm: document.getElementById('chatForm'),
  chatInput: document.getElementById('chatInput'),
  suggestedPromptsList: document.getElementById('suggestedPromptsList'),
  btnClearChat: document.getElementById('btnClearChat'),
  btnToggleSideSource: document.getElementById('btnToggleSideSource'),
  
  // Source Drawer
  sourceDrawer: document.getElementById('sourceDrawer'),
  drawerBreadcrumbs: document.getElementById('drawerBreadcrumbs'),
  drawerMatchBadge: document.getElementById('drawerMatchBadge'),
  drawerSourceHighlightedText: document.getElementById('drawerSourceHighlightedText'),
  drawerDocId: document.getElementById('drawerDocId'),
  drawerSection: document.getElementById('drawerSection'),
  drawerPage: document.getElementById('drawerPage'),
  drawerSpan: document.getElementById('drawerSpan'),
  drawerJsonViewer: document.getElementById('drawerJsonViewer'),
  
  // Chunker
  chunkModeSelect: document.getElementById('chunkModeSelect'),
  chunkSizeInput: document.getElementById('chunkSizeInput'),
  chunkSizeDisplay: document.getElementById('chunkSizeDisplay'),
  chunkOverlapInput: document.getElementById('chunkOverlapInput'),
  chunkOverlapDisplay: document.getElementById('chunkOverlapDisplay'),
  btnExecuteChunk: document.getElementById('btnExecuteChunk'),
  totalChunksCount: document.getElementById('totalChunksCount'),
  chunksGallery: document.getElementById('chunksGallery'),
  consistencyLabel: document.getElementById('consistencyLabel'),
  
  // History
  historyTableBody: document.getElementById('historyTableBody'),
  btnExportJson: document.getElementById('btnExportJson'),
  
  // Settings
  settingsSystemRole: document.getElementById('settingsSystemRole'),
  systemPromptTemplateCode: document.getElementById('systemPromptTemplateCode'),
  settingsTempSlider: document.getElementById('settingsTempSlider'),
  settingsTempValue: document.getElementById('settingsTempValue'),
  settingsModelVal: document.getElementById('settingsModelVal'),
  
  // JSON Lab
  rawJsonInput: document.getElementById('rawJsonInput'),
  btnRunJsonRecovery: document.getElementById('btnRunJsonRecovery'),
  btnPresets: document.querySelectorAll('.btn-preset'),
  statusClean: document.getElementById('statusClean'),
  statusParse: document.getElementById('statusParse'),
  statusValidate: document.getElementById('statusValidate'),
  jsonResultBadge: document.getElementById('jsonResultBadge'),
  jsonResultViewer: document.getElementById('jsonResultViewer'),
  
  btnLogout: document.getElementById('btnLogout'),
};

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  setupSidebarNavigation();
  setupChatWorkspace();
  setupChunkerStudio();
  setupSettingsHandlers();
  setupJsonLabHandlers();
  
  await fetchSystemStatus();
  await loadSampleDocument();
  await executeChunking();
});

// ==========================================================================
// Sidebar Navigation (HOME, CHUNKER, HISTORY, SETTINGS, JSON LAB)
// ==========================================================================
function setupSidebarNavigation() {
  ui.navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetView = btn.dataset.view;
      appState.activeView = targetView;
      
      ui.navButtons.forEach(b => b.classList.toggle('active', b === btn));
      ui.viewPanes.forEach(pane => pane.classList.toggle('active', pane.id === targetView));

      if (targetView === 'view-history') {
        renderHistoryTable();
      }
    });
  });

  ui.btnToggleSideSource.addEventListener('click', () => {
    const isVisible = ui.sourceDrawer.style.display !== 'none';
    ui.sourceDrawer.style.display = isVisible ? 'none' : 'flex';
  });

  ui.btnLogout.addEventListener('click', () => {
    if (confirm('Reset current dialogue session and token telemetry?')) {
      appState.chatHistory = [];
      appState.totalSessionTokens = 0;
      ui.sessionTokensCount.textContent = '0';
      ui.btnClearChat.click();
      renderHistoryTable();
    }
  });
}

// ==========================================================================
// System Status & Sample Regulatory Document
// ==========================================================================
async function fetchSystemStatus() {
  try {
    const res = await fetch('/api/status');
    if (res.ok) {
      const data = await res.json();
      appState.modelName = data.model_name || 'openai/gpt-4o-mini';
      ui.statusModel.textContent = appState.modelName;
      if (ui.settingsModelVal) ui.settingsModelVal.textContent = appState.modelName;
      appState.apiAvailable = true;
    }
  } catch (err) {
    appState.apiAvailable = false;
    ui.statusModel.textContent = 'Local Engine (Offline)';
  }
}

async function loadSampleDocument() {
  try {
    const res = await fetch('/api/sample-data');
    if (res.ok) {
      const data = await res.json();
      appState.documentContent = data.content;
      appState.documentFilename = data.filename;
      appState.documentId = data.doc_id;
      
      // Initial render in source drawer
      renderSourceDrawerText(appState.documentContent, 69, 414, 'DOC_BRCF_2026_001', 'Section 1: Executive Overview and Scope', 1);
    }
  } catch (err) {
    appState.documentContent = `--- Page 1 ---
# Banking Regulatory Compliance Framework (BRCF-2026)
## Section 1: Executive Overview and Scope
This document specifies mandatory compliance directives for financial institutions operating within digital banking infrastructure. 
All licensed entities must implement strict risk controls, maintain detailed audit logs, and adhere to capital adequacy thresholds established by regulatory authorities.
Failure to maintain compliance may result in administrative penalties, operational suspension, or revocation of banking licenses.

--- Page 2 ---
## Section 2: Capital Adequacy and Liquidity Reserve Ratios
Financial institutions are required to maintain a Tier 1 Common Equity Ratio of not less than 10.5% of total risk-weighted assets at all times.
In addition, a Liquidity Coverage Ratio (LCR) of at least 115% must be sustained under simulated 30-day market stress scenarios.
Capital adequacy reports must be submitted electronically to the central supervisory portal on a bi-weekly schedule.

--- Page 3 ---
## Section 3: Data Security and Encryption Directives
All customer records, transaction histories, and identification documents stored at rest must be encrypted using AES-256 or post-quantum cryptographic standards.
Transmission of inter-bank financial messages across public telecommunication networks must utilize TLS version 1.3 or higher with mutual certificate authentication.`;

    renderSourceDrawerText(appState.documentContent, 69, 414, 'DOC_BRCF_2026_001', 'Section 1: Executive Overview and Scope', 1);
  }
}

// ==========================================================================
// RAG Chat Workspace & Message Actions (View Source, Helpful, Not Helpful)
// ==========================================================================
function setupChatWorkspace() {
  // Suggested Prompts
  ui.suggestedPromptsList.addEventListener('click', (e) => {
    const chip = e.target.closest('.prompt-chip');
    if (chip && chip.dataset.query) {
      ui.chatInput.value = chip.dataset.query;
      ui.chatForm.dispatchEvent(new Event('submit'));
    }
  });

  // Clear Chat
  ui.btnClearChat.addEventListener('click', () => {
    appState.chatHistory = [];
    ui.chatMessages.innerHTML = `
      <div class="chat-welcome-banner">
        <div class="welcome-badge">🏛️ Ruler Compliance Core</div>
        <h3>Chat History Cleared</h3>
        <p>Type a question or select a compliance prompt to begin.</p>
      </div>`;
    ui.drawerJsonViewer.textContent = '{}';
  });

  // Chat Form Submission
  ui.chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = ui.chatInput.value.trim();
    if (!query) return;

    ui.chatInput.value = '';
    appendUserBubble(query);

    const loadingId = appendLoadingBubble();

    try {
      let result;
      if (appState.apiAvailable) {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_message: query,
            system_role: ui.settingsSystemRole ? ui.settingsSystemRole.value : 'RAG',
            temperature: parseFloat(ui.settingsTempSlider ? ui.settingsTempSlider.value : 0.2)
          })
        });
        result = await res.json();
      } else {
        await new Promise(r => setTimeout(r, 500));
        result = {
          success: true,
          parsed_object: {
            answer: `Ruler compliance verification: '${query}'. Directives retrieved from Banking Regulatory Compliance Framework (BRCF-2026).`,
            source: 'sample_banking_regulation.txt (Section 1)',
            confidence: 'high'
          },
          token_usage: { prompt_tokens: 42, completion_tokens: 38, total_tokens: 80 }
        };
      }

      removeLoadingBubble(loadingId);

      if (result.success && result.parsed_object) {
        const parsed = result.parsed_object;
        const tokens = result.token_usage || { prompt_tokens: 40, completion_tokens: 40, total_tokens: 80 };

        appendAssistantBubble(parsed, tokens, query);
        
        // Record in state
        appState.chatHistory.push({
          user_question: query,
          assistant_answer: parsed.answer,
          source: parsed.source,
          confidence: parsed.confidence,
          tokens: tokens.total_tokens
        });

        // Update session tokens
        appState.totalSessionTokens += (tokens.total_tokens || 0);
        ui.sessionTokensCount.textContent = appState.totalSessionTokens.toLocaleString();

        // Update Drawer
        ui.drawerJsonViewer.textContent = JSON.stringify(parsed, null, 2);
        highlightSourceFromChatAnswer(parsed);
      }
    } catch (err) {
      removeLoadingBubble(loadingId);
      appendAssistantBubble({
        answer: `Error completing request: ${err.message}. System applied fallback protection.`,
        source: 'System_Fallback_Handler',
        confidence: 'low'
      }, { total_tokens: 0 }, query);
    }
  });

  ui.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      ui.chatForm.dispatchEvent(new Event('submit'));
    }
  });
}

function appendUserBubble(text) {
  const row = document.createElement('div');
  row.className = 'chat-row user';
  row.innerHTML = `
    <div class="row-avatar user">👤</div>
    <div class="row-bubble">${escapeHtml(text)}</div>
  `;
  ui.chatMessages.appendChild(row);
  ui.chatMessages.scrollTop = ui.chatMessages.scrollHeight;
}

function appendAssistantBubble(parsedObj, tokens, originalQuery) {
  const row = document.createElement('div');
  row.className = 'chat-row assistant';

  const answer = parsedObj.answer || 'No answer field';
  const source = parsedObj.source || 'sample_banking_regulation.txt';
  const confidence = parsedObj.confidence || 'high';
  const tokenCount = tokens ? tokens.total_tokens || 0 : 0;

  row.innerHTML = `
    <div class="row-avatar assistant">⚖️</div>
    <div class="row-bubble">
      <div>${escapeHtml(answer)}</div>
      
      <!-- Action Bar with View Source, Helpful, Not Helpful -->
      <div class="bubble-action-bar">
        <button class="btn-action btn-view-source" title="Inspect ground-truth regulatory source">
          <span>🔍</span> View Source
        </button>
        <button class="btn-action btn-helpful" title="Mark response as helpful">
          <span>👍</span> Helpful
        </button>
        <button class="btn-action btn-not-helpful" title="Mark response as not helpful">
          <span>👎</span> Not Helpful
        </button>
        <span class="action-meta-tag">⚡ ${tokenCount} tokens · Conf: ${escapeHtml(String(confidence))}</span>
      </div>
    </div>
  `;

  // Attach button interactions
  const btnViewSource = row.querySelector('.btn-view-source');
  const btnHelpful = row.querySelector('.btn-helpful');
  const btnNotHelpful = row.querySelector('.btn-not-helpful');

  btnViewSource.addEventListener('click', () => {
    highlightSourceFromChatAnswer(parsedObj);
    // Ensure drawer is visible
    ui.sourceDrawer.style.display = 'flex';
  });

  btnHelpful.addEventListener('click', () => {
    btnHelpful.classList.toggle('active');
    btnNotHelpful.classList.remove('active');
  });

  btnNotHelpful.addEventListener('click', () => {
    btnNotHelpful.classList.toggle('active');
    btnHelpful.classList.remove('active');
  });

  ui.chatMessages.appendChild(row);
  ui.chatMessages.scrollTop = ui.chatMessages.scrollHeight;
}

function appendLoadingBubble() {
  const id = `loading_${Date.now()}`;
  const row = document.createElement('div');
  row.id = id;
  row.className = 'chat-row assistant';
  row.innerHTML = `
    <div class="row-avatar assistant">⚖️</div>
    <div class="row-bubble" style="color: var(--text-muted);">
      <em>Querying regulatory knowledge base & generating structured response...</em>
    </div>
  `;
  ui.chatMessages.appendChild(row);
  ui.chatMessages.scrollTop = ui.chatMessages.scrollHeight;
  return id;
}

function removeLoadingBubble(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function highlightSourceFromChatAnswer(parsedObj) {
  const fullText = appState.documentContent;
  let start = 69;
  let end = 414;
  let section = 'Section 1: Executive Overview and Scope';
  let page = 1;

  // Smart section determination based on source or content
  const src = (parsedObj.source || '').toLowerCase();
  const ans = (parsedObj.answer || '').toLowerCase();

  if (src.includes('section 2') || ans.includes('capital adequacy') || ans.includes('tier 1') || ans.includes('liquidity')) {
    start = 580;
    end = 980;
    section = 'Section 2: Capital Adequacy and Liquidity Reserve Ratios';
    page = 2;
  } else if (src.includes('section 3') || ans.includes('encryption') || ans.includes('aes-256') || ans.includes('security')) {
    start = 1020;
    end = 1420;
    section = 'Section 3: Data Security and Encryption Directives';
    page = 3;
  }

  renderSourceDrawerText(fullText, start, end, 'DOC_BRCF_2026_001', section, page);
}

function renderSourceDrawerText(fullText, start, end, docId, section, page) {
  const clampedStart = Math.max(0, Math.min(start, fullText.length));
  const clampedEnd = Math.max(clampedStart, Math.min(end, fullText.length));

  const pre = fullText.substring(0, clampedStart);
  const target = fullText.substring(clampedStart, clampedEnd);
  const post = fullText.substring(clampedEnd);

  ui.drawerSourceHighlightedText.innerHTML = `
    <span>${escapeHtml(pre)}</span><mark class="chunk-highlight">${escapeHtml(target)}</mark><span>${escapeHtml(post)}</span>
  `;

  ui.drawerDocId.textContent = docId || 'DOC_BRCF_2026_001';
  ui.drawerSection.textContent = section || 'Section 1: Executive Overview';
  ui.drawerPage.textContent = `Page ${page || 1}`;
  ui.drawerSpan.textContent = `[${clampedStart}, ${clampedEnd}]`;
  ui.drawerBreadcrumbs.textContent = `Doc: sample_banking_regulation.txt | ${section}`;

  const mark = ui.drawerSourceHighlightedText.querySelector('mark');
  if (mark) {
    mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// ==========================================================================
// Chunker Studio & Token Sizing
// ==========================================================================
function setupChunkerStudio() {
  ui.chunkSizeInput.addEventListener('input', (e) => {
    const isToken = ui.chunkModeSelect.value === 'token';
    ui.chunkSizeDisplay.textContent = `${e.target.value} ${isToken ? 'tokens' : 'chars'}`;
  });

  ui.chunkOverlapInput.addEventListener('input', (e) => {
    const isToken = ui.chunkModeSelect.value === 'token';
    const pct = Math.round((e.target.value / ui.chunkSizeInput.value) * 100) || 0;
    ui.chunkOverlapDisplay.textContent = `${e.target.value} ${isToken ? 'tokens' : 'chars'} (${pct}%)`;
  });

  ui.btnExecuteChunk.addEventListener('click', () => {
    executeChunking();
  });
}

async function executeChunking() {
  const mode = ui.chunkModeSelect.value;
  const chunkSize = parseInt(ui.chunkSizeInput.value, 10);
  const chunkOverlap = parseInt(ui.chunkOverlapInput.value, 10);

  try {
    let data;
    if (appState.apiAvailable) {
      const res = await fetch('/api/chunk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: appState.documentContent,
          mode,
          chunk_size: chunkSize,
          chunk_overlap: chunkOverlap,
          doc_id: appState.documentId,
          filename: appState.documentFilename
        })
      });
      data = await res.json();
    } else {
      data = clientSideChunk(appState.documentContent, chunkSize, chunkOverlap);
    }

    appState.chunks = data.chunks || [];
    renderChunksCards(appState.chunks);
    ui.totalChunksCount.textContent = appState.chunks.length;
  } catch (err) {
    console.error('Chunking error:', err);
  }
}

function renderChunksCards(chunks) {
  ui.chunksGallery.innerHTML = '';

  chunks.forEach((chunk, idx) => {
    const meta = chunk.metadata || {};
    const card = document.createElement('div');
    card.className = 'chunk-box';
    card.innerHTML = `
      <div class="chunk-box-head">
        <span class="chunk-box-id">${escapeHtml(chunk.chunk_id || `chunk_${idx+1}`)}</span>
        <span class="badge badge-accent">${chunk.token_count || Math.round(chunk.text.length / 4)} tokens</span>
      </div>
      <div class="chunk-box-body">${escapeHtml(chunk.text)}</div>
      <div class="chunk-box-foot">
        <span class="foot-chip">📑 ${escapeHtml(meta.section || 'General')}</span>
        <span class="foot-chip">📄 Page ${meta.page_number || 1}</span>
        <span class="foot-chip">📍 [${meta.start_char || 0}, ${meta.end_char || 0}]</span>
        <span class="foot-chip">🔄 ${chunk.overlap_tokens || 0} tokens overlap</span>
      </div>
    `;

    card.addEventListener('click', () => {
      // Open drawer on Home with this chunk
      renderSourceDrawerText(
        appState.documentContent,
        meta.start_char || 0,
        meta.end_char || 0,
        meta.doc_id || 'DOC_BRCF_2026_001',
        meta.section || 'Section 1',
        meta.page_number || 1
      );
      document.getElementById('btnNavHome').click();
    });

    ui.chunksGallery.appendChild(card);
  });
}

function clientSideChunk(text, size, overlap) {
  const step = Math.max(1, size - overlap);
  const chunks = [];
  let start = 0;
  let idx = 0;

  while (start < text.length) {
    const end = Math.min(start + size, text.length);
    const chunkText = text.substring(start, end).trim();
    if (chunkText) {
      idx++;
      chunks.push({
        chunk_id: `DOC_BRCF_2026_001#chunk_${String(idx).padStart(3, '0')}`,
        text: chunkText,
        token_count: Math.round(chunkText.length / 4),
        overlap_tokens: idx > 1 ? Math.round(overlap / 4) : 0,
        metadata: {
          doc_id: 'DOC_BRCF_2026_001',
          filename: 'sample_banking_regulation.txt',
          section: idx === 1 ? 'Section 1: Executive Overview' : (idx === 2 ? 'Section 2: Capital Adequacy' : 'Section 3: Data Security'),
          page_number: idx,
          chunk_index: idx - 1,
          total_chunks: 3,
          start_char: start,
          end_char: end
        }
      });
    }
    start += step;
  }
  return { chunks };
}

// ==========================================================================
// History Audit Table
// ==========================================================================
function renderHistoryTable() {
  ui.historyTableBody.innerHTML = '';

  if (appState.chatHistory.length === 0) {
    ui.historyTableBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
          No dialogue history recorded yet. Ask a question on the HOME tab!
        </td>
      </tr>
    `;
    return;
  }

  appState.chatHistory.forEach((turn, idx) => {
    // User Row
    const uRow = document.createElement('tr');
    uRow.innerHTML = `
      <td>${idx + 1}a</td>
      <td class="role-cell user">USER</td>
      <td><strong>${escapeHtml(turn.user_question)}</strong></td>
      <td>—</td>
      <td>—</td>
      <td>—</td>
    `;
    ui.historyTableBody.appendChild(uRow);

    // Assistant Row
    const aRow = document.createElement('tr');
    aRow.innerHTML = `
      <td>${idx + 1}b</td>
      <td class="role-cell assistant">ASSISTANT</td>
      <td>${escapeHtml(turn.assistant_answer)}</td>
      <td><code>${escapeHtml(turn.source)}</code></td>
      <td><span class="badge badge-success">${escapeHtml(String(turn.confidence))}</span></td>
      <td><strong>${turn.tokens}</strong></td>
    `;
    ui.historyTableBody.appendChild(aRow);
  });
}

// ==========================================================================
// Settings Handlers
// ==========================================================================
function setupSettingsHandlers() {
  ui.settingsSystemRole.addEventListener('change', (e) => {
    ui.systemPromptTemplateCode.textContent = `"You are a helpful {role} specialized AI assistant." -> Role: ${e.target.value}`;
  });

  ui.settingsTempSlider.addEventListener('input', (e) => {
    ui.settingsTempValue.textContent = e.target.value;
  });

  ui.btnExportJson.addEventListener('click', () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(appState.chatHistory, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", "ruler_chat_history.json");
    dlAnchor.click();
  });
}

// ==========================================================================
// JSON Fault Recovery Lab
// ==========================================================================
function setupJsonLabHandlers() {
  ui.rawJsonInput.value = JSON_PRESETS.markdown_trailing_comma;

  ui.btnPresets.forEach(btn => {
    btn.addEventListener('click', () => {
      ui.btnPresets.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const presetKey = btn.dataset.preset;
      if (JSON_PRESETS[presetKey]) {
        ui.rawJsonInput.value = JSON_PRESETS[presetKey];
        runJsonLab();
      }
    });
  });

  ui.btnRunJsonRecovery.addEventListener('click', () => {
    runJsonLab();
  });

  runJsonLab();
}

async function runJsonLab() {
  const raw = ui.rawJsonInput.value;
  try {
    let result;
    if (appState.apiAvailable) {
      const res = await fetch('/api/recover-json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_json: raw,
          required_fields: ['answer', 'source', 'confidence'],
          default_values: { source: 'Fallback_Store', confidence: 'medium' }
        })
      });
      result = await res.json();
    } else {
      result = simulateJsonLab(raw);
    }

    renderJsonLabResults(result);
  } catch (err) {
    console.error('JSON recovery error:', err);
  }
}

function renderJsonLabResults(res) {
  const stageClean = document.getElementById('stageClean');
  const stageParse = document.getElementById('stageParse');
  const stageValidate = document.getElementById('stageValidate');

  if (res.was_recovered || res.parsed_object) {
    stageClean.className = 'stage-card success';
    ui.statusClean.textContent = res.was_recovered ? 'Cleaned markdown fences and trailing commas.' : 'Valid syntax.';
  } else {
    stageClean.className = 'stage-card error';
    ui.statusClean.textContent = 'Could not clean raw string.';
  }

  if (res.parsed_object) {
    stageParse.className = 'stage-card success';
    ui.statusParse.textContent = 'Parsed into Python dictionary.';
  } else {
    stageParse.className = 'stage-card error';
    ui.statusParse.textContent = `JSONDecodeError: ${res.parse_error || 'Invalid syntax'}`;
  }

  if (res.is_valid) {
    stageValidate.className = 'stage-card success';
    ui.statusValidate.textContent = 'All required keys present / recovered.';
    ui.jsonResultBadge.className = 'badge badge-success';
    ui.jsonResultBadge.textContent = 'Valid Object';
    ui.jsonResultViewer.textContent = JSON.stringify(res.final_validated_object || res.parsed_object, null, 2);
  } else {
    stageValidate.className = 'stage-card error';
    ui.statusValidate.textContent = `Missing required fields: ${JSON.stringify(res.missing_fields)}`;
    ui.jsonResultBadge.className = 'badge badge-error';
    ui.jsonResultBadge.textContent = 'Rejected';
    ui.jsonResultViewer.textContent = JSON.stringify({ error: 'Validation Rejected', missing: res.missing_fields }, null, 2);
  }
}

function simulateJsonLab(raw) {
  let cleaned = raw.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim();
  const match = cleaned.match(/\{[\s\S]*\}/);
  if (match) cleaned = match[0];
  cleaned = cleaned.replace(/,\s*([}\]])/g, '$1');

  try {
    const parsed = JSON.parse(cleaned);
    const defaults = { source: 'Fallback_Store', confidence: 'medium' };
    const missing = [];
    const recovered = { ...parsed };

    ['answer', 'source', 'confidence'].forEach(f => {
      if (!recovered[f]) {
        if (defaults[f]) recovered[f] = defaults[f];
        else missing.push(f);
      }
    });

    return {
      was_recovered: cleaned !== raw.trim(),
      parsed_object: parsed,
      is_valid: missing.length === 0,
      missing_fields: missing,
      final_validated_object: missing.length === 0 ? recovered : null
    };
  } catch (err) {
    return {
      was_recovered: false,
      parsed_object: null,
      parse_error: err.message,
      is_valid: false,
      missing_fields: ['answer', 'source', 'confidence']
    };
  }
}

// Utility
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
