'use client';

import { useState, type FormEvent } from 'react';
import { SizeGuide } from '@/components/product/SizeGuide';
import type { Product } from '@/types/product';

const oneSize = 'One Size';

export function BuyBox({ product }: { product: Product }) {
  const [size, setSize] = useState<string | null>(
    product.sizes.length === 1 ? product.sizes[0] : null,
  );
  const [message, setMessage] = useState<{ kind: 'error' | 'success'; text: string } | null>(null);
  const hasSizeChart = !product.sizes.includes(oneSize);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!size) {
      setMessage({ kind: 'error', text: 'Please select a size.' });
      return;
    }
    // The cart itself arrives with the cart drawer; until then this only confirms the choice.
    setMessage({ kind: 'success', text: `Added ${product.name}, size ${size}.` });
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <fieldset>
        <div className="mb-3 flex items-center justify-between">
          <legend className="text-sm">
            <span className="text-muted">Size:</span> {size ?? 'Select a size'}
          </legend>
          {hasSizeChart && <SizeGuide />}
        </div>
        <div className="flex flex-wrap gap-2">
          {product.sizes.map((option) => (
            <label key={option} className="cursor-pointer">
              <input
                type="radio"
                name="size"
                value={option}
                className="peer sr-only"
                checked={size === option}
                onChange={() => {
                  setSize(option);
                  setMessage(null);
                }}
              />
              <span className="border-border peer-checked:bg-text peer-checked:text-bg peer-checked:border-text peer-focus-visible:outline-text block min-w-12 rounded-sm border px-4 py-3 text-center text-sm peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2">
                {option}
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      <button
        type="submit"
        className="bg-text text-bg hover:bg-dark-2 w-full rounded-sm px-8 py-4 text-xs font-medium tracking-wide uppercase transition-colors"
      >
        Add to cart
      </button>

      <p
        role="status"
        className={`min-h-5 text-sm ${message?.kind === 'error' ? 'text-error' : 'text-success'}`}
      >
        {message?.text}
      </p>
    </form>
  );
}
