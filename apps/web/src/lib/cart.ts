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

export type CartProblem = 'unavailable' | 'size';

/** What is known about one product while the cart is being displayed. */
export type ProductLookup =
  | { state: 'loading' }
  | { state: 'error' }
  | { state: 'found'; product: Product }
  | { state: 'missing' };

export interface CartLine {
  item: CartItem;
  /** Whether the product details have loaded, failed to load, or are still loading. */
  state: 'loading' | 'error' | 'ready';
  /** Null until loaded, and when the product no longer exists. */
  product: Product | null;
  /** Why a loaded line cannot be ordered, if it cannot. */
  problem: CartProblem | null;
  /** Price of this line in whole LKR, for display. It is 0 unless the line can be ordered. */
  total: number;
}

/**
 * Joins cart items with product details. A product that is gone, or a size it no longer has, is
 * flagged instead of dropped, so the shopper can see it and remove it.
 */
export function buildCartLines(
  items: CartItem[],
  lookup: (productId: string) => ProductLookup,
): CartLine[] {
  return items.map((item): CartLine => {
    const found = lookup(item.productId);
    switch (found.state) {
      case 'loading':
        return { item, state: 'loading', product: null, problem: null, total: 0 };
      case 'error':
        return { item, state: 'error', product: null, problem: null, total: 0 };
      case 'missing':
        return { item, state: 'ready', product: null, problem: 'unavailable', total: 0 };
      case 'found': {
        const { product } = found;
        if (!product.sizes.includes(item.size)) {
          return { item, state: 'ready', product, problem: 'size', total: 0 };
        }
        return {
          item,
          state: 'ready',
          product,
          problem: null,
          total: product.price * item.quantity,
        };
      }
    }
  });
}

/** The subtotal of the lines that can be ordered. The server works out the real one. */
export function cartSubtotal(lines: CartLine[]): number {
  return lines.reduce((total, line) => total + line.total, 0);
}

export function hasCartProblems(lines: CartLine[]): boolean {
  return lines.some((line) => line.problem !== null);
}

export type CartStatus = 'empty' | 'loading' | 'error' | 'ready';

/** An error wins over loading, so a failure is never hidden behind a spinner. */
export function cartStatus(lines: CartLine[]): CartStatus {
  if (lines.length === 0) return 'empty';
  if (lines.some((line) => line.state === 'error')) return 'error';
  if (lines.some((line) => line.state === 'loading')) return 'loading';
  return 'ready';
}

/** True when every line has loaded and can be ordered. */
export function canCheckout(lines: CartLine[]): boolean {
  return cartStatus(lines) === 'ready' && !hasCartProblems(lines);
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

/** Picks products to suggest from a list, leaving out styles already in the cart. */
export function pickRecommendations(
  candidates: Product[],
  lines: CartLine[],
  limit = 2,
): Product[] {
  const seen = new Set(lines.flatMap((line) => (line.product ? [line.product.styleId] : [])));
  const picked: Product[] = [];
  for (const product of candidates) {
    if (seen.has(product.styleId)) continue;
    seen.add(product.styleId);
    picked.push(product);
    if (picked.length === limit) break;
  }
  return picked;
}
