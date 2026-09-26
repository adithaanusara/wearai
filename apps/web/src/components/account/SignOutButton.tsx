'use client';

import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import { SESSION_QUERY_KEY } from '@/components/account/useSession';
import { logout } from '@/lib/api';

export function SignOutButton() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const running = useRef(false);
  const [failed, setFailed] = useState(false);

  async function signOut() {
    if (running.current) return;
    running.current = true;
    setFailed(false);
    try {
      await logout();
      // Forget who was signed in, then leave: the account page would only send them to /login.
      queryClient.setQueryData(SESSION_QUERY_KEY, null);
      router.replace('/');
      router.refresh();
    } catch {
      setFailed(true);
    } finally {
      running.current = false;
    }
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        className="border-text hover:bg-surface rounded-sm border px-8 py-3 text-xs font-medium tracking-wide uppercase transition-colors"
        onClick={signOut}
      >
        Sign out
      </button>
      {failed && (
        <p role="alert" className="text-error text-sm">
          We could not sign you out. Please try again.
        </p>
      )}
    </div>
  );
}
