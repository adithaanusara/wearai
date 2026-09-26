'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import type { Notice } from '@/components/admin/ProductAdminPanel';
import { ApiError, setProductArchived } from '@/lib/api';

interface ProductArchiveButtonProps {
  onNotice: (notice: Notice | null) => void;
  id: string;
  updatedAt: string;
  archived: boolean;
}

const buttonClass =
  'border-text hover:bg-surface rounded-sm border px-5 py-3 text-xs font-medium tracking-wide uppercase disabled:opacity-40';

export function ProductArchiveButton({
  id,
  updatedAt,
  archived,
  onNotice,
}: ProductArchiveButtonProps) {
  const router = useRouter();
  const running = useRef(false);
  const [confirming, setConfirming] = useState(false);
  const [saving, setSaving] = useState(false);

  async function change() {
    if (running.current) return;
    // Archiving takes the product off the shop, so it asks once more. Restoring does not.
    if (!archived && !confirming) {
      setConfirming(true);
      return;
    }
    running.current = true;
    setSaving(true);
    onNotice(null);
    try {
      await setProductArchived(id, updatedAt, !archived);
    } catch (failure) {
      onNotice({
        kind: 'error',
        text:
          failure instanceof ApiError && failure.status === 409
            ? failure.message
            : 'We could not change the product. Please try again.',
      });
    } finally {
      running.current = false;
      setSaving(false);
      setConfirming(false);
      router.refresh();
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" disabled={saving} className={buttonClass} onClick={change}>
          {archived ? 'Restore product' : confirming ? 'Click again to archive' : 'Archive product'}
        </button>
        {confirming && (
          <button type="button" className="text-xs underline" onClick={() => setConfirming(false)}>
            Keep it in the shop
          </button>
        )}
      </div>
      {!archived && (
        <p className="text-muted text-xs">
          Archiving hides the product from the shop and the assistant. Past orders keep it.
        </p>
      )}
    </div>
  );
}
