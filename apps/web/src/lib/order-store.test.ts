import { describe, expect, it } from 'vitest';
import { createOrderReference } from '@/lib/order-store';

describe('createOrderReference', () => {
  it('starts with WA- and uses only uppercase letters and digits', () => {
    expect(createOrderReference()).toMatch(/^WA-[A-Z0-9]+$/);
  });

  it('is derived from the time, so later orders sort after earlier ones', () => {
    const earlier = createOrderReference(1_000_000_000_000);
    const later = createOrderReference(2_000_000_000_000);
    expect(later.slice(3, -2) > earlier.slice(3, -2)).toBe(true);
  });
});
