'use client';

import { ButtonLink } from '@/components/ui/ButtonLink';
import { readOrder } from '@/lib/order-store';
import { useHydrated } from '@/lib/use-hydrated';

/**
 * PayHere's cancel_url: the shopper backed out of paying. The order still exists (unpaid), but
 * nothing here retries the payment automatically, so the honest thing is to say so plainly.
 */
export function CancelledOrderNotice({ reference }: { reference: string | undefined }) {
  const hydrated = useHydrated();
  if (!hydrated) return <div className="min-h-64" aria-hidden="true" />;

  const order = reference ? readOrder(reference) : null;

  return (
    <div className="mt-8 space-y-6">
      <p>
        {order
          ? `Your order (reference ${order.reference}) was placed, but the payment was cancelled and nothing was charged.`
          : 'The payment was cancelled and nothing was charged.'}
      </p>
      <p className="text-sm">
        Please place the order again if you would like to pay a different way, or contact us about
        this order if you already spoke with support.
      </p>
      <ButtonLink href="/cart">Back to your cart</ButtonLink>
    </div>
  );
}
