'use client';

import { createContext, useContext, useMemo, useSyncExternalStore, type ReactNode } from 'react';
import type { Session } from '@/lib/session';
import {
  clearSession,
  getServerSessionSnapshot,
  getSessionSnapshot,
  saveSession,
  subscribeToSession,
} from '@/lib/session-store';

interface SessionContextValue {
  session: Session | null;
  signIn: (session: Session) => void;
  signOut: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const session = useSyncExternalStore(
    subscribeToSession,
    getSessionSnapshot,
    getServerSessionSnapshot,
  );

  const value = useMemo<SessionContextValue>(
    () => ({ session, signIn: saveSession, signOut: clearSession }),
    [session],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (!context) throw new Error('useSession must be used inside SessionProvider');
  return context;
}
