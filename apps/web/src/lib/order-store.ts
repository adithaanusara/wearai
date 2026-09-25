import type { Order } from '@/types/api';

const STORAGE_KEY = 'wearai-last-order';

/**
 * Keeps the order the server returned so the confirmation page can show it. Guests cannot look an
 * order up later, so this handover is how they see it.
 */
export function saveOrder(order: Order): void {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(order));
  } catch {
    // The confirmation page still works without the details.
  }
}

export function readOrder(reference: string): Order | null {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const order = JSON.parse(raw) as Order;
    return order.reference === reference && Array.isArray(order.lines) ? order : null;
  } catch {
    return null;
  }
}
