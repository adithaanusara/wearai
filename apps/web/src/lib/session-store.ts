import { parseStoredSession, type Session } from '@/lib/session';

// Demo only: the session is kept in the browser until the API provides real authentication.
const STORAGE_KEY = 'wearai-session';

const listeners = new Set<() => void>();

// The snapshot keeps the same reference until the stored value changes, as React requires.
let cache: { raw: string | null; session: Session | null } = { raw: null, session: null };
let storageWorks = true;

function readStorage(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function getSessionSnapshot(): Session | null {
  if (!storageWorks) return cache.session;
  const raw = readStorage();
  if (raw !== cache.raw) cache = { raw, session: parseStoredSession(raw) };
  return cache.session;
}

export function getServerSessionSnapshot(): Session | null {
  return null;
}

export function subscribeToSession(listener: () => void): () => void {
  listeners.add(listener);
  window.addEventListener('storage', listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener('storage', listener);
  };
}

function write(session: Session | null): void {
  const raw = session ? JSON.stringify(session) : null;
  try {
    if (raw) window.localStorage.setItem(STORAGE_KEY, raw);
    else window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    storageWorks = false;
  }
  cache = { raw, session };
  listeners.forEach((listener) => listener());
}

export const saveSession = (session: Session) => write(session);
export const clearSession = () => write(null);
