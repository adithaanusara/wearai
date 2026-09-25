const STORAGE_KEY = 'wearai-checkout-key';

/** A random key such as 3f1c…: 8 to 64 letters, digits, `-` or `_`, which is what the API accepts. */
export function newIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // randomUUID needs a secure context; getRandomValues does not.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

/**
 * The key for the current checkout attempt. It is kept for the whole attempt, so a double click,
 * a retry after a slow network, or a reload all send the same key and can only create one order.
 */
export function getCheckoutKey(
  storage: Pick<Storage, 'getItem' | 'setItem'> = window.sessionStorage,
): string {
  try {
    const existing = storage.getItem(STORAGE_KEY);
    if (existing) return existing;
    const key = newIdempotencyKey();
    storage.setItem(STORAGE_KEY, key);
    return key;
  } catch {
    // Storage can be blocked; the key then lasts only for this call.
    return newIdempotencyKey();
  }
}

/** Forget the key once the attempt is over, so the next order gets a fresh one. */
export function clearCheckoutKey(
  storage: Pick<Storage, 'removeItem'> = window.sessionStorage,
): void {
  try {
    storage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to clear.
  }
}
