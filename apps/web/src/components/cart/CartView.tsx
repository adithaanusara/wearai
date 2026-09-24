'use client';

import { CartLineItem } from '@/components/cart/CartLineItem';
import { useCart } from '@/components/cart/CartProvider';
import { OrderSummary } from '@/components/cart/OrderSummary';
import { ButtonLink } from '@/components/ui/ButtonLink';
import { cartSubtotal, resolveCartLines } from '@/lib/cart';
import { useHydrated } from '@/lib/use-hydrated';

export function CartView() {
  const { items } = useCart();
  const hydrated = useHydrated();
  const lines = resolveCartLines(items);

  // The cart lives in the browser, so wait for it instead of flashing an empty cart.
  if (!hydrated) return <div className="min-h-64" aria-hidden="true" />;

  if (lines.length === 0) {
    return (
      <div className="mt-12 flex flex-col items-center gap-6 text-center">
        <p>Your cart is empty.</p>
        <ButtonLink href="/collections/new">Continue shopping</ButtonLink>
      </div>
    );
  }

  return (
    <div className="mt-8 gap-12 lg:grid lg:grid-cols-[1fr_22rem]">
      <ul className="divide-border border-border divide-y border-y">
        {lines.map((line) => (
          <CartLineItem key={`${line.item.productId}-${line.item.size}`} line={line} />
        ))}
      </ul>

      <aside aria-label="Order summary" className="bg-surface mt-8 space-y-6 p-6 lg:mt-0">
        <OrderSummary subtotal={cartSubtotal(lines)} shipping={null} />
        <ButtonLink href="/checkout" className="w-full">
          Checkout
        </ButtonLink>
        <ButtonLink href="/collections/new" variant="secondary" className="w-full">
          Continue shopping
        </ButtonLink>
      </aside>
    </div>
  );
}
