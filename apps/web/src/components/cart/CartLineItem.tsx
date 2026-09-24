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
          <button
            type="button"
            aria-label={`Remove ${product.name}, size ${item.size}`}
            className="text-muted text-xs underline"
            onClick={() => removeItem(item.productId, item.size)}
          >
            Remove
          </button>
        </div>
      </div>
    </li>
  );
}
