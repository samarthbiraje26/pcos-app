/**
 * api.js — Centralized API client
 * Handles fetch calls, JWT injection, token refresh, and auth redirects.
 */

const API_BASE = 'http://localhost:5000/api';

const TokenStore = {
  get access() { return localStorage.getItem('access_token'); },
  get refresh() { return localStorage.getItem('refresh_token'); },
  get user() { try { return JSON.parse(localStorage.getItem('user')); } catch { return null; } },

  set(access, refresh, user) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user', JSON.stringify(user));
  },
  setAccess(token) { localStorage.setItem('access_token', token); },
  clear() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  isLoggedIn() { return !!this.access; },
};

// ── Core fetch wrapper ────────────────────────────────────────────────────────

async function apiFetch(endpoint, options = {}, retry = true) {
  const url = `${API_BASE}${endpoint}`;
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };

  if (TokenStore.access) {
    headers['Authorization'] = `Bearer ${TokenStore.access}`;
  }

  const res = await fetch(url, { ...options, headers });

  // Token expired → try to refresh once
  if (res.status === 401 && retry && TokenStore.refresh) {
    const refreshed = await tryRefresh();
    if (refreshed) return apiFetch(endpoint, options, false);
    TokenStore.clear();
    redirectToLogin();
    return null;
  }

  return res;
}

async function tryRefresh() {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TokenStore.refresh}`,
      },
    });
    if (!res.ok) return false;
    const data = await res.json();
    TokenStore.setAccess(data.access_token);
    return true;
  } catch {
    return false;
  }
}

function redirectToLogin() {
  if (!window.location.pathname.endsWith('login.html')) {
    window.location.href = '/login.html';
  }
}

// ── Public API helpers ────────────────────────────────────────────────────────

const API = {
  // Auth
  async register(payload) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return { ok: res.ok, data: await res.json() };
  },

  async login(payload) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return { ok: res.ok, data: await res.json() };
  },

  async forgotPassword(payload) {
    const res = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return { ok: res.ok, data: await res.json() };
  },

  async resetPassword(payload) {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return { ok: res.ok, data: await res.json() };
  },

  async getMe() {
    const res = await apiFetch('/auth/me');
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  // Prediction
  async predict(payload) {
    const res = await apiFetch('/predict', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  // History
  async getHistory(page = 1, perPage = 10) {
    const res = await apiFetch(`/history?page=${page}&per_page=${perPage}`);
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  async deleteHistory(id) {
    const res = await apiFetch(`/history/${id}`, { method: 'DELETE' });
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  async getStats() {
    const res = await apiFetch('/stats');
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  // Diet
  async getDietPlan() {
    const res = await apiFetch('/diet-plan');
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  async regenerateDietPlan() {
    const res = await apiFetch('/diet-plan/regenerate', { method: 'POST' });
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  // Chat
  async getChatHistory() {
    const res = await apiFetch('/chat/history');
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  async sendChatMessage(message) {
    const res = await apiFetch('/chat/send', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  // Awareness
  async getAwareness() {
    const res = await apiFetch('/awareness');
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },

  async refreshAwarenessTips() {
    const res = await apiFetch('/awareness/refresh-tips', { method: 'POST' });
    if (!res) return null;
    return { ok: res.ok, data: await res.json() };
  },
};

// ── Guard: require auth on protected pages ────────────────────────────────────

function requireAuth() {
  if (!TokenStore.isLoggedIn()) {
    redirectToLogin();
    return false;
  }
  return true;
}

function requireGuest() {
  if (TokenStore.isLoggedIn()) {
    window.location.href = '/dashboard.html';
  }
}

// ── Shared UI helpers ─────────────────────────────────────────────────────────

function showAlert(elId, message, type = 'error') {
  const el = document.getElementById(elId);
  if (!el) return;
  el.className = `alert alert-${type} show`;
  el.textContent = message;
  setTimeout(() => el.classList.remove('show'), 5000);
}

function setLoading(btnId, loading, label = null) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  if (loading) {
    btn.dataset.label = btn.textContent;
    btn.innerHTML = '<span class="spinner"></span>';
    btn.disabled = true;
  } else {
    btn.innerHTML = label || btn.dataset.label || btn.textContent;
    btn.disabled = false;
  }
}

function fmtDate(isoString) {
  if (!isoString) return '—';
  let datestr = isoString;
  if (typeof datestr === 'string' && !datestr.includes('Z') && !datestr.includes('+') && !datestr.includes('-')) {
    datestr += 'Z';
  }
  return new Date(datestr).toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function pct(val) { return `${Math.round(val * 100)}%`; }

function populateSidebarUser() {
  const user = TokenStore.user;
  if (!user) return;
  const nameEls = document.querySelectorAll('.js-user-name');
  const emailEls = document.querySelectorAll('.js-user-email');
  const avatarEls = document.querySelectorAll('.js-user-avatar');
  nameEls.forEach(el => el.textContent = user.name);
  emailEls.forEach(el => el.textContent = user.email);
  avatarEls.forEach(el => el.textContent = user.name.charAt(0).toUpperCase());
}

function logout() {
  TokenStore.clear();
  window.location.href = '/login.html';
}

// Bind logout buttons
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.js-logout').forEach(btn => btn.addEventListener('click', logout));
  populateSidebarUser();
});
