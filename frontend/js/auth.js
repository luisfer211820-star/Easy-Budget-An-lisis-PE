// ─────────────────────────────────────────────
// EasyBudget — Auth Module (API-based + SQLite)
// ─────────────────────────────────────────────

const API_BASE = 'http://localhost:5000/api';
const DB_SESSION = 'eb_session';

/* ── Session helpers ── */
function setSession(user) {
  localStorage.setItem(DB_SESSION, JSON.stringify({ id: user.id, name: user.name, email: user.email }));
}

export function getSession() {
  const s = localStorage.getItem(DB_SESSION);
  return s ? JSON.parse(s) : null;
}

export function requireAuth() {
  if (!getSession()) {
    window.location.href = 'login.html';
    return null;
  }
  return getSession();
}

export function logout() {
  localStorage.removeItem(DB_SESSION);
  window.location.href = 'login.html';
}

/* ── Register (async — calls backend API) ── */
export async function register(name, email, password) {
  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    });
    const data = await res.json();
    if (data.ok) {
      setSession(data.user);
    }
    return data;
  } catch (err) {
    return { ok: false, error: 'No se pudo conectar al servidor. Verifica que el backend esté corriendo.' };
  }
}

/* ── Login (async — calls backend API) ── */
export async function login(email, password) {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.ok) {
      setSession(data.user);
    }
    return data;
  } catch (err) {
    return { ok: false, error: 'No se pudo conectar al servidor. Verifica que el backend esté corriendo.' };
  }
}
