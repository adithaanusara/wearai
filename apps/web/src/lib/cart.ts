import { products } from '@/data/products';
import type { CartItem } from '@/types/cart';
import type { Product } from '@/types/product';

export const MAX_QUANTITY = 10;

export type CartAction =
  | { type: 'add'; productId: string; size: string }
  | { type: 'remove'; productId: string; size: string }
  | { type: 'setQuantity'; productId: string; size: string; quantity: number }
  | { type: 'clear' }
  | { type: 'load'; items: CartItem[] };

const isSameLine = (item: CartItem, productId: string, size: string) =>
  item.productId === productId && item.size === size;

const clampQuantity = (quantity: number) =>
  Math.min(MAX_QUANTITY, Math.max(0, Math.floor(quantity)));

export function cartReducer(items: CartItem[], action: CartAction): CartItem[] {
  switch (action.type) {
    case 'add': {
      const existing = items.find((item) => isSameLine(item, action.productId, action.size));
      if (!existing)
        return [...items, { productId: action.productId, size: action.size, quantity: 1 }];
      return items.map((item) =>
        item === existing ? { ...item, quantity: clampQuantity(item.quantity + 1) } : item,
      );
    }
    case 'setQuantity': {
      const quantity = clampQuantity(action.quantity);
      if (quantity === 0)
        return items.filter((item) => !isSameLine(item, action.productId, action.size));
      return items.map((item) =>
        isSameLine(item, action.productId, action.size) ? { ...item, quantity } : item,
      );
    }
    case 'remove':
      return items.filter((item) => !isSameLine(item, action.productId, action.size));
    case 'clear':
      return [];
    case 'load':
      return action.items;
  }
}

export function cartCount(items: CartItem[]): number {
  return items.reduce((total, item) => total + item.quantity, 0);
}

export interface CartLine {
  item: CartItem;
  product: Product;
  /** Price of this line in whole LKR. */
  total: number;
}

/** Joins cart items with the current product data, dropping products that no longer exist. */
export function resolveCartLines(items: CartItem[]): CartLine[] {
  return items.flatMap((item) => {
    const product = products.find((candidate) => candidate.id === item.productId);
    return product ? [{ item, product, total: product.price * item.quantity }] : [];
  });
}

export function cartSubtotal(lines: CartLine[]): number {
  return lines.reduce((total, line) => total + line.total, 0);
}

/** Reads saved cart JSON, keeping only well-formed lines so bad storage never breaks the site. */
export function parseStoredCart(raw: string | null): CartItem[] {
  if (!raw) return [];
  try {
    const data: unknown = JSON.parse(raw);
    if (!Array.isArray(data)) return [];
    return data.flatMap((entry) => {
      if (typeof entry !== 'object' || entry === null) return [];
      const { productId, size, quantity } = entry as Record<string, unknown>;
      if (typeof productId !== 'string' || typeof size !== 'string') return [];
      if (typeof quantity !== 'number' || !Number.isFinite(quantity)) return [];
      const clamped = clampQuantity(quantity);
      return clamped > 0 ? [{ productId, size, quantity: clamped }] : [];
    });
  } catch {
    return [];
  }
}
