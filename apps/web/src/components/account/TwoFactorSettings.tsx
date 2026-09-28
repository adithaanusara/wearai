'use client';

import { useQueryClient } from '@tanstack/react-query';
import QRCode from 'qrcode';
import { useRef, useState, type FormEvent } from 'react';
import { PasswordField } from '@/components/account/PasswordField';
import { SESSION_QUERY_KEY } from '@/components/account/useSession';
import { Field } from '@/components/ui/Field';
import { ApiError, confirmTwoFactor, disableTwoFactor, setUpTwoFactor } from '@/lib/api';
import { cleanCode } from '@/lib/two-factor';
import type { User } from '@/types/api';

type Stage = 'idle' | 'setting-up' | 'showing-codes' | 'disabling';

const unreachable = 'We could not reach the store. Please try again in a moment.';
const buttonClass =
  'border-text hover:bg-surface rounded-sm border px-6 py-3 text-xs font-medium tracking-wide uppercase disabled:opacity-40';

export function TwoFactorSettings({ user }: { user: User }) {
  const queryClient = useQueryClient();
  const running = useRef(false);
  // `user` is a prop from the server, fixed at page load: it never updates on its own after a
  // client-side change here, so once this component is in charge, its own state is instead.
  const [enabled, setEnabled] = useState(user.twoFactorEnabled);
  const [stage, setStage] = useState<Stage>('idle');
  const [secret, setSecret] = useState('');
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function reset() {
    setStage('idle');
    setSecret('');
    setQrDataUrl(null);
    setCode('');
    setPassword('');
    setError(null);
  }

  async function startSetup() {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setError(null);
    try {
      const setup = await setUpTwoFactor();
      setSecret(setup.secret);
      setQrDataUrl(await QRCode.toDataURL(setup.provisioningUri));
      setStage('setting-up');
    } catch (failure) {
      setError(failure instanceof ApiError && failure.status < 500 ? failure.message : unreachable);
    } finally {
      running.current = false;
      setBusy(false);
    }
  }

  async function onConfirm(event: FormEvent) {
    event.preventDefault();
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setError(null);
    try {
      const { recoveryCodes: codes } = await confirmTwoFactor(cleanCode(code));
      setRecoveryCodes(codes);
      setStage('showing-codes');
      setEnabled(true);
      queryClient.setQueryData(SESSION_QUERY_KEY, { ...user, twoFactorEnabled: true });
    } catch (failure) {
      setError(failure instanceof ApiError && failure.status < 500 ? failure.message : unreachable);
    } finally {
      running.current = false;
      setBusy(false);
    }
  }

  async function onDisable(event: FormEvent) {
    event.preventDefault();
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setError(null);
    try {
      await disableTwoFactor(password, cleanCode(code));
      setEnabled(false);
      queryClient.setQueryData(SESSION_QUERY_KEY, { ...user, twoFactorEnabled: false });
      reset();
    } catch (failure) {
      setError(failure instanceof ApiError && failure.status < 500 ? failure.message : unreachable);
    } finally {
      running.current = false;
      setBusy(false);
    }
  }

  if (stage === 'showing-codes' && recoveryCodes) {
    return (
      <div className="space-y-4">
        <p role="status" className="text-success text-sm">
          Two-factor authentication is on.
        </p>
        <div className="bg-surface space-y-2 p-4">
          <p className="text-xs font-medium tracking-wide uppercase">
            Save these recovery codes now
          </p>
          <p className="text-muted text-xs">
            Each works once, if you lose access to your authenticator app. They will not be shown
            again.
          </p>
          <ul className="grid grid-cols-2 gap-2 font-mono text-sm">
            {recoveryCodes.map((recoveryCode) => (
              <li key={recoveryCode}>{recoveryCode}</li>
            ))}
          </ul>
        </div>
        <button type="button" className={buttonClass} onClick={reset}>
          Done
        </button>
      </div>
    );
  }

  if (stage === 'setting-up') {
    return (
      <form onSubmit={onConfirm} className="max-w-sm space-y-4">
        {error && (
          <p role="alert" className="text-error text-sm">
            {error}
          </p>
        )}
        <p className="text-sm">
          Scan this with your authenticator app, then enter the code it shows.
        </p>
        {qrDataUrl && (
          // eslint-disable-next-line @next/next/no-img-element -- a data: URL, not an optimisable asset
          <img src={qrDataUrl} alt="QR code for the authenticator app" width={200} height={200} />
        )}
        <p className="text-muted text-xs break-all">Or enter this manually: {secret}</p>
        <Field
          name="code"
          label="Code"
          inputMode="numeric"
          autoFocus
          value={code}
          onChange={(event) => setCode(event.target.value)}
        />
        <div className="flex gap-3">
          <button type="submit" disabled={busy || !code.trim()} className={buttonClass}>
            {busy ? 'Confirming…' : 'Confirm'}
          </button>
          <button type="button" className="text-xs underline" onClick={reset}>
            Cancel
          </button>
        </div>
      </form>
    );
  }

  if (stage === 'disabling') {
    return (
      <form onSubmit={onDisable} className="max-w-sm space-y-4">
        {error && (
          <p role="alert" className="text-error text-sm">
            {error}
          </p>
        )}
        <p className="text-sm">Enter your password and a current code to turn this off.</p>
        <PasswordField
          name="password"
          label="Password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Field
          name="code"
          label="Code or recovery code"
          value={code}
          onChange={(event) => setCode(event.target.value)}
        />
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={busy || !password || !code.trim()}
            className={buttonClass}
          >
            {busy ? 'Turning off…' : 'Turn off'}
          </button>
          <button type="button" className="text-xs underline" onClick={reset}>
            Cancel
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="space-y-3">
      {error && (
        <p role="alert" className="text-error text-sm">
          {error}
        </p>
      )}
      <p className="text-sm">
        {enabled
          ? 'On. Signing in also asks for a code from your authenticator app.'
          : 'Off. Turn this on to ask for a code from an authenticator app when signing in.'}
      </p>
      <button
        type="button"
        disabled={busy}
        className={buttonClass}
        onClick={() => (enabled ? setStage('disabling') : startSetup())}
      >
        {enabled ? 'Turn off' : busy ? 'Starting…' : 'Turn on'}
      </button>
    </div>
  );
}
