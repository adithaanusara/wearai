'use client';

import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useRef, useState, type FormEvent } from 'react';
import { SESSION_QUERY_KEY } from '@/components/account/useSession';
import { Field } from '@/components/ui/Field';
import { ApiError, verifyTwoFactor } from '@/lib/api';

const unreachable = 'We could not reach the store. Please try again in a moment.';

/** The second step of signing in, once the password was right but the account has 2FA on. */
export function TwoFactorStep({
  pendingToken,
  onBack,
}: {
  pendingToken: string;
  onBack: () => void;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const submitting = useRef(false);
  const [code, setCode] = useState('');
  const [banner, setBanner] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setBanner(null);

    try {
      const user = await verifyTwoFactor(pendingToken, code.trim());
      queryClient.setQueryData(SESSION_QUERY_KEY, user);
      router.replace('/account');
      router.refresh();
    } catch (error) {
      setBanner(error instanceof ApiError && error.status < 500 ? error.message : unreachable);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      {banner && (
        <p role="alert" className="border-error text-error rounded-sm border p-3 text-sm">
          {banner}
        </p>
      )}
      <p className="text-sm">
        Enter the 6-digit code from your authenticator app, or one of your recovery codes.
      </p>
      <Field
        name="code"
        label="Code"
        inputMode="numeric"
        autoComplete="one-time-code"
        autoFocus
        value={code}
        onChange={(event) => setCode(event.target.value)}
      />
      <button
        type="submit"
        disabled={busy || !code.trim()}
        className="bg-text text-bg hover:bg-dark-2 w-full rounded-sm px-8 py-4 text-xs font-medium tracking-wide uppercase transition-colors disabled:opacity-40"
      >
        {busy ? 'Verifying…' : 'Verify'}
      </button>
      <button type="button" onClick={onBack} className="text-sm underline">
        Back to sign in
      </button>
    </form>
  );
}
