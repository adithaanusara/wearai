import { cartReducer, parseStoredCart, type CartAction } from '@/lib/cart';
import type { CartItem } from '@/types/cart';

const STORAGE_KEY = 'wearai-cart';

const emptyCart: CartItem[] = [];
const listeners = new Set<() => void>();

// The snapshot must keep the same reference until the data changes, or React re-renders forever.
let cache: { raw: string | null; items: CartItem[] } = { raw: null, items: emptyCart };
let storageWorks = true;

function readStorage(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function getCartSnapshot(): CartItem[] {
  if (!storageWorks) return cache.items;
  const raw = readStorage();
  if (raw !== cache.raw) cache = { raw, items: raw ? parseStoredCart(raw) : emptyCart };
  return cache.items;
}

/** The server has no saved cart, so the first client render matches it and nothing mismatches. */
export function getServerCartSnapshot(): CartItem[] {
  return emptyCart;
}

export function subscribeToCart(listener: () => void): () => void {
  listeners.add(listener);
  // The storage event fires when another tab changes the cart.
  window.addEventListener('storage', listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener('storage', listener);
  };
}

export function dispatchCart(action: CartAction): void {
  const items = cartReducer(getCartSnapshot(), action);
  const raw = JSON.stringify(items);
  try {
    window.localStorage.setItem(STORAGE_KEY, raw);
  } catch {
    // Storage can be blocked (private mode); the cart then lives in memory for this visit.
    storageWorks = false;
  }
  cache = { raw, items };
  listeners.forEach((listener) => listener());
}
