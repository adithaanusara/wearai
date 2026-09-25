'use client';

import { CartLineItem } from '@/components/cart/CartLineItem';
import { CartNotice } from '@/components/cart/CartNotice';
import { OrderSummary } from '@/components/cart/OrderSummary';
import { CheckoutButton } from '@/components/cart/CheckoutButton';
import { useCartLines } from '@/components/cart/useCartLines';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { canCheckout, cartSubtotal, hasCartProblems } from '@/lib/cart';
import { useHydrated } from '@/lib/use-hydrated';

export function CartView() {
  const { lines, status, retry } = useCartLines();
  const hydrated = useHydrated();

  // The cart lives in the browser, so wait for it instead of flashing an empty cart.
  if (!hydrated) return <div className="min-h-64" aria-hidden="true" />;

  if (status === 'empty') {
    return (
      <div className="mt-12 flex flex-col items-center gap-6 text-center">
        <p>Your cart is empty.</p>
        <ButtonLink href="/collections/new">Continue shopping</ButtonLink>
      </div>
    );
  }

  return (
    <div className="mt-8 gap-12 lg:grid lg:grid-cols-[1fr_22rem]">
      <div>
        <CartNotice status={status} hasProblems={hasCartProblems(lines)} onRetry={retry} />
        <ul className="divide-border border-border divide-y border-y">
          {lines.map((line) => (
            <CartLineItem key={`${line.item.productId}-${line.item.size}`} line={line} />
          ))}
        </ul>
      </div>

      <aside aria-label="Order summary" className="bg-surface mt-8 space-y-6 p-6 lg:mt-0">
        {status === 'ready' ? (
          <OrderSummary subtotal={cartSubtotal(lines)} shipping={null} />
        ) : (
          <p className="text-muted text-sm">Prices appear once your items have loaded.</p>
        )}
        <CheckoutButton enabled={canCheckout(lines)} className="w-full" />
        <ButtonLink href="/collections/new" variant="secondary" className="w-full">
          Continue shopping
        </ButtonLink>
      </aside>
    </div>
  );
}
