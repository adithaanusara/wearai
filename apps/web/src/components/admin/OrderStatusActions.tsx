'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import { needsConfirmation, statusActionLabel, statusChangeError } from '@/lib/admin';
import { changeOrderStatus } from '@/lib/api';

interface OrderStatusActionsProps {
  reference: string;
  status: string;
  /** The moves the API says are allowed right now. Nothing else is offered. */
  allowedNext: string[];
}

const buttonClass =
  'border-text hover:bg-surface rounded-sm border px-5 py-3 text-xs font-medium tracking-wide uppercase disabled:opacity-40';

export function OrderStatusActions({ reference, status, allowedNext }: OrderStatusActionsProps) {
  const router = useRouter();
  const running = useRef(false);
  const [confirming, setConfirming] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  if (allowedNext.length === 0) {
    return <p className="text-muted text-sm">This order is {status}. It cannot be changed.</p>;
  }

  async function move(target: string) {
    if (running.current) return;
    if (needsConfirmation(target) && confirming !== target) {
      setConfirming(target);
      return;
    }
    running.current = true;
    setSaving(true);
    setError('');
    try {
      await changeOrderStatus(reference, status, target);
    } catch (failure) {
      setError(statusChangeError(failure));
    } finally {
      running.current = false;
      setSaving(false);
      setConfirming(null);
      // Either way, show what the server now says, including after someone else's change.
      router.refresh();
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3">
        {allowedNext.map((target) => (
          <button
            key={target}
            type="button"
            disabled={saving}
            className={buttonClass}
            onClick={() => move(target)}
          >
            {confirming === target ? 'Click again to confirm' : statusActionLabel(target)}
          </button>
        ))}
        {confirming && (
          <button type="button" className="text-xs underline" onClick={() => setConfirming(null)}>
            Keep the order
          </button>
        )}
      </div>
      {error && (
        <p role="alert" className="text-error text-sm">
          {error}
        </p>
      )}
    </div>
  );
}
