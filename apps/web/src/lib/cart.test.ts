import { describe, expect, it } from 'vitest';
import {
  MAX_QUANTITY,
  cartCount,
  cartReducer,
  cartSubtotal,
  parseStoredCart,
  resolveCartLines,
} from '@/lib/cart';
import type { CartItem } from '@/types/cart';

const line = (productId: string, size: string, quantity = 1): CartItem => ({
  productId,
  size,
  quantity,
});

describe('cartReducer', () => {
  it('adds a new line with quantity 1', () => {
    expect(cartReducer([], { type: 'add', productId: 'w-tee-01', size: 'M' })).toEqual([
      line('w-tee-01', 'M'),
    ]);
  });

  it('increases the quantity when the same product and size is added again', () => {
    const items = [line('w-tee-01', 'M')];
    expect(cartReducer(items, { type: 'add', productId: 'w-tee-01', size: 'M' })).toEqual([
      line('w-tee-01', 'M', 2),
    ]);
  });

  it('keeps different sizes of a product as separate lines', () => {
    const items = [line('w-tee-01', 'M')];
    expect(cartReducer(items, { type: 'add', productId: 'w-tee-01', size: 'L' })).toHaveLength(2);
  });

  it('caps the quantity', () => {
    const items = [line('w-tee-01', 'M', MAX_QUANTITY)];
    const next = cartReducer(items, { type: 'add', productId: 'w-tee-01', size: 'M' });
    expect(next[0].quantity).toBe(MAX_QUANTITY);
  });

  it('sets the quantity, clamped to the limit', () => {
    const items = [line('w-tee-01', 'M')];
    const next = cartReducer(items, {
      type: 'setQuantity',
      productId: 'w-tee-01',
      size: 'M',
      quantity: 99,
    });
    expect(next[0].quantity).toBe(MAX_QUANTITY);
  });

  it('removes a line when the quantity is set to zero', () => {
    const items = [line('w-tee-01', 'M', 2)];
    expect(
      cartReducer(items, { type: 'setQuantity', productId: 'w-tee-01', size: 'M', quantity: 0 }),
    ).toEqual([]);
  });

  it('removes only the matching line', () => {
    const items = [line('w-tee-01', 'M'), line('w-tee-01', 'L')];
    expect(cartReducer(items, { type: 'remove', productId: 'w-tee-01', size: 'M' })).toEqual([
      line('w-tee-01', 'L'),
    ]);
  });

  it('clears and loads', () => {
    const items = [line('w-tee-01', 'M')];
    expect(cartReducer(items, { type: 'clear' })).toEqual([]);
    expect(cartReducer([], { type: 'load', items })).toEqual(items);
  });

  it('does not change the previous state', () => {
    const items = [line('w-tee-01', 'M')];
    cartReducer(items, { type: 'add', productId: 'w-tee-01', size: 'M' });
    expect(items).toEqual([line('w-tee-01', 'M')]);
  });
});

describe('cart totals', () => {
  it('counts every unit in the cart', () => {
    expect(cartCount([line('a', 'M', 2), line('b', 'L', 3)])).toBe(5);
  });

  it('prices lines from the catalogue and sums the subtotal', () => {
    // w-tee-01 costs 3250 and m-jog-01 costs 7450.
    const lines = resolveCartLines([line('w-tee-01', 'M', 2), line('m-jog-01', 'L')]);
    expect(lines.map((entry) => entry.total)).toEqual([6500, 7450]);
    expect(cartSubtotal(lines)).toBe(13950);
  });

  it('drops lines for products that no longer exist', () => {
    expect(resolveCartLines([line('gone', 'M')])).toEqual([]);
  });
});

describe('parseStoredCart', () => {
  it('returns an empty cart for missing or invalid JSON', () => {
    expect(parseStoredCart(null)).toEqual([]);
    expect(parseStoredCart('not json')).toEqual([]);
    expect(parseStoredCart('{"a":1}')).toEqual([]);
  });

  it('keeps valid lines and drops malformed ones', () => {
    const raw = JSON.stringify([
      { productId: 'w-tee-01', size: 'M', quantity: 2 },
      { productId: 5, size: 'M', quantity: 1 },
      { productId: 'w-tee-01', size: 'L', quantity: 'many' },
      { productId: 'w-tee-01', size: 'S', quantity: 0 },
      null,
    ]);
    expect(parseStoredCart(raw)).toEqual([line('w-tee-01', 'M', 2)]);
  });

  it('clamps stored quantities', () => {
    const raw = JSON.stringify([{ productId: 'w-tee-01', size: 'M', quantity: 500 }]);
    expect(parseStoredCart(raw)[0].quantity).toBe(MAX_QUANTITY);
  });
});
