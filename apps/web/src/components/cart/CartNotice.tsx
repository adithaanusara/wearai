import type { CartStatus } from '@/lib/cart';

interface CartNoticeProps {
  status: CartStatus;
  hasProblems: boolean;
  onRetry: () => void;
}

/** Explains why the cart cannot be checked out yet, and what to do about it. */
export function CartNotice({ status, hasProblems, onRetry }: CartNoticeProps) {
  if (status === 'error') {
    return (
      <div role="alert" className="border-border my-4 space-y-3 rounded-sm border p-4 text-sm">
        <p>We could not load the details of your cart. Your items are saved.</p>
        <button type="button" className="underline" onClick={onRetry}>
          Try again
        </button>
      </div>
    );
  }
  if (status === 'ready' && hasProblems) {
    return (
      <p role="alert" className="border-border my-4 rounded-sm border p-4 text-sm">
        Some items can no longer be ordered. Remove them to continue.
      </p>
    );
  }
  return null;
}
