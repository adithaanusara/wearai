import { describe, expect, it } from 'vitest';
import { clearCheckoutKey, getCheckoutKey, newIdempotencyKey } from '@/lib/idempotency';

function fakeStorage() {
  const data = new Map<string, string>();
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => void data.set(key, value),
    removeItem: (key: string) => void data.delete(key),
    size: () => data.size,
  };
}

describe('newIdempotencyKey', () => {
  it('produces keys the API accepts', () => {
    for (let i = 0; i < 20; i++) expect(newIdempotencyKey()).toMatch(/^[A-Za-z0-9_-]{8,64}$/);
  });

  it('is different every time', () => {
    expect(new Set(Array.from({ length: 50 }, newIdempotencyKey)).size).toBe(50);
  });
});

describe('getCheckoutKey', () => {
  it('returns the same key for the whole attempt, so retries cannot create a second order', () => {
    const storage = fakeStorage();

    expect(getCheckoutKey(storage)).toBe(getCheckoutKey(storage));
    expect(storage.size()).toBe(1);
  });

  it('gives a new key after the attempt is cleared', () => {
    const storage = fakeStorage();
    const first = getCheckoutKey(storage);

    clearCheckoutKey(storage);

    expect(getCheckoutKey(storage)).not.toBe(first);
  });

  it('still works when storage is blocked', () => {
    const blocked = {
      getItem: () => {
        throw new Error('blocked');
      },
      setItem: () => {
        throw new Error('blocked');
      },
      removeItem: () => {
        throw new Error('blocked');
      },
    };

    expect(getCheckoutKey(blocked)).toMatch(/^[A-Za-z0-9_-]{8,64}$/);
    expect(() => clearCheckoutKey(blocked)).not.toThrow();
  });
});
