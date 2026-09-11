/**
 * API Client for Ruler REST Services & Server-Side Protected Admin Routes
 */

// -------------------------------------------------------------
// PUBLIC / USER ENDPOINTS
// -------------------------------------------------------------
export async function queryRAG(question, topK = 3, temperature = 0.2) {
  const response = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK, temperature }),
  });

  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.message || errBody.detail || `Server error: ${response.status}`);
  }

  return await response.json();
}

// -------------------------------------------------------------
// ADMIN AUTHENTICATION API (SERVER-SIDE WITH HTTPONLY COOKIES)
// -------------------------------------------------------------
export async function loginAdminPasskey(passkey) {
  const response = await fetch('/api/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ passkey }),
    credentials: 'include',
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.message || 'Authentication failed.');
    error.status = response.status;
    error.retryAfterMinutes = data.retryAfterMinutes;
    throw error;
  }

  return data;
}

export async function logoutAdminSession() {
  const response = await fetch('/api/admin/logout', {
    method: 'POST',
    credentials: 'include',
  });

  return await response.json().catch(() => ({}));
}

export async function checkAdminSession() {
  const response = await fetch('/api/admin/session', {
    method: 'GET',
    credentials: 'include',
    cache: 'no-store',
  });

  if (!response.ok) {
    return { authenticated: false };
  }

  return await response.json();
}

// -------------------------------------------------------------
// PROTECTED ADMIN DATA & INGESTION API
// -------------------------------------------------------------
export async function fetchServerConfig() {
  const response = await fetch('/api/admin/config', {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch config: ${response.status}`);
  }
  return await response.json();
}

export async function uploadDocumentText({ text, title, category, doc_id }) {
  const response = await fetch('/api/admin/upload-text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, title, category, doc_id }),
    credentials: 'include',
  });

  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.message || errBody.detail || `Upload failed: ${response.status}`);
  }

  return await response.json();
}

export async function uploadDocumentFile(formData) {
  const response = await fetch('/api/admin/upload', {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.message || errBody.detail || `File upload failed: ${response.status}`);
  }

  return await response.json();
}

export async function fetchDocuments() {
  const response = await fetch('/api/admin/documents', {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch documents: ${response.status}`);
  }
  return await response.json();
}
