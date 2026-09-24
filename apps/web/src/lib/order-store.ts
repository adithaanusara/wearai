import type { PlacedOrder } from '@/types/order';

const STORAGE_KEY = 'wearai-last-order';

/** A short, readable reference such as WA-LM3K9Q2X. The API will issue real order numbers later. */
export function createOrderReference(now: number = Date.now()): string {
  const random = Math.random().toString(36).slice(2, 4).toUpperCase();
  return `WA-${now.toString(36).toUpperCase()}${random}`;
}

/** Keeps the last order for the confirmation page until the real API stores orders. */
export function saveOrder(order: PlacedOrder): void {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(order));
  } catch {
    // The confirmation page still works without the details.
  }
}

export function readOrder(reference: string): PlacedOrder | null {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const order = JSON.parse(raw) as PlacedOrder;
    return order.reference === reference && Array.isArray(order.lines) ? order : null;
  } catch {
    return null;
  }
}
