'use client';

import { useCart } from '@/components/cart/CartProvider';
import { BagIcon } from '@/components/ui/icons';

export function CartButton() {
  const { count, openCart } = useCart();

  return (
    <button
      type="button"
      aria-label={`Open cart, ${count} ${count === 1 ? 'item' : 'items'}`}
      aria-haspopup="dialog"
      className="relative -mr-2 p-2"
      onClick={openCart}
    >
      <BagIcon />
      {count > 0 && (
        <span
          aria-hidden="true"
          className="bg-text text-bg absolute top-0.5 right-0.5 flex h-4 min-w-4 items-center justify-center rounded-sm px-1 text-[10px] leading-none font-medium"
        >
          {count}
        </span>
      )}
    </button>
  );
}
