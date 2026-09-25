'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useCart } from '@/components/cart/CartProvider';
import { MAX_QUANTITY, type CartLine } from '@/lib/cart';
import { formatPrice } from '@/lib/format';

const stepButton =
  'border-border flex h-8 w-8 items-center justify-center rounded-sm border text-base disabled:opacity-40';

export function CartLineItem({ line }: { line: CartLine }) {
  const { closeCart, removeItem, setQuantity } = useCart();
  const { item, product, total } = line;

  const remove = (
    <button
      type="button"
      aria-label={product ? `Remove ${product.name}, size ${item.size}` : 'Remove this item'}
      className="text-muted text-xs underline"
      onClick={() => removeItem(item.productId, item.size)}
    >
      Remove
    </button>
  );

  // The details are still loading, or could not be loaded: show a placeholder, never lose the item.
  if (line.state !== 'ready') {
    return (
      <li className="flex gap-4 py-5" aria-busy={line.state === 'loading'}>
        <div className="bg-surface aspect-4/5 w-24 shrink-0 motion-safe:animate-pulse" />
        <div className="flex flex-1 flex-col justify-between text-sm">
          <p className="text-muted">
            {line.state === 'loading' ? 'Loading…' : 'Could not load this item.'}
          </p>
          <div className="flex justify-end">{remove}</div>
        </div>
      </li>
    );
  }

  if (line.problem === 'unavailable' || !product) {
    return (
      <li className="flex items-center justify-between gap-4 py-5 text-sm">
        <p>This product is no longer available.</p>
        {remove}
      </li>
    );
  }

  return (
    <li className="flex gap-4 py-5">
      <div className="bg-surface relative aspect-4/5 w-24 shrink-0">
        <Image
          src={product.images[0]}
          alt={`${product.name} in ${product.colour}`}
          fill
          sizes="96px"
          className="object-cover"
        />
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-1 text-sm">
        <Link
          href={`/products/${product.slug}`}
          onClick={closeCart}
          className="font-medium hover:underline"
        >
          {product.name}
        </Link>
        <p className="text-muted">
          {product.colour} · {item.size}
        </p>

        {line.problem === 'size' ? (
          <div className="mt-2 flex items-center justify-between gap-4">
            <p>Size {item.size} is no longer available.</p>
            {remove}
          </div>
        ) : (
          <>
            <div className="mt-2 flex items-center gap-2">
              <button
                type="button"
                aria-label={`Decrease quantity of ${product.name}`}
                disabled={item.quantity <= 1}
                className={stepButton}
                onClick={() => setQuantity(item.productId, item.size, item.quantity - 1)}
              >
                −
              </button>
              <span aria-live="polite" className="w-6 text-center">
                {item.quantity}
              </span>
              <button
                type="button"
                aria-label={`Increase quantity of ${product.name}`}
                disabled={item.quantity >= MAX_QUANTITY}
                className={stepButton}
                onClick={() => setQuantity(item.productId, item.size, item.quantity + 1)}
              >
                +
              </button>
            </div>

            <div className="mt-2 flex items-center justify-between">
              <span>{formatPrice(total)}</span>
              {remove}
            </div>
          </>
        )}
      </div>
    </li>
  );
}
